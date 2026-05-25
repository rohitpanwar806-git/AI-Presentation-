"""
FastAPI Application Entry Point
AI Presentation Avatar SaaS Platform
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.api import auth, presentations, avatars, voices, presentations_session
from backend.db.database import init_db

# Load environment variables
load_dotenv()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="PresenterAI API",
    description="AI Presentation Avatar Platform — Generate professional presenter videos from documents",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://localhost:3001,https://web-orskelu3q-rohitpanwar806-gits-projects.vercel.app,https://web-seven-swart-96tyghlog6.vercel.app"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Global exception handler — prevent leaking internal details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "PresenterAI API",
        "version": "2.0.0",
        "status": "active",
        "docs": "/docs",
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(presentations.router, prefix="/presentations", tags=["presentations"])
app.include_router(presentations_session.router, prefix="/session", tags=["session"])
app.include_router(avatars.router, prefix="/avatars", tags=["avatars"])
app.include_router(voices.router, prefix="/voices", tags=["voices"])
# app.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])


@app.on_event("startup")
async def startup_event() -> None:
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
