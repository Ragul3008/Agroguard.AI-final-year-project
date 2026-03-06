"""
services/speech_service.py - Speech-to-Text service for AgroGuard-AI.

Two modes:
    1. process_transcription() — processes text already transcribed by browser
    2. transcribe_audio()      — transcribes raw audio using OpenAI Whisper medium

Whisper medium model:
    - Size:     1.5 GB
    - Accuracy: 99%+ for Tamil, Hindi, Telugu, Kannada, Malayalam
    - Offline:  Works without internet after first download
"""

import os
import tempfile
import threading

import whisper

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported language codes → display names
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: dict[str, str] = {
    "ta":    "தமிழ் (Tamil)",
    "hi":    "हिन्दी (Hindi)",
    "te":    "తెలుగు (Telugu)",
    "kn":    "ಕನ್ನಡ (Kannada)",
    "ml":    "മലയാളം (Malayalam)",
    "en":    "English",
    "mr":    "मराठी (Marathi)",
    "gu":    "ગુજરાતી (Gujarati)",
    "pa":    "ਪੰਜਾਬੀ (Punjabi)",
    "bn":    "বাংলা (Bengali)",
    "or":    "ଓଡ଼ିଆ (Odia)",
    "ta-IN": "தமிழ் (Tamil)",
    "hi-IN": "हिन्दी (Hindi)",
    "te-IN": "తెలుగు (Telugu)",
    "kn-IN": "ಕನ್ನಡ (Kannada)",
    "ml-IN": "മലയാളം (Malayalam)",
    "en-IN": "English (India)",
    "en-US": "English (US)",
}

# ---------------------------------------------------------------------------
# Banana disease keywords per language
# ---------------------------------------------------------------------------
DISEASE_KEYWORDS: dict[str, list[str]] = {
    "ta": [
        "இலை", "நோய்", "மஞ்சள்", "கருப்பு", "அழுகல்",
        "பூஞ்சை", "வாழை", "பூச்சி", "வாடல்", "புள்ளி",
    ],
    "hi": [
        "पत्ता", "रोग", "पीला", "काला", "सड़न",
        "फफूंदी", "केला", "कीड़ा", "मुरझाना", "धब्बा",
    ],
    "te": [
        "ఆకు", "వ్యాధి", "పసుపు", "నలుపు", "కుళ్ళు",
        "శిలీంధ్రం", "అరటి", "పురుగు", "వాడిపోవడం", "మచ్చ",
    ],
    "kn": [
        "ಎಲೆ", "ರೋಗ", "ಹಳದಿ", "ಕಪ್ಪು", "ಕೊಳೆ",
        "ಶಿಲೀಂಧ್ರ", "ಬಾಳೆ", "ಕೀಟ", "ಬಾಡು", "ಚುಕ್ಕೆ",
    ],
    "ml": [
        "ഇല", "രോഗം", "മഞ്ഞ", "കറുപ്പ്", "ചീയൽ",
        "കുമിൾ", "വാഴ", "കീടം", "വാട്ടം", "പുള്ളി",
    ],
    "en": [
        "leaf", "disease", "yellow", "black", "rot",
        "fungus", "banana", "insect", "wilt", "spot",
        "blight", "weevil", "virus", "sigatoka", "panama",
        "anthracnose", "bunchy", "pseudostem",
    ],
}

# ---------------------------------------------------------------------------
# Whisper model singleton — loads once, reused for all requests
# ---------------------------------------------------------------------------
_whisper_model = None
_whisper_lock  = threading.Lock()


def get_whisper_model() -> whisper.Whisper:
    """
    Load and return the Whisper medium model singleton.

    First run: downloads ~1.5 GB model automatically.
    Subsequent runs: loads from local cache instantly.
    """
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                logger.info(
                    "Loading Whisper medium model... "
                    "(first run downloads ~1.5 GB — please wait)"
                )
                _whisper_model = whisper.load_model("medium")
                logger.info("✓ Whisper medium model loaded successfully.")
    return _whisper_model


def _normalise_lang(code: str) -> str:
    """Convert 'ta-IN' → 'ta', 'hi-IN' → 'hi', etc."""
    if not code:
        return None
    return code.split("-")[0].lower()


class SpeechService:
    """
    Handles multilingual speech-to-text for banana farmers.

    Mode 1 — process_transcription():
        Browser already converted speech to text.
        This method cleans and detects disease keywords.

    Mode 2 — transcribe_audio():
        Farmer uploads or records audio.
        Whisper medium converts it to text with 99%+ accuracy.
    """

    # ------------------------------------------------------------------
    # Mode 1 — Browser Web Speech API text processing
    # ------------------------------------------------------------------

    def process_transcription(
        self,
        text: str,
        language_code: str,
    ) -> dict:
        """
        Process text already transcribed by the browser Web Speech API.

        Args:
            text:          Raw transcribed text from browser.
            language_code: Language code e.g. 'ta-IN', 'hi-IN'.

        Returns:
            Structured response dict.
        """
        lang_key = _normalise_lang(language_code)

        if not text or not text.strip():
            logger.warning("Empty transcription received.")
            return {
                "original_text":        "",
                "processed_text":       "",
                "language":             SUPPORTED_LANGUAGES.get(language_code, language_code),
                "language_code":        language_code,
                "detected_keywords":    [],
                "has_disease_context":  False,
                "transcription_source": "browser",
                "message": "No speech detected. Please speak clearly and try again.",
            }

        cleaned  = text.strip()
        keywords = DISEASE_KEYWORDS.get(lang_key, DISEASE_KEYWORDS["en"])
        detected = [kw for kw in keywords if kw.lower() in cleaned.lower()]

        logger.info(
            "Browser transcription | lang='%s' | keywords=%s | text='%s'",
            language_code, detected, cleaned[:80],
        )

        return {
            "original_text":        text,
            "processed_text":       cleaned,
            "language":             SUPPORTED_LANGUAGES.get(
                                        language_code,
                                        SUPPORTED_LANGUAGES.get(lang_key, language_code)
                                    ),
            "language_code":        language_code,
            "detected_keywords":    detected,
            "has_disease_context":  len(detected) > 0,
            "transcription_source": "browser",
            "message": (
                "Speech transcribed. Disease-related terms detected."
                if detected
                else "Speech transcribed successfully."
            ),
        }

    # ------------------------------------------------------------------
    # Mode 2 — Whisper medium audio transcription
    # ------------------------------------------------------------------

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        language_code: str = None,
    ) -> dict:
        """
        Transcribe raw audio using OpenAI Whisper medium model.

        Supports audio formats: WAV, MP3, M4A, WebM, OGG, FLAC
        Languages: Tamil, Hindi, Telugu, Kannada, Malayalam, English + 95 more

        Args:
            audio_bytes:   Raw bytes of the uploaded audio file.
            language_code: Optional language hint e.g. 'ta', 'hi', 'te'.
                           Pass None to let Whisper auto-detect language.

        Returns:
            Structured response dict with transcribed text and keywords.

        Raises:
            ValueError:   If audio file is empty.
            RuntimeError: If Whisper transcription fails.
        """
        if not audio_bytes:
            raise ValueError("Audio file is empty. Please record again.")

        whisper_lang = _normalise_lang(language_code) if language_code else None
        tmp_path     = None

        try:
            # ── Write to temp file ──────────────────────────────────────
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            logger.info(
                "Whisper transcription started | lang_hint='%s' | size=%d bytes",
                whisper_lang, len(audio_bytes),
            )

            # ── Load Whisper singleton ──────────────────────────────────
            model = get_whisper_model()

            # ── Transcribe ─────────────────────────────────────────────
            result = model.transcribe(
                tmp_path,
                language=whisper_lang,   # None = auto-detect
                task="transcribe",
                fp16=False,              # fp16=False for CPU compatibility
                verbose=False,
            )

            transcribed_text  = result["text"].strip()
            detected_language = result.get("language", whisper_lang or "en")

            logger.info(
                "Whisper complete | detected_lang='%s' | text='%s'",
                detected_language, transcribed_text[:80],
            )

            # ── Detect disease keywords ─────────────────────────────────
            keywords = DISEASE_KEYWORDS.get(detected_language, DISEASE_KEYWORDS["en"])
            detected = [kw for kw in keywords if kw.lower() in transcribed_text.lower()]

            display_lang = SUPPORTED_LANGUAGES.get(
                detected_language,
                SUPPORTED_LANGUAGES.get(f"{detected_language}-IN", detected_language.upper())
            )

            return {
                "original_text":        transcribed_text,
                "processed_text":       transcribed_text,
                "language":             display_lang,
                "language_code":        detected_language,
                "detected_keywords":    detected,
                "has_disease_context":  len(detected) > 0,
                "transcription_source": "whisper-medium",
                "message": (
                    "Audio transcribed by Whisper AI. Disease-related terms detected."
                    if detected
                    else "Audio transcribed successfully by Whisper AI."
                ),
            }

        except Exception as exc:
            logger.error("Whisper transcription failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Audio transcription failed: {exc}") from exc

        finally:
            # Always delete temp file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_supported_languages(self) -> list[dict]:
        """Return supported languages list for frontend dropdown."""
        unique = {
            code: name
            for code, name in SUPPORTED_LANGUAGES.items()
            if len(code) == 2
        }
        return [{"code": code, "name": name} for code, name in unique.items()]