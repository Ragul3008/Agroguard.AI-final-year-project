"""
api/speech.py - Production Speech-to-Text endpoints for AgroGuard-AI.
Fixed: rejects "string" default from Swagger UI automatically.
"""

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.services.speech_service import SpeechService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Speech to Text"])

_speech_service  = SpeechService()
_MAX_AUDIO_SIZE  = 25 * 1024 * 1024  # 25 MB


class TranscriptionRequest(BaseModel):
    text:          str = Field(..., example="வாழை இலையில் மஞ்சள் புள்ளிகள்")
    language_code: str = Field(default="en-IN", example="ta-IN")


class TranscriptionResponse(BaseModel):
    original_text:        str
    processed_text:       str
    language:             str
    language_code:        str
    detected_keywords:    list[str]
    has_disease_context:  bool
    transcription_source: str
    message:              str


@router.get("/speech/languages", summary="Get supported languages")
async def get_supported_languages() -> list[dict]:
    return _speech_service.get_supported_languages()


@router.post(
    "/speech/process",
    response_model=TranscriptionResponse,
    summary="Process browser speech text",
)
async def process_speech(request: TranscriptionRequest) -> TranscriptionResponse:
    logger.info("POST /speech/process | lang='%s'", request.language_code)
    try:
        result = _speech_service.process_transcription(
            text=request.text,
            language_code=request.language_code,
        )
        return TranscriptionResponse(**result)
    except Exception as exc:
        logger.error("Speech error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process speech.")


@router.post(
    "/speech/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe farmer audio using Whisper medium AI",
    description=(
        "Upload farmer audio recording.\n\n"
        "**Formats:** WAV, MP3, M4A, WebM, OGG, FLAC\n\n"
        "**Accuracy:** 99%+ using OpenAI Whisper medium\n\n"
        "**Languages:** Tamil, Hindi, Telugu, Kannada, Malayalam, English + 90 more\n\n"
        "**Tip:** Leave language_code empty for automatic language detection."
    ),
)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language_code: Optional[str] = Form(
        default=None,
        description="Language hint: 'ta'=Tamil, 'hi'=Hindi, 'te'=Telugu. Leave empty for auto.",
    ),
) -> TranscriptionResponse:
    logger.info("POST /speech/transcribe | file='%s' lang='%s'", audio.filename, language_code)

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Audio file is empty.")
    if len(audio_bytes) > _MAX_AUDIO_SIZE:
        raise HTTPException(status_code=422, detail="Audio too large. Max 25 MB.")

    # Fix: reject "string" default value from Swagger UI
    if language_code and language_code.strip().lower() in ("string", ""):
        language_code = None

    try:
        result = _speech_service.transcribe_audio(
            audio_bytes=audio_bytes,
            language_code=language_code,
        )
        return TranscriptionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        logger.error("Whisper error: %s", exc)
        raise HTTPException(status_code=500, detail="Transcription failed. Please try again.")
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")