"""
services/speech_service.py - Speech-to-Text service for AgroGuard-AI.

Allows farmers to describe their crop problem by speaking in ANY language.
Transcribed text is received from the frontend Web Speech API and processed
here for banana disease keyword detection and language identification.

Supported languages:
    Tamil, Hindi, Telugu, Kannada, Malayalam, English, Marathi,
    Gujarati, Punjabi, Bengali, Odia, and more.
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported language codes → display names
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: dict[str, str] = {
    "ta-IN": "தமிழ் (Tamil)",
    "hi-IN": "हिन्दी (Hindi)",
    "te-IN": "తెలుగు (Telugu)",
    "kn-IN": "ಕನ್ನಡ (Kannada)",
    "ml-IN": "മലയാളം (Malayalam)",
    "en-IN": "English (India)",
    "en-US": "English (US)",
    "mr-IN": "मराठी (Marathi)",
    "gu-IN": "ગુજરાતી (Gujarati)",
    "pa-IN": "ਪੰਜਾਬੀ (Punjabi)",
    "bn-IN": "বাংলা (Bengali)",
    "or-IN": "ଓଡ଼ିଆ (Odia)",
}

# ---------------------------------------------------------------------------
# Banana disease keywords per language for context detection
# ---------------------------------------------------------------------------
DISEASE_KEYWORDS: dict[str, list[str]] = {
    "ta-IN": [
        "இலை", "நோய்", "மஞ்சள்", "கருப்பு", "அழுகல்",
        "பூஞ்சை", "வாழை", "பூச்சி", "வாடல்", "புள்ளி",
    ],
    "hi-IN": [
        "पत्ता", "रोग", "पीला", "काला", "सड़न",
        "फफूंदी", "केला", "कीड़ा", "मुरझाना", "धब्बा",
    ],
    "te-IN": [
        "ఆకు", "వ్యాధి", "పసుపు", "నలుపు", "కుళ్ళు",
        "శిలీంధ్రం", "అరటి", "పురుగు", "వాడిపోవడం", "మచ్చ",
    ],
    "kn-IN": [
        "ಎಲೆ", "ರೋಗ", "ಹಳದಿ", "ಕಪ್ಪು", "ಕೊಳೆ",
        "ಶಿಲೀಂಧ್ರ", "ಬಾಳೆ", "ಕೀಟ", "ಬಾಡು", "ಚುಕ್ಕೆ",
    ],
    "ml-IN": [
        "ഇല", "രോഗം", "മഞ്ഞ", "കറുപ്പ്", "ചീയൽ",
        "കുമിൾ", "വാഴ", "കീടം", "വാട്ടം", "പുള്ളി",
    ],
    "en-IN": [
        "leaf", "disease", "yellow", "black", "rot",
        "fungus", "banana", "insect", "wilt", "spot",
        "blight", "weevil", "virus", "sigatoka", "panama",
    ],
    "en-US": [
        "leaf", "disease", "yellow", "black", "rot",
        "fungus", "banana", "insect", "wilt", "spot",
        "blight", "weevil", "virus", "sigatoka", "panama",
    ],
}


class SpeechService:
    """
    Processes farmer speech transcriptions for banana disease context.

    The actual speech-to-text conversion happens in the browser using the
    Web Speech API. This service handles:
        1. Text cleaning and normalisation.
        2. Banana disease keyword detection.
        3. Language identification and metadata.
    """

    def process_transcription(
        self,
        text: str,
        language_code: str,
    ) -> dict:
        """
        Process raw speech transcription from the farmer.

        Args:
            text:          Raw transcribed text from Web Speech API.
            language_code: BCP-47 language code (e.g. 'ta-IN', 'hi-IN').

        Returns:
            Dictionary with:
                - original_text:      Raw input text.
                - processed_text:     Cleaned text.
                - language:           Human-readable language name.
                - detected_keywords:  Banana disease keywords found in text.
                - message:            Status message.
        """
        if not text or not text.strip():
            logger.warning("Empty transcription received for lang='%s'", language_code)
            return {
                "original_text": "",
                "processed_text": "",
                "language": SUPPORTED_LANGUAGES.get(language_code, language_code),
                "language_code": language_code,
                "detected_keywords": [],
                "has_disease_context": False,
                "message": "No speech detected. Please speak clearly and try again.",
            }

        # Clean and normalise
        cleaned = text.strip()

        # Detect disease-related keywords
        # Check language-specific keywords first, then fallback to English
        keywords = DISEASE_KEYWORDS.get(
            language_code,
            DISEASE_KEYWORDS.get("en-IN", [])
        )
        detected = [kw for kw in keywords if kw.lower() in cleaned.lower()]

        has_disease_context = len(detected) > 0

        logger.info(
            "Speech processed | lang='%s' | keywords=%s | text='%s'",
            language_code,
            detected,
            cleaned[:80],
        )

        return {
            "original_text": text,
            "processed_text": cleaned,
            "language": SUPPORTED_LANGUAGES.get(language_code, language_code),
            "language_code": language_code,
            "detected_keywords": detected,
            "has_disease_context": has_disease_context,
            "message": (
                "Speech transcribed successfully. Disease-related terms detected."
                if has_disease_context
                else "Speech transcribed successfully."
            ),
        }

    def get_supported_languages(self) -> list[dict]:
        """
        Return all supported languages as a list for the frontend dropdown.

        Returns:
            List of dicts with 'code' and 'name' keys.
        """
        return [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
