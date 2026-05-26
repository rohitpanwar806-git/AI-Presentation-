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


# Public shared presentation endpoint (no auth, top-level to avoid route conflicts)
@app.get("/shared/{share_token}", tags=["public"])
async def public_shared_presentation(share_token: str):
    """View a shared presentation (no authentication required). Links expire after 24 hours."""
    from backend.api.presentations import _get_db_presentation_by_token, _update_analytics
    from backend.db.database import SessionLocal
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        pres = _get_db_presentation_by_token(db, share_token)
        if not pres:
            return JSONResponse(status_code=404, content={"detail": "Shared link not found or has expired"})

        if pres.share_expires_at and datetime.now(timezone.utc) > pres.share_expires_at:
            pres.share_token = None
            pres.share_expires_at = None
            db.commit()
            return JSONResponse(status_code=410, content={"detail": "This shared link has expired (24-hour limit)"})

        _update_analytics(pres, "view")
        db.commit()

        d = pres.to_dict()
        return {
            "title": d["title"],
            "slides": d["slides"],
            "scripts": d["scripts"],
            "avatar_id": d["avatar_id"],
            "voice_id": d["voice_id"],
            "total_slides": len(d["slides"]),
            "has_qa": bool(pres.document_text),
            "quiz": d.get("quiz"),
            "summary": d.get("summary"),
            "document_text": pres.document_text[:500] if pres.document_text else None,
            "expires_at": pres.share_expires_at.isoformat() if pres.share_expires_at else None,
        }
    finally:
        db.close()


# Public Q&A for shared presentations (no auth required)
@app.post("/shared/{share_token}/ask", tags=["public"])
async def public_shared_ask(share_token: str, body: dict):
    """Ask a question about a shared presentation. Avatar answers in real-time."""
    from backend.api.presentations import _get_db_presentation_by_token
    from backend.db.database import SessionLocal
    from backend.services.agentic_pipeline import answer_question
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        pres = _get_db_presentation_by_token(db, share_token)
        if not pres:
            return JSONResponse(status_code=404, content={"detail": "Shared link not found or has expired"})

        if pres.share_expires_at and datetime.now(timezone.utc) > pres.share_expires_at:
            pres.share_token = None
            pres.share_expires_at = None
            db.commit()
            return JSONResponse(status_code=410, content={"detail": "This shared link has expired"})

        question = (body.get("question") or "").strip()
        if not question:
            return JSONResponse(status_code=400, content={"detail": "Question cannot be empty"})

        # Special command: generate quiz for shared viewers
        if question == "__generate_quiz__":
            from backend.services.rag_service import generate_quiz
            import json
            document_text = pres.document_text or ""
            quiz = generate_quiz(document_text, pres.title, num_questions=5)
            # Cache quiz in the presentation
            if quiz:
                pres.quiz_json = json.dumps(quiz)
                db.commit()
            return {"status": "success", "quiz": quiz}

        document_text = pres.document_text or ""
        answer = answer_question(
            document_text=document_text,
            question=question,
            presentation_title=pres.title,
            chat_history=body.get("chat_history")
        )

        return {
            "status": "success",
            "answer": answer,
            "avatar_id": pres.avatar_id,
        }
    finally:
        db.close()


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
