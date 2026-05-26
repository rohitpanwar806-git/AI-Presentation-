"""
Backend Configuration
"""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Only load .env in development (when running locally)
# In production (Cloud Run), environment variables are set via gcloud
if os.getenv("ENVIRONMENT") != "production" and os.path.exists(".env"):
	load_dotenv()

# Server Config
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database Config
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
	db_name = os.getenv("DB_NAME", "presentation_saas_db")
	db_user = os.getenv("DB_USER", "user")
	db_password = quote_plus(os.getenv("DB_PASSWORD", "password"))
	db_host = os.getenv("DB_HOST", "localhost")
	db_socket = os.getenv("DB_SOCKET", "")

	if db_socket:
		# Cloud Run + Cloud SQL Unix socket format.
		DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@/{db_name}?host={db_socket}"
	else:
		DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}/{db_name}"

# Security Config
_default_secret = "your-super-secret-key-change-in-production"
SECRET_KEY = os.getenv("SECRET_KEY", _default_secret)
if ENVIRONMENT == "production" and SECRET_KEY == _default_secret:
	import secrets as _sec
	SECRET_KEY = _sec.token_urlsafe(64)
	print("WARNING: SECRET_KEY not set in production — auto-generated ephemeral key. Set SECRET_KEY env var!")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security: max failed login attempts before temporary lockout
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))

# OAuth Config
GOOGLE_CLIENT_ID = (os.getenv("GOOGLE_CLIENT_ID") or "").strip() or None
GOOGLE_CLIENT_SECRET = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip() or None
GOOGLE_REDIRECT_URI = (os.getenv("GOOGLE_REDIRECT_URI") or "").strip() or None

# Supabase Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# LLM Config
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Voice Synthesis Config
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Vector Database Config
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "presentations")

# File Storage Config
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# Rate Limiting Config
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# CORS Config
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Auth persistence and admin config
_auth_database_url = (os.getenv("AUTH_DATABASE_URL") or "").strip()
if _auth_database_url:
	AUTH_DATABASE_URL = _auth_database_url
else:
	_auth_db_name = os.getenv("DB_NAME", "presentation_saas")
	_auth_db_user = os.getenv("DB_USER", "app_user")
	_auth_db_password = quote_plus(os.getenv("DB_PASSWORD", "password"))
	_auth_db_host = os.getenv("DB_HOST", "localhost")
	_auth_db_socket = os.getenv("DB_SOCKET", "")

	if _auth_db_socket:
		AUTH_DATABASE_URL = f"postgresql+psycopg2://{_auth_db_user}:{_auth_db_password}@/{_auth_db_name}?host={_auth_db_socket}"
	else:
		AUTH_DATABASE_URL = f"postgresql+psycopg2://{_auth_db_user}:{_auth_db_password}@{_auth_db_host}/{_auth_db_name}"

ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or "").strip().lower() or None
VERIFICATION_CODE_EXPIRE_MINUTES = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "10"))

# SMTP / email verification config
SMTP_HOST = (os.getenv("SMTP_HOST") or "").strip() or None
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = (os.getenv("SMTP_USERNAME") or "").strip() or None
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = (os.getenv("SMTP_FROM_EMAIL") or "").strip() or None
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
