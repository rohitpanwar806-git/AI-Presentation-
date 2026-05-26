"""
Presentation Management Endpoints
- Upload documents
- List/view/edit/delete presentations
- Track views and engagement analytics
- Generate AI presentation from document
- Q&A tutor mode

Presentations are persisted in the database so they survive container restarts.
"""
import base64
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.auth import _get_current_user
from backend.db.database import get_db
from backend.db.models import Presentation
from backend.services.agentic_pipeline import (
    extract_text_from_file,
    generate_slides_from_content,
    answer_question,
)
from backend.services.rag_service import (
    chunk_document,
    find_relevant_chunks,
    generate_summary,
    generate_quiz,
    generate_script_from_slides,
)

router = APIRouter()

# Supported file types
ALLOWED_EXTENSIONS = {'.pdf', '.pptx', '.docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

SHARE_LINK_TTL_HOURS = 24


class PresentationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    status: Optional[str] = None


# ── DB helpers ──────────────────────────────────────────────────

def _get_db_presentation(db: Session, user_id: int, pid: str) -> Presentation | None:
    return db.query(Presentation).filter(
        Presentation.user_id == user_id,
        Presentation.pid == pid,
    ).first()


def _get_db_presentation_by_token(db: Session, share_token: str) -> Presentation | None:
    return db.query(Presentation).filter(
        Presentation.share_token == share_token,
    ).first()


def _save_file_to_db(pres: Presentation, contents: bytes):
    """Store raw file bytes as base64 in the DB so uploads survive restarts."""
    pres.file_content = base64.b64encode(contents).decode("ascii")


def _restore_file_from_db(pres: Presentation, file_path: str) -> bool:
    """Restore a file from DB to disk (for text extraction). Returns True on success."""
    if not pres.file_content:
        return False
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(pres.file_content))
        return True
    except Exception:
        return False


def _ensure_file(pres: Presentation, user_id) -> str:
    """Ensure the uploaded file exists on disk (restoring from DB if needed).
    Returns the file path."""
    uploads_dir = os.path.join(os.path.dirname(__file__), '../../uploads')
    file_path = os.path.join(uploads_dir, f"user_{user_id}", pres.filename)
    if not os.path.exists(file_path):
        _restore_file_from_db(pres, file_path)
    return file_path


def _update_analytics(pres: Presentation, key: str):
    analytics = json.loads(pres.analytics_json) if pres.analytics_json else {
        "views": 0, "unique_viewers": 0, "avg_watch_time": 0,
        "completion_rate": 0, "shares": 0, "downloads": 0,
        "last_viewed": None, "view_history": [],
    }
    if key == "view":
        analytics["views"] = analytics.get("views", 0) + 1
        analytics["last_viewed"] = datetime.now(timezone.utc).isoformat()
        history = analytics.get("view_history", [])
        history.append({"timestamp": analytics["last_viewed"], "viewer": "self"})
        analytics["view_history"] = history[-50:]
    elif key == "share":
        analytics["shares"] = analytics.get("shares", 0) + 1
    pres.analytics_json = json.dumps(analytics)
    return analytics


def _build_deck_slides(document_text: str, title: str) -> list:
    """Build slides from extracted deck text (preserving original slide structure)."""
    slides = []
    # If text has [Slide N] markers (from PPTX extraction), split on them
    import re
    slide_parts = re.split(r'\[Slide \d+\]', document_text)
    slide_parts = [p.strip() for p in slide_parts if p.strip()]

    if not slide_parts:
        # Fallback: split by paragraphs
        paragraphs = [p.strip() for p in document_text.split('\n\n') if p.strip()]
        slide_parts = paragraphs

    for i, part in enumerate(slide_parts[:30]):
        lines = [l.strip() for l in part.split('\n') if l.strip()]
        if not lines:
            continue
        slide_title = lines[0][:80]
        remaining = lines[1:]
        if i == 0:
            slides.append({"title": slide_title, "body": " ".join(remaining)[:200] if remaining else None, "bullets": None, "type": "title"})
        elif len(remaining) >= 2:
            slides.append({"title": slide_title, "body": None, "bullets": [l[:100] for l in remaining[:8]], "type": "content"})
        else:
            slides.append({"title": slide_title, "body": " ".join(remaining)[:300] if remaining else None, "bullets": None, "type": "content"})

    if not slides:
        slides = [{"title": title, "body": "Presentation content from uploaded deck", "bullets": None, "type": "title"}]

    return slides


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/upload")
async def upload_presentation(
    file: UploadFile = File(...),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a presentation document (PDF, PPTX, or DOCX)."""
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )

        filename = file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        mime_type = file.content_type
        allowed_mimes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if mime_type not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MIME type: {mime_type}"
            )

        # Save file to disk (ephemeral — also saved in DB)
        uploads_dir = os.path.join(os.path.dirname(__file__), '../../uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        user_id = getattr(current_user, "id", 0)
        user_dir = os.path.join(uploads_dir, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(contents)

        # Create presentation record in DB
        pid = str(uuid.uuid4())[:8]
        file_type_map = {'.pdf': 'PDF', '.pptx': 'PowerPoint', '.docx': 'Word'}

        pres = Presentation(
            pid=pid,
            user_id=user_id,
            title=os.path.splitext(filename)[0],
            filename=filename,
            file_type=file_type_map.get(file_ext, 'Document'),
            file_size=len(contents),
            status="uploaded",
        )
        _save_file_to_db(pres, contents)
        db.add(pres)
        db.commit()
        db.refresh(pres)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"File '{filename}' uploaded successfully",
                "presentation": pres.to_dict(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/")
async def list_presentations(
    status_filter: Optional[str] = Query(None, alias="status"),
    sort: Optional[str] = Query("newest", description="Sort: newest, oldest, most_viewed, title"),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of user's presentations with analytics"""
    user_id = getattr(current_user, "id", 0)

    query = db.query(Presentation).filter(Presentation.user_id == user_id)
    if status_filter:
        query = query.filter(Presentation.status == status_filter)

    if sort == "oldest":
        query = query.order_by(Presentation.created_at.asc())
    elif sort == "title":
        query = query.order_by(Presentation.title.asc())
    else:  # newest (default)
        query = query.order_by(Presentation.created_at.desc())

    all_presentations = query.all()
    presentations = [p.to_dict() for p in all_presentations]

    # For most_viewed sort, do it in Python (analytics is JSON)
    if sort == "most_viewed":
        presentations.sort(key=lambda p: p["analytics"].get("views", 0), reverse=True)

    # Get totals from all user presentations (unfiltered)
    total_count = db.query(Presentation).filter(Presentation.user_id == user_id).count()
    all_dicts = presentations
    if status_filter:
        all_user = db.query(Presentation).filter(Presentation.user_id == user_id).all()
        all_dicts = [p.to_dict() for p in all_user]
    total_views = sum(p["analytics"].get("views", 0) for p in all_dicts)
    total_shares = sum(p["analytics"].get("shares", 0) for p in all_dicts)

    return {
        "presentations": presentations,
        "total": len(presentations),
        "summary": {
            "total_presentations": total_count,
            "total_views": total_views,
            "total_shares": total_shares,
            "statuses": {
                s: db.query(Presentation).filter(
                    Presentation.user_id == user_id,
                    Presentation.status == s,
                ).count()
                for s in ("uploaded", "processing", "ready", "published")
            }
        }
    }


@router.get("/{presentation_id}")
async def get_presentation(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Get full presentation details with analytics"""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    return {"presentation": pres.to_dict()}


@router.put("/{presentation_id}")
async def update_presentation(
    presentation_id: str,
    update: PresentationUpdate,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Update presentation title, description, avatar, voice, or status"""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    if update.title is not None:
        pres.title = update.title
    if update.description is not None:
        pres.description = update.description
    if update.avatar_id is not None:
        pres.avatar_id = update.avatar_id
    if update.voice_id is not None:
        pres.voice_id = update.voice_id
    if update.status is not None:
        pres.status = update.status
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pres)

    return {"status": "success", "presentation": pres.to_dict()}


@router.post("/{presentation_id}/view")
async def record_view(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Record a view event for analytics tracking"""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    analytics = _update_analytics(pres, "view")
    db.commit()
    return {"status": "success", "views": analytics["views"]}


@router.post("/{presentation_id}/share")
async def record_share(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Record a share event"""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    analytics = _update_analytics(pres, "share")
    db.commit()
    return {"status": "success", "shares": analytics["shares"]}


@router.delete("/{presentation_id}")
async def delete_presentation(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a presentation"""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    title = pres.title
    # Delete file from disk if present
    uploads_dir = os.path.join(os.path.dirname(__file__), '../../uploads')
    file_path = os.path.join(uploads_dir, f"user_{user_id}", pres.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(pres)
    db.commit()
    return {"status": "success", "message": f"Presentation '{title}' deleted"}


# ==================== GENERATE PRESENTATION ====================

class GenerateRequest(BaseModel):
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    mode: Optional[str] = "generate"  # "generate" = create new slides from doc, "present_deck" = use uploaded slides as-is


@router.post("/{presentation_id}/generate")
async def generate_presentation(
    presentation_id: str,
    req: GenerateRequest = Body(default=GenerateRequest()),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate AI presentation from uploaded document.
    Analyzes document, extracts content, creates slides, assigns avatar & voice.
    """
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    if req.avatar_id:
        pres.avatar_id = req.avatar_id
    if req.voice_id:
        pres.voice_id = req.voice_id

    pres.status = "processing"
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Ensure file on disk (restore from DB if container restarted)
    file_path = _ensure_file(pres, user_id)

    document_text = ""
    if os.path.exists(file_path):
        try:
            document_text = extract_text_from_file(file_path)
        except Exception:
            document_text = ""

    pres.document_text = document_text

    if req.mode == "present_deck" and document_text.strip():
        # Use uploaded deck slides directly (for PPTX/PDF with slide markers)
        slides = _build_deck_slides(document_text, pres.title)
    else:
        # Generate new AI presentation from document content
        slides = generate_slides_from_content(document_text, pres.title)

    pres.slides_json = json.dumps(slides)
    pres.status = "ready"
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pres)

    return {
        "status": "success",
        "message": "Presentation generated successfully",
        "presentation": {
            "id": pres.pid,
            "title": pres.title,
            "status": pres.status,
            "slides": slides,
            "total_slides": len(slides),
            "avatar_id": pres.avatar_id,
            "voice_id": pres.voice_id,
        }
    }


# ==================== Q&A TUTOR MODE ====================

class AskRequest(BaseModel):
    question: str
    chat_history: Optional[List[dict]] = None


@router.post("/{presentation_id}/ask")
async def ask_question_endpoint(
    presentation_id: str,
    req: AskRequest = Body(...),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask the AI tutor a question about the presentation content.
    """
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty")

    document_text = pres.document_text or ""
    if not document_text:
        file_path = _ensure_file(pres, user_id)
        if os.path.exists(file_path):
            try:
                document_text = extract_text_from_file(file_path)
                pres.document_text = document_text
                db.commit()
            except Exception:
                pass

    answer = answer_question(
        document_text=document_text,
        question=req.question.strip(),
        presentation_title=pres.title,
        chat_history=req.chat_history
    )

    return {
        "status": "success",
        "answer": answer,
        "presentation_id": presentation_id,
        "avatar_id": pres.avatar_id,
    }


# ==================== SHARE LINKS ====================

@router.post("/{presentation_id}/publish")
async def publish_presentation(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a public shareable link for the presentation (valid for 24 hours)."""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    slides = json.loads(pres.slides_json) if pres.slides_json else []
    if not slides:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Generate presentation first")

    share_token = str(uuid.uuid4())[:12]
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SHARE_LINK_TTL_HOURS)
    pres.share_token = share_token
    pres.share_expires_at = expires_at
    pres.status = "published"
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "share_token": share_token,
        "share_url": f"/shared/{share_token}",
        "expires_at": expires_at.isoformat(),
        "expires_in_hours": SHARE_LINK_TTL_HOURS,
        "message": f"Presentation published! Link valid for {SHARE_LINK_TTL_HOURS} hours."
    }


@router.get("/shared/{share_token}")
async def get_shared_presentation(share_token: str, db: Session = Depends(get_db)):
    """View a shared presentation (no auth required)."""
    pres = _get_db_presentation_by_token(db, share_token)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found or has expired")

    if pres.share_expires_at and datetime.now(timezone.utc) > pres.share_expires_at:
        pres.share_token = None
        pres.share_expires_at = None
        db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This shared link has expired (24-hour limit)")

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
        "created_at": d["created_at"],
        "has_qa": bool(pres.document_text),
        "quiz": d.get("quiz"),
        "summary": d.get("summary"),
    }


@router.post("/shared/{share_token}/ask")
async def shared_ask_question(share_token: str, req: AskRequest = Body(...), db: Session = Depends(get_db)):
    """Public Q&A endpoint for shared presentations (no auth required)."""
    pres = _get_db_presentation_by_token(db, share_token)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found or has expired")

    if pres.share_expires_at and datetime.now(timezone.utc) > pres.share_expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This shared link has expired")

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty")

    document_text = pres.document_text or ""
    answer = answer_question(
        document_text=document_text,
        question=req.question.strip(),
        presentation_title=pres.title,
        chat_history=req.chat_history
    )

    return {"status": "success", "answer": answer}


@router.post("/shared/{share_token}/quiz")
async def shared_quiz_endpoint(share_token: str, db: Session = Depends(get_db)):
    """Generate quiz for shared presentations (no auth required)."""
    pres = _get_db_presentation_by_token(db, share_token)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found")
    if pres.share_expires_at and datetime.now(timezone.utc) > pres.share_expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link expired")

    # Return cached quiz if available
    if pres.quiz_json:
        return {"status": "success", "quiz": json.loads(pres.quiz_json)}

    document_text = pres.document_text or ""
    questions = generate_quiz(document_text, pres.title, 5)
    pres.quiz_json = json.dumps(questions)
    db.commit()
    return {"status": "success", "quiz": questions, "total_questions": len(questions)}


@router.get("/shared/{share_token}/summary")
async def shared_summary_endpoint(share_token: str, db: Session = Depends(get_db)):
    """Get summary for shared presentations (no auth required)."""
    pres = _get_db_presentation_by_token(db, share_token)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared link not found")
    if pres.share_expires_at and datetime.now(timezone.utc) > pres.share_expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link expired")

    if pres.summary_json:
        return {"status": "success", "summary": json.loads(pres.summary_json)}

    document_text = pres.document_text or ""
    summary = generate_summary(document_text, pres.title)
    pres.summary_json = json.dumps(summary)
    db.commit()
    return {"status": "success", "summary": summary}


# ==================== QUIZ GENERATION ====================

class QuizRequest(BaseModel):
    num_questions: int = 5


@router.post("/{presentation_id}/quiz")
async def generate_quiz_endpoint(
    presentation_id: str,
    req: QuizRequest = Body(default=QuizRequest()),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Generate quiz questions from the presentation content."""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    document_text = pres.document_text or ""
    if not document_text:
        file_path = _ensure_file(pres, user_id)
        if os.path.exists(file_path):
            document_text = extract_text_from_file(file_path)
            pres.document_text = document_text

    num_q = min(max(req.num_questions, 2), 10)
    questions = generate_quiz(document_text, pres.title, num_q)

    pres.quiz_json = json.dumps(questions)
    db.commit()

    return {
        "status": "success",
        "quiz": questions,
        "total_questions": len(questions),
    }


# ==================== SUMMARY / RAG ====================

@router.get("/{presentation_id}/summary")
async def get_summary(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Get AI-generated summary with key points, topics, and metadata."""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    if pres.summary_json:
        return {"status": "success", "summary": json.loads(pres.summary_json)}

    document_text = pres.document_text or ""
    if not document_text:
        file_path = _ensure_file(pres, user_id)
        if os.path.exists(file_path):
            document_text = extract_text_from_file(file_path)
            pres.document_text = document_text

    summary = generate_summary(document_text, pres.title)
    pres.summary_json = json.dumps(summary)
    db.commit()

    return {"status": "success", "summary": summary}


# ==================== SCRIPT EDITOR ====================

class ScriptUpdateRequest(BaseModel):
    scripts: list


@router.post("/{presentation_id}/scripts")
async def generate_scripts(
    presentation_id: str,
    style: str = Query("professional", description="Style: professional, friendly, educational, energetic"),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Auto-generate narration scripts for all slides."""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    slides = json.loads(pres.slides_json) if pres.slides_json else []
    if not slides:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No slides to script. Generate first.")

    scripts = generate_script_from_slides(slides, style)
    pres.scripts_json = json.dumps(scripts)
    db.commit()

    return {"status": "success", "scripts": scripts, "style": style}


@router.put("/{presentation_id}/scripts")
async def update_scripts(
    presentation_id: str,
    req: ScriptUpdateRequest = Body(...),
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Save user-edited narration scripts."""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    pres.scripts_json = json.dumps(req.scripts)
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "success", "message": "Scripts updated", "total": len(req.scripts)}


# ==================== ANALYTICS ====================

@router.get("/{presentation_id}/analytics")
async def get_analytics(
    presentation_id: str,
    current_user=Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed analytics for a presentation."""
    user_id = getattr(current_user, "id", 0)
    pres = _get_db_presentation(db, user_id, presentation_id)
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    d = pres.to_dict()
    analytics = d["analytics"]
    return {
        "status": "success",
        "analytics": {
            **analytics,
            "presentation_title": d["title"],
            "total_slides": len(d["slides"]),
            "has_quiz": bool(d.get("quiz")),
            "is_published": d["status"] == "published",
            "share_token": d.get("share_token"),
        }
    }
