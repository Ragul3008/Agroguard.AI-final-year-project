"""
database/models.py - Production ORM models for AgroGuard-AI.
Added: is_confident, is_banana_image, rejection_reason, nearest_center, model_version columns.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Prediction(Base):
    """Stores each banana disease prediction with full production metadata."""

    __tablename__ = "predictions"

    id               = Column(Integer,  primary_key=True, autoincrement=True)
    disease          = Column(String(255), nullable=False)
    confidence       = Column(Float,       nullable=False)
    confidence_pct   = Column(String(20),  nullable=False, default="0.00%")
    severity         = Column(String(50),  nullable=False)
    advisory         = Column(Text,        nullable=False)
    is_confident     = Column(Boolean,     nullable=False, default=True)
    is_banana_image  = Column(Boolean,     nullable=False, default=True)
    rejection_reason = Column(Text,        nullable=True)
    latitude         = Column(Float,       nullable=True)
    longitude        = Column(Float,       nullable=True)
    nearest_center   = Column(String(500), nullable=True)
    model_version    = Column(String(20),  nullable=False, default="1.1.0")
    created_at       = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} disease='{self.disease}' "
            f"severity='{self.severity}' confidence={self.confidence:.4f}>"
        )