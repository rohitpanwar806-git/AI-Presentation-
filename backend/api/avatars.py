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
# Using 'avataaars' style with gender-appropriate options for consistent appearance
def _avatar_url(seed, gender, bg="b6e3f4"):
    """Build a DiceBear avataaars URL with gender-appropriate features."""
    base = f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor={bg}&mouth=smile,default,twinkle"
    if gender == "female":
        base += "&top=bigHair,bob,bun,curly,curvy,straight01,straight02,straightAndStrand&facialHairProbability=0&accessories=prescription01,prescription02,round,sunglasses&accessoriesProbability=20"
    elif gender == "male":
        base += "&top=shortFlat,shortRound,shortWaved,shortCurly,theCaesar,theCaesarAndSidePart,sides&facialHairProbability=33&accessories=prescription01,prescription02,round&accessoriesProbability=15"
    else:
        base += "&top=shortWaved,bob,bun,curly,hat&facialHairProbability=0&accessoriesProbability=20"
    return base

AVAILABLE_AVATARS = [
    # === PROFESSIONAL / CORPORATE (10) ===
    {"id": "pro_01", "name": "Alex Chen", "gender": "male", "category": "professional", "age_range": "30-40", "description": "Confident tech executive with clean-cut look", "thumbnail": _avatar_url("AlexChen2", "male", "b6e3f4")},
    {"id": "pro_02", "name": "Sarah Mitchell", "gender": "female", "category": "professional", "age_range": "30-40", "description": "Polished corporate presenter with warm demeanor", "thumbnail": _avatar_url("SarahMitchell", "female", "c0aede")},
    {"id": "pro_03", "name": "David Okafor", "gender": "male", "category": "professional", "age_range": "35-45", "description": "Authoritative business leader", "thumbnail": _avatar_url("DavidOkafor", "male", "d1d4f9")},
    {"id": "pro_04", "name": "Priya Sharma", "gender": "female", "category": "professional", "age_range": "28-35", "description": "Dynamic tech industry professional", "thumbnail": _avatar_url("PriyaSharma", "female", "ffd5dc")},
    {"id": "pro_05", "name": "Michael Roberts", "gender": "male", "category": "professional", "age_range": "40-50", "description": "Senior executive with gravitas", "thumbnail": _avatar_url("MichaelRoberts", "male", "b6e3f4")},
    {"id": "pro_06", "name": "Aisha Hassan", "gender": "female", "category": "professional", "age_range": "30-40", "description": "Composed corporate strategist", "thumbnail": _avatar_url("AishaHassan", "female", "c0aede")},
    {"id": "pro_07", "name": "James Lee", "gender": "male", "category": "professional", "age_range": "35-45", "description": "Seasoned finance professional", "thumbnail": _avatar_url("JamesLee2", "male", "d1d4f9")},
    {"id": "pro_08", "name": "Elena Volkov", "gender": "female", "category": "professional", "age_range": "35-45", "description": "Sophisticated international executive", "thumbnail": _avatar_url("ElenaVolkov", "female", "ffd5dc")},
    {"id": "pro_09", "name": "Carlos Mendez", "gender": "male", "category": "professional", "age_range": "30-40", "description": "Charismatic business development lead", "thumbnail": _avatar_url("CarlosMendez", "male", "b6e3f4")},
    {"id": "pro_10", "name": "Nina Tanaka", "gender": "female", "category": "professional", "age_range": "28-35", "description": "Sharp product manager persona", "thumbnail": _avatar_url("NinaTanaka", "female", "c0aede")},

    # === FRIENDLY / APPROACHABLE (8) ===
    {"id": "fri_01", "name": "Emma Taylor", "gender": "female", "category": "friendly", "age_range": "25-35", "description": "Warm and approachable educator", "thumbnail": _avatar_url("EmmaTaylor", "female", "ffd5dc")},
    {"id": "fri_02", "name": "Jordan Blake", "gender": "non-binary", "category": "friendly", "age_range": "25-35", "description": "Casual and relatable host", "thumbnail": _avatar_url("JordanBlake", "non-binary", "b6e3f4")},
    {"id": "fri_03", "name": "Omar Farouk", "gender": "male", "category": "friendly", "age_range": "28-38", "description": "Energetic and engaging storyteller", "thumbnail": _avatar_url("OmarFarouk", "male", "d1d4f9")},
    {"id": "fri_04", "name": "Lisa Park", "gender": "female", "category": "friendly", "age_range": "25-32", "description": "Enthusiastic and personable guide", "thumbnail": _avatar_url("LisaPark2", "female", "c0aede")},
    {"id": "fri_05", "name": "Marcus Johnson", "gender": "male", "category": "friendly", "age_range": "28-35", "description": "Friendly team facilitator", "thumbnail": _avatar_url("MarcusJohnson", "male", "ffd5dc")},
    {"id": "fri_06", "name": "Sophia Rivera", "gender": "female", "category": "friendly", "age_range": "25-35", "description": "Cheerful community builder", "thumbnail": _avatar_url("SophiaRivera", "female", "b6e3f4")},
    {"id": "fri_07", "name": "Ryan Cooper", "gender": "male", "category": "friendly", "age_range": "25-35", "description": "Easygoing tech explainer", "thumbnail": _avatar_url("RyanCooper", "male", "d1d4f9")},
    {"id": "fri_08", "name": "Mei Lin", "gender": "female", "category": "friendly", "age_range": "22-30", "description": "Bright and engaging presenter", "thumbnail": _avatar_url("MeiLin2", "female", "c0aede")},

    # === CREATIVE / MODERN (8) ===
    {"id": "cre_01", "name": "Zara Obi", "gender": "female", "category": "creative", "age_range": "25-35", "description": "Bold creative director persona", "thumbnail": _avatar_url("ZaraObi", "female", "ffd5dc")},
    {"id": "cre_02", "name": "Kai Nakamura", "gender": "non-binary", "category": "creative", "age_range": "22-30", "description": "Edgy design-forward avatar", "thumbnail": _avatar_url("KaiNakamura", "non-binary", "b6e3f4")},
    {"id": "cre_03", "name": "Luna Garcia", "gender": "female", "category": "creative", "age_range": "25-32", "description": "Artistic and expressive storyteller", "thumbnail": _avatar_url("LunaGarcia", "female", "c0aede")},
    {"id": "cre_04", "name": "Felix Storm", "gender": "male", "category": "creative", "age_range": "25-35", "description": "Trendy startup founder vibes", "thumbnail": _avatar_url("FelixStorm", "male", "d1d4f9")},
    {"id": "cre_05", "name": "Nia Williams", "gender": "female", "category": "creative", "age_range": "28-35", "description": "Vibrant visual artist persona", "thumbnail": _avatar_url("NiaWilliams", "female", "ffd5dc")},
    {"id": "cre_06", "name": "Ravi Patel", "gender": "male", "category": "creative", "age_range": "25-35", "description": "Innovative tech creative", "thumbnail": _avatar_url("RaviPatel", "male", "b6e3f4")},
    {"id": "cre_07", "name": "Isla Chen", "gender": "female", "category": "creative", "age_range": "22-28", "description": "Fresh and modern influencer style", "thumbnail": _avatar_url("IslaChen", "female", "c0aede")},
    {"id": "cre_08", "name": "Andre Santos", "gender": "male", "category": "creative", "age_range": "28-38", "description": "Dynamic multimedia creator", "thumbnail": _avatar_url("AndreSantos", "male", "d1d4f9")},

    # === EDUCATION / TRAINING (6) ===
    {"id": "edu_01", "name": "Dr. Rebecca Lane", "gender": "female", "category": "education", "age_range": "40-50", "description": "Authoritative academic lecturer", "thumbnail": _avatar_url("RebeccaLane", "female", "ffd5dc")},
    {"id": "edu_02", "name": "Prof. Kwame Asante", "gender": "male", "category": "education", "age_range": "45-55", "description": "Wise and patient professor", "thumbnail": _avatar_url("KwameAsante", "male", "b6e3f4")},
    {"id": "edu_03", "name": "Ms. Yuki Hayashi", "gender": "female", "category": "education", "age_range": "30-40", "description": "Clear and structured instructor", "thumbnail": _avatar_url("YukiHayashi", "female", "c0aede")},
    {"id": "edu_04", "name": "Coach Dan Miller", "gender": "male", "category": "education", "age_range": "35-45", "description": "Motivational training coach", "thumbnail": _avatar_url("DanMiller", "male", "d1d4f9")},
    {"id": "edu_05", "name": "Dr. Amira Khalil", "gender": "female", "category": "education", "age_range": "35-45", "description": "Knowledgeable research presenter", "thumbnail": _avatar_url("AmiraKhalil", "female", "ffd5dc")},
    {"id": "edu_06", "name": "Mr. Raj Gupta", "gender": "male", "category": "education", "age_range": "40-50", "description": "Patient and thorough teacher", "thumbnail": _avatar_url("RajGupta2", "male", "b6e3f4")},

    # === MEDIA / BROADCAST (6) ===
    {"id": "med_01", "name": "Chris Anderson", "gender": "male", "category": "media", "age_range": "30-40", "description": "Professional news anchor style", "thumbnail": _avatar_url("ChrisAnderson", "male", "d1d4f9")},
    {"id": "med_02", "name": "Jasmine Wright", "gender": "female", "category": "media", "age_range": "28-38", "description": "Polished broadcast journalist", "thumbnail": _avatar_url("JasmineWright", "female", "c0aede")},
    {"id": "med_03", "name": "Arjun Mehta", "gender": "male", "category": "media", "age_range": "30-40", "description": "Articulate documentary narrator", "thumbnail": _avatar_url("ArjunMehta", "male", "ffd5dc")},
    {"id": "med_04", "name": "Victoria Stone", "gender": "female", "category": "media", "age_range": "35-45", "description": "Sophisticated talk show host", "thumbnail": _avatar_url("VictoriaStone", "female", "b6e3f4")},
    {"id": "med_05", "name": "Kenji Yamamoto", "gender": "male", "category": "media", "age_range": "35-45", "description": "Calm and authoritative commentator", "thumbnail": _avatar_url("KenjiYamamoto", "male", "d1d4f9")},
    {"id": "med_06", "name": "Isabella Rossi", "gender": "female", "category": "media", "age_range": "30-40", "description": "Engaging lifestyle presenter", "thumbnail": _avatar_url("IsabellaRossi", "female", "c0aede")},

    # === SALES / MARKETING (4) ===
    {"id": "sal_01", "name": "Brandon Hayes", "gender": "male", "category": "sales", "age_range": "30-40", "description": "Persuasive sales pitch delivery", "thumbnail": _avatar_url("BrandonHayes", "male", "ffd5dc")},
    {"id": "sal_02", "name": "Tanya Okonkwo", "gender": "female", "category": "sales", "age_range": "28-35", "description": "High-energy product evangelist", "thumbnail": _avatar_url("TanyaOkonkwo", "female", "b6e3f4")},
    {"id": "sal_03", "name": "Diego Fernandez", "gender": "male", "category": "sales", "age_range": "30-40", "description": "Charismatic deal closer", "thumbnail": _avatar_url("DiegoFernandez", "male", "d1d4f9")},
    {"id": "sal_04", "name": "Hannah Kim", "gender": "female", "category": "sales", "age_range": "25-35", "description": "Compelling growth marketer", "thumbnail": _avatar_url("HannahKim", "female", "c0aede")},

    # === HEALTHCARE / SCIENCE (4) ===
    {"id": "hc_01", "name": "Dr. Nathan Brooks", "gender": "male", "category": "healthcare", "age_range": "40-50", "description": "Trusted medical professional", "thumbnail": _avatar_url("NathanBrooks", "male", "ffd5dc")},
    {"id": "hc_02", "name": "Dr. Fatima Al-Rashid", "gender": "female", "category": "healthcare", "age_range": "35-45", "description": "Expert clinical researcher", "thumbnail": _avatar_url("FatimaRashid", "female", "b6e3f4")},
    {"id": "hc_03", "name": "Dr. Samuel Okoro", "gender": "male", "category": "healthcare", "age_range": "35-45", "description": "Knowledgeable health educator", "thumbnail": _avatar_url("SamuelOkoro", "male", "d1d4f9")},
    {"id": "hc_04", "name": "Dr. Mia Zhang", "gender": "female", "category": "healthcare", "age_range": "30-40", "description": "Biotech research scientist", "thumbnail": _avatar_url("MiaZhang", "female", "c0aede")},

    # === TECH / STARTUP (6) ===
    {"id": "tech_01", "name": "Jason Wu", "gender": "male", "category": "tech", "age_range": "25-35", "description": "Startup CTO demoing product", "thumbnail": _avatar_url("JasonWu2", "male", "ffd5dc")},
    {"id": "tech_02", "name": "Olivia Harper", "gender": "female", "category": "tech", "age_range": "25-35", "description": "DevRel engineer persona", "thumbnail": _avatar_url("OliviaHarper", "female", "b6e3f4")},
    {"id": "tech_03", "name": "Vikram Singh", "gender": "male", "category": "tech", "age_range": "28-38", "description": "AI/ML product demo specialist", "thumbnail": _avatar_url("VikramSingh", "male", "d1d4f9")},
    {"id": "tech_04", "name": "Chloe Bennett", "gender": "female", "category": "tech", "age_range": "25-32", "description": "UX design thought leader", "thumbnail": _avatar_url("ChloeBennett", "female", "c0aede")},
    {"id": "tech_05", "name": "Leo Tanaka", "gender": "male", "category": "tech", "age_range": "22-30", "description": "Young indie developer", "thumbnail": _avatar_url("LeoTanaka", "male", "ffd5dc")},
    {"id": "tech_06", "name": "Zoe Adeyemi", "gender": "female", "category": "tech", "age_range": "28-35", "description": "Cloud architecture expert", "thumbnail": _avatar_url("ZoeAdeyemi", "female", "b6e3f4")},
]

AVATAR_CATEGORIES = [
    {"id": "all", "name": "All Avatars", "icon": "則", "count": len(AVAILABLE_AVATARS)},
    {"id": "professional", "name": "Professional", "icon": "直", "count": 10},
    {"id": "friendly", "name": "Friendly", "icon": "・", "count": 8},
    {"id": "creative", "name": "Creative", "icon": "耳", "count": 8},
    {"id": "education", "name": "Education", "icon": "答", "count": 6},
    {"id": "media", "name": "Media", "icon": "銅", "count": 6},
    {"id": "sales", "name": "Sales", "icon": "嶋", "count": 4},
    {"id": "healthcare", "name": "Healthcare", "icon": "唱", "count": 4},
    {"id": "tech", "name": "Tech", "icon": "捗", "count": 6},
]


@router.get("/")
async def list_avatars(
    category: Optional[str] = Query(None, description="Filter by category"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
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
async def get_avatar(avatar_id: str):
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

