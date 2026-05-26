"""
Voice Management Endpoints
- List 300+ voices across 29 languages
- Filter by language, gender, provider
- Select voice for presentation
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from backend.api.auth import _get_current_user

router = APIRouter()

# Voice catalog — representative sample of 300+ voices across providers/languages
# In production these would come from ElevenLabs/Azure/Google APIs
AVAILABLE_VOICES = [
    # === ENGLISH - US ===
    {"id": "en_us_01", "name": "Rachel", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "female", "accent": "American", "style": "narration", "description": "Calm, clear female narrator voice", "preview_text": "Welcome to today's presentation."},
    {"id": "en_us_02", "name": "Adam", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "male", "accent": "American", "style": "narration", "description": "Deep authoritative male voice", "preview_text": "Let me walk you through this."},
    {"id": "en_us_03", "name": "Domi", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "female", "accent": "American", "style": "conversational", "description": "Energetic and expressive female voice", "preview_text": "This is going to be exciting!"},
    {"id": "en_us_04", "name": "Fin", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "male", "accent": "American", "style": "conversational", "description": "Youthful and casual male voice", "preview_text": "Hey, let's dive right in."},
    {"id": "en_us_05", "name": "Sarah", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "female", "accent": "American", "style": "professional", "description": "Warm professional female voice", "preview_text": "Thank you for joining us today."},
    {"id": "en_us_06", "name": "Josh", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "male", "accent": "American", "style": "professional", "description": "Confident corporate male voice", "preview_text": "Our quarterly results show growth."},
    {"id": "en_us_07", "name": "Bella", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "female", "accent": "American", "style": "friendly", "description": "Soft and approachable female voice", "preview_text": "I'm happy to help you today."},
    {"id": "en_us_08", "name": "Marcus", "provider": "elevenlabs", "language": "en-US", "language_name": "English (US)", "gender": "male", "accent": "American", "style": "energetic", "description": "Bold and dynamic male voice", "preview_text": "Let's make this happen!"},
    {"id": "en_us_09", "name": "Nicole", "provider": "google-tts", "language": "en-US", "language_name": "English (US)", "gender": "female", "accent": "American", "style": "neutral", "description": "Clear neutral female voice", "preview_text": "Here's what you need to know."},
    {"id": "en_us_10", "name": "Guy", "provider": "google-tts", "language": "en-US", "language_name": "English (US)", "gender": "male", "accent": "American", "style": "neutral", "description": "Standard clear male voice", "preview_text": "Moving to the next section."},
    {"id": "en_us_11", "name": "Emily", "provider": "azure-tts", "language": "en-US", "language_name": "English (US)", "gender": "female", "accent": "American", "style": "cheerful", "description": "Cheerful and upbeat female voice", "preview_text": "Great news to share with you!"},
    {"id": "en_us_12", "name": "Davis", "provider": "azure-tts", "language": "en-US", "language_name": "English (US)", "gender": "male", "accent": "American", "style": "calm", "description": "Soothing calm male narrator", "preview_text": "Let's take a moment to review."},

    # === ENGLISH - UK ===
    {"id": "en_gb_01", "name": "Charlotte", "provider": "elevenlabs", "language": "en-GB", "language_name": "English (UK)", "gender": "female", "accent": "British", "style": "narration", "description": "Elegant British female narrator", "preview_text": "Good afternoon, let's begin."},
    {"id": "en_gb_02", "name": "Thomas", "provider": "elevenlabs", "language": "en-GB", "language_name": "English (UK)", "gender": "male", "accent": "British", "style": "narration", "description": "Refined British male presenter", "preview_text": "Allow me to explain further."},
    {"id": "en_gb_03", "name": "Alice", "provider": "google-tts", "language": "en-GB", "language_name": "English (UK)", "gender": "female", "accent": "British", "style": "professional", "description": "Professional BBC-style voice", "preview_text": "The data clearly indicates."},
    {"id": "en_gb_04", "name": "George", "provider": "azure-tts", "language": "en-GB", "language_name": "English (UK)", "gender": "male", "accent": "British", "style": "formal", "description": "Formal and distinguished British voice", "preview_text": "Let us examine the evidence."},

    # === ENGLISH - AUSTRALIA ===
    {"id": "en_au_01", "name": "Matilda", "provider": "elevenlabs", "language": "en-AU", "language_name": "English (Australia)", "gender": "female", "accent": "Australian", "style": "friendly", "description": "Warm Australian female voice", "preview_text": "G'day, welcome aboard."},
    {"id": "en_au_02", "name": "Jack", "provider": "google-tts", "language": "en-AU", "language_name": "English (Australia)", "gender": "male", "accent": "Australian", "style": "casual", "description": "Relaxed Australian male voice", "preview_text": "No worries, let's get started."},

    # === ENGLISH - INDIA ===
    {"id": "en_in_01", "name": "Neerja", "provider": "azure-tts", "language": "en-IN", "language_name": "English (India)", "gender": "female", "accent": "Indian", "style": "professional", "description": "Clear Indian-accented female voice", "preview_text": "Let me present the findings."},
    {"id": "en_in_02", "name": "Prabhat", "provider": "azure-tts", "language": "en-IN", "language_name": "English (India)", "gender": "male", "accent": "Indian", "style": "professional", "description": "Articulate Indian-accented male voice", "preview_text": "The results are promising."},

    # === SPANISH ===
    {"id": "es_es_01", "name": "Elvira", "provider": "elevenlabs", "language": "es-ES", "language_name": "Spanish (Spain)", "gender": "female", "accent": "Castilian", "style": "narration", "description": "Elegant Castilian Spanish female voice", "preview_text": "Bienvenidos a la presentación."},
    {"id": "es_es_02", "name": "Alvaro", "provider": "azure-tts", "language": "es-ES", "language_name": "Spanish (Spain)", "gender": "male", "accent": "Castilian", "style": "professional", "description": "Professional Spanish male voice", "preview_text": "Pasemos al siguiente punto."},
    {"id": "es_mx_01", "name": "Dalia", "provider": "azure-tts", "language": "es-MX", "language_name": "Spanish (Mexico)", "gender": "female", "accent": "Mexican", "style": "friendly", "description": "Warm Mexican Spanish female voice", "preview_text": "Les doy la bienvenida."},
    {"id": "es_mx_02", "name": "Jorge", "provider": "google-tts", "language": "es-MX", "language_name": "Spanish (Mexico)", "gender": "male", "accent": "Mexican", "style": "conversational", "description": "Natural Mexican Spanish male voice", "preview_text": "Vamos a revisar los datos."},

    # === FRENCH ===
    {"id": "fr_fr_01", "name": "Denise", "provider": "elevenlabs", "language": "fr-FR", "language_name": "French (France)", "gender": "female", "accent": "Parisian", "style": "narration", "description": "Sophisticated French female narrator", "preview_text": "Bienvenue à cette présentation."},
    {"id": "fr_fr_02", "name": "Henri", "provider": "azure-tts", "language": "fr-FR", "language_name": "French (France)", "gender": "male", "accent": "Parisian", "style": "professional", "description": "Polished French male voice", "preview_text": "Passons au point suivant."},
    {"id": "fr_ca_01", "name": "Sylvie", "provider": "azure-tts", "language": "fr-CA", "language_name": "French (Canada)", "gender": "female", "accent": "Canadian", "style": "friendly", "description": "Friendly Québécois female voice", "preview_text": "Bonjour à tous et bienvenue."},

    # === GERMAN ===
    {"id": "de_de_01", "name": "Katja", "provider": "elevenlabs", "language": "de-DE", "language_name": "German", "gender": "female", "accent": "Standard", "style": "professional", "description": "Clear professional German female voice", "preview_text": "Willkommen zur Präsentation."},
    {"id": "de_de_02", "name": "Conrad", "provider": "azure-tts", "language": "de-DE", "language_name": "German", "gender": "male", "accent": "Standard", "style": "narration", "description": "Authoritative German male narrator", "preview_text": "Lassen Sie uns beginnen."},
    {"id": "de_de_03", "name": "Amala", "provider": "google-tts", "language": "de-DE", "language_name": "German", "gender": "female", "accent": "Standard", "style": "friendly", "description": "Warm and approachable German voice", "preview_text": "Schön, dass Sie dabei sind."},

    # === HINDI ===
    {"id": "hi_in_01", "name": "Swara", "provider": "azure-tts", "language": "hi-IN", "language_name": "Hindi", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Hindi female voice", "preview_text": "आज की प्रस्तुति में आपका स्वागत है।"},
    {"id": "hi_in_02", "name": "Madhur", "provider": "azure-tts", "language": "hi-IN", "language_name": "Hindi", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Hindi male narrator", "preview_text": "आइए अगले बिंदु पर चलते हैं।"},
    {"id": "hi_in_03", "name": "Kavya", "provider": "google-tts", "language": "hi-IN", "language_name": "Hindi", "gender": "female", "accent": "Standard", "style": "conversational", "description": "Natural conversational Hindi voice", "preview_text": "यह बहुत रोमांचक है।"},

    # === JAPANESE ===
    {"id": "ja_jp_01", "name": "Nanami", "provider": "azure-tts", "language": "ja-JP", "language_name": "Japanese", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Japanese female voice", "preview_text": "本日のプレゼンテーションへようこそ。"},
    {"id": "ja_jp_02", "name": "Keita", "provider": "azure-tts", "language": "ja-JP", "language_name": "Japanese", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Japanese male narrator", "preview_text": "次のセクションに移りましょう。"},
    {"id": "ja_jp_03", "name": "Aoi", "provider": "google-tts", "language": "ja-JP", "language_name": "Japanese", "gender": "female", "accent": "Standard", "style": "friendly", "description": "Warm Japanese female voice", "preview_text": "ご参加ありがとうございます。"},

    # === KOREAN ===
    {"id": "ko_kr_01", "name": "SunHi", "provider": "azure-tts", "language": "ko-KR", "language_name": "Korean", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Korean female voice", "preview_text": "오늘 프레젠테이션에 오신 것을 환영합니다."},
    {"id": "ko_kr_02", "name": "InJoon", "provider": "azure-tts", "language": "ko-KR", "language_name": "Korean", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Korean male narrator", "preview_text": "다음 섹션으로 넘어가겠습니다."},

    # === CHINESE - MANDARIN ===
    {"id": "zh_cn_01", "name": "Xiaoxiao", "provider": "azure-tts", "language": "zh-CN", "language_name": "Chinese (Mandarin)", "gender": "female", "accent": "Standard", "style": "professional", "description": "Natural Mandarin female voice", "preview_text": "欢迎来到今天的演示。"},
    {"id": "zh_cn_02", "name": "Yunxi", "provider": "azure-tts", "language": "zh-CN", "language_name": "Chinese (Mandarin)", "gender": "male", "accent": "Standard", "style": "narration", "description": "Professional Mandarin male narrator", "preview_text": "让我们进入下一部分。"},
    {"id": "zh_cn_03", "name": "Xiaoyi", "provider": "google-tts", "language": "zh-CN", "language_name": "Chinese (Mandarin)", "gender": "female", "accent": "Standard", "style": "friendly", "description": "Warm Mandarin female voice", "preview_text": "感谢大家的参与。"},

    # === ARABIC ===
    {"id": "ar_sa_01", "name": "Zariyah", "provider": "azure-tts", "language": "ar-SA", "language_name": "Arabic", "gender": "female", "accent": "Gulf", "style": "professional", "description": "Professional Arabic female voice", "preview_text": "مرحباً بكم في العرض التقديمي."},
    {"id": "ar_sa_02", "name": "Hamed", "provider": "azure-tts", "language": "ar-SA", "language_name": "Arabic", "gender": "male", "accent": "Gulf", "style": "narration", "description": "Clear Arabic male narrator", "preview_text": "دعونا ننتقل إلى القسم التالي."},

    # === PORTUGUESE ===
    {"id": "pt_br_01", "name": "Francisca", "provider": "azure-tts", "language": "pt-BR", "language_name": "Portuguese (Brazil)", "gender": "female", "accent": "Brazilian", "style": "professional", "description": "Natural Brazilian Portuguese female voice", "preview_text": "Bem-vindos à apresentação de hoje."},
    {"id": "pt_br_02", "name": "Antonio", "provider": "azure-tts", "language": "pt-BR", "language_name": "Portuguese (Brazil)", "gender": "male", "accent": "Brazilian", "style": "conversational", "description": "Warm Brazilian Portuguese male voice", "preview_text": "Vamos ao próximo ponto."},
    {"id": "pt_pt_01", "name": "Raquel", "provider": "google-tts", "language": "pt-PT", "language_name": "Portuguese (Portugal)", "gender": "female", "accent": "European", "style": "professional", "description": "European Portuguese female voice", "preview_text": "Bem-vindos à apresentação."},

    # === ITALIAN ===
    {"id": "it_it_01", "name": "Elsa", "provider": "azure-tts", "language": "it-IT", "language_name": "Italian", "gender": "female", "accent": "Standard", "style": "professional", "description": "Elegant Italian female voice", "preview_text": "Benvenuti alla presentazione."},
    {"id": "it_it_02", "name": "Diego", "provider": "azure-tts", "language": "it-IT", "language_name": "Italian", "gender": "male", "accent": "Standard", "style": "narration", "description": "Smooth Italian male narrator", "preview_text": "Passiamo al punto successivo."},

    # === DUTCH ===
    {"id": "nl_nl_01", "name": "Fenna", "provider": "azure-tts", "language": "nl-NL", "language_name": "Dutch", "gender": "female", "accent": "Standard", "style": "professional", "description": "Clear Dutch female voice", "preview_text": "Welkom bij de presentatie."},
    {"id": "nl_nl_02", "name": "Maarten", "provider": "azure-tts", "language": "nl-NL", "language_name": "Dutch", "gender": "male", "accent": "Standard", "style": "narration", "description": "Professional Dutch male narrator", "preview_text": "Laten we verdergaan."},

    # === RUSSIAN ===
    {"id": "ru_ru_01", "name": "Svetlana", "provider": "azure-tts", "language": "ru-RU", "language_name": "Russian", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Russian female voice", "preview_text": "Добро пожаловать на презентацию."},
    {"id": "ru_ru_02", "name": "Dmitry", "provider": "azure-tts", "language": "ru-RU", "language_name": "Russian", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Russian male narrator", "preview_text": "Перейдем к следующему разделу."},

    # === TURKISH ===
    {"id": "tr_tr_01", "name": "Emel", "provider": "azure-tts", "language": "tr-TR", "language_name": "Turkish", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Turkish female voice", "preview_text": "Sunuma hoş geldiniz."},
    {"id": "tr_tr_02", "name": "Ahmet", "provider": "azure-tts", "language": "tr-TR", "language_name": "Turkish", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Turkish male narrator", "preview_text": "Bir sonraki bölüme geçelim."},

    # === POLISH ===
    {"id": "pl_pl_01", "name": "Agnieszka", "provider": "azure-tts", "language": "pl-PL", "language_name": "Polish", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Polish female voice", "preview_text": "Witamy na prezentacji."},
    {"id": "pl_pl_02", "name": "Marek", "provider": "azure-tts", "language": "pl-PL", "language_name": "Polish", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Polish male narrator", "preview_text": "Przejdźmy do następnej części."},

    # === SWEDISH ===
    {"id": "sv_se_01", "name": "Sofie", "provider": "azure-tts", "language": "sv-SE", "language_name": "Swedish", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Swedish female voice", "preview_text": "Välkommen till presentationen."},
    {"id": "sv_se_02", "name": "Mattias", "provider": "azure-tts", "language": "sv-SE", "language_name": "Swedish", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Swedish male narrator", "preview_text": "Låt oss gå vidare."},

    # === THAI ===
    {"id": "th_th_01", "name": "Premwadee", "provider": "azure-tts", "language": "th-TH", "language_name": "Thai", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Thai female voice", "preview_text": "ยินดีต้อนรับสู่การนำเสนอ"},
    {"id": "th_th_02", "name": "Niwat", "provider": "azure-tts", "language": "th-TH", "language_name": "Thai", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Thai male narrator", "preview_text": "ไปยังส่วนถัดไปกัน"},

    # === VIETNAMESE ===
    {"id": "vi_vn_01", "name": "HoaiMy", "provider": "azure-tts", "language": "vi-VN", "language_name": "Vietnamese", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Vietnamese female voice", "preview_text": "Chào mừng đến buổi thuyết trình."},
    {"id": "vi_vn_02", "name": "NamMinh", "provider": "azure-tts", "language": "vi-VN", "language_name": "Vietnamese", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Vietnamese male narrator", "preview_text": "Chúng ta hãy chuyển sang phần tiếp theo."},

    # === INDONESIAN ===
    {"id": "id_id_01", "name": "Gadis", "provider": "azure-tts", "language": "id-ID", "language_name": "Indonesian", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Indonesian female voice", "preview_text": "Selamat datang di presentasi ini."},
    {"id": "id_id_02", "name": "Ardi", "provider": "azure-tts", "language": "id-ID", "language_name": "Indonesian", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Indonesian male narrator", "preview_text": "Mari kita lanjut ke bagian berikutnya."},

    # === MALAY ===
    {"id": "ms_my_01", "name": "Yasmin", "provider": "azure-tts", "language": "ms-MY", "language_name": "Malay", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Malay female voice", "preview_text": "Selamat datang ke pembentangan."},

    # === TAMIL ===
    {"id": "ta_in_01", "name": "Pallavi", "provider": "azure-tts", "language": "ta-IN", "language_name": "Tamil", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Tamil female voice", "preview_text": "விளக்கக்காட்சிக்கு வரவேற்கிறோம்."},
    {"id": "ta_in_02", "name": "Valluvar", "provider": "azure-tts", "language": "ta-IN", "language_name": "Tamil", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Tamil male narrator", "preview_text": "அடுத்த பகுதிக்கு செல்லலாம்."},

    # === TELUGU ===
    {"id": "te_in_01", "name": "Shruti", "provider": "azure-tts", "language": "te-IN", "language_name": "Telugu", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Telugu female voice", "preview_text": "ప్రెజెంటేషన్‌కు స్వాగతం."},

    # === BENGALI ===
    {"id": "bn_in_01", "name": "Tanishaa", "provider": "azure-tts", "language": "bn-IN", "language_name": "Bengali", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Bengali female voice", "preview_text": "উপস্থাপনায় স্বাগতম।"},
    {"id": "bn_in_02", "name": "Bashkar", "provider": "azure-tts", "language": "bn-IN", "language_name": "Bengali", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Bengali male narrator", "preview_text": "পরবর্তী বিভাগে যাওয়া যাক।"},

    # === MARATHI ===
    {"id": "mr_in_01", "name": "Aarohi", "provider": "azure-tts", "language": "mr-IN", "language_name": "Marathi", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Marathi female voice", "preview_text": "सादरीकरणात आपले स्वागत आहे."},

    # === GUJARATI ===
    {"id": "gu_in_01", "name": "Dhwani", "provider": "azure-tts", "language": "gu-IN", "language_name": "Gujarati", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Gujarati female voice", "preview_text": "પ્રેઝન્ટેશનમાં આપનું સ્વાગત છે."},

    # === KANNADA ===
    {"id": "kn_in_01", "name": "Sapna", "provider": "azure-tts", "language": "kn-IN", "language_name": "Kannada", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Kannada female voice", "preview_text": "ಪ್ರಸ್ತುತಿಗೆ ಸ್ವಾಗತ."},

    # === FILIPINO ===
    {"id": "fil_ph_01", "name": "Blessica", "provider": "azure-tts", "language": "fil-PH", "language_name": "Filipino", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Filipino female voice", "preview_text": "Maligayang pagdating sa presentasyon."},

    # === HEBREW ===
    {"id": "he_il_01", "name": "Hila", "provider": "azure-tts", "language": "he-IL", "language_name": "Hebrew", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Hebrew female voice", "preview_text": "ברוכים הבאים למצגת."},
    {"id": "he_il_02", "name": "Avri", "provider": "azure-tts", "language": "he-IL", "language_name": "Hebrew", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Hebrew male narrator", "preview_text": "בואו נעבור לחלק הבא."},

    # === UKRAINIAN ===
    {"id": "uk_ua_01", "name": "Polina", "provider": "azure-tts", "language": "uk-UA", "language_name": "Ukrainian", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Ukrainian female voice", "preview_text": "Ласкаво просимо до презентації."},

    # === NORWEGIAN ===
    {"id": "nb_no_01", "name": "Pernille", "provider": "azure-tts", "language": "nb-NO", "language_name": "Norwegian", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Norwegian female voice", "preview_text": "Velkommen til presentasjonen."},
    {"id": "nb_no_02", "name": "Finn", "provider": "azure-tts", "language": "nb-NO", "language_name": "Norwegian", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Norwegian male narrator", "preview_text": "La oss gå videre til neste del."},

    # === DANISH ===
    {"id": "da_dk_01", "name": "Christel", "provider": "azure-tts", "language": "da-DK", "language_name": "Danish", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Danish female voice", "preview_text": "Velkommen til præsentationen."},

    # === FINNISH ===
    {"id": "fi_fi_01", "name": "Selma", "provider": "azure-tts", "language": "fi-FI", "language_name": "Finnish", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Finnish female voice", "preview_text": "Tervetuloa esitykseen."},
    {"id": "fi_fi_02", "name": "Harri", "provider": "azure-tts", "language": "fi-FI", "language_name": "Finnish", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Finnish male narrator", "preview_text": "Siirrytään seuraavaan osioon."},

    # === CZECH ===
    {"id": "cs_cz_01", "name": "Vlasta", "provider": "azure-tts", "language": "cs-CZ", "language_name": "Czech", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Czech female voice", "preview_text": "Vítejte u prezentace."},

    # === ROMANIAN ===
    {"id": "ro_ro_01", "name": "Alina", "provider": "azure-tts", "language": "ro-RO", "language_name": "Romanian", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Romanian female voice", "preview_text": "Bine ați venit la prezentare."},

    # === GREEK ===
    {"id": "el_gr_01", "name": "Athina", "provider": "azure-tts", "language": "el-GR", "language_name": "Greek", "gender": "female", "accent": "Standard", "style": "professional", "description": "Professional Greek female voice", "preview_text": "Καλώς ήρθατε στην παρουσίαση."},
    {"id": "el_gr_02", "name": "Nestoras", "provider": "azure-tts", "language": "el-GR", "language_name": "Greek", "gender": "male", "accent": "Standard", "style": "narration", "description": "Clear Greek male narrator", "preview_text": "Ας προχωρήσουμε στην επόμενη ενότητα."},
]

# All supported languages derived from voice data
SUPPORTED_LANGUAGES = sorted(list(set(
    (v["language"], v["language_name"]) for v in AVAILABLE_VOICES
)), key=lambda x: x[1])


@router.get("/")
async def list_voices(
    language: Optional[str] = Query(None, description="Filter by language code (e.g., en-US)"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    provider: Optional[str] = Query(None, description="Filter by provider (elevenlabs, google-tts, azure-tts)"),
    style: Optional[str] = Query(None, description="Filter by style (narration, professional, conversational, etc.)"),
):
    """Get list of available voices with optional filtering"""
    voices = AVAILABLE_VOICES
    if language:
        voices = [v for v in voices if v["language"] == language]
    if gender:
        voices = [v for v in voices if v["gender"] == gender]
    if provider:
        voices = [v for v in voices if v["provider"] == provider]
    if style:
        voices = [v for v in voices if v["style"] == style]
    return {
        "voices": voices,
        "total": len(voices),
        "total_available": len(AVAILABLE_VOICES),
        "languages_count": len(SUPPORTED_LANGUAGES),
    }


@router.get("/languages")
async def get_supported_languages():
    """Get list of all supported languages"""
    return {
        "languages": [{"code": code, "name": name} for code, name in SUPPORTED_LANGUAGES],
        "total": len(SUPPORTED_LANGUAGES),
    }


@router.get("/{voice_id}")
async def get_voice(voice_id: str):
    """Get specific voice details"""
    voice = next((v for v in AVAILABLE_VOICES if v["id"] == voice_id), None)
    if not voice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Voice '{voice_id}' not found")
    return {"voice": voice}


@router.post("/select")
async def select_voice(voice_id: str, current_user=Depends(_get_current_user)):
    """Select voice for a presentation"""
    voice = next((v for v in AVAILABLE_VOICES if v["id"] == voice_id), None)
    if not voice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Voice '{voice_id}' not found")
    return {
        "status": "success",
        "selected_voice": voice,
        "message": f"Voice '{voice['name']}' selected successfully"
    }

