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
	privacy_consent: bool = Field(default=False)

	@staticmethod
	def validate_password_strength(password: str) -> str | None:
		"""Returns error message if password is weak, None if strong."""
		if len(password) < 8:
			return "Password must be at least 8 characters"
		if not any(c.isupper() for c in password):
			return "Password must contain at least one uppercase letter"
		if not any(c.islower() for c in password):
			return "Password must contain at least one lowercase letter"
		if not any(c.isdigit() for c in password):
			return "Password must contain at least one digit"
		if not any(c in "!@#$%^&*()_+-=[]{}|;:',.<>?/`~" for c in password):
			return "Password must contain at least one special character"
		return None


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


def _send_email(to: str, subject: str, html_body: str, text_body: str) -> bool:
	"""Send an HTML email via SMTP."""
	if not all([config.SMTP_HOST, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.SMTP_FROM_EMAIL]):
		logger.warning("SMTP not configured — skipping email send")
		return False
	try:
		msg = EmailMessage()
		msg["Subject"] = subject
		msg["From"] = f"PresenterAI <{config.SMTP_FROM_EMAIL}>"
		msg["To"] = to
		msg.set_content(text_body)
		msg.add_alternative(html_body, subtype="html")

		with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
			if config.SMTP_USE_TLS:
				server.starttls()
			server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
			server.send_message(msg)
		logger.info(f"Email sent to {to}: {subject}")
		return True
	except Exception as e:
		logger.error(f"SMTP send failed: {type(e).__name__}: {e}")
		return False


_EMAIL_WRAPPER = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
.container{{max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.header{{background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px 40px;text-align:center}}
.header img{{width:48px;height:48px;border-radius:12px;margin-bottom:10px}}
.header h1{{color:#fff;margin:0;font-size:26px;font-weight:700;letter-spacing:-.5px}}
.header p{{color:rgba(255,255,255,.85);margin:8px 0 0;font-size:14px}}
.body{{padding:36px 40px}}
.body h2{{color:#1e293b;font-size:20px;margin:0 0 12px}}
.body p{{color:#475569;font-size:15px;line-height:1.7;margin:0 0 16px}}
.otp-box{{background:#f1f5f9;border:2px dashed #6366f1;border-radius:10px;text-align:center;padding:20px;margin:24px 0}}
.otp-code{{font-size:36px;font-weight:800;color:#6366f1;letter-spacing:8px;font-family:'Courier New',monospace}}
.otp-label{{font-size:12px;color:#94a3b8;margin-top:6px;text-transform:uppercase;letter-spacing:1px}}
.cta{{display:inline-block;background:#6366f1;color:#fff!important;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:600;font-size:15px;margin:8px 0 24px}}
.cta:hover{{background:#4f46e5}}
.tip{{background:#f8fafc;border-left:3px solid #6366f1;padding:14px 18px;border-radius:0 8px 8px 0;margin:20px 0}}
.tip strong{{color:#1e293b;font-size:13px}}
.tip p{{color:#64748b;font-size:13px;margin:4px 0 0}}
.footer{{background:#f8fafc;padding:24px 40px;text-align:center;border-top:1px solid #e2e8f0}}
.footer p{{color:#94a3b8;font-size:12px;margin:0 0 4px;line-height:1.6}}
.footer a{{color:#6366f1;text-decoration:none}}
.social{{margin:12px 0 0}}
.social a{{color:#94a3b8;text-decoration:none;margin:0 8px;font-size:12px}}
</style></head><body>
<div class="container">
<div class="header"><img src="https://ai-presentation-avatar.vercel.app/logo.svg" alt="PresenterAI"><h1>Presenter AI</h1><p>DOCUMENT TO PRESENTER</p></div>
<div class="body">{content}</div>
<div class="footer">
<p>PresenterAI — AI-Powered Presentation Avatars</p>
<p><a href="https://ai-presentation-avatar.vercel.app">ai-presentation-avatar.vercel.app</a></p>
<div class="social">
<a href="https://ai-presentation-avatar.vercel.app">Website</a> &bull;
<a href="https://github.com/rohitpanwar806-git/AI-Presentation-">GitHub</a>
</div>
</div>
</div></body></html>"""


def _send_verification_email(email: str, code: str) -> bool:
	html_content = f"""
<h2>Verify your email</h2>
<p>Welcome to <strong>PresenterAI</strong>! Enter the code below to verify your email and start creating AI-hosted presentations.</p>
<div class="otp-box">
  <div class="otp-code">{code}</div>
  <div class="otp-label">Verification Code</div>
</div>
<p>This code expires in <strong>{config.VERIFICATION_CODE_EXPIRE_MINUTES} minutes</strong>.</p>
<div class="tip">
  <strong>What's next?</strong>
  <p>Upload a document, pick an avatar, and generate a presentation — all in under a minute.</p>
</div>
<p style="color:#94a3b8;font-size:12px;margin-top:24px">If you didn't create an account on PresenterAI, you can safely ignore this email.</p>
"""
	text = f"Your PresenterAI verification code is: {code}\nThis code expires in {config.VERIFICATION_CODE_EXPIRE_MINUTES} minutes."
	return _send_email(email, "Your PresenterAI Verification Code", _EMAIL_WRAPPER.format(content=html_content), text)


def _send_welcome_email(email: str, name: str) -> bool:
	html_content = f"""
<h2>Welcome to PresenterAI, {name}!</h2>
<p>Your email is verified and your account is ready. Here's everything you need to create your first AI presentation:</p>

<p style="text-align:center"><a class="cta" href="https://ai-presentation-avatar.vercel.app">Create Your First Presentation &rarr;</a></p>

<div class="tip">
  <strong>Quick Start</strong>
  <p>Upload a PDF, PPTX, or DOCX &rarr; Pick an avatar &rarr; Generate a natural AI-hosted presentation with voice narration in seconds.</p>
</div>

<h2 style="font-size:16px;margin-top:28px">What you can do</h2>
<p><strong>🎙️ AI Avatar Narration</strong> — Your presentation is narrated by a lifelike AI avatar that speaks naturally, like a real teacher.</p>
<p><strong>📝 Smart Quiz Generation</strong> — Auto-generate quizzes from your content to test understanding.</p>
<p><strong>💬 Q&amp;A with AI</strong> — Viewers can ask questions about the content and get instant answers.</p>
<p><strong>🔗 Share Instantly</strong> — Generate a link and share with anyone — no login required for viewers.</p>

<div class="tip">
  <strong>Pro Tip</strong>
  <p>Use "Use Uploaded Deck" mode to preserve your original slides exactly as they are, or "Generate New" to let AI create fresh slides from your document.</p>
</div>

<p>Excited to see what you'll create,<br><strong>The PresenterAI Team</strong></p>
"""
	text = f"Welcome to PresenterAI, {name}! Your account is verified. Start creating at https://ai-presentation-avatar.vercel.app"
	return _send_email(email, f"Welcome to PresenterAI, {name}! 🎉", _EMAIL_WRAPPER.format(content=html_content), text)


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
	# DPDP Act: require explicit privacy consent
	if not payload.privacy_consent:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must accept the Privacy Policy to register")

	# Enforce strong password
	pw_error = RegisterRequest.validate_password_strength(payload.password)
	if pw_error:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pw_error)

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
			privacy_consent=True,
			privacy_consent_at=datetime.now(timezone.utc),
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
@limiter.limit("10/minute")
async def verify_email(request: Request, payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
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

	# Send welcome email (fire-and-forget)
	name = (user.first_name or user.email.split("@")[0]).strip()
	try:
		_send_welcome_email(user.email, name)
	except Exception:
		pass

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

	# Account lockout check
	now = datetime.now(timezone.utc)
	if user.locked_until and user.locked_until > now:
		remaining = int((user.locked_until - now).total_seconds() / 60) + 1
		raise HTTPException(
			status_code=status.HTTP_429_TOO_MANY_REQUESTS,
			detail=f"Account temporarily locked due to too many failed attempts. Try again in {remaining} minutes.",
		)

	if not verify_password(payload.password, user.password_hash):
		# Increment failed attempts
		user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
		if user.failed_login_attempts >= config.MAX_LOGIN_ATTEMPTS:
			user.locked_until = now + timedelta(minutes=config.LOGIN_LOCKOUT_MINUTES)
			user.failed_login_attempts = 0
			db.commit()
			raise HTTPException(
				status_code=status.HTTP_429_TOO_MANY_REQUESTS,
				detail=f"Account locked for {config.LOGIN_LOCKOUT_MINUTES} minutes due to too many failed attempts.",
			)
		db.commit()
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

	if not user.is_verified:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email first")

	# Reset failed attempts on successful login
	user.failed_login_attempts = 0
	user.locked_until = None
	user.last_login_at = now
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


# ==================== DPDP ACT 2023 COMPLIANCE ====================

@router.get("/privacy/my-data")
async def export_my_data(
	current_user: User = Depends(_get_current_user),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	"""DPDP Act Section 11: Right to access personal data. Export all user data."""
	from backend.db.models import Presentation, SupportTicket

	# Gather all user data
	presentations = db.query(Presentation).filter(Presentation.user_id == current_user.id).all()
	tickets = db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).all()

	return {
		"personal_info": {
			"email": current_user.email,
			"first_name": current_user.first_name,
			"last_name": current_user.last_name,
			"gender": current_user.gender,
			"bio": current_user.bio,
			"login_provider": current_user.login_provider,
			"created_at": current_user.created_at.isoformat() if current_user.created_at else None,
			"last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
			"privacy_consent": current_user.privacy_consent,
			"privacy_consent_at": current_user.privacy_consent_at.isoformat() if current_user.privacy_consent_at else None,
		},
		"presentations": [
			{"title": p.title, "filename": p.filename, "created_at": p.created_at.isoformat() if p.created_at else None}
			for p in presentations
		],
		"support_tickets": [
			{"subject": t.subject, "category": t.category, "status": t.status, "created_at": t.created_at.isoformat() if t.created_at else None}
			for t in tickets
		],
		"data_export_date": datetime.now(timezone.utc).isoformat(),
		"note": "This export contains all personal data stored by PresenterAI as required under India's Digital Personal Data Protection Act 2023.",
	}


@router.post("/privacy/delete-account")
async def request_account_deletion(
	current_user: User = Depends(_get_current_user),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	"""DPDP Act Section 12: Right to erasure. Request account and data deletion."""
	from backend.db.models import Presentation, SupportTicket

	# Delete all user presentations
	db.query(Presentation).filter(Presentation.user_id == current_user.id).delete()
	# Delete all user tickets
	db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).delete()
	# Delete the user account
	db.delete(current_user)
	db.commit()

	return {
		"status": "deleted",
		"message": "Your account and all associated data have been permanently deleted as per DPDP Act 2023.",
	}


@router.get("/privacy/policy")
async def privacy_policy() -> dict[str, Any]:
	"""Return privacy policy summary for DPDP Act compliance."""
	return {
		"policy_version": "1.0",
		"effective_date": "2026-05-26",
		"data_fiduciary": "PresenterAI",
		"data_collected": [
			"Email address (for authentication)",
			"Name and gender (for personalization)",
			"Uploaded documents (for presentation generation)",
			"Usage analytics (presentations viewed, created)",
		],
		"purpose": [
			"User authentication and account management",
			"AI-powered presentation generation from uploaded documents",
			"Voice synthesis and avatar rendering",
			"Customer support via help centre",
		],
		"data_retention": "Data is retained until you delete your account or request erasure",
		"data_sharing": "We do not sell or share personal data with third parties except for essential service providers (Google Cloud, ElevenLabs for voice synthesis)",
		"user_rights": [
			"Right to access and download all your personal data",
			"Right to permanent erasure and account deletion",
			"Right to withdraw consent at any time",
			"Right to lodge a grievance with the Data Protection Board of India",
		],
		"grievance_officer": "Contact us via the Help Centre or email the support address",
		"applicable_law": "Digital Personal Data Protection Act, 2023 (India)",
	}


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


# ──────────────── Account Settings Endpoints ────────────────

class ChangePasswordRequest(BaseModel):
	current_password: str
	new_password: str = Field(min_length=8, max_length=128)


class ChangeEmailRequest(BaseModel):
	new_email: EmailStr
	password: str


@router.post("/change-password")
async def change_password(
	payload: ChangePasswordRequest,
	db: Session = Depends(get_db),
	current_user: User = Depends(_get_current_user),
) -> dict[str, str]:
	if not current_user.password_hash:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account uses Google sign-in. Password change not available.")
	if not verify_password(payload.current_password, current_user.password_hash):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
	current_user.password_hash = hash_password(payload.new_password)
	db.commit()
	return {"status": "ok", "message": "Password changed successfully"}


@router.post("/change-email")
async def change_email(
	payload: ChangeEmailRequest,
	db: Session = Depends(get_db),
	current_user: User = Depends(_get_current_user),
) -> dict[str, Any]:
	if not current_user.password_hash:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account uses Google sign-in. Email change not available.")
	if not verify_password(payload.password, current_user.password_hash):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect")
	new_email = str(payload.new_email).strip().lower()
	if db.query(User).filter(User.email == new_email).first():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
	current_user.email = new_email
	db.commit()
	db.refresh(current_user)
	return {"status": "ok", "message": "Email updated successfully", "user": _serialize_user(current_user)}


# ──────────────── Support Ticket Endpoints ────────────────

class CreateTicketRequest(BaseModel):
	subject: str = Field(min_length=5, max_length=300)
	category: str = Field(default="general", max_length=50)
	description: str = Field(min_length=10, max_length=5000)


class ReplyTicketRequest(BaseModel):
	reply: str = Field(min_length=1, max_length=5000)
	status: str = Field(default="resolved", max_length=30)


def _serialize_ticket(ticket) -> dict[str, Any]:
	return {
		"id": ticket.id,
		"user_id": ticket.user_id,
		"subject": ticket.subject,
		"category": ticket.category,
		"description": ticket.description,
		"status": ticket.status,
		"admin_reply": ticket.admin_reply,
		"created_at": ticket.created_at.isoformat() if ticket.created_at else None,
		"updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
	}


@router.post("/support/tickets")
async def create_ticket(
	payload: CreateTicketRequest,
	db: Session = Depends(get_db),
	current_user: User = Depends(_get_current_user),
) -> dict[str, Any]:
	from backend.db.models import SupportTicket
	ticket = SupportTicket(
		user_id=current_user.id,
		subject=payload.subject.strip(),
		category=payload.category.strip(),
		description=payload.description.strip(),
		status="open",
	)
	db.add(ticket)
	db.commit()
	db.refresh(ticket)
	return _serialize_ticket(ticket)


@router.get("/support/tickets")
async def list_my_tickets(
	db: Session = Depends(get_db),
	current_user: User = Depends(_get_current_user),
) -> dict[str, Any]:
	from backend.db.models import SupportTicket
	tickets = db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).order_by(SupportTicket.created_at.desc()).all()
	return {"items": [_serialize_ticket(t) for t in tickets]}


@router.get("/admin/tickets")
async def list_all_tickets(
	_: User = Depends(_require_admin),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	from backend.db.models import SupportTicket
	tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).all()
	# Attach user email to each ticket
	user_ids = {t.user_id for t in tickets}
	users = {u.id: u.email for u in db.query(User).filter(User.id.in_(user_ids)).all()}
	items = []
	for t in tickets:
		d = _serialize_ticket(t)
		d["user_email"] = users.get(t.user_id, "unknown")
		items.append(d)
	return {"total": len(items), "open": sum(1 for t in tickets if t.status == "open"), "items": items}


@router.post("/admin/tickets/{ticket_id}/reply")
async def reply_to_ticket(
	ticket_id: int,
	payload: ReplyTicketRequest,
	_: User = Depends(_require_admin),
	db: Session = Depends(get_db),
) -> dict[str, Any]:
	from backend.db.models import SupportTicket
	ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
	if not ticket:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
	ticket.admin_reply = payload.reply.strip()
	ticket.status = payload.status.strip()
	db.commit()
	db.refresh(ticket)
	return _serialize_ticket(ticket)
