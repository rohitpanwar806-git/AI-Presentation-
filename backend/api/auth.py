"""Authentication and admin endpoints."""

import logging
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import random
import smtplib
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import config
from backend.core.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.db.database import get_db
from backend.db.models import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class RegisterRequest(BaseModel):
	first_name: str = Field(min_length=1, max_length=100)
	last_name: str = Field(min_length=1, max_length=100)
	gender: str = Field(min_length=1, max_length=30)
	email: EmailStr
	password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
	email: EmailStr
	code: str = Field(min_length=4, max_length=10)


class LoginRequest(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8, max_length=128)


class ResendCodeRequest(BaseModel):
	email: EmailStr


class GoogleAuthRequest(BaseModel):
	credential: str
	mode: str = "signin"


class ProfileUpdateRequest(BaseModel):
	first_name: str | None = None
	last_name: str | None = None
	bio: str | None = None
	avatar_url: str | None = None
	gender: str | None = None


def _extract_bearer_token(authorization: str | None) -> str:
	if not authorization:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
	parts = authorization.split(" ", 1)
	if len(parts) != 2 or parts[0].lower() != "bearer":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
	return parts[1].strip()


def _serialize_user(user: User) -> dict[str, Any]:
	return {
		"id": user.id,
		"email": user.email,
		"first_name": user.first_name,
		"last_name": user.last_name,
		"name": " ".join(part for part in [user.first_name or "", user.last_name or ""] if part).strip()
		or user.email.split("@")[0],
		"gender": user.gender,
		"avatar_url": user.avatar_url,
		"bio": user.bio or "",
		"is_verified": user.is_verified,
		"is_admin": user.is_admin,
		"is_active": user.is_active,
		"login_provider": user.login_provider,
		"created_at": user.created_at.isoformat() if user.created_at else None,
		"last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
	}


def _create_auth_response(user: User, is_new_user: bool = False) -> dict[str, Any]:
	access_token = create_access_token(
		subject=user.email,
		extra={
			"name": _serialize_user(user)["name"],
			"is_admin": user.is_admin,
			"login_provider": user.login_provider,
		},
	)
	return {
		"access_token": access_token,
		"token_type": "bearer",
		"is_new_user": is_new_user,
		"user": _serialize_user(user),
	}


def _generate_verification_code() -> str:
	return f"{random.randint(100000, 999999)}"


def _send_verification_email(email: str, code: str) -> bool:
	if not all([config.SMTP_HOST, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.SMTP_FROM_EMAIL]):
		logger.warning(f"SMTP not configured: HOST={bool(config.SMTP_HOST)}, USER={bool(config.SMTP_USERNAME)}, PASS={bool(config.SMTP_PASSWORD)}, FROM={bool(config.SMTP_FROM_EMAIL)}")
		return False

	try:
		msg = EmailMessage()
		msg["Subject"] = "AI Presentation Avatar - Verify your email"
		msg["From"] = config.SMTP_FROM_EMAIL
		msg["To"] = email
		msg.set_content(
			"Your verification code is: "
			f"{code}\n\n"
			f"This code expires in {config.VERIFICATION_CODE_EXPIRE_MINUTES} minutes."
		)

		with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
			if config.SMTP_USE_TLS:
				server.starttls()
			server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
			server.send_message(msg)

		logger.info(f"Verification email sent to {email}")
		return True
	except Exception as e:
		logger.error(f"SMTP send failed: {type(e).__name__}: {e}")
		return False


def _get_current_user(
	authorization: str | None = Header(default=None),
	db: Session = Depends(get_db),
) -> User:
	token = _extract_bearer_token(authorization)
	try:
		payload = decode_access_token(token)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

	email = (payload.get("sub") or "").strip().lower()
	if not email:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

	user = db.query(User).filter(User.email == email).first()
	if not user or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
	return user


def _require_admin(user: User = Depends(_get_current_user)) -> User:
	if not user.is_admin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
	return user


@router.get("/google/client-id")
async def google_client_id() -> dict[str, Any]:
	return {
		"configured": bool(config.GOOGLE_CLIENT_ID),
		"client_id": config.GOOGLE_CLIENT_ID,
	}


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
	email = str(payload.email).strip().lower()
	existing = db.query(User).filter(User.email == email).first()

	code = _generate_verification_code()
	expires_at = datetime.now(timezone.utc) + timedelta(minutes=config.VERIFICATION_CODE_EXPIRE_MINUTES)

	if existing and existing.is_verified:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists. Please sign in.")

	if existing:
		user = existing
		user.first_name = payload.first_name.strip()
		user.last_name = payload.last_name.strip()
		user.gender = payload.gender.strip()
		user.password_hash = hash_password(payload.password)
		user.login_provider = "email"
		user.verification_code = code
		user.verification_expires_at = expires_at
	else:
		user = User(
			email=email,
			first_name=payload.first_name.strip(),
			last_name=payload.last_name.strip(),
			gender=payload.gender.strip(),
			password_hash=hash_password(payload.password),
			login_provider="email",
			is_verified=False,
			is_active=True,
			is_admin=(config.ADMIN_EMAIL == email),
			verification_code=code,
			verification_expires_at=expires_at,
		)
		db.add(user)

	db.commit()

	email_sent = False
	try:
		email_sent = _send_verification_email(email, code)
	except Exception:
		email_sent = False

	return {
		"status": "verification_required",
		"email": email,
		"email_sent": email_sent,
		"message": "Verification code sent to your email."
		if email_sent
		else "Verification code generated, but SMTP is not configured on backend.",
	}


@router.post("/resend-code")
@limiter.limit("3/minute")
async def resend_code(request: Request, payload: ResendCodeRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
	email = str(payload.email).strip().lower()
	user = db.query(User).filter(User.email == email).first()
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	if user.is_verified:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")

	user.verification_code = _generate_verification_code()
	user.verification_expires_at = datetime.now(timezone.utc) + timedelta(
		minutes=config.VERIFICATION_CODE_EXPIRE_MINUTES
	)
	db.commit()

	email_sent = False
	try:
		email_sent = _send_verification_email(user.email, user.verification_code)
	except Exception:
		email_sent = False

	return {
		"status": "resent",
		"email": user.email,
		"email_sent": email_sent,
	}


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
	email = str(payload.email).strip().lower()
	user = db.query(User).filter(User.email == email).first()
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	if user.is_verified:
		return _create_auth_response(user, is_new_user=False)

	now = datetime.now(timezone.utc)
	if not user.verification_code or user.verification_code != payload.code.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
	if not user.verification_expires_at or user.verification_expires_at < now:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")

	user.is_verified = True
	user.verification_code = None
	user.verification_expires_at = None
	user.last_login_at = now

	if config.ADMIN_EMAIL and user.email == config.ADMIN_EMAIL:
		user.is_admin = True

	db.commit()
	db.refresh(user)
	return _create_auth_response(user, is_new_user=True)


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
	email = str(payload.email).strip().lower()
	user = db.query(User).filter(User.email == email).first()

	if not user or user.login_provider != "email":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
	if not user.is_active:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
	if not verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
	if not user.is_verified:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email first")

	user.last_login_at = datetime.now(timezone.utc)
	db.commit()
	db.refresh(user)

	return _create_auth_response(user, is_new_user=False)


@router.post("/google")
@limiter.limit("10/minute")
async def google_auth(request: Request, payload: GoogleAuthRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
	if not config.GOOGLE_CLIENT_ID:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Google sign-in is not configured on the backend",
		)

	try:
		token_info = id_token.verify_oauth2_token(
			payload.credential,
			google_requests.Request(),
			config.GOOGLE_CLIENT_ID,
		)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential") from exc

	email = (token_info.get("email") or "").strip().lower()
	if not email:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account email not available")

	user = db.query(User).filter(User.email == email).first()
	is_new_user = user is None

	if user and not user.is_active:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

	if not user:
		user = User(
			email=email,
			first_name=(token_info.get("given_name") or token_info.get("name") or "").strip() or None,
			last_name=(token_info.get("family_name") or "").strip() or None,
			login_provider="google",
			is_verified=True,
			is_active=True,
			is_admin=(config.ADMIN_EMAIL == email),
			avatar_url=token_info.get("picture"),
			verification_code=None,
			verification_expires_at=None,
			last_login_at=datetime.now(timezone.utc),
		)
		db.add(user)
	else:
		if not user.first_name:
			user.first_name = (token_info.get("given_name") or token_info.get("name") or "").strip() or user.first_name
		if not user.last_name:
			user.last_name = (token_info.get("family_name") or "").strip() or user.last_name
		if token_info.get("picture"):
			user.avatar_url = token_info.get("picture")
		user.login_provider = "google"
		user.is_verified = True
		user.last_login_at = datetime.now(timezone.utc)

	db.commit()
	db.refresh(user)

	return _create_auth_response(user, is_new_user=is_new_user)


@router.get("/profile")
async def get_profile(current_user: User = Depends(_get_current_user)) -> dict[str, Any]:
	return _serialize_user(current_user)


@router.put("/profile")
async def update_profile(
	payload: ProfileUpdateRequest,
	db: Session = Depends(get_db),
	current_user: User = Depends(_get_current_user),
) -> dict[str, Any]:
	if payload.first_name is not None:
		current_user.first_name = payload.first_name.strip() or None
	if payload.last_name is not None:
		current_user.last_name = payload.last_name.strip() or None
	if payload.gender is not None:
		current_user.gender = payload.gender.strip() or None
	if payload.bio is not None:
		current_user.bio = payload.bio.strip()
	if payload.avatar_url is not None:
		current_user.avatar_url = payload.avatar_url.strip() or None

	db.commit()
	db.refresh(current_user)
	return _serialize_user(current_user)


@router.get("/admin/users")
async def list_users(
	_: User = Depends(_require_admin),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	users = db.query(User).order_by(User.created_at.desc()).all()
	return {
		"total": len(users),
		"verified": db.query(func.count(User.id)).filter(User.is_verified.is_(True)).scalar() or 0,
		"admins": db.query(func.count(User.id)).filter(User.is_admin.is_(True)).scalar() or 0,
		"items": [_serialize_user(user) for user in users],
	}


@router.post("/admin/users/{user_id}/toggle-admin")
async def toggle_admin(
	user_id: int,
	admin_user: User = Depends(_require_admin),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	user = db.query(User).filter(User.id == user_id).first()
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	if user.id == admin_user.id and user.is_admin:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove your own admin access")

	user.is_admin = not user.is_admin
	db.commit()
	db.refresh(user)
	return _serialize_user(user)


@router.post("/admin/users/{user_id}/toggle-active")
async def toggle_active(
	user_id: int,
	admin_user: User = Depends(_require_admin),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	user = db.query(User).filter(User.id == user_id).first()
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	if user.id == admin_user.id and user.is_active:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot disable your own account")

	user.is_active = not user.is_active
	db.commit()
	db.refresh(user)
	return _serialize_user(user)


@router.post("/logout")
async def logout() -> dict[str, str]:
	return {"status": "ok"}
