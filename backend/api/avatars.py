"""
Avatar Management Endpoints
- List 52 professional AI avatars across 8 categories
- Filter by category, gender
- Select avatar for presentation
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from backend.api.auth import _get_current_user

router = APIRouter()

# 52 Professional AI Avatars using DiceBear API for unique SVG thumbnails
AVAILABLE_AVATARS = [
    # === PROFESSIONAL / CORPORATE (10) ===
    {"id": "pro_01", "name": "Alex Chen", "gender": "male", "category": "professional", "age_range": "30-40", "description": "Confident tech executive with clean-cut look", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=AlexChen&backgroundColor=b6e3f4"},
    {"id": "pro_02", "name": "Sarah Mitchell", "gender": "female", "category": "professional", "age_range": "30-40", "description": "Polished corporate presenter with warm demeanor", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=SarahMitch&backgroundColor=c0aede"},
    {"id": "pro_03", "name": "David Okafor", "gender": "male", "category": "professional", "age_range": "35-45", "description": "Authoritative business leader", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DavidOka&backgroundColor=d1d4f9"},
    {"id": "pro_04", "name": "Priya Sharma", "gender": "female", "category": "professional", "age_range": "28-35", "description": "Dynamic tech industry professional", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=PriyaSha&backgroundColor=ffd5dc"},
    {"id": "pro_05", "name": "Michael Roberts", "gender": "male", "category": "professional", "age_range": "40-50", "description": "Senior executive with gravitas", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=MikeRob&backgroundColor=b6e3f4"},
    {"id": "pro_06", "name": "Aisha Hassan", "gender": "female", "category": "professional", "age_range": "30-40", "description": "Composed corporate strategist", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=AishaHas&backgroundColor=c0aede"},
    {"id": "pro_07", "name": "James Lee", "gender": "male", "category": "professional", "age_range": "35-45", "description": "Seasoned finance professional", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=JamesLee&backgroundColor=d1d4f9"},
    {"id": "pro_08", "name": "Elena Volkov", "gender": "female", "category": "professional", "age_range": "35-45", "description": "Sophisticated international executive", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ElenaVol&backgroundColor=ffd5dc"},
    {"id": "pro_09", "name": "Carlos Mendez", "gender": "male", "category": "professional", "age_range": "30-40", "description": "Charismatic business development lead", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=CarlosMen&backgroundColor=b6e3f4"},
    {"id": "pro_10", "name": "Nina Tanaka", "gender": "female", "category": "professional", "age_range": "28-35", "description": "Sharp product manager persona", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=NinaTan&backgroundColor=c0aede"},

    # === FRIENDLY / APPROACHABLE (8) ===
    {"id": "fri_01", "name": "Emma Taylor", "gender": "female", "category": "friendly", "age_range": "25-35", "description": "Warm and approachable educator", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=EmmaTay&backgroundColor=ffd5dc"},
    {"id": "fri_02", "name": "Jordan Blake", "gender": "non-binary", "category": "friendly", "age_range": "25-35", "description": "Casual and relatable host", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=JordanBl&backgroundColor=b6e3f4"},
    {"id": "fri_03", "name": "Omar Farouk", "gender": "male", "category": "friendly", "age_range": "28-38", "description": "Energetic and engaging storyteller", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=OmarFar&backgroundColor=d1d4f9"},
    {"id": "fri_04", "name": "Lisa Park", "gender": "female", "category": "friendly", "age_range": "25-32", "description": "Enthusiastic and personable guide", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=LisaPark&backgroundColor=c0aede"},
    {"id": "fri_05", "name": "Marcus Johnson", "gender": "male", "category": "friendly", "age_range": "28-35", "description": "Friendly team facilitator", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=MarcusJo&backgroundColor=ffd5dc"},
    {"id": "fri_06", "name": "Sophia Rivera", "gender": "female", "category": "friendly", "age_range": "25-35", "description": "Cheerful community builder", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=SophiaRi&backgroundColor=b6e3f4"},
    {"id": "fri_07", "name": "Ryan Cooper", "gender": "male", "category": "friendly", "age_range": "25-35", "description": "Easygoing tech explainer", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=RyanCoop&backgroundColor=d1d4f9"},
    {"id": "fri_08", "name": "Mei Lin", "gender": "female", "category": "friendly", "age_range": "22-30", "description": "Bright and engaging presenter", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=MeiLin&backgroundColor=c0aede"},

    # === CREATIVE / MODERN (8) ===
    {"id": "cre_01", "name": "Zara Obi", "gender": "female", "category": "creative", "age_range": "25-35", "description": "Bold creative director persona", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ZaraObi&backgroundColor=ffd5dc"},
    {"id": "cre_02", "name": "Kai Nakamura", "gender": "non-binary", "category": "creative", "age_range": "22-30", "description": "Edgy design-forward avatar", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=KaiNak&backgroundColor=b6e3f4"},
    {"id": "cre_03", "name": "Luna Garcia", "gender": "female", "category": "creative", "age_range": "25-32", "description": "Artistic and expressive storyteller", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=LunaGar&backgroundColor=c0aede"},
    {"id": "cre_04", "name": "Felix Storm", "gender": "male", "category": "creative", "age_range": "25-35", "description": "Trendy startup founder vibes", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=FelixSt&backgroundColor=d1d4f9"},
    {"id": "cre_05", "name": "Nia Williams", "gender": "female", "category": "creative", "age_range": "28-35", "description": "Vibrant visual artist persona", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=NiaWill&backgroundColor=ffd5dc"},
    {"id": "cre_06", "name": "Ravi Patel", "gender": "male", "category": "creative", "age_range": "25-35", "description": "Innovative tech creative", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=RaviPat&backgroundColor=b6e3f4"},
    {"id": "cre_07", "name": "Isla Chen", "gender": "female", "category": "creative", "age_range": "22-28", "description": "Fresh and modern influencer style", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=IslaChe&backgroundColor=c0aede"},
    {"id": "cre_08", "name": "Andre Santos", "gender": "male", "category": "creative", "age_range": "28-38", "description": "Dynamic multimedia creator", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=AndreSan&backgroundColor=d1d4f9"},

    # === EDUCATION / TRAINING (6) ===
    {"id": "edu_01", "name": "Dr. Rebecca Lane", "gender": "female", "category": "education", "age_range": "40-50", "description": "Authoritative academic lecturer", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DrLane&backgroundColor=ffd5dc"},
    {"id": "edu_02", "name": "Prof. Kwame Asante", "gender": "male", "category": "education", "age_range": "45-55", "description": "Wise and patient professor", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ProfKwame&backgroundColor=b6e3f4"},
    {"id": "edu_03", "name": "Ms. Yuki Hayashi", "gender": "female", "category": "education", "age_range": "30-40", "description": "Clear and structured instructor", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=YukiHay&backgroundColor=c0aede"},
    {"id": "edu_04", "name": "Coach Dan Miller", "gender": "male", "category": "education", "age_range": "35-45", "description": "Motivational training coach", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=CoachDan&backgroundColor=d1d4f9"},
    {"id": "edu_05", "name": "Dr. Amira Khalil", "gender": "female", "category": "education", "age_range": "35-45", "description": "Knowledgeable research presenter", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DrAmira&backgroundColor=ffd5dc"},
    {"id": "edu_06", "name": "Mr. Raj Gupta", "gender": "male", "category": "education", "age_range": "40-50", "description": "Patient and thorough teacher", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=RajGupta&backgroundColor=b6e3f4"},

    # === MEDIA / BROADCAST (6) ===
    {"id": "med_01", "name": "Chris Anderson", "gender": "male", "category": "media", "age_range": "30-40", "description": "Professional news anchor style", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ChrisAn&backgroundColor=d1d4f9"},
    {"id": "med_02", "name": "Jasmine Wright", "gender": "female", "category": "media", "age_range": "28-38", "description": "Polished broadcast journalist", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=JasmineW&backgroundColor=c0aede"},
    {"id": "med_03", "name": "Arjun Mehta", "gender": "male", "category": "media", "age_range": "30-40", "description": "Articulate documentary narrator", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ArjunMe&backgroundColor=ffd5dc"},
    {"id": "med_04", "name": "Victoria Stone", "gender": "female", "category": "media", "age_range": "35-45", "description": "Sophisticated talk show host", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=VicStone&backgroundColor=b6e3f4"},
    {"id": "med_05", "name": "Kenji Yamamoto", "gender": "male", "category": "media", "age_range": "35-45", "description": "Calm and authoritative commentator", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=KenjiYam&backgroundColor=d1d4f9"},
    {"id": "med_06", "name": "Isabella Rossi", "gender": "female", "category": "media", "age_range": "30-40", "description": "Engaging lifestyle presenter", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=IsabRos&backgroundColor=c0aede"},

    # === SALES / MARKETING (4) ===
    {"id": "sal_01", "name": "Brandon Hayes", "gender": "male", "category": "sales", "age_range": "30-40", "description": "Persuasive sales pitch delivery", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=BrandonH&backgroundColor=ffd5dc"},
    {"id": "sal_02", "name": "Tanya Okonkwo", "gender": "female", "category": "sales", "age_range": "28-35", "description": "High-energy product evangelist", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=TanyaOk&backgroundColor=b6e3f4"},
    {"id": "sal_03", "name": "Diego Fernandez", "gender": "male", "category": "sales", "age_range": "30-40", "description": "Charismatic deal closer", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DiegoFer&backgroundColor=d1d4f9"},
    {"id": "sal_04", "name": "Hannah Kim", "gender": "female", "category": "sales", "age_range": "25-35", "description": "Compelling growth marketer", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=HannahKi&backgroundColor=c0aede"},

    # === HEALTHCARE / SCIENCE (4) ===
    {"id": "hc_01", "name": "Dr. Nathan Brooks", "gender": "male", "category": "healthcare", "age_range": "40-50", "description": "Trusted medical professional", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DrBrooks&backgroundColor=ffd5dc"},
    {"id": "hc_02", "name": "Dr. Fatima Al-Rashid", "gender": "female", "category": "healthcare", "age_range": "35-45", "description": "Expert clinical researcher", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DrFatima&backgroundColor=b6e3f4"},
    {"id": "hc_03", "name": "Dr. Samuel Okoro", "gender": "male", "category": "healthcare", "age_range": "35-45", "description": "Knowledgeable health educator", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DrSamuel&backgroundColor=d1d4f9"},
    {"id": "hc_04", "name": "Dr. Mia Zhang", "gender": "female", "category": "healthcare", "age_range": "30-40", "description": "Biotech research scientist", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=DrMiaZ&backgroundColor=c0aede"},

    # === TECH / STARTUP (6) ===
    {"id": "tech_01", "name": "Jason Wu", "gender": "male", "category": "tech", "age_range": "25-35", "description": "Startup CTO demoing product", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=JasonWu&backgroundColor=ffd5dc"},
    {"id": "tech_02", "name": "Olivia Harper", "gender": "female", "category": "tech", "age_range": "25-35", "description": "DevRel engineer persona", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=OliviaHa&backgroundColor=b6e3f4"},
    {"id": "tech_03", "name": "Vikram Singh", "gender": "male", "category": "tech", "age_range": "28-38", "description": "AI/ML product demo specialist", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=VikramSi&backgroundColor=d1d4f9"},
    {"id": "tech_04", "name": "Chloe Bennett", "gender": "female", "category": "tech", "age_range": "25-32", "description": "UX design thought leader", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ChloeBen&backgroundColor=c0aede"},
    {"id": "tech_05", "name": "Leo Tanaka", "gender": "male", "category": "tech", "age_range": "22-30", "description": "Young indie developer", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=LeoTan&backgroundColor=ffd5dc"},
    {"id": "tech_06", "name": "Zoe Adeyemi", "gender": "female", "category": "tech", "age_range": "28-35", "description": "Cloud architecture expert", "thumbnail": "https://api.dicebear.com/9.x/personas/svg?seed=ZoeAde&backgroundColor=b6e3f4"},
]

AVATAR_CATEGORIES = [
    {"id": "all", "name": "All Avatars", "icon": "👥", "count": len(AVAILABLE_AVATARS)},
    {"id": "professional", "name": "Professional", "icon": "💼", "count": 10},
    {"id": "friendly", "name": "Friendly", "icon": "😊", "count": 8},
    {"id": "creative", "name": "Creative", "icon": "🎨", "count": 8},
    {"id": "education", "name": "Education", "icon": "📚", "count": 6},
    {"id": "media", "name": "Media", "icon": "📺", "count": 6},
    {"id": "sales", "name": "Sales", "icon": "📈", "count": 4},
    {"id": "healthcare", "name": "Healthcare", "icon": "🏥", "count": 4},
    {"id": "tech", "name": "Tech", "icon": "💻", "count": 6},
]


@router.get("/")
async def list_avatars(
    category: Optional[str] = Query(None, description="Filter by category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    current_user=Depends(_get_current_user)
):
    """Get list of 52 professional AI avatars with optional filtering"""
    avatars = AVAILABLE_AVATARS
    if category and category != "all":
        avatars = [a for a in avatars if a["category"] == category]
    if gender:
        avatars = [a for a in avatars if a["gender"] == gender]
    return {
        "avatars": avatars,
        "total": len(avatars),
        "categories": AVATAR_CATEGORIES,
    }


@router.get("/{avatar_id}")
async def get_avatar(avatar_id: str, current_user=Depends(_get_current_user)):
    """Get specific avatar details"""
    avatar = next((a for a in AVAILABLE_AVATARS if a["id"] == avatar_id), None)
    if not avatar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Avatar '{avatar_id}' not found")
    return {"avatar": avatar}


@router.post("/select")
async def select_avatar(avatar_id: str, current_user=Depends(_get_current_user)):
    """Select avatar for a presentation"""
    avatar = next((a for a in AVAILABLE_AVATARS if a["id"] == avatar_id), None)
    if not avatar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Avatar '{avatar_id}' not found")
    return {
        "status": "success",
        "selected_avatar": avatar,
        "message": f"Avatar '{avatar['name']}' selected successfully"
    }

