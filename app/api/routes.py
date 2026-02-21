"""
api/routes.py - Banana disease prediction endpoint for AgroGuard-AI.
"""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.response_schema import PredictResponse
from app.services.prediction_service import PredictionService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Banana Disease Detection"])

# One PredictionService instance is shared across all requests (thread-safe)
_prediction_service = PredictionService()


@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect banana plant disease from an uploaded image",
    description=(
        "Upload a banana leaf, stem, or fruit image to detect diseases "
        "(Panama Disease, Black/Yellow Sigatoka, Pseudostem Weevil, BBTV, Anthracnose). "
        "Optionally provide GPS coordinates to receive the nearest ICAR/Horticulture office."
    ),
)
async def predict_banana_disease(
    image: UploadFile = File(
        ...,
        description="Banana plant image — leaf, pseudostem, or fruit (JPEG/PNG/WebP).",
    ),
    latitude: Optional[float] = Form(
        default=None,
        ge=-90.0,
        le=90.0,
        description="GPS latitude of the banana farm (optional).",
    ),
    longitude: Optional[float] = Form(
        default=None,
        ge=-180.0,
        le=180.0,
        description="GPS longitude of the banana farm (optional).",
    ),
    db: AsyncSession = Depends(get_db),
) -> PredictResponse:
    """
    Accepts a banana plant image and optional GPS coordinates.

    Returns detected disease, confidence, severity, ICAR-aligned advisory,
    and the nearest banana farming support centre.
    """
    logger.info(
        "POST /predict | file='%s' type='%s' lat=%s lng=%s",
        image.filename,
        image.content_type,
        latitude,
        longitude,
    )

    image_bytes = await image.read()

    try:
        response = await _prediction_service.predict(
            image_bytes=image_bytes,
            content_type=image.content_type or "application/octet-stream",
            latitude=latitude,
            longitude=longitude,
            db=db,
        )
    except ValueError as exc:
        logger.warning("Validation error in /predict: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error in /predict: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction. Please try again.",
        )

    return response
