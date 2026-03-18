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
from app.services.advisory_service import get_supported_languages, SUPPORTED_LANGUAGES
from app.utils.dependencies import get_current_farmer
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Banana Disease Detection"])
_prediction_service = PredictionService()


@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect banana plant disease (Login required)",
    description=(
        "Upload a banana leaf, stem, or fruit image.\n\n"
        "🔐 **Authentication required**\n\n"
        "🛡️ **Rate limit:** 10 requests per minute per IP\n\n"
        "**Diseases detected:** Panama Disease, Black Sigatoka, Yellow Sigatoka, "
        "Pseudostem Weevil, BBTV, Anthracnose, Healthy\n\n"
        "🌐 **Language support:** Pass `language` field to get advisory in your language.\n\n"
        "**Supported languages:** english, hindi, tamil, telugu, kannada, malayalam, "
        "marathi, gujarati, punjabi, bengali, odia, assamese, urdu, sanskrit, "
        "konkani, manipuri, bodo, dogri, kashmiri, maithili, nepali, santali, sindhi"
    ),
)
@limiter.limit("10/minute")
async def predict_banana_disease(
    request:   Request,
    image:     UploadFile      = File(...,  description="Banana plant image JPEG/PNG/WebP."),
    latitude:  Optional[float] = Form(None, ge=-90.0,  le=90.0),
    longitude: Optional[float] = Form(None, ge=-180.0, le=180.0),
    language:  str             = Form(
        default="english",
        description=(
            "Advisory language. Supported: english, hindi, tamil, telugu, kannada, "
            "malayalam, marathi, gujarati, punjabi, bengali, odia, assamese, urdu, "
            "sanskrit, konkani, manipuri, bodo, dogri, kashmiri, maithili, nepali, "
            "santali, sindhi"
        ),
    ),
    db:        AsyncSession    = Depends(get_db),
    farmer:    Farmer          = Depends(get_current_farmer),
) -> PredictResponse:
    """Full production banana disease prediction pipeline with language support."""

    # Validate language
    lang_clean = language.lower().strip()
    if lang_clean not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported language '{language}'. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            ),
        )

    logger.info(
        "POST /predict | farmer_id=%d phone='%s' file='%s' lat=%s lng=%s language='%s'",
        farmer.id, farmer.phone, image.filename, latitude, longitude, lang_clean,
    )

    image_bytes = await image.read()

    try:
        return await _prediction_service.predict(
            image_bytes=image_bytes,
            content_type=image.content_type or "application/octet-stream",
            latitude=latitude,
            longitude=longitude,
            language=lang_clean,
            db=db,
            farmer_id=farmer.id,
        )
    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")


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
    summary="Get supported advisory languages",
    description="Returns all 23 supported languages for advisory generation.",
)
def list_languages() -> dict:
    """Return all supported languages for advisory."""
    return get_supported_languages()


@router.get(
    "/predictions/stats",
    summary="Get disease statistics (Public)",
    description="Returns disease distribution statistics. No authentication required.",
)
@limiter.limit("60/minute")
async def get_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return disease statistics — public endpoint."""
    return await get_prediction_stats(db)