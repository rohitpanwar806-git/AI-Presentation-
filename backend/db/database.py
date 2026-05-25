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
	except Exception as e:
		# Log but don't fail if database initialization fails
		print(f"Warning: Database initialization failed: {e}")
		pass
