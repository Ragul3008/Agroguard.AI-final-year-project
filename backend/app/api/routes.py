"""
api/routes.py - Production API endpoints with JWT + Rate Limiting.
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.database.crud import get_recent_predictions, get_prediction_stats
from app.database.models import Farmer
from pydantic import BaseModel
from app.schemas.response_schema import PredictResponse
from app.services.prediction_service import PredictionService
from app.services.location_service import LocationService
from app.services.advisory_service import AdvisoryService, get_supported_languages, SUPPORTED_LANGUAGES
from app.utils.dependencies import get_current_farmer
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger              = get_logger(__name__)
router              = APIRouter(tags=["Banana Disease Detection"])
_prediction_service = PredictionService()
_location_service   = LocationService()
_advisory_service   = AdvisoryService()

# ─────────────────────────────────────────────────────────────────────────────
# Language aliases — maps short ISO codes → full language keys
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE_ALIASES: dict[str, str] = {
    "en": "english", "hi": "hindi", "ta": "tamil", "te": "telugu",
    "kn": "kannada", "ml": "malayalam", "mr": "marathi", "gu": "gujarati",
    "pa": "punjabi", "bn": "bengali", "or": "odia", "as": "assamese",
    "ur": "urdu", "sa": "sanskrit", "ne": "nepali", "sd": "sindhi",
    "kok": "konkani", "mni": "manipuri", "brx": "bodo", "doi": "dogri",
    "ks": "kashmiri", "mai": "maithili", "sat": "santali",
    "eng": "english", "hin": "hindi", "tam": "tamil", "tel": "telugu",
    "kan": "kannada", "mal": "malayalam", "mar": "marathi", "guj": "gujarati",
    "pun": "punjabi", "ben": "bengali",
    "en-in": "english", "hi-in": "hindi", "ta-in": "tamil", "te-in": "telugu",
    "kn-in": "kannada", "ml-in": "malayalam", "mr-in": "marathi",
    "gu-in": "gujarati", "pa-in": "punjabi", "bn-in": "bengali",
    "or-in": "odia", "as-in": "assamese", "ur-in": "urdu",
}


def _resolve_language(language: str) -> str:
    """Resolve language input to a valid key."""
    lang     = language.lower().strip()
    resolved = LANGUAGE_ALIASES.get(lang, lang)
    if resolved in SUPPORTED_LANGUAGES:
        return resolved
    return "english"


# ─────────────────────────────────────────────────────────────────────────────
# Helper — shared nearby centres logic
# ─────────────────────────────────────────────────────────────────────────────
async def _get_centres(
    latitude: Optional[float],
    longitude: Optional[float],
    max_results: int,
    farmer: Optional[Farmer] = None,
) -> dict:
    """Shared logic for all nearby-centres endpoints."""
    if latitude is None or longitude is None:
        coords = None
        if farmer:
            loc_parts = [farmer.village, farmer.district, farmer.state]
            loc_query = ", ".join(p for p in loc_parts if p)
            if loc_query:
                logger.info("Resolving location for farmer '%s' via registered profile '%s'...", farmer.name, loc_query)
                coords = await _location_service.geocode_address(loc_query)

        if coords:
            latitude, longitude = coords
            logger.info("Successfully geocoded farmer profile to lat=%.4f, lng=%.4f", latitude, longitude)
        else:
            logger.info("Latitude/Longitude missing and profile un-geocoded, defaulting to Chidambaram (11.3995, 79.6909)")
            latitude = 11.3995
            longitude = 79.6909

    centres = await _location_service.get_all_nearby_centres(
        latitude    = latitude,
        longitude   = longitude,
        max_results = min(max_results, 10),
    )
    return {
        "latitude":    latitude,
        "longitude":   longitude,
        "total_found": len(centres),
        "centres":     centres,
        "centers":     centres,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PREDICT
# ─────────────────────────────────────────────────────────────────────────────
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
        description="Advisory language. Accepts full names or short codes: en, hi, ta, te, kn, ml...",
    ),
    db:        AsyncSession    = Depends(get_db),
    farmer:    Farmer          = Depends(get_current_farmer),
) -> PredictResponse:
    """Full banana disease prediction pipeline with language + location support."""

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


# ─────────────────────────────────────────────────────────────────────────────
# NEARBY CENTRES — original route
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/nearby-centres",
    summary="Get all nearby horticulture offices",
    description="📍 Returns nearby horticulture and agriculture offices sorted by distance.",
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
    return await _get_centres(latitude, longitude, max_results, farmer=farmer)


# ─────────────────────────────────────────────────────────────────────────────
# NEARBY CENTRES — frontend alias routes (fixes 404 errors)
# Frontend calls: /api/v1/maps/nearby-centers  (different spelling + prefix)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/maps/nearby-centers",
    summary="Get nearby centres (frontend alias)",
    description="📍 Alias for /nearby-centres — matches frontend URL format.",
)
@limiter.limit("30/minute")
async def get_nearby_centers_alias(
    request:     Request,
    latitude:    Optional[float] = None,
    longitude:   Optional[float] = None,
    max_results: int             = 5,
    farmer:      Farmer          = Depends(get_current_farmer),
) -> dict:
    """Alias — same as /nearby-centres but matches frontend URL."""
    logger.info(
        "GET /maps/nearby-centers | lat=%s lng=%s (frontend alias)",
        latitude, longitude,
    )
    return await _get_centres(latitude, longitude, max_results, farmer=farmer)


@router.get(
    "/nearby-centers",
    summary="Get nearby centres (US spelling alias)",
    description="📍 Alias for /nearby-centres — US spelling variant.",
)
@limiter.limit("30/minute")
async def get_nearby_centers_us(
    request:     Request,
    latitude:    Optional[float] = None,
    longitude:   Optional[float] = None,
    max_results: int             = 5,
    farmer:      Farmer          = Depends(get_current_farmer),
) -> dict:
    """Alias — US spelling variant of /nearby-centres."""
    return await _get_centres(latitude, longitude, max_results, farmer=farmer)


# ─────────────────────────────────────────────────────────────────────────────
# PREDICTION HISTORY
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGES
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/languages",
    summary="Get all supported advisory languages",
    description="Returns all 23 supported Indian languages for advisory generation.",
)
def list_languages() -> dict:
    """Return all supported languages."""
    return get_supported_languages()


# ─────────────────────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# FARMING ADVISORY CHAT & TRANSLATION
# ─────────────────────────────────────────────────────────────────────────────
class TranslateRequest(BaseModel):
    text:            str
    target_language: str = "english"


@router.post(
    "/chat",
    summary="Farming advisory chat assistant",
    description="Ask questions about banana farming, disease treatment, fertilizer, or irrigation in your language.",
)
@limiter.limit("30/minute")
async def chat_advisory(
    request:         Request,
    message:         Optional[str] = Form(None),
    language:        Optional[str] = Form("english"),
    disease_context: Optional[str] = Form(None),
    farmer:          Optional[Farmer] = Depends(get_current_farmer),
) -> dict:
    """Chat endpoint supporting both FormData and JSON requests."""
    if not message:
        try:
            body = await request.json()
            message = body.get("message") or body.get("text")
            language = body.get("language") or language
            disease_context = body.get("disease_context") or disease_context
        except Exception:
            pass

    if not message or not str(message).strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    lang_clean = _resolve_language(language or "english")
    reply = await _advisory_service.generate_chat_response(
        message=message,
        language=lang_clean,
        disease_context=disease_context,
    )
    return {"reply": reply, "language": lang_clean}


@router.post(
    "/translate",
    summary="Translate text to target language",
    description="Translate text to any supported Indian language.",
)
@limiter.limit("30/minute")
async def translate_advisory_text(
    request: Request,
    payload: TranslateRequest,
    farmer: Optional[Farmer] = Depends(get_current_farmer),
) -> dict:
    """Translate text to requested target language via Gemini."""
    lang_clean = _resolve_language(payload.target_language)
    translated = await _advisory_service.translate_text(
        text=payload.text,
        target_language=lang_clean,
    )
    return {"translated_text": translated, "language": lang_clean}