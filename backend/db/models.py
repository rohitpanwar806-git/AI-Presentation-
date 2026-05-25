"""Database models used by auth/profile/admin endpoints."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base


def _utcnow() -> datetime:
	return datetime.now(timezone.utc)


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
	last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
	gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
	password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
	login_provider: Mapped[str] = mapped_column(String(30), default="email", nullable=False)
	is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
	bio: Mapped[str | None] = mapped_column(Text, nullable=True)
	verification_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
	verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=_utcnow,
		onupdate=_utcnow,
		nullable=False,
	)
	last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
