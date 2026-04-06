"""
api/routes.py - Production API endpoints with JWT + Rate Limiting.
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.database.crud import get_recent_predictions, get_prediction_stats
from app.database.models import Farmer
from app.schemas.response_schema import PredictResponse
from app.services.prediction_service import PredictionService
from app.services.location_service import LocationService
from app.services.advisory_service import get_supported_languages, SUPPORTED_LANGUAGES
from app.utils.dependencies import get_current_farmer
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger              = get_logger(__name__)
router              = APIRouter(tags=["Banana Disease Detection"])
_prediction_service = PredictionService()
_location_service   = LocationService()

# ─────────────────────────────────────────────────────────────────────────────
# Language aliases — maps short ISO codes → full language keys
# Handles frontend sending 'en', 'ta', 'hi' instead of 'english', 'tamil', 'hindi'
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE_ALIASES: dict[str, str] = {
    # ISO 639-1 short codes
    "en":  "english",
    "hi":  "hindi",
    "ta":  "tamil",
    "te":  "telugu",
    "kn":  "kannada",
    "ml":  "malayalam",
    "mr":  "marathi",
    "gu":  "gujarati",
    "pa":  "punjabi",
    "bn":  "bengali",
    "or":  "odia",
    "as":  "assamese",
    "ur":  "urdu",
    "sa":  "sanskrit",
    "ne":  "nepali",
    "sd":  "sindhi",
    # ISO 639-3 codes
    "kok": "konkani",
    "mni": "manipuri",
    "brx": "bodo",
    "doi": "dogri",
    "ks":  "kashmiri",
    "mai": "maithili",
    "sat": "santali",
    # Common alternate spellings
    "eng": "english",
    "hin": "hindi",
    "tam": "tamil",
    "tel": "telugu",
    "kan": "kannada",
    "mal": "malayalam",
    "mar": "marathi",
    "guj": "gujarati",
    "pun": "punjabi",
    "ben": "bengali",
    # Locale codes (e.g. en-IN, ta-IN)
    "en-in":  "english",
    "hi-in":  "hindi",
    "ta-in":  "tamil",
    "te-in":  "telugu",
    "kn-in":  "kannada",
    "ml-in":  "malayalam",
    "mr-in":  "marathi",
    "gu-in":  "gujarati",
    "pa-in":  "punjabi",
    "bn-in":  "bengali",
    "or-in":  "odia",
    "as-in":  "assamese",
    "ur-in":  "urdu",
}


def _resolve_language(language: str) -> str:
    """
    Resolve language input to a valid key.
    Handles: 'en', 'ta', 'hi', 'en-IN', 'english', 'tamil' etc.
    """
    lang = language.lower().strip()
    # Check aliases first
    resolved = LANGUAGE_ALIASES.get(lang, lang)
    # Check if resolved key is valid
    if resolved in SUPPORTED_LANGUAGES:
        return resolved
    # Default to English if still not found
    return "english"


@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect banana plant disease (Login required)",
    description=(
        "Upload a banana leaf image.\n\n"
        "🔐 **Authentication required**\n\n"
        "🛡️ **Rate limit:** 10 requests per minute\n\n"
        "**Diseases detected:** Panama, Black Sigatoka, Yellow Sigatoka, "
        "Pseudostem Weevil, BBTV, Anthracnose, Healthy\n\n"
        "🌐 **Language:** Pass `language` for advisory in your language.\n"
        "Accepts full names (english, tamil) or short codes (en, ta, hi).\n\n"
        "📍 **Location:** Pass `latitude` and `longitude` for nearby centres."
    ),
)
@limiter.limit("10/minute")
async def predict_banana_disease(
    request:   Request,
    image:     UploadFile      = File(..., description="Banana plant image JPEG/PNG/WebP."),
    latitude:  Optional[float] = Form(None, ge=-90.0,  le=90.0),
    longitude: Optional[float] = Form(None, ge=-180.0, le=180.0),
    language:  str             = Form(
        default="english",
        description=(
            "Advisory language. Accepts full names or short codes.\n"
            "Full: english, hindi, tamil, telugu, kannada, malayalam, "
            "marathi, gujarati, punjabi, bengali, odia, assamese, urdu, "
            "sanskrit, konkani, manipuri, bodo, dogri, kashmiri, maithili, "
            "nepali, santali, sindhi\n"
            "Short codes: en, hi, ta, te, kn, ml, mr, gu, pa, bn, or, as, ur"
        ),
    ),
    db:        AsyncSession    = Depends(get_db),
    farmer:    Farmer          = Depends(get_current_farmer),
) -> PredictResponse:
    """Full banana disease prediction pipeline with language + location support."""

    # Resolve language — handles 'en', 'ta', 'english', 'tamil', 'en-IN' etc.
    lang_clean = _resolve_language(language)

    logger.info(
        "POST /predict | farmer_id=%d phone='%s' file='%s' "
        "lat=%s lng=%s language='%s' (resolved from '%s')",
        farmer.id, farmer.phone, image.filename,
        latitude, longitude, lang_clean, language,
    )

    image_bytes = await image.read()

    try:
        return await _prediction_service.predict(
            image_bytes  = image_bytes,
            content_type = image.content_type or "application/octet-stream",
            latitude     = latitude,
            longitude    = longitude,
            language     = lang_clean,
            db           = db,
            farmer_id    = farmer.id,
        )
    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")


@router.get(
    "/nearby-centres",
    summary="Get all nearby horticulture offices",
    description=(
        "📍 Returns ALL nearby horticulture and agriculture offices "
        "sorted by distance from farmer GPS location.\n\n"
        "Pass `latitude` and `longitude` as query parameters.\n\n"
        "Returns top 5 nearest offices by default (max 10)."
    ),
)
@limiter.limit("30/minute")
async def get_nearby_centres(
    request:     Request,
    latitude:    Optional[float] = None,
    longitude:   Optional[float] = None,
    max_results: int             = 5,
    farmer:      Farmer          = Depends(get_current_farmer),
) -> dict:
    """Return all nearby horticulture offices sorted by distance."""

    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "latitude and longitude are required. "
                "Example: /nearby-centres?latitude=10.82&longitude=78.68"
            ),
        )

    centres = _location_service.get_all_nearby_centres(
        latitude    = latitude,
        longitude   = longitude,
        max_results = min(max_results, 10),
    )

    return {
        "latitude":    latitude,
        "longitude":   longitude,
        "total_found": len(centres),
        "centres":     centres,
    }


@router.get(
    "/predictions",
    summary="Get prediction history (Login required)",
    description="🔐 Returns the 50 most recent predictions.",
)
@limiter.limit("30/minute")
async def get_prediction_history(
    request: Request,
    db:      AsyncSession = Depends(get_db),
    farmer:  Farmer       = Depends(get_current_farmer),
) -> list[dict]:
    """Return recent prediction history."""
    predictions = await get_recent_predictions(db, limit=50)
    return [
        {
            "id":              p.id,
            "disease":         p.disease,
            "confidence_pct":  p.confidence_pct,
            "severity":        p.severity,
            "is_confident":    p.is_confident,
            "is_banana_image": p.is_banana_image,
            "nearest_center":  p.nearest_center,
            "created_at":      p.created_at.isoformat() if p.created_at else None,
        }
        for p in predictions
    ]


@router.get(
    "/languages",
    summary="Get all supported advisory languages",
    description="Returns all 23 supported Indian languages for advisory generation.",
)
def list_languages() -> dict:
    """Return all supported languages."""
    return get_supported_languages()


@router.get(
    "/predictions/stats",
    summary="Get disease statistics (Public)",
    description="Returns disease distribution statistics. No authentication required.",
)
@limiter.limit("60/minute")
async def get_stats(
    request: Request,
    db:      AsyncSession = Depends(get_db),
) -> dict:
    """Return disease statistics — public endpoint."""
    return await get_prediction_stats(db)