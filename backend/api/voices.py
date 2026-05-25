"""
Voice Management Endpoints
- List available voices (per language/region)
- Upload custom voice
- Get voice details
"""
from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.auth import _get_current_user

router = APIRouter()

# Predefined voice models (from ElevenLabs and Google TTS)
AVAILABLE_VOICES = [
    {
        "id": "voice_001",
        "name": "Alex - Deep Professional",
        "provider": "elevenlabs",
        "language": "en-US",
        "gender": "male",
        "description": "Deep, confident male voice perfect for business presentations",
        "accent": "American",
        "speed_range": [0.75, 1.25],
        "preview_url": "https://via.placeholder.com/audio?text=Preview"
    },
    {
        "id": "voice_002",
        "name": "Sarah - Warm Female",
        "provider": "elevenlabs",
        "language": "en-US",
        "gender": "female",
        "description": "Warm and engaging female voice for friendly presentations",
        "accent": "American",
        "speed_range": [0.75, 1.25],
        "preview_url": "https://via.placeholder.com/audio?text=Preview"
    },
    {
        "id": "voice_003",
        "name": "James - British Professional",
        "provider": "google-tts",
        "language": "en-GB",
        "gender": "male",
        "description": "Professional British accent for international presentations",
        "accent": "British",
        "speed_range": [0.75, 1.25],
        "preview_url": "https://via.placeholder.com/audio?text=Preview"
    },
    {
        "id": "voice_004",
        "name": "Emma - Neutral Standard",
        "provider": "google-tts",
        "language": "en-US",
        "gender": "female",
        "description": "Clear and neutral female voice suitable for all presentations",
        "accent": "American",
        "speed_range": [0.75, 1.25],
        "preview_url": "https://via.placeholder.com/audio?text=Preview"
    },
    {
        "id": "voice_005",
        "name": "David - Energetic Dynamic",
        "provider": "elevenlabs",
        "language": "en-US",
        "gender": "male",
        "description": "Energetic and dynamic voice for engaging presentations",
        "accent": "American",
        "speed_range": [0.75, 1.25],
        "preview_url": "https://via.placeholder.com/audio?text=Preview"
    }
]


@router.get("/")
async def list_voices(current_user = Depends(_get_current_user)):
    """Get list of available voice models"""
    return {
        "status": "success",
        "voices": AVAILABLE_VOICES,
        "total": len(AVAILABLE_VOICES),
        "message": "Available voice models for your presentation"
    }


@router.get("/{voice_id}")
async def get_voice(voice_id: str, current_user = Depends(_get_current_user)):
    """Get specific voice details"""
    voice = next((v for v in AVAILABLE_VOICES if v["id"] == voice_id), None)
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice '{voice_id}' not found"
        )
    return {
        "status": "success",
        "voice": voice
    }


@router.get("/languages/supported")
async def get_supported_languages(current_user = Depends(_get_current_user)):
    """Get list of supported languages"""
    languages = set(v["language"] for v in AVAILABLE_VOICES)
    return {
        "status": "success",
        "languages": sorted(list(languages)),
        "message": "Supported languages for voice synthesis"
    }


@router.post("/select")
async def select_voice(voice_id: str, current_user = Depends(_get_current_user)):
    """Select voice for presentation"""
    voice = next((v for v in AVAILABLE_VOICES if v["id"] == voice_id), None)
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice '{voice_id}' not found"
        )
    
    return {
        "status": "success",
        "selected_voice": voice,
        "message": f"Voice '{voice['name']}' selected successfully"
    }

