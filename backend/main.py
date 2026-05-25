"""
FastAPI Application Entry Point
AI Presentation Avatar SaaS Platform
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.api import auth, presentations, avatars, voices, presentations_session
from backend.db.database import init_db

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Presentation Avatar SaaS API",
    description="API for creating personalized presentation avatars",
    version="1.0.0",
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://web-orskelu3q-rohitpanwar806-gits-projects.vercel.app"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_origin_regex=r"^https://([a-zA-Z0-9-]+-rohitpanwar806-gits-projects\.vercel\.app|web-seven-swart-96tyghlog6\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Presentation Avatar SaaS API",
        "version": "1.0.0",
        "status": "active",
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

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
