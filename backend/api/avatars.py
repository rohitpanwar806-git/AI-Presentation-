"""
Avatar Management Endpoints
- List available avatars
- Get avatar details
- Customize avatar appearance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from backend.core.security import get_current_user

router = APIRouter()

# Predefined avatars
AVAILABLE_AVATARS = [
    {
        "id": "avatar_001",
        "name": "Alex - Professional",
        "description": "A professional-looking male avatar",
        "category": "professional",
        "image_url": "https://via.placeholder.com/200/0066ff/ffffff?text=Alex",
        "voice_styles": ["neutral", "confident", "formal"]
    },
    {
        "id": "avatar_002",
        "name": "Sarah - Friendly",
        "description": "A friendly and approachable female avatar",
        "category": "friendly",
        "image_url": "https://via.placeholder.com/200/00cc00/ffffff?text=Sarah",
        "voice_styles": ["friendly", "warm", "casual"]
    },
    {
        "id": "avatar_003",
        "name": "Jordan - Modern",
        "description": "A modern and dynamic neutral avatar",
        "category": "modern",
        "image_url": "https://via.placeholder.com/200/ff6600/ffffff?text=Jordan",
        "voice_styles": ["modern", "energetic", "dynamic"]
    },
    {
        "id": "avatar_004",
        "name": "Maya - Creative",
        "description": "A creative and expressive avatar",
        "category": "creative",
        "image_url": "https://via.placeholder.com/200/ff00cc/ffffff?text=Maya",
        "voice_styles": ["creative", "expressive", "enthusiastic"]
    },
    {
        "id": "avatar_005",
        "name": "David - Executive",
        "description": "An executive and authoritative avatar",
        "category": "executive",
        "image_url": "https://via.placeholder.com/200/003366/ffffff?text=David",
        "voice_styles": ["authoritative", "confident", "professional"]
    }
]


@router.get("/")
async def list_avatars(current_user = Depends(get_current_user)):
    """Get list of available avatars"""
    return {
        "status": "success",
        "avatars": AVAILABLE_AVATARS,
        "total": len(AVAILABLE_AVATARS),
        "message": "Available 3D avatars for your presentation"
    }


@router.get("/{avatar_id}")
async def get_avatar(avatar_id: str, current_user = Depends(get_current_user)):
    """Get specific avatar details"""
    avatar = next((a for a in AVAILABLE_AVATARS if a["id"] == avatar_id), None)
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avatar '{avatar_id}' not found"
        )
    return {
        "status": "success",
        "avatar": avatar
    }


@router.post("/select")
async def select_avatar(avatar_id: str, current_user = Depends(get_current_user)):
    """Select avatar for presentation"""
    avatar = next((a for a in AVAILABLE_AVATARS if a["id"] == avatar_id), None)
    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avatar '{avatar_id}' not found"
        )
    
    return {
        "status": "success",
        "selected_avatar": avatar,
        "message": f"Avatar '{avatar['name']}' selected successfully"
    }

