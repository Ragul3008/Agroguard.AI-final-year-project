"""
services/advisory_service.py - Comprehensive ICAR-NRCB Knowledge Base for AgroGuard-AI.

MAIN CONCEPT: ICAR-NRCB (National Research Centre for Banana), Trichy knowledge base
              is the primary source of all advisories.

KB Features:
    1. Detailed treatment steps (chemical + biological + cultural)
    2. Seasonal advisory (Kharif / Rabi / Summer)
    3. Soil & fertilizer guidance per disease
    4. Regional language KB (native language — not just translation)

Architecture:
    Primary  → ICAR KB (main concept — always reliable, free forever)
    Enhanced → Gemini LLM (dynamic generation — bonus feature)
    Fallback → Generic ICAR message
"""

from google import genai
from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# SUPPORTED LANGUAGES — All 22 official Indian languages + English
# ─────────────────────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "english":   "English",
    "hindi":     "Hindi (हिंदी)",
    "tamil":     "Tamil (தமிழ்)",
    "telugu":    "Telugu (తెలుగు)",
    "kannada":   "Kannada (ಕನ್ನಡ)",
    "malayalam": "Malayalam (മലയാളം)",
    "marathi":   "Marathi (मराठी)",
    "gujarati":  "Gujarati (ગુજરાતી)",
    "punjabi":   "Punjabi (ਪੰਜਾਬੀ)",
    "bengali":   "Bengali (বাংলা)",
    "odia":      "Odia (ଓଡ଼ିଆ)",
    "assamese":  "Assamese (অসমীয়া)",
    "urdu":      "Urdu (اردو)",
    "sanskrit":  "Sanskrit (संस्कृतम्)",
    "konkani":   "Konkani (कोंकणी)",
    "manipuri":  "Manipuri (মৈতৈলোন্)",
    "bodo":      "Bodo (बड़ो)",
    "dogri":     "Dogri (डोगरी)",
    "kashmiri":  "Kashmiri (کٲشُر)",
    "maithili":  "Maithili (मैथिली)",
    "nepali":    "Nepali (नेपाली)",
    "santali":   "Santali (ᱥᱟᱱᱛᱟᱲᱤ)",
    "sindhi":    "Sindhi (سنڌي)",
}

DEFAULT_LANGUAGE = "english"

# ─────────────────────────────────────────────────────────────────────────────
# REGIONAL LANGUAGE KB — Native advisories (NOT just translations)
# Written in local farming terminology used by farmers in each region
# ─────────────────────────────────────────────────────────────────────────────
REGIONAL_KB = {

    # ── TAMIL ─────────────────────────────────────────────────────────────────
    "tamil": {
        "panama": {
            "High": (
                "🔍 நோய்: பனாமா நோய் (Fusarium Wilt)\n"
                "⚠ தீவிரம்: அதிகம்\n\n"
                "📋 உடனடி நடவடிக்கை:\n"
                "• ⚠ அவசரம் — பாதிக்கப்பட்ட செடிகளை உடனே வேரோடு பிடுங்கி எரிக்கவும்\n"
                "• பாதிக்கப்பட்ட மண், கருவிகள் மற்றும் நீரை வேறு இடத்திற்கு கொண்டு செல்ல வேண்டாம்\n"
                "• பாதிக்கப்பட்ட நிலத்தை தனிமைப்படுத்தவும்\n\n"
                "💊 இரசாயன சிகிச்சை:\n"
                "• இந்நோய்க்கு இரசாயன மருந்து இல்லை\n"
                "• வெளிப்படையான பாலித்தீன் கொண்டு 6–8 வாரம் மண்ணை சூரிய ஒளியில் வைக்கவும்\n\n"
                "🌿 உயிரியல் கட்டுப்பாடு:\n"
                "• Trichoderma viride @ 2.5 கிலோ/ஹெக்டேர் — மண்ணில் கலக்கவும்\n"
                "• Pseudomonas fluorescens @ 2 கிலோ/ஹெக்டேர் — மண்ணில் ஊற்றவும்\n\n"
                "🌱 மண் & உரம்:\n"
                "• pH 6.0–7.0 உள்ள மண்ணில் மட்டுமே மீண்டும் நடவு செய்யவும்\n"
                "• நன்கு மக்கிய தொழு உரம் @ 10 கிலோ/செடி கலக்கவும்\n"
                "• தழைச்சத்து குறைவாக போடவும் — நோயை அதிகரிக்கும்\n\n"
                "🌦 பருவகால ஆலோசனை:\n"
                "• கோடை காலம்: மண் சூரிய சிகிச்சை மிகவும் பயனுள்ளது\n"
                "• மழை காலம்: நீர் தேங்காமல் பார்க்கவும் — நோய் பரவும்\n"
                "• குளிர் காலம்: Trichoderma தாக்கம் குறைவாக இருக்கும்\n\n"
                "🛡 தடுப்பு நடவடிக்கை:\n"
                "• Grand Nain, FHIA-01 போன்ற நோய் எதிர்ப்பு திறன் கொண்ட ரகங்களை நடவும்\n"
                "• சான்றிதழ் பெற்ற நோய் இல்லாத கன்றுகளை மட்டுமே பயன்படுத்தவும்\n\n"
                "📅 கண்காணிப்பு:\n"
                "• அருகில் உள்ள செடிகளை 3 நாட்களுக்கு ஒரு முறை சோதிக்கவும்\n"
                "• உங்கள் மாவட்ட தோட்டக்கலை அலுவலகத்தில் உடனே தெரிவிக்கவும்\n\n"
                "📌 ஆதாரம்: ICAR-NRCB, திருச்சி."
            ),
            "Low": (
                "🔍 நோய்: பனாமா நோய் (ஆரம்ப நிலை)\n"
                "⚠ தீவிரம்: குறைவு\n\n"
                "📋 நடவடிக்கை:\n"
                "• நிலத்தில் நீர் தேங்காமல் பார்க்கவும்\n"
                "• Pseudomonas fluorescens @ 2 கிலோ/ஹெக்டேர் மண்ணில் ஊற்றவும்\n\n"
                "📅 கண்காணிப்பு:\n"
                "• வாரம் ஒரு முறை தோட்டத்தை சுற்றி பார்க்கவும்\n\n"
                "📌 ஆதாரம்: ICAR-NRCB, திருச்சி."
            ),
        },
        "black sigatoka": {
            "High": (
                "🔍 நோய்: கருப்பு சிகடோகா\n"
                "⚠ தீவிரம்: அதிகம்\n\n"
                "📋 உடனடி நடவடிக்கை:\n"
                "• ⚠ அவசரம் — கடுமையாக பாதிக்கப்பட்ட இலைகளை உடனே அகற்றி எரிக்கவும்\n"
                "• தலை வழி நீர்ப்பாசனம் நிறுத்தி சொட்டு நீர் பாசனம் பயன்படுத்தவும்\n\n"
                "💊 இரசாயன சிகிச்சை:\n"
                "• Propiconazole 25 EC @ 0.1% — 10 நாட்களுக்கு ஒரு முறை தெளிக்கவும்\n"
                "• Copper oxychloride @ 0.2% — பாதுகாப்பு தெளிப்பு\n\n"
                "🌱 மண் & உரம்:\n"
                "• பொட்டாஷ் உரம் @ 100 கிராம்/செடி போடவும் — நோய் எதிர்ப்பு சக்தி அதிகரிக்கும்\n"
                "• மிகை தழைச்சத்து போடாதீர்கள் — நோயை அதிகரிக்கும்\n\n"
                "🌦 பருவகால ஆலோசனை:\n"
                "• மழை காலம்: 10 நாட்களுக்கு ஒரு முறை தெளிக்கவும்\n"
                "• கோடை காலம்: 14–21 நாட்களுக்கு ஒரு முறை போதும்\n\n"
                "📅 கண்காணிப்பு:\n"
                "• 7 நாட்களுக்கு ஒரு முறை புதிய இலை தொற்றை சோதிக்கவும்\n\n"
                "📌 ஆதாரம்: ICAR-NRCB, திருச்சி."
            ),
        },
        "healthy": {
            "None": (
                "🔍 நிலை: ஆரோக்கியமான செடி\n"
                "✅ தீவிரம்: இல்லை\n\n"
                "✅ உங்கள் வாழை செடி ஆரோக்கியமாக உள்ளது!\n\n"
                "📋 நல்ல விவசாய நடைமுறைகள்:\n"
                "• NPK @ 200:60:300 கிராம்/செடி/ஆண்டு — 4 தவணைகளில் போடவும்\n"
                "• மண் ஈரப்பதம் 70–75% பராமரிக்கவும்\n"
                "• சொட்டு நீர் பாசனம் சிறந்தது\n"
                "• காய்ந்த மற்றும் நோயுற்ற இலைகளை தொடர்ந்து அகற்றவும்\n"
                "• ஒரு தாய்ச் செடிக்கு ஒரே ஒரு குருத்து மட்டும் வளர விடவும்\n\n"
                "🌱 மண் & உரம்:\n"
                "• மண் pH 6.0–7.5 பராமரிக்கவும்\n"
                "• 6 மாதங்களுக்கு ஒரு முறை மண் பரிசோதனை செய்யவும்\n"
                "• தொழு உரம் @ 10 கிலோ/செடி ஆண்டுக்கு ஒரு முறை கலக்கவும்\n\n"
                "🌦 பருவகால ஆலோசனை:\n"
                "• மழை காலம்: நீர் தேங்காமல் பார்க்கவும், சிகடோகா கவனிக்கவும்\n"
                "• கோடை காலம்: சொட்டு நீர் பாசனம் கட்டாயம், மல்ச்சிங் செய்யவும்\n"
                "• குளிர் காலம்: பூஞ்சை நோய்களுக்கு கவனமாக இருக்கவும்\n\n"
                "📅 கண்காணிப்பு:\n"
                "• சிகடோகா, அசுவினி மற்றும் BBTV ஆகியவற்றை வாரம் ஒரு முறை சோதிக்கவும்\n\n"
                "📌 ஆதாரம்: ICAR-NRCB, திருச்சி."
            ),
        },
    },

    # ── TELUGU ────────────────────────────────────────────────────────────────
    "telugu": {
        "panama": {
            "High": (
                "🔍 వ్యాధి: పనామా వ్యాధి (Fusarium Wilt)\n"
                "⚠ తీవ్రత: అధికం\n\n"
                "📋 తక్షణ చర్యలు:\n"
                "• ⚠ అత్యవసరం — పాడైన మొక్కలను వెంటనే పీకి కాల్చివేయండి\n"
                "• మట్టి, పనిముట్లు వేరే చోటికి తీసుకెళ్ళవద్దు\n"
                "• పాడైన ప్లాట్‌ను వేరుచేయండి\n\n"
                "💊 రసాయన చికిత్స:\n"
                "• ఈ వ్యాధికి రసాయన మందు లేదు\n"
                "• పారదర్శక పాలిథిన్‌తో 6–8 వారాలు నేలను కప్పండి\n\n"
                "🌿 జీవ నియంత్రణ:\n"
                "• Trichoderma viride @ 2.5 కేజీ/హెక్టార్ — నేలలో కలపండి\n\n"
                "🌱 నేల & ఎరువు:\n"
                "• pH 6.0–7.0 నేలలో మాత్రమే తిరిగి నాటండి\n"
                "• సేంద్రీయ ఎరువు @ 10 కేజీ/మొక్క వేయండి\n"
                "• నత్రజని ఎరువు తక్కువగా వాడండి\n\n"
                "🌦 సీజన్ సలహా:\n"
                "• వేసవిలో నేల సౌర చికిత్స చాలా ప్రభావవంతం\n"
                "• వర్షాకాలంలో నీరు నిల్వ కాకుండా చూసుకోండి\n\n"
                "📌 మూలం: ICAR-NRCB, తిరుచ్చి."
            ),
        },
        "healthy": {
            "None": (
                "🔍 స్థితి: ఆరోగ్యకరమైన మొక్క\n"
                "✅ తీవ్రత: లేదు\n\n"
                "✅ మీ అరటి మొక్క ఆరోగ్యంగా ఉంది!\n\n"
                "📋 మంచి వ్యవసాయ పద్ధతులు:\n"
                "• NPK @ 200:60:300 గ్రా/మొక్క/సంవత్సరం — 4 విడతలుగా వేయండి\n"
                "• మట్టి తేమ 70–75% నిర్వహించండి\n"
                "• డ్రిప్ నీటిపారుదల ఉత్తమం\n"
                "• ఎండిన మరియు రోగగ్రస్త ఆకులు తొలగించండి\n\n"
                "🌱 నేల & ఎరువు:\n"
                "• నేల pH 6.0–7.5 నిర్వహించండి\n"
                "• 6 నెలలకు ఒకసారి నేల పరీక్ష చేయించండి\n\n"
                "🌦 సీజన్ సలహా:\n"
                "• వర్షాకాలం: నీరు నిల్వ కాకుండా చూసుకోండి\n"
                "• వేసవి: డ్రిప్ నీటిపారుదల తప్పనిసరి\n\n"
                "📌 మూలం: ICAR-NRCB, తిరుచ్చి."
            ),
        },
    },

    # ── HINDI ─────────────────────────────────────────────────────────────────
    "hindi": {
        "panama": {
            "High": (
                "🔍 रोग: पनामा रोग (Fusarium Wilt)\n"
                "⚠ गंभीरता: अधिक\n\n"
                "📋 तत्काल कार्रवाई:\n"
                "• ⚠ आपातकाल — सभी संक्रमित पौधों को तुरंत जड़ से उखाड़कर जलाएं\n"
                "• संक्रमित मिट्टी, औजार और पानी को अन्य स्थान पर न ले जाएं\n"
                "• प्रभावित क्षेत्र को अलग करें\n\n"
                "💊 रासायनिक उपचार:\n"
                "• इस रोग का कोई रासायनिक इलाज नहीं है\n"
                "• पारदर्शी पॉलीथिन से 6–8 सप्ताह मिट्टी को ढकें (सोलराइजेशन)\n\n"
                "🌿 जैविक नियंत्रण:\n"
                "• Trichoderma viride @ 2.5 किग्रा/हेक्टेयर — मिट्टी में मिलाएं\n"
                "• Pseudomonas fluorescens @ 2 किग्रा/हेक्टेयर — मिट्टी में डालें\n\n"
                "🌱 मिट्टी और उर्वरक:\n"
                "• pH 6.0–7.0 वाली मिट्टी में ही दोबारा रोपण करें\n"
                "• 10 किग्रा गोबर खाद प्रति पौधे मिलाएं\n"
                "• नाइट्रोजन उर्वरक कम डालें — रोग बढ़ता है\n\n"
                "🌦 मौसम सलाह:\n"
                "• गर्मी: मिट्टी सोलराइजेशन बहुत प्रभावी\n"
                "• बारिश: पानी न रुके — रोग फैलता है\n"
                "• सर्दी: Trichoderma का असर कम होता है\n\n"
                "🛡 रोकथाम:\n"
                "• Grand Nain, FHIA-01 जैसी रोग-प्रतिरोधी किस्में लगाएं\n"
                "• केवल प्रमाणित रोग-मुक्त पौध सामग्री का उपयोग करें\n\n"
                "📅 निगरानी:\n"
                "• हर 3 दिन में पड़ोसी पौधों की जांच करें\n"
                "• नजदीकी बागवानी विभाग को तुरंत सूचित करें\n\n"
                "📌 स्रोत: ICAR-NRCB, त्रिची."
            ),
        },
        "healthy": {
            "None": (
                "🔍 स्थिति: स्वस्थ पौधा\n"
                "✅ गंभीरता: कोई नहीं\n\n"
                "✅ आपका केला का पौधा स्वस्थ है!\n\n"
                "📋 अच्छी कृषि पद्धतियाँ:\n"
                "• NPK @ 200:60:300 ग्राम/पौधे/वर्ष — 4 भागों में दें\n"
                "• मिट्टी की नमी 70–75% बनाए रखें\n"
                "• ड्रिप सिंचाई सबसे अच्छी है\n"
                "• सूखे और रोगग्रस्त पत्ते नियमित रूप से हटाएं\n\n"
                "🌱 मिट्टी और उर्वरक:\n"
                "• मिट्टी pH 6.0–7.5 बनाए रखें\n"
                "• हर 6 महीने में मिट्टी परीक्षण कराएं\n"
                "• 10 किग्रा गोबर खाद साल में एक बार मिलाएं\n\n"
                "🌦 मौसम सलाह:\n"
                "• बारिश: पानी न रुके, सिगाटोका देखते रहें\n"
                "• गर्मी: ड्रिप सिंचाई जरूरी, मल्चिंग करें\n"
                "• सर्दी: फफूंद रोगों के प्रति सावधान रहें\n\n"
                "📅 निगरानी:\n"
                "• सिगाटोका, माहू और BBTV की हर हफ्ते जांच करें\n\n"
                "📌 स्रोत: ICAR-NRCB, त्रिची."
            ),
        },
    },

    # ── KANNADA ───────────────────────────────────────────────────────────────
    "kannada": {
        "healthy": {
            "None": (
                "🔍 ಸ್ಥಿತಿ: ಆರೋಗ್ಯಕರ ಗಿಡ\n"
                "✅ ತೀವ್ರತೆ: ಇಲ್ಲ\n\n"
                "✅ ನಿಮ್ಮ ಬಾಳೆ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ!\n\n"
                "📋 ಉತ್ತಮ ಕೃಷಿ ಅಭ್ಯಾಸಗಳು:\n"
                "• NPK @ 200:60:300 ಗ್ರಾಂ/ಗಿಡ/ವರ್ಷ — 4 ಕಂತುಗಳಲ್ಲಿ ಹಾಕಿ\n"
                "• ಮಣ್ಣಿನ ತೇವಾಂಶ 70–75% ಇರಿಸಿ\n"
                "• ಹನಿ ನೀರಾವರಿ ಉತ್ತಮ\n\n"
                "🌱 ಮಣ್ಣು & ಗೊಬ್ಬರ:\n"
                "• ಮಣ್ಣಿನ pH 6.0–7.5 ಕಾಪಾಡಿ\n"
                "• 6 ತಿಂಗಳಿಗೊಮ್ಮೆ ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮಾಡಿಸಿ\n\n"
                "📌 ಮೂಲ: ICAR-NRCB, ತ್ರಿಚಿ."
            ),
        },
    },

    # ── MALAYALAM ─────────────────────────────────────────────────────────────
    "malayalam": {
        "healthy": {
            "None": (
                "🔍 അവസ്ഥ: ആരോഗ്യകരമായ ചെടി\n"
                "✅ തീവ്രത: ഇല്ല\n\n"
                "✅ നിങ്ങളുടെ വാഴ ചെടി ആരോഗ്യകരമാണ്!\n\n"
                "📋 നല്ല കൃഷിരീതികൾ:\n"
                "• NPK @ 200:60:300 ഗ്രാം/ചെടി/വർഷം — 4 ഗഡുക്കളായി നൽകുക\n"
                "• മണ്ണിലെ ഈർപ്പം 70–75% നിലനിർത്തുക\n"
                "• തുള്ളി ജലസേചനം ഏറ്റവും നല്ലത്\n\n"
                "🌱 മണ്ണും വളവും:\n"
                "• മണ്ണിന്റെ pH 6.0–7.5 നിലനിർത്തുക\n"
                "• 6 മാസത്തിലൊരിക്കൽ മണ്ണ് പരിശോധന നടത്തുക\n\n"
                "📌 ഉറവിടം: ICAR-NRCB, തൃശ്ശൂർ."
            ),
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# COMPREHENSIVE ICAR KB — English (Main KB with all enhancements)
# ─────────────────────────────────────────────────────────────────────────────
ICAR_KB = {

    # ══════════════════════════════════════════════════════════════════════════
    # PANAMA DISEASE (Fusarium Wilt)
    # ══════════════════════════════════════════════════════════════════════════
    "panama": {
        "High": (
            "🔍 DISEASE: Panama Disease (Fusarium Wilt)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Uproot and burn ALL infected plants immediately\n"
            "• Do NOT compost — burn only to destroy fungal spores\n"
            "• Quarantine affected plot — block all entry/exit\n"
            "• Restrict movement of soil, tools, water and workers\n"
            "• Mark infected area with stakes for identification\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• No chemical cure exists for Panama Disease (Fusarium oxysporum)\n"
            "• Soil solarisation: cover with transparent polythene for 6–8 weeks\n"
            "• Drench soil with 2% Formaldehyde solution before replanting\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Trichoderma viride @ 2.5 kg/ha — mix in soil 30 days before replanting\n"
            "• Pseudomonas fluorescens @ 2 kg/ha — soil drench at planting\n"
            "• Apply FYM (farmyard manure) enriched with Trichoderma @ 5 kg/pit\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Replant ONLY in soil with pH 6.0–7.0\n"
            "• Apply well-decomposed FYM @ 10 kg/plant before replanting\n"
            "• Reduce nitrogen (N) fertilizer — high N promotes fungal growth\n"
            "• Increase potassium (K) @ 300 g K2O/plant/year — improves resistance\n"
            "• Apply lime if soil pH is below 6.0 to reduce pathogen survival\n"
            "• Avoid waterlogging — maintain proper drainage channels\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif (Jun–Oct): High risk — avoid planting in waterlogged fields\n"
            "• Rabi (Nov–Feb):   Best time for soil solarisation treatment\n"
            "• Summer (Mar–May): Ideal for new planting with resistant varieties\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Replant with resistant varieties: Grand Nain, FHIA-01, FHIA-17, Nendran\n"
            "• Use only certified disease-free TC (tissue culture) suckers\n"
            "• Disinfect all farm tools with 2% formaldehyde before use\n"
            "• Practice crop rotation with non-host crops for 2–3 years\n\n"
            "📅 MONITORING:\n"
            "• Scout neighbouring plants every 3 days\n"
            "• Report outbreak immediately to nearest Horticulture Department\n"
            "• Maintain a disease map of the affected area\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Panama Disease (Fusarium Wilt)\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove and burn all wilting or yellowing plants\n"
            "• Avoid overhead irrigation — switch to drip irrigation immediately\n"
            "• Disinfect all farm tools with 2% formaldehyde\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Trichoderma viride @ 25 g per plant — apply in root zone\n"
            "• Pseudomonas fluorescens @ 10 g per plant — root zone drench\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Avoid excess nitrogen — increases disease severity\n"
            "• Apply potash @ 100 g K2O/plant to boost resistance\n"
            "• Maintain soil pH 6.5 — apply lime if needed\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Monsoon: Extra vigilance — disease spreads fast in waterlogged soils\n"
            "• Dry season: Apply bioagents every 30 days\n\n"
            "📅 MONITORING:\n"
            "• Monitor neighbouring plants every 3 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Panama Disease (Fusarium Wilt)\n"
            "⚠ SEVERITY: LOW\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Improve field drainage — avoid waterlogging at root zone\n"
            "• Remove lower yellowing leaves as precaution\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pseudomonas fluorescens @ 2 kg/ha — preventive soil drench\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Test soil pH — maintain between 6.0–7.0\n"
            "• Reduce nitrogen, increase potassium in fertilizer schedule\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Monsoon: Monitor drainage channels weekly\n\n"
            "📅 MONITORING:\n"
            "• Scout plantation weekly for yellowing lower leaves\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════════
    # BLACK SIGATOKA
    # ══════════════════════════════════════════════════════════════════════════
    "black sigatoka": {
        "High": (
            "🔍 DISEASE: Black Sigatoka (Mycosphaerella fijiensis)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Remove and burn all heavily infected leaves immediately\n"
            "• Avoid overhead irrigation — switch to drip irrigation\n"
            "• Remove lower 2–3 leaves even if mildly infected\n"
            "• Bag and seal removed leaves before disposal\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Propiconazole 25 EC @ 0.1% — systemic fungicide, spray every 10 days\n"
            "• Copper oxychloride @ 0.2% — protective spray, alternating with systemic\n"
            "• Mancozeb 75 WP @ 0.2% — broad-spectrum protectant\n"
            "• Alternate fungicides to prevent resistance development\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Trichoderma asperellum — foliar spray for mild cases\n"
            "• Not sufficient alone for High severity\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Potassium @ 300 g K2O/plant/year — critical for leaf strength\n"
            "• Avoid excess nitrogen — promotes lush leaves that attract disease\n"
            "• Apply magnesium sulfate @ 50 g/plant — improves leaf health\n"
            "• Maintain soil pH 5.5–7.0 for optimal nutrient uptake\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif/Monsoon: Spray every 10 days — high humidity favours spread\n"
            "• Rabi/Winter:    Spray every 14 days — moderate risk\n"
            "• Summer:         Spray every 21 days — lower risk period\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Improve canopy ventilation by thinning excess suckers\n"
            "• Maintain adequate spacing between plants (2.5m x 2.5m)\n"
            "• Use resistant varieties where possible\n\n"
            "📅 MONITORING:\n"
            "• Check every 7 days for new leaf streaks and spots\n"
            "• Count diseased leaves per bunch — more than 5 = urgent treatment\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Black Sigatoka\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove lower infected leaves and destroy them\n"
            "• Improve canopy ventilation by removing excess suckers\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Mancozeb 75 WP @ 0.2% — foliar spray every 14 days\n"
            "• Carbendazim 50 WP @ 0.1% — systemic alternative\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Increase potassium @ 150 g K2O/plant\n"
            "• Balanced NPK — avoid excess nitrogen\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Monsoon: Increase spray frequency to every 10 days\n"
            "• Dry season: Every 14–21 days\n\n"
            "📅 MONITORING:\n"
            "• Inspect every 10 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Black Sigatoka\n"
            "⚠ SEVERITY: LOW\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove leaves showing early streak symptoms\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Copper oxychloride @ 0.2% — preventive spray\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Ensure balanced NPK fertilisation\n"
            "• Potassium application boosts natural resistance\n\n"
            "📅 MONITORING:\n"
            "• Monitor weekly — act immediately if streaks appear\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════════
    # YELLOW SIGATOKA
    # ══════════════════════════════════════════════════════════════════════════
    "yellow sigatoka": {
        "High": (
            "🔍 DISEASE: Yellow Sigatoka (Mycosphaerella musicola)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Remove all leaves with more than 50% lesion coverage\n"
            "• Destroy removed material — do not compost\n"
            "• Improve field ventilation immediately\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbendazim 50 WP @ 0.1% — systemic fungicide, every 14 days\n"
            "• OR Propiconazole 25 EC @ 0.1% — spray at 14-day intervals\n"
            "• Mancozeb 75 WP @ 0.25% — protectant spray between systemic sprays\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Potassium @ 250 g K2O/plant — critical to strengthen leaf tissue\n"
            "• Calcium ammonium nitrate instead of urea — less disease promotion\n"
            "• Organic mulch @ 5 kg/plant — maintains soil moisture and health\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif: Spray every 14 days — peak disease season\n"
            "• Rabi:   Spray every 21 days\n"
            "• Summer: Preventive spray every 28 days\n\n"
            "📅 MONITORING:\n"
            "• Check every 7 days during monsoon\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Yellow Sigatoka\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Regular leaf pruning to remove infected material\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Mancozeb 75 WP @ 0.25% — foliar spray every 14 days\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Potassium @ 150 g K2O/plant\n"
            "• Avoid excess nitrogen\n\n"
            "📅 MONITORING:\n"
            "• Check every 10 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Yellow Sigatoka\n"
            "⚠ SEVERITY: LOW\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Copper oxychloride @ 0.3% — preventive spray\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Maintain adequate drainage — keep leaves dry\n"
            "• Potassium application improves resistance\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════════
    # PSEUDOSTEM WEEVIL
    # ══════════════════════════════════════════════════════════════════════════
    "weevil": {
        "High": (
            "🔍 DISEASE: Pseudostem Weevil (Odoiporus longicollis)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Begin treatment within 24 hours\n"
            "• Remove and destroy heavily infested pseudostems\n"
            "• Cut and examine pseudostem — look for tunnels and larvae\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbofuran 3G granules @ 40 g/plant — apply at pseudostem base\n"
            "• Chlorpyrifos 20 EC @ 2.5 ml/litre — pseudostem injection & drench\n"
            "• Monocrotophos 36 SL @ 1.5 ml/litre — pseudostem injection\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pheromone traps @ 10 traps/hectare — for mass trapping\n"
            "• Beauveria bassiana @ 5 g/litre — spray at pseudostem base\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Avoid excess nitrogen — attracts more pests\n"
            "• Apply potassium @ 300 g K2O/plant — strengthens pseudostem\n"
            "• Mulching with dry leaves @ 5 kg/plant discourages egg laying\n"
            "• Maintain good drainage — waterlogging weakens pseudostem\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif: Peak season — inspect every 5 days\n"
            "• Rabi:   Moderate risk — inspect every 10 days\n"
            "• Summer: Low risk — maintain pheromone traps\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Remove old pseudostems after harvest immediately\n"
            "• Destroy crop debris — do not leave in field\n"
            "• Cut pseudostems at ground level after harvest\n\n"
            "📅 MONITORING:\n"
            "• Inspect pheromone traps every 3 days\n"
            "• Count weevils in traps — more than 5/week = urgent treatment\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Pseudostem Weevil\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbofuran 3G @ 25 g/plant — pseudostem base application\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pheromone traps @ 5 traps/hectare\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Potassium @ 150 g K2O/plant — strengthens pseudostem\n\n"
            "📅 MONITORING:\n"
            "• Check traps every 5 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Pseudostem Weevil\n"
            "⚠ SEVERITY: LOW\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pheromone traps @ 2–3 traps/hectare — monitoring\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Maintain field sanitation\n"
            "• Remove old pseudostems after harvest\n\n"
            "📅 MONITORING:\n"
            "• Inspect weekly\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════════
    # BUNCHY TOP VIRUS (BBTV)
    # ══════════════════════════════════════════════════════════════════════════
    "bunchy": {
        "High": (
            "🔍 DISEASE: Banana Bunchy Top Virus (BBTV)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Uproot and burn ALL infected plants immediately\n"
            "• No chemical cure exists for BBTV\n"
            "• Establish 50-metre buffer zone around infection area\n"
            "• Remove all volunteer banana plants in buffer zone\n\n"
            "💊 CHEMICAL TREATMENT (Aphid Vector Control):\n"
            "• Imidacloprid 17.8 SL @ 0.3 ml/litre — foliar spray to kill aphid vectors\n"
            "• Dimethoate 30 EC @ 2 ml/litre — aphid control spray\n"
            "• Thiamethoxam 25 WG @ 0.3 g/litre — systemic aphid control\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Encourage natural predators: ladybird beetles, lacewings\n"
            "• Avoid broad-spectrum insecticides that kill natural enemies\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Maintain balanced nutrition — stressed plants more susceptible\n"
            "• Apply NPK @ 200:60:300 g/plant for healthy regrowth\n"
            "• Good drainage reduces plant stress and BBTV susceptibility\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif: Peak aphid season — spray every 7 days\n"
            "• Rabi:   Spray every 14 days\n"
            "• Summer: Monitor weekly — hot dry weather increases aphid spread\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Use ONLY certified virus-free tissue culture planting material\n"
            "• Control aphid population continuously throughout crop season\n"
            "• Plant resistant varieties where available\n"
            "• Inspect new planting material before introducing to field\n\n"
            "📅 MONITORING:\n"
            "• Scout for aphids on leaf undersides every 5 days\n"
            "• Watch for characteristic dark-green streaks on leaf midrib\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Banana Bunchy Top Virus (BBTV)\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Rogue out all symptomatic plants — destroy immediately\n\n"
            "💊 CHEMICAL TREATMENT (Vector Control):\n"
            "• Imidacloprid 17.8 SL @ 0.5 ml/litre — aphid vector spray\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Balanced NPK to reduce plant stress\n\n"
            "📅 MONITORING:\n"
            "• Check for aphid colonies every 5 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Banana Bunchy Top Virus (BBTV)\n"
            "⚠ SEVERITY: LOW\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove and destroy all symptomatic plants\n\n"
            "💊 CHEMICAL TREATMENT (Vector Control):\n"
            "• Imidacloprid spray — control aphid population\n\n"
            "📅 MONITORING:\n"
            "• Weekly scouting for aphid activity\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ANTHRACNOSE
    # ══════════════════════════════════════════════════════════════════════════
    "anthracnose": {
        "High": (
            "🔍 DISEASE: Anthracnose (Colletotrichum musae)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Apply post-harvest treatment immediately\n"
            "• Remove all visibly infected fruit from storage\n"
            "• Sanitise storage facility with Sodium hypochlorite @ 200 ppm\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbendazim 50 WP @ 0.1% — post-harvest fungicide dip/spray\n"
            "• Hot water treatment: immerse fruit bunches at 52°C for 3 minutes\n"
            "• Thiabendazole @ 0.1% — post-harvest dip as alternative\n"
            "• Wax coating after treatment reduces infection spread\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Bacillus subtilis @ 2 g/litre — post-harvest spray\n"
            "• Trichoderma viride spray on flower bracts at shooting stage\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Calcium @ 50 g CaO/plant — strengthens fruit skin, reduces cracking\n"
            "• Potassium @ 300 g K2O/plant — improves post-harvest quality\n"
            "• Avoid excess nitrogen — causes soft fruit susceptible to infection\n"
            "• Boron @ 2 g/plant — improves fruit skin integrity\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif/Monsoon: Highest risk — apply pre-harvest fungicide spray\n"
            "• Rabi:   Apply Carbendazim spray 3 weeks before harvest\n"
            "• Summer: Lower risk — maintain hygiene in storage\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Store fruit at 13–14°C with 90–95% relative humidity\n"
            "• Handle fruit carefully to minimise wounds during harvest\n"
            "• Clean all harvesting tools with disinfectant\n"
            "• Remove flower bracts at finger development stage\n\n"
            "📅 MONITORING:\n"
            "• Check stored fruit every 2 days\n"
            "• Inspect fruit at harvest for early infection signs\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Anthracnose\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbendazim 50 WP @ 0.1% — post-harvest fungicide\n"
            "• Hot water treatment @ 52°C for 3 minutes\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Calcium and potassium application improve fruit quality\n\n"
            "📅 MONITORING:\n"
            "• Inspect stored fruit every 3 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Anthracnose\n"
            "⚠ SEVERITY: LOW\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Mancozeb 75 WP @ 0.2% — preventive spray at flowering stage\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Careful harvesting to minimise fruit wounds\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════════
    # HEALTHY
    # ══════════════════════════════════════════════════════════════════════════
    "healthy": {
        "None": (
            "🔍 STATUS: Healthy Banana Plant\n"
            "✅ SEVERITY: NONE\n\n"
            "✅ Your banana plant appears HEALTHY!\n\n"
            "📋 RECOMMENDED PRACTICES:\n"
            "• Apply NPK @ 200:60:300 g/plant/year — in 4 equal split doses\n"
            "• Maintain soil moisture at 70–75% field capacity\n"
            "• Drip irrigation preferred — prevents foliar diseases\n"
            "• Remove dry and diseased leaves regularly\n"
            "• Retain only one ratoon sucker per mat\n"
            "• Earth up the base of plant every 3 months\n\n"
            "🌱 SOIL & FERTILIZER GUIDANCE:\n"
            "• Maintain soil pH 6.0–7.5 for optimal nutrient uptake\n"
            "• Soil test every 6 months — adjust fertiliser accordingly\n"
            "• Apply FYM (farmyard manure) @ 10 kg/plant once a year\n"
            "• Micronutrient mix (Zn, Fe, Mn, B) @ 50 g/plant twice a year\n"
            "• Mulch with dry leaves @ 5 kg/plant — conserves moisture\n"
            "• Green manure crops in row middles improve soil health\n\n"
            "🌦 SEASONAL ADVISORY:\n"
            "• Kharif (Jun–Oct): Ensure drainage — monitor for Sigatoka and weevils\n"
            "• Rabi (Nov–Feb):   Apply full NPK dose — main growth season\n"
            "• Summer (Mar–May): Drip irrigation mandatory — apply mulch 5 kg/plant\n\n"
            "🛡 PREVENTIVE SPRAY SCHEDULE:\n"
            "• Copper oxychloride @ 0.2% — preventive spray every 30 days\n"
            "• Imidacloprid @ 0.3 ml/litre — aphid control every 45 days\n"
            "• Carbendazim @ 0.1% — preventive fungicide at flowering\n\n"
            "📅 MONITORING SCHEDULE:\n"
            "• Weekly: Scout for Sigatoka, weevils, BBTV, and aphids\n"
            "• Monthly: Soil moisture check and sucker management\n"
            "• 6-monthly: Soil testing and nutritional assessment\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
}

_GENERIC_FALLBACK: dict[str, str] = {
    "High": (
        "⚠ URGENT — Severe disease detected.\n\n"
        "📋 IMMEDIATE ACTIONS:\n"
        "• Contact your nearest ICAR-NRCB office immediately\n"
        "• Isolate affected plants from healthy ones\n"
        "• Do not move soil or plant material\n\n"
        "📌 Source: ICAR-NRCB, Trichy."
    ),
    "Medium": (
        "Moderate disease detected.\n\n"
        "📋 ACTIONS:\n"
        "• Apply ICAR-recommended treatments\n"
        "• Monitor every 3–5 days\n\n"
        "📌 Source: ICAR-NRCB, Trichy."
    ),
    "Low": (
        "Mild symptoms detected.\n\n"
        "📋 ACTIONS:\n"
        "• Continue monitoring\n"
        "• Apply preventive treatments\n\n"
        "📌 Source: ICAR-NRCB, Trichy."
    ),
    "None": (
        "✅ Plant appears healthy.\n\n"
        "📋 ACTIONS:\n"
        "• Maintain ICAR-recommended practices\n\n"
        "📌 Source: ICAR-NRCB, Trichy."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI SETUP
# ─────────────────────────────────────────────────────────────────────────────
_gemini_client = None


def _get_gemini_model():
    global _gemini_client
    if _gemini_client is None:
        try:
            _gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options={"api_version": "v1beta"}
            )
            logger.info("✓ Gemini 2.5 Flash client initialised.")
        except Exception as exc:
            logger.error("✗ Gemini initialisation failed: %s", exc)
            _gemini_client = None
    return _gemini_client


def _build_gemini_prompt(disease_name: str, severity: str, language: str) -> str:
    lang_display = SUPPORTED_LANGUAGES.get(language, "English")
    lang_note = (
        f"\nRespond ENTIRELY in {lang_display}. Keep chemical names in English."
        if language != "english" else ""
    )
    return f"""You are AgroGuard-AI — an ICAR-NRCB expert advisor for banana diseases.

Generate a bullet-point advisory ONLY (no paragraphs) for:
Disease: {disease_name}
Severity: {severity}
Guidelines: ICAR-NRCB, Trichy, India

Use this exact format:
🔍 DISEASE: ...
⚠ SEVERITY: ...

📋 IMMEDIATE ACTIONS:
• ...

💊 CHEMICAL TREATMENT:
• chemical name @ exact dosage — method

🌿 BIOLOGICAL CONTROL:
• ...

🌱 SOIL & FERTILIZER GUIDANCE:
• ...

🌦 SEASONAL ADVISORY:
• Kharif: ...
• Rabi: ...
• Summer: ...

🛡 PREVENTIVE MEASURES:
• ...

📅 MONITORING:
• ...

📌 Source: ICAR-NRCB, Trichy.{lang_note}"""


# ─────────────────────────────────────────────────────────────────────────────
# ADVISORY SERVICE
# ─────────────────────────────────────────────────────────────────────────────
class AdvisoryService:
    """
    ICAR-NRCB Knowledge Base advisory service — main concept of AgroGuard-AI.

    Priority order:
        1. Regional Language KB  — native language advisories
        2. ICAR English KB       — comprehensive English advisory
        3. Gemini LLM            — dynamic generation (bonus feature)
        4. Generic fallback      — last resort

    Supported: 23 Indian languages (all 22 official + English)
    Features:  Detailed steps, seasonal advisory, soil/fertilizer guidance,
               regional language KB
    """

    def get_advisory(
        self,
        disease_name: str,
        severity: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> str:
        language = language.lower().strip() if language else DEFAULT_LANGUAGE
        if language not in SUPPORTED_LANGUAGES:
            language = DEFAULT_LANGUAGE

        # Step 1: Try regional language KB first (native — not translation)
        regional = self._get_regional_advisory(disease_name, severity, language)
        if regional:
            logger.info(
                "Regional KB advisory — disease='%s' severity='%s' language='%s'",
                disease_name, severity, language,
            )
            return regional

        # Step 2: Use comprehensive ICAR English KB
        icar = self._get_icar_advisory(disease_name, severity)
        if icar and language == DEFAULT_LANGUAGE:
            logger.info(
                "ICAR KB advisory — disease='%s' severity='%s'",
                disease_name, severity,
            )
            return icar

        # Step 3: Gemini LLM (dynamic — for non-English without regional KB)
        if icar and language != DEFAULT_LANGUAGE:
            gemini = self._get_gemini_advisory(disease_name, severity, language)
            if gemini:
                logger.info(
                    "Gemini advisory — disease='%s' severity='%s' language='%s'",
                    disease_name, severity, language,
                )
                return gemini
            # Gemini failed — return English ICAR with note
            lang_display = SUPPORTED_LANGUAGES.get(language, language)
            return (
                f"[{lang_display} advisory unavailable — showing English]\n\n"
                + icar
            )

        # Step 4: Generic fallback
        logger.warning("Using generic fallback for disease='%s'", disease_name)
        return _GENERIC_FALLBACK.get(severity, "No advisory available.")

    def _get_regional_advisory(
        self, disease_name: str, severity: str, language: str
    ) -> str | None:
        """Look up native language KB."""
        if language not in REGIONAL_KB:
            return None
        lang_kb = REGIONAL_KB[language]
        disease_lower = disease_name.lower()
        for keyword, severity_map in lang_kb.items():
            if keyword in disease_lower:
                return severity_map.get(severity)
        return None

    def _get_icar_advisory(self, disease_name: str, severity: str) -> str | None:
        """Look up comprehensive ICAR English KB."""
        disease_lower = disease_name.lower()
        for keyword, severity_map in ICAR_KB.items():
            if keyword in disease_lower:
                advice = severity_map.get(severity)
                if advice:
                    logger.info(
                        "ICAR KB matched keyword='%s' severity='%s'",
                        keyword, severity,
                    )
                    return advice
        return None

    def _get_gemini_advisory(
        self, disease_name: str, severity: str, language: str
    ) -> str | None:
        """Call Gemini API as bonus dynamic generation."""
        try:
            model = _get_gemini_model()
            if model is None:
                return None
            prompt = _build_gemini_prompt(disease_name, severity, language)
            response = model.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
            return None
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            return None


def get_supported_languages() -> dict:
    """Return all supported languages for API response."""
    return {
        "total":     len(SUPPORTED_LANGUAGES),
        "default":   DEFAULT_LANGUAGE,
        "languages": SUPPORTED_LANGUAGES,
        "usage":     "Pass 'language' field in predict request (e.g. language=tamil)",
        "note":      "Tamil, Telugu, Hindi have native KB. Others use Gemini translation."
    }