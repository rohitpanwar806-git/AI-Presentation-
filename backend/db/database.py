"""Database connection and session utilities for auth/admin features."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend import config


Base = declarative_base()

_connect_args = {"check_same_thread": False} if config.AUTH_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
	config.AUTH_DATABASE_URL,
	pool_pre_ping=True,
	connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def init_db() -> None:
	# Import here to avoid circular imports with Base.
	try:
		from backend.db import models  # noqa: F401
		Base.metadata.create_all(bind=engine)
		# Add missing columns for existing tables (safe to run multiple times)
		_migrate_add_columns()
	except Exception as e:
		# Log but don't fail if database initialization fails
		print(f"Warning: Database initialization failed: {e}")
		pass


def _migrate_add_columns() -> None:
	"""Add new columns to existing tables if they don't exist. Safe to call repeatedly."""
	from sqlalchemy import text, inspect
	insp = inspect(engine)
	try:
		if "users" in insp.get_table_names():
			existing = {c["name"] for c in insp.get_columns("users")}
			new_cols = {
				"failed_login_attempts": "INTEGER DEFAULT 0 NOT NULL",
				"locked_until": "TIMESTAMP WITH TIME ZONE",
				"privacy_consent": "BOOLEAN DEFAULT false NOT NULL",
				"privacy_consent_at": "TIMESTAMP WITH TIME ZONE",
				"data_deletion_requested_at": "TIMESTAMP WITH TIME ZONE",
			}
			with engine.begin() as conn:
				for col, col_type in new_cols.items():
					if col not in existing:
						# Use %s-style safe formatting since column names are hardcoded constants
						conn.execute(text(f'ALTER TABLE users ADD COLUMN {col} {col_type}'))
						print(f"Migration: Added column users.{col}")
	except Exception as e:
		print(f"Migration warning: {e}")
