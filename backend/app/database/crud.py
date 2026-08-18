"""
database/crud.py - Production CRUD operations for AgroGuard-AI.
Updated: farmer_id tracking added to predictions.
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Prediction, Farmer
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_prediction(
    db:              AsyncSession,
    disease:         str,
    confidence:      float,
    confidence_pct:  str,
    severity:        str,
    advisory:        str,
    is_confident:    bool,
    is_banana_image: bool,
    rejection_reason: Optional[str],
    latitude:        Optional[float],
    longitude:       Optional[float],
    nearest_center:  Optional[str],
    farmer_id:       Optional[int] = None,
) -> Prediction:
    """Save a prediction to the database."""
    prediction = Prediction(
        farmer_id=farmer_id,
        disease=disease,
        confidence=confidence,
        confidence_pct=confidence_pct,
        severity=severity,
        advisory=advisory,
        is_confident=is_confident,
        is_banana_image=is_banana_image,
        rejection_reason=rejection_reason,
        latitude=latitude,
        longitude=longitude,
        nearest_center=nearest_center,
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)
    logger.info("Prediction saved → id=%d farmer_id=%s disease='%s'",
                prediction.id, farmer_id, prediction.disease)
    return prediction


async def get_prediction_by_id(
    db: AsyncSession, prediction_id: int
) -> Optional[Prediction]:
    """Retrieve a single prediction by primary key."""
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    return result.scalar_one_or_none()


async def get_farmer_by_id(db: AsyncSession, farmer_id: int) -> Optional[Farmer]:
    """Retrieve farmer by primary key ID."""
    result = await db.execute(select(Farmer).where(Farmer.id == farmer_id))
    return result.scalar_one_or_none()


async def get_recent_predictions(
    db: AsyncSession, limit: int = 50
) -> list[Prediction]:
    """Return most recent predictions."""
    result = await db.execute(
        select(Prediction).order_by(Prediction.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_prediction_stats(db: AsyncSession) -> dict:
    """Return disease statistics for dashboard."""
    total_result = await db.execute(select(func.count(Prediction.id)))
    total_count  = total_result.scalar()

    by_disease = await db.execute(
        select(Prediction.disease, func.count(Prediction.id))
        .group_by(Prediction.disease)
        .order_by(func.count(Prediction.id).desc())
    )
    by_severity = await db.execute(
        select(Prediction.severity, func.count(Prediction.id))
        .group_by(Prediction.severity)
    )
    farmer_count = await db.execute(select(func.count(Farmer.id)))

    return {
        "total_predictions": total_count,
        "total_farmers":     farmer_count.scalar(),
        "by_disease":        {row[0]: row[1] for row in by_disease},
        "by_severity":       {row[0]: row[1] for row in by_severity},
    }