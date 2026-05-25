"""
Presentation Management Endpoints
- Upload documents
- List/view/edit/delete presentations
- Track views and engagement analytics
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api.auth import _get_current_user
from backend.db.database import get_db

router = APIRouter()

# Supported file types
ALLOWED_EXTENSIONS = {'.pdf', '.pptx', '.docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# In-memory presentation store (per-user, keyed by user_id)
# In production this would be a database table
_presentations_store: dict = {}


class PresentationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    avatar_id: Optional[str] = None
    voice_id: Optional[str] = None
    status: Optional[str] = None


def _get_user_presentations(user_id) -> list:
    return _presentations_store.setdefault(str(user_id), [])


def _find_presentation(user_id, presentation_id: str):
    presentations = _get_user_presentations(user_id)
    return next((p for p in presentations if p["id"] == presentation_id), None)


@router.post("/upload")
async def upload_presentation(
    file: UploadFile = File(...),
    current_user=Depends(_get_current_user)
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

        # Save file
        uploads_dir = os.path.join(os.path.dirname(__file__), '../../uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        user_id = getattr(current_user, "id", "anonymous")
        user_dir = os.path.join(uploads_dir, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)

        file_path = os.path.join(user_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(contents)

        # Create presentation record
        presentation_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()

        file_type_map = {'.pdf': 'PDF', '.pptx': 'PowerPoint', '.docx': 'Word'}

        presentation = {
            "id": presentation_id,
            "title": os.path.splitext(filename)[0],
            "filename": filename,
            "file_type": file_type_map.get(file_ext, 'Document'),
            "file_size": len(contents),
            "status": "uploaded",
            "avatar_id": None,
            "voice_id": None,
            "description": "",
            "created_at": now,
            "updated_at": now,
            "analytics": {
                "views": 0,
                "unique_viewers": 0,
                "avg_watch_time": 0,
                "completion_rate": 0,
                "shares": 0,
                "downloads": 0,
                "last_viewed": None,
                "view_history": []
            }
        }

        _get_user_presentations(user_id).insert(0, presentation)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"File '{filename}' uploaded successfully",
                "presentation": presentation,
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
    current_user=Depends(_get_current_user)
):
    """Get list of user's presentations with analytics"""
    user_id = getattr(current_user, "id", "anonymous")
    presentations = _get_user_presentations(user_id).copy()

    if status_filter:
        presentations = [p for p in presentations if p["status"] == status_filter]

    if sort == "oldest":
        presentations.sort(key=lambda p: p["created_at"])
    elif sort == "most_viewed":
        presentations.sort(key=lambda p: p["analytics"]["views"], reverse=True)
    elif sort == "title":
        presentations.sort(key=lambda p: p["title"].lower())
    # default: newest first (already inserted at front)

    total_views = sum(p["analytics"]["views"] for p in presentations)
    total_shares = sum(p["analytics"]["shares"] for p in presentations)

    return {
        "presentations": presentations,
        "total": len(presentations),
        "summary": {
            "total_presentations": len(_get_user_presentations(user_id)),
            "total_views": total_views,
            "total_shares": total_shares,
            "statuses": {
                "uploaded": len([p for p in _get_user_presentations(user_id) if p["status"] == "uploaded"]),
                "processing": len([p for p in _get_user_presentations(user_id) if p["status"] == "processing"]),
                "ready": len([p for p in _get_user_presentations(user_id) if p["status"] == "ready"]),
                "published": len([p for p in _get_user_presentations(user_id) if p["status"] == "published"]),
            }
        }
    }


@router.get("/{presentation_id}")
async def get_presentation(presentation_id: str, current_user=Depends(_get_current_user)):
    """Get full presentation details with analytics"""
    user_id = getattr(current_user, "id", "anonymous")
    presentation = _find_presentation(user_id, presentation_id)
    if not presentation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    return {"presentation": presentation}


@router.put("/{presentation_id}")
async def update_presentation(
    presentation_id: str,
    update: PresentationUpdate,
    current_user=Depends(_get_current_user)
):
    """Update presentation title, description, avatar, voice, or status"""
    user_id = getattr(current_user, "id", "anonymous")
    presentation = _find_presentation(user_id, presentation_id)
    if not presentation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    if update.title is not None:
        presentation["title"] = update.title
    if update.description is not None:
        presentation["description"] = update.description
    if update.avatar_id is not None:
        presentation["avatar_id"] = update.avatar_id
    if update.voice_id is not None:
        presentation["voice_id"] = update.voice_id
    if update.status is not None:
        presentation["status"] = update.status
    presentation["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {"status": "success", "presentation": presentation}


@router.post("/{presentation_id}/view")
async def record_view(presentation_id: str, current_user=Depends(_get_current_user)):
    """Record a view event for analytics tracking"""
    user_id = getattr(current_user, "id", "anonymous")
    presentation = _find_presentation(user_id, presentation_id)
    if not presentation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    now = datetime.now(timezone.utc).isoformat()
    presentation["analytics"]["views"] += 1
    presentation["analytics"]["last_viewed"] = now
    presentation["analytics"]["view_history"].append({"timestamp": now, "viewer": "self"})
    # Keep only last 50 view events
    presentation["analytics"]["view_history"] = presentation["analytics"]["view_history"][-50:]

    return {"status": "success", "views": presentation["analytics"]["views"]}


@router.post("/{presentation_id}/share")
async def record_share(presentation_id: str, current_user=Depends(_get_current_user)):
    """Record a share event"""
    user_id = getattr(current_user, "id", "anonymous")
    presentation = _find_presentation(user_id, presentation_id)
    if not presentation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    presentation["analytics"]["shares"] += 1
    return {"status": "success", "shares": presentation["analytics"]["shares"]}


@router.delete("/{presentation_id}")
async def delete_presentation(presentation_id: str, current_user=Depends(_get_current_user)):
    """Delete a presentation"""
    user_id = getattr(current_user, "id", "anonymous")
    presentations = _get_user_presentations(user_id)
    idx = next((i for i, p in enumerate(presentations) if p["id"] == presentation_id), None)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    removed = presentations.pop(idx)
    # Also delete file from disk
    uploads_dir = os.path.join(os.path.dirname(__file__), '../../uploads')
    file_path = os.path.join(uploads_dir, f"user_{user_id}", removed["filename"])
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"status": "success", "message": f"Presentation '{removed['title']}' deleted"}

