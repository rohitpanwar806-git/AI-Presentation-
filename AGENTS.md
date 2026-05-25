# AI Presentation Avatar SaaS - Agent Customization Guide

**Last Updated:** May 25, 2026 | **Project ID:** `project-987f80c5-14e3-450d-9b0`

## Overview

This is a **SaaS platform for AI-powered presentation avatars** that allows users to upload presentations, select an avatar, and generate natural-looking AI-hosted presentations with voice synthesis. The platform uses a **FastAPI backend** deployed on **GCP Cloud Run** and a **static frontend** served via **Firebase Hosting**.

```
┌─────────────────────────────────────────────────────┐
│  Firebase Hosting (Static SPA)                       │
│  https://project-987f80c5-14e3-450d-9b0.web.app    │
└────────────────────┬────────────────────────────────┘
                     │ (API calls via CORS)
┌────────────────────▼────────────────────────────────┐
│  Cloud Run Backend (FastAPI)                         │
│  https://presentation-api-558900038680...run.app    │
│                                                      │
│  POST /auth/register  →  User authentication        │
│  POST /presentations/upload  →  Document processing │
│  GET  /avatars        →  Avatar selection           │
│  GET  /voices         →  TTS voices                 │
│  POST /api-keys       →  Developer API management   │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        │            │            │             │
    Cloud SQL   Supabase      Pinecone    ElevenLabs
    (PostgreSQL) (Auth)     (Vector DB)    (TTS)
```

---

## 1. Quick Start for Developers

### Prerequisites
- Python 3.9+
- Node.js 16+ (for Firebase CLI)
- GCP account with Cloud Run access
- PowerShell 5.1 (Windows) or bash (macOS/Linux)

### Local Development Setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate              # Windows
source venv/bin/activate           # macOS/Linux

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Configure environment
cp env.example .env
# Edit .env with: ANTHROPIC_API_KEY, SUPABASE_URL, DATABASE_URL, etc.

# 4. Start backend API
python -m uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# 5. In another terminal, serve frontend
cd frontend/web
npx http-server -p 8080 -c-1
# Open: http://localhost:8080
```

### Running Tests & Verification
```bash
# Check backend health
curl http://localhost:8000/health

# View API documentation
# Open: http://localhost:8000/docs (Swagger UI)

# Test E2E connectivity
node verify-e2e.js
```

---

## 2. Architecture & Component Responsibilities

### Backend Services

#### **Authentication Service** (`backend/api/auth.py`)
- **Responsibility:** User registration, login, email verification, JWT tokens
- **Pattern:** Bearer token in `Authorization: Bearer {jwt_token}` header
- **Supported Methods:** Email/password, Google OAuth (via Supabase)
- **Key Functions:**
  - `register()` - Email verification code sent
  - `verify_email()` - Confirm email with code
  - `login()` - Generate JWT access token
  - `_get_current_user()` - Dependency for protected endpoints
- **Security:** Passwords hashed with bcrypt, tokens signed with HS256
- **File:** [backend/core/security.py](backend/core/security.py)

#### **Presentation Service** (`backend/api/presentations.py` - TODO)
- **Responsibility:** Document upload, parsing, storage, metadata management
- **Supported Formats:** PDF, PPTX, DOCX
- **Processing Pipeline:**
  1. Upload file → validate format
  2. Parse content → extract text, slides, metadata
  3. Generate embeddings → store in Pinecone
  4. Create presentation record in Cloud SQL
- **Key Endpoints:**
  - `POST /presentations/upload` - File upload
  - `GET /presentations` - List user presentations
  - `GET /presentations/{id}` - Get details
  - `DELETE /presentations/{id}` - Remove

#### **Avatar Service** (`backend/api/avatars.py` - TODO)
- **Responsibility:** Avatar selection, customization, rendering
- **Built-in Avatars:** Pre-defined avatar library
- **Customization:** Appearance, voice, gesture style
- **Key Endpoints:**
  - `GET /avatars` - List available avatars
  - `GET /avatars/{id}` - Get avatar details

#### **Voice Service** (`backend/api/voices.py` - TODO)
- **Responsibility:** TTS synthesis, voice selection, language support
- **Provider:** ElevenLabs API (11 languages supported)
- **Features:** Multi-language, custom voice upload
- **Key Endpoints:**
  - `GET /voices` - List available voices
  - `GET /voices/languages` - Supported languages

#### **API Keys Service** (`backend/api/api_keys.py` - TODO)
- **Responsibility:** Developer API key management, rate limiting
- **Pattern:** API keys passed as header: `Authorization: Bearer {api_key}`
- **Rate Limiting:** 60 requests/minute per user (configurable)
- **Key Endpoints:**
  - `POST /api-keys` - Generate new key
  - `GET /api-keys` - List keys
  - `DELETE /api-keys/{id}` - Revoke key

### Database Layer

#### **Models** (`backend/db/models.py` - TODO)
- **ORM:** SQLAlchemy with async support
- **Database:** PostgreSQL on Cloud SQL
- **Planned Models:**
  - `User` - Email, password hash, profile, subscription tier
  - `Presentation` - File metadata, owner, access control
  - `Avatar` - Definition, customization options
  - `Voice` - Voice ID, language, provider
  - `APIKey` - Developer keys with rate limit tracking
  - `Document` - Raw file storage, processing status

#### **Schemas** (`backend/db/schemas.py` - TODO)
- Pydantic request/response models for all endpoints
- Input validation with detailed error messages
- Example: `UserRegisterRequest`, `PresentationUploadResponse`

#### **Configuration** (`backend/config.py`)
- **Pattern:** Environment variables with intelligent defaults
- **Key Variables:**
  - `DATABASE_URL` - PostgreSQL connection (supports Cloud SQL Unix socket)
  - `ANTHROPIC_API_KEY` - Claude LLM for presentation generation
  - `SUPABASE_URL/KEY` - OAuth provider
  - `ELEVENLABS_API_KEY` - Voice synthesis
  - `PINECONE_API_KEY` - Vector embeddings
  - `CORS_ORIGINS` - Frontend domains (comma-separated)

### Frontend Structure

#### **Static SPA** (`frontend/web/`)
- **Files:**
  - `index.html` - Modern responsive UI
  - `app.js` - Backend connectivity, state management
  - `config.js` - Environment detection
- **Technology:** Vanilla JavaScript (no build step)
- **Features:**
  - Real-time backend connectivity indicator
  - Cost breakdown calculator
  - Feature preview cards
  - Google Sign-In button

---

## 3. Build & Deployment Commands

### Backend Development
```bash
# Start with auto-reload
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Production (4 workers)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Database migrations
alembic upgrade head              # Apply pending migrations
alembic downgrade base            # Rollback to initial state
alembic revision --autogenerate   # Auto-detect schema changes
```

### Frontend Deployment (Firebase)
```bash
# Authenticate with Firebase
firebase login --no-localhost

# Deploy frontend only
firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0

# Automated script
node deploy.js

# Verify E2E connectivity
node verify-e2e.js
```

### Backend Deployment (GCP Cloud Run)
```bash
# From repository root, run PowerShell script
cd scripts/gcp

# 1. Preflight checks
./preflight.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0"

# 2. Bootstrap GCP resources (one-time)
./bootstrap.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"

# 3. Store secrets in Secret Manager
./create-secrets.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0"

# 4. Deploy backend
./deploy-backend.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0" -Region "asia-south1"

# 5. Deploy frontend
./deploy-frontend-firebase.ps1 -ProjectId "project-987f80c5-14e3-450d-9b0"
```

### Docker Deployment
```bash
# Build image
docker build -f backend/Dockerfile -t presentation-api:latest .

# Run locally
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host/db" \
  -e ANTHROPIC_API_KEY="sk-..." \
  presentation-api:latest
```

---

## 4. Key Conventions & Patterns

### Naming Conventions
```
Files:              snake_case.py
Classes:            PascalCase
Functions/methods:  snake_case()
Constants:          UPPER_CASE
Private:            _leading_underscore()
Database tables:    lowercase_plural (users, presentations)
```

### API Request/Response Pattern
**All endpoints use Pydantic models for validation:**

```python
# Request model
class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str  # min 8 characters

# Response model
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict
    is_new_user: bool

# Endpoint
@router.post("/register")
async def register(req: RegisterRequest) -> AuthResponse:
    # Implementation
```

### Authentication Pattern
```python
# Protected endpoint using dependency injection
@router.get("/presentations")
async def list_presentations(
    current_user: User = Depends(_get_current_user)
) -> List[PresentationResponse]:
    # current_user is automatically validated from JWT
```

### Error Handling
- Return `HTTPException` with appropriate status codes
- 400 = Invalid request (validation error)
- 401 = Unauthorized (invalid token)
- 403 = Forbidden (insufficient permissions)
- 404 = Not found (resource doesn't exist)
- 500 = Server error (unexpected failure)

### Database & ORM
- **ORM:** SQLAlchemy with async/await support
- **Driver:** `asyncpg` for PostgreSQL
- **Connection Pool:** Managed by `create_engine()` with health checks
- **Pattern:** Async session dependency injection
  ```python
  async def get_db() -> AsyncGenerator:
      async with SessionLocal() as session:
          yield session
  ```

### Service Initialization (Singleton Pattern)
```python
# At startup, initialize services once
@app.on_event("startup")
async def startup_event():
    global auth_service, presentation_service
    auth_service = AuthService(db)
    presentation_service = PresentationService(db)

# Reuse in endpoints
@router.get("/presentations")
async def list_presentations():
    return await presentation_service.list_all()
```

---

## 5. Environment & Configuration

### Critical Environment Variables

| Variable | Type | Example | Required | Purpose |
|----------|------|---------|----------|---------|
| `DATABASE_URL` | String | `postgresql+asyncpg://user:pass@host/db` | ✅ | PostgreSQL async connection |
| `ANTHROPIC_API_KEY` | String | `sk-...` | ✅ | Claude LLM for content generation |
| `SUPABASE_URL` | String | `https://xxxx.supabase.co` | ✅ | Supabase auth service |
| `SUPABASE_KEY` | String | `eyJ...` | ✅ | Supabase API key |
| `ELEVENLABS_API_KEY` | String | `sk_...` | ✅ | Voice synthesis API |
| `PINECONE_API_KEY` | String | `...` | ✅ | Vector database API |
| `GOOGLE_CLIENT_ID` | String | `...apps.googleusercontent.com` | ❌ | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | String | `GOCSPX-...` | ❌ | OAuth client secret |
| `CORS_ORIGINS` | CSV | `http://localhost:3000,https://domain.com` | ❌ | Allowed frontend origins |
| `RATE_LIMIT_PER_MINUTE` | Integer | `60` | ❌ | Rate limiting threshold |
| `SECRET_KEY` | String | Auto-generated | ⚠️ | JWT signing key (generated if missing) |
| `ALGORITHM` | String | `HS256` | ❌ | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `30` | ❌ | Token TTL in minutes |

### GCP-Specific Configuration
```bash
# Cloud Run environment
GCP_PROJECT_ID=project-987f80c5-14e3-450d-9b0
GCP_REGION=asia-south1
GCP_CLOUD_RUN_SERVICE=presentation-api
GCP_SQL_INSTANCE=presentation-db

# Cloud SQL Unix socket (production)
DATABASE_URL=postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# Cloud SQL TCP (development/testing)
DATABASE_URL=postgresql+asyncpg://user:pass@cloudsql-proxy-host/dbname
```

### SMTP Configuration (Email Verification)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=app-specific-password-16-chars
SMTP_FROM_EMAIL=no-reply@yourdomain.com
SMTP_USE_TLS=true
```

---

## 6. Implementation Roadmap

### Phase 1: Core Infrastructure ✅ (Complete)
- [x] FastAPI project structure
- [x] PostgreSQL + Cloud SQL integration
- [x] JWT authentication framework
- [x] CORS middleware
- [x] GCP deployment scripts
- [x] Firebase hosting setup

### Phase 2: Authentication (Partial - TODO)
- [x] Email/password registration
- [x] Email verification framework
- [x] JWT token generation
- [ ] Google OAuth implementation
- [ ] Refresh token rotation
- [ ] Password reset flow

### Phase 3: Presentation Management (TODO)
- [ ] Document upload endpoint
- [ ] PPTX/PDF/DOCX parsing
- [ ] Text extraction + chunking
- [ ] Pinecone embedding + storage
- [ ] Metadata database schema
- [ ] List/retrieve/delete endpoints

### Phase 4: Avatar & Voice Services (TODO)
- [ ] Avatar selection endpoint
- [ ] Avatar customization endpoint
- [ ] ElevenLabs TTS integration
- [ ] Voice list + language support
- [ ] Custom voice upload

### Phase 5: Developer APIs (TODO)
- [ ] API key generation
- [ ] Rate limiting middleware
- [ ] API usage analytics
- [ ] Developer dashboard

---

## 7. Common Pitfalls & Solutions

### 🔴 Database Connection Issues

**Problem:** `OperationalError: FATAL: password authentication failed`

**Cause:** Incorrect DATABASE_URL format or credentials

**Solutions:**
```bash
# Verify async driver prefix
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname

# For Cloud SQL with Unix socket
DATABASE_URL=postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# For Cloud SQL with TCP connection
DATABASE_URL=postgresql+asyncpg://user:pass@cloudsql-proxy-host:5432/dbname
```

### 🔴 CORS Errors from Frontend

**Problem:** `Access to XMLHttpRequest blocked by CORS policy`

**Cause:** Frontend domain not in `CORS_ORIGINS` list

**Solution:**
```bash
# Add frontend domain to environment
CORS_ORIGINS=http://localhost:3000,https://project-987f80c5-14e3-450d-9b0.web.app
```

### 🔴 Authentication Token Invalid

**Problem:** `HTTPException 401: Invalid token` or `token expired`

**Cause:** Missing or malformed JWT, or token TTL exceeded

**Solutions:**
- Verify `Authorization: Bearer {token}` format in request header
- Check `ACCESS_TOKEN_EXPIRE_MINUTES` is set (default 30)
- Implement token refresh endpoint for long sessions

### 🔴 Cloud SQL Connection from Cloud Run

**Problem:** `Connection refused` or `timeout`

**Cause:** Cloud SQL Proxy not configured or IP allowlist issue

**Solution:**
```bash
# In Cloud Run environment variable, use Unix socket
DATABASE_URL=postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# Or ensure Cloud SQL Proxy is running
gcloud sql connect presentation-db --user=app_user
```

### 🔴 GCP Billing Disabled

**Problem:** Deployment fails: `Billing account closed`

**Current Status:** Account `013F74-EA0BA7-0642BA` is closed

**Solution:**
```bash
# Reopen existing billing account
gcloud billing accounts update 013F74-EA0BA7-0642BA --name="AI Presentation Avatar"

# Or link new billing account
gcloud billing projects link PROJECT_ID --billing-account=ACCOUNT_ID
```

### 🔴 Secret Manager Access Denied

**Problem:** `Permission 'secretmanager.versions.access' denied`

**Cause:** Cloud Run service account missing `secretmanager.admin` role

**Solution:**
```bash
# Grant role to Cloud Run service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:CLOUD-RUN-SA@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"
```

### ⚠️ Email Verification Not Sending

**Problem:** Verification emails not received

**Cause:** SMTP not configured

**Solution:**
```bash
# Fill in SMTP variables for Gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=16-character-app-password
SMTP_USE_TLS=true

# Generate Gmail app password:
# 1. Enable 2-factor authentication
# 2. Go to https://myaccount.google.com/apppasswords
# 3. Select "Mail" and "Windows Computer"
# 4. Copy the 16-character password
```

---

## 8. Key File Reference

### Important Files by Purpose

| File | Purpose | Status |
|------|---------|--------|
| [backend/main.py](backend/main.py) | FastAPI app setup, routers, CORS | ✅ Core |
| [backend/config.py](backend/config.py) | Environment config loading | ✅ Complete |
| [backend/core/security.py](backend/core/security.py) | JWT, password hashing | ✅ Complete |
| [backend/db/database.py](backend/db/database.py) | SQLAlchemy async session | ✅ Complete |
| [backend/db/models.py](backend/db/models.py) | SQLAlchemy ORM models | 🔲 TODO |
| [backend/db/schemas.py](backend/db/schemas.py) | Pydantic request/response models | 🔲 TODO |
| [backend/api/auth.py](backend/api/auth.py) | Authentication endpoints | ⏳ Partial |
| [backend/api/presentations.py](backend/api/presentations.py) | Presentation management | 🔲 TODO |
| [backend/api/avatars.py](backend/api/avatars.py) | Avatar endpoints | 🔲 TODO |
| [backend/api/voices.py](backend/api/voices.py) | Voice endpoints | 🔲 TODO |
| [backend/api/api_keys.py](backend/api/api_keys.py) | Developer API management | 🔲 TODO |
| [frontend/web/index.html](frontend/web/index.html) | Frontend SPA | ✅ Complete |
| [frontend/web/app.js](frontend/web/app.js) | Frontend logic | ✅ Complete |
| [firebase.json](firebase.json) | Firebase hosting config | ✅ Complete |
| [backend/Dockerfile](backend/Dockerfile) | Container image | ✅ Complete |
| [scripts/gcp/deploy-backend.ps1](scripts/gcp/deploy-backend.ps1) | GCP deployment | ✅ Complete |

### Template & Configuration Files

| File | Purpose |
|------|---------|
| [env.example](env.example) | Environment variable template |
| [requirements.txt](requirements.txt) | Python dependencies |
| [vercel.json](vercel.json) | Vercel deployment config |

### Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | Quick start guide |
| [docs/API.md](docs/API.md) | API endpoint reference |
| [docs/GCP_DEPLOYMENT.md](docs/GCP_DEPLOYMENT.md) | GCP deployment guide |
| [FIREBASE_DEPLOYMENT_GUIDE.md](FIREBASE_DEPLOYMENT_GUIDE.md) | Firebase setup guide |

---

## 9. Development Priorities by Role

### Backend Developer
1. **Priority 1:** Implement [backend/api/presentations.py](backend/api/presentations.py) - Document upload, parsing, storage
2. **Priority 2:** Create [backend/db/models.py](backend/db/models.py) - Database schema
3. **Priority 3:** Implement [backend/api/avatars.py](backend/api/avatars.py) - Avatar service
4. **Priority 4:** Complete OAuth flow in [backend/api/auth.py](backend/api/auth.py)

### Database Developer
1. Create all ORM models in [backend/db/models.py](backend/db/models.py)
2. Create Pydantic schemas in [backend/db/schemas.py](backend/db/schemas.py)
3. Set up initial migration: `alembic revision --autogenerate -m "init"`
4. Test Cloud SQL connectivity with Cloud SQL Proxy

### Frontend Developer
1. Update [frontend/web/app.js](frontend/web/app.js) to consume completed API endpoints
2. Add presentation upload form
3. Implement avatar selection UI
4. Add voice selection and settings

### DevOps/GCP Developer
1. Run GCP preflight checks: `.\scripts\gcp\preflight.ps1`
2. Set up billing and reopen closed account if needed
3. Create Cloud SQL user and test connectivity
4. Deploy backend with `.\scripts\gcp\deploy-backend.ps1`
5. Deploy frontend with `.\scripts\gcp\deploy-frontend-firebase.ps1`

### Full Stack
1. Clone repo and run local setup
2. Start backend with `uvicorn backend.main:app --reload`
3. Serve frontend with `http-server`
4. Test health endpoint: `curl http://localhost:8000/health`
5. Verify E2E connectivity: `node verify-e2e.js`

---

## 10. Testing & Verification

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# View API docs
# Open browser: http://localhost:8000/docs

# Test registration endpoint (when implemented)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","email":"john@example.com","password":"SecurePass123"}'

# Test protected endpoint (requires token)
curl http://localhost:8000/presentations \
  -H "Authorization: Bearer eyJ..."
```

### Automated Testing
```bash
# E2E connectivity test
node verify-e2e.js

# Backend service tests (when implemented)
pytest backend/tests/
```

### Pre-Deployment Checklist
- [ ] Environment variables configured in `.env`
- [ ] Database migrations applied: `alembic upgrade head`
- [ ] Backend starts without errors: `uvicorn backend.main:app --reload`
- [ ] API docs load: `http://localhost:8000/docs`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Frontend loads and connects to backend
- [ ] E2E test passes: `node verify-e2e.js`

---

## 11. Resources & Documentation

- **API Documentation:** [docs/API.md](docs/API.md)
- **GCP Deployment Guide:** [docs/GCP_DEPLOYMENT.md](docs/GCP_DEPLOYMENT.md)
- **Firebase Setup:** [FIREBASE_DEPLOYMENT_GUIDE.md](FIREBASE_DEPLOYMENT_GUIDE.md)
- **Quick Start:** [README.md](README.md)
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **GCP Cloud Run:** https://cloud.google.com/run/docs
- **Firebase Hosting:** https://firebase.google.com/docs/hosting

---

## 12. Getting Help

When working on this codebase:

1. **Check the API docs** at `http://localhost:8000/docs` (Swagger UI)
2. **Review exemplar files** in the [backend/api/auth.py](backend/api/auth.py) for patterns
3. **Check [env.example](env.example)** for all available configuration options
4. **Reference this AGENTS.md** for architecture and conventions
5. **Run E2E tests** with `node verify-e2e.js` to verify full stack connectivity

---

**Status:** Early-stage implementation with solid infrastructure. Focus needed on service implementations (presentations, avatars, voices) and database schema.
