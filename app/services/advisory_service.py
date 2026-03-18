"""
services/advisory_service.py - Gemini LLM-powered ICAR advisory for AgroGuard-AI.

Architecture:
    Primary  → Google Gemini 2.5 Flash (dynamic AI-generated advisory)
    Fallback → Hardcoded ICAR knowledge base (if Gemini fails)

Features:
    - Advisory formatted as clean bullet points
    - 22 language support including all major Indian + international languages
    - User can request advisory in their preferred language
"""

from google import genai

from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Supported languages — 22 languages
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    # Indian Languages (22 official + English)
    "english":    "English",
    "hindi":      "Hindi (हिंदी)",
    "tamil":      "Tamil (தமிழ்)",
    "telugu":     "Telugu (తెలుగు)",
    "kannada":    "Kannada (ಕನ್ನಡ)",
    "malayalam":  "Malayalam (മലയാളം)",
    "marathi":    "Marathi (मराठी)",
    "gujarati":   "Gujarati (ગુજરાતી)",
    "punjabi":    "Punjabi (ਪੰਜਾਬੀ)",
    "bengali":    "Bengali (বাংলা)",
    "odia":       "Odia (ଓଡ଼ିଆ)",
    "assamese":   "Assamese (অসমীয়া)",
    "urdu":       "Urdu (اردو)",
    "sanskrit":   "Sanskrit (संस्कृतम्)",
    "konkani":    "Konkani (कोंकणी)",
    "manipuri":   "Manipuri (মৈতৈলোন্)",
    "bodo":       "Bodo (बड़ो)",
    "dogri":      "Dogri (डोगरी)",
    "kashmiri":   "Kashmiri (کٲشُر)",
    "maithili":   "Maithili (मैथिली)",
    "nepali":     "Nepali (नेपाली)",
    "santali":    "Santali (ᱥᱟᱱᱛᱟᱲᱤ)",
    "sindhi":     "Sindhi (سنڌي)",
}

# Language display names for API response
LANGUAGE_NAMES = list(SUPPORTED_LANGUAGES.keys())
DEFAULT_LANGUAGE = "english"

# ---------------------------------------------------------------------------
# Gemini client singleton
# ---------------------------------------------------------------------------
_gemini_client = None


def _get_gemini_model():
    """Lazy-load Gemini client singleton."""
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


# ---------------------------------------------------------------------------
# System prompt — bullet point format + language support
# ---------------------------------------------------------------------------
def _build_system_prompt(language: str) -> str:
    lang_display = SUPPORTED_LANGUAGES.get(language.lower(), "English")

    lang_instruction = ""
    if language.lower() != "english":
        lang_instruction = f"""

LANGUAGE INSTRUCTION:
- Respond ENTIRELY in {lang_display}
- Translate ALL content including section headers, steps and source line
- Keep chemical dosages as numbers (e.g., 0.1%, 2.5 ml/litre)
- Chemical names may remain in English within the {lang_display} text
- Translate emoji labels too (e.g., IMMEDIATE ACTIONS → Tamil equivalent)
"""

    return f"""You are AgroGuard-AI, an expert agricultural advisor specializing 
in banana crop disease management. You provide treatment advisories strictly aligned 
with ICAR (Indian Council of Agricultural Research) guidelines, specifically from 
ICAR-NRCB (National Research Centre for Banana), Trichy, India.

STRICT FORMATTING RULES — FOLLOW EXACTLY:
1. NEVER write paragraphs — use ONLY bullet points
2. Use this EXACT structure:

🔍 DISEASE: [disease name]
⚠ SEVERITY: [severity level]

📋 IMMEDIATE ACTIONS:
• [action 1]
• [action 2]
• [action 3]

💊 CHEMICAL TREATMENT:
• [chemical name] @ [exact dosage] — [application method]
• [chemical name] @ [exact dosage] — [application method]

🌿 BIOLOGICAL CONTROL:
• [bioagent name] @ [dosage] — [method]
• (write "Not applicable" if none recommended)

🔄 SPRAY SCHEDULE:
• [schedule details]
• [frequency]

🛡 PREVENTIVE MEASURES:
• [measure 1]
• [measure 2]
• [measure 3]

📅 MONITORING:
• [monitoring frequency and what to look for]

📌 Source: ICAR-NRCB, Trichy.

CONTENT RULES:
- Recommend ONLY ICAR-NRCB approved treatments
- Include EXACT chemical dosages (e.g., Mancozeb 75 WP @ 0.2%)
- Add ⚠ URGENT prefix for High severity diseases
- Add ✅ for healthy plants
- Keep practical and simple for Indian banana farmers
- Do NOT use paragraphs or prose — bullets ONLY{lang_instruction}"""


# ---------------------------------------------------------------------------
# Hardcoded ICAR fallback knowledge base — bullet point format
# ---------------------------------------------------------------------------
_FALLBACK_KB: dict[str, dict[str, str]] = {
    "panama": {
        "High": (
            "🔍 DISEASE: Panama Disease (Fusarium Wilt)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Uproot and burn ALL infected plants immediately\n"
            "• Do NOT compost infected material — burn only\n"
            "• Quarantine the affected plot immediately\n"
            "• Restrict movement of soil, tools, and irrigation water\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• No chemical cure exists for Panama Disease\n"
            "• Soil solarisation using transparent polythene for 6–8 weeks\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Trichoderma viride @ 2.5 kg/ha — apply to soil before replanting\n"
            "• Pseudomonas fluorescens @ 2 kg/ha — soil drench application\n\n"
            "🔄 SPRAY SCHEDULE:\n"
            "• Apply bioagents every 30 days during replanting phase\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Replant with resistant varieties: Grand Nain, FHIA-01, FHIA-17\n"
            "• Use only certified disease-free suckers\n"
            "• Maintain field drainage to prevent root waterlogging\n"
            "• Disinfect all farm tools with 2% formaldehyde solution\n\n"
            "📅 MONITORING:\n"
            "• Scout neighbouring plants every 3 days\n"
            "• Report outbreak to nearest Horticulture Department\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Panama Disease (Fusarium Wilt)\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove and burn all wilting or yellowing plants\n"
            "• Avoid overhead irrigation — switch to drip irrigation\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• No chemical cure available for this disease\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Trichoderma viride @ 25 g per plant — apply in root zone\n\n"
            "🔄 SPRAY SCHEDULE:\n"
            "• Apply Trichoderma every 30 days\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Disinfect all farm tools with 2% formaldehyde solution\n"
            "• Avoid waterlogging at root zone\n\n"
            "📅 MONITORING:\n"
            "• Monitor neighbouring plants every 3 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Panama Disease (Fusarium Wilt)\n"
            "⚠ SEVERITY: LOW\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Improve field drainage — avoid waterlogging at root zone\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pseudomonas fluorescens @ 2 kg/ha — soil drench\n\n"
            "📅 MONITORING:\n"
            "• Scout plantation weekly for yellowing lower leaves\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
    "black sigatoka": {
        "High": (
            "🔍 DISEASE: Black Sigatoka\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Remove and burn all heavily infected leaves\n"
            "• Avoid overhead irrigation — switch to drip irrigation\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Propiconazole 25 EC @ 0.1% — spray at 10-day intervals\n"
            "• Copper oxychloride @ 0.2% — protective spray\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Not applicable for High severity\n\n"
            "🔄 SPRAY SCHEDULE:\n"
            "• Apply Propiconazole every 10 days until controlled\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Improve canopy ventilation by removing excess suckers\n"
            "• Maintain adequate drainage\n\n"
            "📅 MONITORING:\n"
            "• Check every 7 days for new leaf infections\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Black Sigatoka\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove lower infected leaves and destroy them\n"
            "• Improve canopy ventilation\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Mancozeb 75 WP @ 0.2% — foliar spray\n\n"
            "🔄 SPRAY SCHEDULE:\n"
            "• Apply every 14 days\n\n"
            "📅 MONITORING:\n"
            "• Inspect every 10 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Black Sigatoka\n"
            "⚠ SEVERITY: LOW\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove leaves showing streak symptoms\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Copper-based fungicide — preventive spray\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Ensure balanced NPK fertilisation\n\n"
            "📅 MONITORING:\n"
            "• Monitor weekly\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
    "yellow sigatoka": {
        "High": (
            "🔍 DISEASE: Yellow Sigatoka\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Remove all leaves with more than 50% lesion coverage\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbendazim 50 WP @ 0.1% — foliar spray\n"
            "• OR Propiconazole 25 EC @ 0.1% — foliar spray\n\n"
            "🔄 SPRAY SCHEDULE:\n"
            "• Spray at 14-day intervals during wet season\n\n"
            "📅 MONITORING:\n"
            "• Check every 7 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Yellow Sigatoka\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Regular leaf pruning to remove infected material\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Mancozeb 75 WP @ 0.25% — foliar spray\n\n"
            "📅 MONITORING:\n"
            "• Check every 10 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Yellow Sigatoka\n"
            "⚠ SEVERITY: LOW\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Copper oxychloride @ 0.3% — preventive spray\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Maintain adequate drainage to keep leaves dry\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
    "weevil": {
        "High": (
            "🔍 DISEASE: Pseudostem Weevil Infestation\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Apply treatment immediately\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbofuran 3G granules @ 40 g per plant — apply at pseudostem base\n"
            "• Chlorpyrifos 20 EC @ 2.5 ml/litre — pseudostem drench\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pheromone traps @ 10 traps per hectare\n\n"
            "📅 MONITORING:\n"
            "• Inspect traps every 3 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Pseudostem Weevil Infestation\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbofuran 3G @ 25 g per plant — apply at pseudostem base\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pheromone traps @ 5 traps per hectare\n\n"
            "📅 MONITORING:\n"
            "• Check traps every 5 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Pseudostem Weevil Infestation\n"
            "⚠ SEVERITY: LOW\n\n"
            "🌿 BIOLOGICAL CONTROL:\n"
            "• Pheromone traps @ 2–3 traps per hectare — monitoring only\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Maintain field sanitation\n\n"
            "📅 MONITORING:\n"
            "• Inspect weekly\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
    "bunchy": {
        "High": (
            "🔍 DISEASE: Banana Bunchy Top Virus (BBTV)\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Uproot and burn ALL infected plants immediately\n"
            "• No chemical cure exists for BBTV\n"
            "• Establish 50-metre buffer zone around infection area\n\n"
            "💊 CHEMICAL TREATMENT (Vector Control):\n"
            "• Imidacloprid 17.8 SL @ 0.3 ml/litre — controls aphid vectors\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Use ONLY certified virus-free tissue culture planting material\n"
            "• Control aphid population continuously\n\n"
            "📅 MONITORING:\n"
            "• Scout for aphids every 5 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Banana Bunchy Top Virus (BBTV)\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Rogue out all symptomatic plants and destroy immediately\n\n"
            "💊 CHEMICAL TREATMENT (Vector Control):\n"
            "• Imidacloprid 17.8 SL @ 0.5 ml/litre — aphid vector control\n\n"
            "📅 MONITORING:\n"
            "• Check for new aphid colonies every 5 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Banana Bunchy Top Virus (BBTV)\n"
            "⚠ SEVERITY: LOW\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• Remove and destroy all symptomatic plants immediately\n\n"
            "💊 CHEMICAL TREATMENT (Vector Control):\n"
            "• Imidacloprid spray — control aphid vector population\n\n"
            "📅 MONITORING:\n"
            "• Weekly scouting for aphid activity\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
    "anthracnose": {
        "High": (
            "🔍 DISEASE: Anthracnose\n"
            "⚠ SEVERITY: HIGH\n\n"
            "📋 IMMEDIATE ACTIONS:\n"
            "• ⚠ URGENT — Apply treatment immediately\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbendazim 50 WP @ 0.1% — fungicide spray\n"
            "• Hot water treatment: immerse bunches at 52°C for 3 minutes\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Store harvested fruit at 13–14°C with 90–95% relative humidity\n"
            "• Handle fruit carefully to minimise wounds during harvest\n\n"
            "📅 MONITORING:\n"
            "• Check stored fruit every 2 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "🔍 DISEASE: Anthracnose\n"
            "⚠ SEVERITY: MEDIUM\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Carbendazim 50 WP — fungicide spray\n"
            "• Hot water treatment @ 52°C for 3 minutes — post-harvest\n\n"
            "📅 MONITORING:\n"
            "• Inspect stored fruit every 3 days\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "🔍 DISEASE: Anthracnose\n"
            "⚠ SEVERITY: LOW\n\n"
            "💊 CHEMICAL TREATMENT:\n"
            "• Mancozeb 75 WP @ 0.2% — preventive spray during flowering\n\n"
            "🛡 PREVENTIVE MEASURES:\n"
            "• Ensure careful harvesting to minimise fruit wounds\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
    "healthy": {
        "None": (
            "🔍 STATUS: Healthy Plant\n"
            "✅ SEVERITY: NONE\n\n"
            "✅ Your banana plant appears HEALTHY!\n\n"
            "📋 GOOD AGRICULTURAL PRACTICES:\n"
            "• Apply NPK @ 200:60:300 g per plant per year — 4 split doses\n"
            "• Maintain soil moisture at 70–75% field capacity\n"
            "• Drip irrigation preferred over overhead irrigation\n"
            "• Remove dry and diseased leaves regularly\n"
            "• Retain only one ratoon sucker per mat\n\n"
            "📅 MONITORING:\n"
            "• Scout weekly for early signs of Sigatoka, weevils, and BBTV\n\n"
            "📌 Source: ICAR-NRCB, Trichy."
        ),
    },
}

_GENERIC_FALLBACK: dict[str, str] = {
    "High": (
        "⚠ URGENT — Severe disease detected.\n\n"
        "📋 IMMEDIATE ACTIONS:\n"
        "• Contact your nearest ICAR-NRCB office immediately\n"
        "• Isolate affected plants from healthy ones\n\n"
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


class AdvisoryService:
    """
    Gemini LLM-powered ICAR advisory service.

    Primary:  Gemini 2.5 Flash — dynamic bullet-point advisory
    Fallback: Hardcoded ICAR KB — reliable static bullet-point advisory

    Supported Languages (23 — All Indian Official Languages + English):
        English, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi,
        Gujarati, Punjabi, Bengali, Odia, Assamese, Urdu, Sanskrit,
        Konkani, Manipuri, Bodo, Dogri, Kashmiri, Maithili,
        Nepali, Santali, Sindhi
    """

    def get_advisory(
        self,
        disease_name: str,
        severity: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> str:
        """
        Generate ICAR-aligned bullet-point advisory.

        Args:
            disease_name: Detected banana disease label.
            severity:     Low, Medium, High, or None.
            language:     Response language key (e.g. 'tamil', 'hindi').

        Returns:
            Bullet-point advisory string in requested language.
        """
        # Normalise language input
        language = language.lower().strip() if language else DEFAULT_LANGUAGE
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(
                "Unsupported language '%s' — falling back to English", language
            )
            language = DEFAULT_LANGUAGE

        # Try Gemini first
        advisory = self._get_gemini_advisory(disease_name, severity, language)

        if advisory:
            logger.info(
                "Gemini advisory generated — disease='%s' severity='%s' language='%s'",
                disease_name, severity, language,
            )
            return advisory

        # Fallback to hardcoded KB
        logger.warning(
            "Gemini unavailable — using fallback KB — disease='%s' severity='%s'",
            disease_name, severity,
        )
        fallback = self._get_fallback_advisory(disease_name, severity)

        # Add note if non-English requested but Gemini failed
        if language != DEFAULT_LANGUAGE:
            lang_display = SUPPORTED_LANGUAGES.get(language, language)
            fallback = (
                f"[{lang_display} advisory unavailable — showing English]\n\n"
                + fallback
            )

        return fallback

    def _get_gemini_advisory(
        self,
        disease_name: str,
        severity: str,
        language: str = DEFAULT_LANGUAGE,
    ) -> str | None:
        """Call Gemini API to generate dynamic bullet-point advisory."""
        try:
            model = _get_gemini_model()
            if model is None:
                return None

            system_prompt = _build_system_prompt(language)
            lang_display  = SUPPORTED_LANGUAGES.get(language, "English")

            prompt = f"""{system_prompt}

Generate a structured bullet-point ICAR advisory for the following detection:

Disease Detected : {disease_name}
Severity Level   : {severity}
Detection System : AgroGuard-AI (ConvNeXt Small — 99.78% accuracy)
Guidelines       : ICAR-NRCB, Trichy, India
Response Language: {lang_display}

IMPORTANT:
- Use ONLY bullet points — absolutely no paragraphs
- Follow the exact section headers from the system prompt
- Keep it practical and simple for Indian banana farmers
- All content including headers must be in {lang_display}"""

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

    def _get_fallback_advisory(self, disease_name: str, severity: str) -> str:
        """Return hardcoded ICAR advisory in bullet-point format."""
        disease_lower = disease_name.lower()

        for keyword, severity_map in _FALLBACK_KB.items():
            if keyword in disease_lower:
                advice = severity_map.get(
                    severity,
                    _GENERIC_FALLBACK.get(severity, "")
                )
                logger.info(
                    "Fallback KB matched keyword='%s' severity='%s'",
                    keyword, severity,
                )
                return advice

        return _GENERIC_FALLBACK.get(severity, "No advisory available.")


def get_supported_languages() -> dict:
    """Return all supported languages for API response."""
    return {
        "total": len(SUPPORTED_LANGUAGES),
        "default": DEFAULT_LANGUAGE,
        "languages": SUPPORTED_LANGUAGES,
        "usage": "Pass 'language' field in predict request (e.g. language=tamil)"
    }