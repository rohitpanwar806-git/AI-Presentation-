"""
Security Utilities
- Password hashing
- Token generation/verification
- JWT handling
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend import config


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, expires_minutes: int | None = None, extra: dict[str, Any] | None = None) -> str:
	"""Create a signed JWT access token."""
	ttl_minutes = expires_minutes or config.ACCESS_TOKEN_EXPIRE_MINUTES
	expire = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
	payload: dict[str, Any] = {"sub": subject, "exp": expire}
	if extra:
		payload.update(extra)
	return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
	"""Decode and validate a JWT access token."""
	try:
		return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
	except JWTError as exc:
		raise ValueError("Invalid or expired token") from exc


def hash_password(password: str) -> str:
	"""Hash password using bcrypt."""
	return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
	"""Verify plain password against hash."""
	if not hashed_password:
		return False
	return _pwd_context.verify(plain_password, hashed_password)
