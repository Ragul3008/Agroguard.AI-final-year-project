"""
api/speech.py - Speech-to-Text API endpoints for AgroGuard-AI.

Farmers can speak in their native language (Tamil, Hindi, Telugu, etc.)
to describe their banana crop problem. The Web Speech API in the browser
handles the actual speech recognition and sends the transcribed text here.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.services.speech_service import SpeechService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Speech to Text"])

_speech_service = SpeechService()


# ---------------------------------------------------------------------------
# Request / Response schemas (defined here to keep speech feature self-contained)
# ---------------------------------------------------------------------------

class TranscriptionRequest(BaseModel):
    """Request body sent by the frontend after Web Speech API transcription."""

    text: str = Field(
        ...,
        description="Raw transcribed text from the farmer's speech.",
        example="வாழை இலையில் மஞ்சள் நிற புள்ளிகள் உள்ளன",
    )
    language_code: str = Field(
        default="en-IN",
        description="BCP-47 language code of the spoken language.",
        example="ta-IN",
    )


class TranscriptionResponse(BaseModel):
    """Response returned after processing the transcription."""

    original_text: str       = Field(..., description="Raw transcribed text as received.")
    processed_text: str      = Field(..., description="Cleaned and normalised text.")
    language: str            = Field(..., description="Human-readable language name.")
    language_code: str       = Field(..., description="BCP-47 language code.")
    detected_keywords: list[str] = Field(..., description="Banana disease keywords found in text.")
    has_disease_context: bool = Field(..., description="True if disease-related terms were detected.")
    message: str             = Field(..., description="Status message.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/speech/process",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Process farmer speech transcription",
    description=(
        "Receives transcribed text from the farmer's speech (in any language) "
        "and processes it for banana disease keyword detection.\n\n"
        "The frontend uses the browser's Web Speech API to convert speech to text, "
        "then sends the text to this endpoint.\n\n"
        "Supported languages: Tamil, Hindi, Telugu, Kannada, Malayalam, "
        "English, Marathi, Gujarati, Punjabi, Bengali, Odia."
    ),
)
async def process_speech(
    request: TranscriptionRequest,
) -> TranscriptionResponse:
    """
    Process farmer's speech transcription.

    Steps:
        1. Receive transcribed text from frontend.
        2. Clean and normalise the text.
        3. Detect banana disease keywords.
        4. Return structured response.
    """
    logger.info(
        "POST /speech/process | lang='%s' | text='%s'",
        request.language_code,
        request.text[:60],
    )

    try:
        result = _speech_service.process_transcription(
            text=request.text,
            language_code=request.language_code,
        )
        return TranscriptionResponse(**result)

    except Exception as exc:
        logger.error("Speech processing error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process speech transcription. Please try again.",
        )


@router.get(
    "/speech/languages",
    summary="Get all supported languages",
    description="Returns the list of all languages supported for speech recognition.",
)
async def get_supported_languages() -> list[dict]:
    """
    Return all supported languages for the frontend language dropdown.

    Example response:
        [
            {"code": "ta-IN", "name": "தமிழ் (Tamil)"},
            {"code": "hi-IN", "name": "हिन्दी (Hindi)"},
            ...
        ]
    """
    return _speech_service.get_supported_languages()
