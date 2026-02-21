"""
database/crud.py - Async CRUD operations for AgroGuard-AI prediction records.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Prediction
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_prediction(
    db:         AsyncSession,
    disease:    str,
    confidence: float,
    severity:   str,
    advisory:   str,
    latitude:   Optional[float],
    longitude:  Optional[float],
) -> Prediction:
    """
    Persist a new banana disease prediction to the database.

    Args:
        db:         Async database session.
        disease:    Detected disease label.
        confidence: Model confidence score [0, 1].
        severity:   Estimated severity level.
        advisory:   ICAR-aligned advisory text.
        latitude:   Optional GPS latitude of the farm.
        longitude:  Optional GPS longitude of the farm.

    Returns:
        The newly created Prediction ORM object with ``id`` populated.
    """
    prediction = Prediction(
        disease=disease,
        confidence=confidence,
        severity=severity,
        advisory=advisory,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)

    logger.info(
        "Prediction saved → id=%d  disease='%s'  severity='%s'",
        prediction.id,
        prediction.disease,
        prediction.severity,
    )
    return prediction


async def get_prediction_by_id(
    db: AsyncSession, prediction_id: int
) -> Optional[Prediction]:
    """Retrieve a single prediction by primary key."""
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    return result.scalar_one_or_none()


async def get_recent_predictions(
    db: AsyncSession, limit: int = 100
) -> list[Prediction]:
    """Return the most recent predictions ordered by creation time (newest first)."""
    result = await db.execute(
        select(Prediction).order_by(Prediction.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
