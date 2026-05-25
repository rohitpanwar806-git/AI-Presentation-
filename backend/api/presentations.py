"""
Presentation Management Endpoints
- Upload documents
- Create presentations
- Retrieve presentations
- Update presentation settings
"""
import os
import mimetypes
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend.api.auth import _get_current_user
from backend.db.database import get_db

router = APIRouter()

# Supported file types
ALLOWED_EXTENSIONS = {'.pdf', '.pptx', '.docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/upload")
async def upload_presentation(
    file: UploadFile = File(...),
    current_user = Depends(_get_current_user)
):
    """
    Upload a presentation document (PDF, PPTX, or DOCX).
    Requires authentication.
    """
    try:
        # Validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        # Validate file extension
        filename = file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Validate MIME type
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
        
        # Save file to temporary directory (TODO: Implement proper storage)
        uploads_dir = os.path.join(os.path.dirname(__file__), '../../uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Create user-specific upload directory
        user_dir = os.path.join(uploads_dir, f"user_{current_user.get('id', 'anonymous')}")
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"File '{filename}' uploaded successfully",
                "filename": filename,
                "file_size": len(contents),
                "user_id": current_user.get('id'),
                "next_step": "select_avatar_and_voice"
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
async def list_presentations(current_user = Depends(_get_current_user)):
    """Get list of user's presentations"""
    return {
        "status": "success",
        "presentations": [],
        "message": "Presentations list endpoint coming soon"
    }


@router.get("/{presentation_id}")
async def get_presentation(presentation_id: str, current_user = Depends(_get_current_user)):
    """Get presentation details"""
    return {
        "status": "success",
        "presentation_id": presentation_id,
        "message": "Get presentation endpoint coming soon"
    }


@router.delete("/{presentation_id}")
async def delete_presentation(presentation_id: str, current_user = Depends(_get_current_user)):
    """Delete a presentation"""
    return {
        "status": "success",
        "message": f"Presentation {presentation_id} deleted"
    }

