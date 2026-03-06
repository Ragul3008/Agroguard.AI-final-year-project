"""
api/routes.py - Production API endpoints for AgroGuard-AI.

Endpoints:
    POST /predict            — disease prediction
    GET  /predictions        — prediction history
    GET  /predictions/stats  — disease statistics
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.database.crud import get_recent_predictions, get_prediction_stats
from app.schemas.response_schema import PredictResponse
from app.services.prediction_service import PredictionService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Banana Disease Detection"])

_prediction_service = PredictionService()


@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect banana plant disease from uploaded image",
    description=(
        "Upload a banana leaf, stem, or fruit image.\n\n"
        "**Production features:**\n"
        "- Confidence threshold filtering (rejects uncertain predictions)\n"
        "- Non-banana image rejection\n"
        "- Full probability distribution for all 7 classes\n"
        "- ICAR-aligned treatment advisory\n"
        "- Nearest banana farming support centre\n\n"
        "**Diseases:** Panama Disease, Black Sigatoka, Yellow Sigatoka, "
        "Pseudostem Weevil, BBTV, Anthracnose, Healthy"
    ),
)
async def predict_banana_disease(
    image:     UploadFile        = File(..., description="Banana plant image JPEG/PNG/WebP."),
    latitude:  Optional[float]   = Form(None, ge=-90.0,  le=90.0),
    longitude: Optional[float]   = Form(None, ge=-180.0, le=180.0),
    db:        AsyncSession       = Depends(get_db),
) -> PredictResponse:
    """Full production banana disease prediction pipeline."""
    logger.info(
        "POST /predict | file='%s' type='%s' lat=%s lng=%s",
        image.filename, image.content_type, latitude, longitude,
    )

    image_bytes = await image.read()

    try:
        return await _prediction_service.predict(
            image_bytes=image_bytes,
            content_type=image.content_type or "application/octet-stream",
            latitude=latitude,
            longitude=longitude,
            db=db,
        )
    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")


@router.get(
    "/predictions",
    summary="Get prediction history",
    description="Returns the 50 most recent predictions.",
)
async def get_prediction_history(db: AsyncSession = Depends(get_db)) -> list[dict]:
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
    "/predictions/stats",
    summary="Get disease statistics",
    description="Returns disease distribution statistics for dashboard.",
)
async def get_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """Return disease statistics."""
    return await get_prediction_stats(db)