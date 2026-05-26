"""Database models used by auth/profile/admin endpoints."""

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
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
	# Security: brute-force protection
	failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
	locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	# DPDP Act: consent tracking
	privacy_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
	privacy_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	data_deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupportTicket(Base):
	"""Help centre support tickets."""
	__tablename__ = "support_tickets"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
	subject: Mapped[str] = mapped_column(String(300), nullable=False)
	category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
	admin_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


class Presentation(Base):
	"""Persistent presentation storage — survives container restarts."""
	__tablename__ = "presentations"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	pid: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
	user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
	title: Mapped[str] = mapped_column(String(500), nullable=False)
	filename: Mapped[str] = mapped_column(String(500), nullable=False)
	file_type: Mapped[str] = mapped_column(String(30), nullable=False, default="Document")
	file_size: Mapped[int] = mapped_column(Integer, default=0)
	status: Mapped[str] = mapped_column(String(30), default="uploaded")
	avatar_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
	voice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
	description: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
	share_token: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
	share_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	# Large data stored as JSON text
	slides_json: Mapped[str | None] = mapped_column(Text, nullable=True)
	scripts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
	quiz_json: Mapped[str | None] = mapped_column(Text, nullable=True)
	summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
	analytics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
	document_text: Mapped[str | None] = mapped_column(Text, nullable=True)
	file_content: Mapped[bytes | None] = mapped_column(Text, nullable=True)  # base64 encoded
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=_utcnow,
		onupdate=_utcnow,
		nullable=False,
	)

	def _default_analytics(self) -> dict:
		return {
			"views": 0, "unique_viewers": 0, "avg_watch_time": 0,
			"completion_rate": 0, "shares": 0, "downloads": 0,
			"last_viewed": None, "view_history": [],
		}

	def to_dict(self) -> dict:
		"""Convert to the dict format the API already uses."""
		return {
			"id": self.pid,
			"title": self.title,
			"filename": self.filename,
			"file_type": self.file_type,
			"file_size": self.file_size,
			"status": self.status,
			"avatar_id": self.avatar_id,
			"voice_id": self.voice_id,
			"description": self.description or "",
			"share_token": self.share_token,
			"created_at": self.created_at.isoformat() if self.created_at else None,
			"updated_at": self.updated_at.isoformat() if self.updated_at else None,
			"slides": json.loads(self.slides_json) if self.slides_json else [],
			"scripts": json.loads(self.scripts_json) if self.scripts_json else [],
			"quiz": json.loads(self.quiz_json) if self.quiz_json else None,
			"summary": json.loads(self.summary_json) if self.summary_json else None,
			"analytics": json.loads(self.analytics_json) if self.analytics_json else self._default_analytics(),
			"_document_text": self.document_text or "",
		}
