"""
database/models.py - SQLAlchemy ORM models for AgroGuard-AI (Banana Edition).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


class Prediction(Base):
    """
    Stores each banana disease prediction result.

    Table: predictions
    """

    __tablename__ = "predictions"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    disease     = Column(String(255), nullable=False, comment="Detected banana disease name")
    confidence  = Column(Float,       nullable=False, comment="Model confidence score [0,1]")
    severity    = Column(String(50),  nullable=False, comment="Low / Medium / High / None")
    advisory    = Column(String(4000), nullable=False, comment="ICAR-aligned treatment advisory")
    latitude    = Column(Float,       nullable=True,  comment="GPS latitude of farm")
    longitude   = Column(Float,       nullable=True,  comment="GPS longitude of farm")
    created_at  = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp of prediction",
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} "
            f"disease='{self.disease}' "
            f"severity='{self.severity}' "
            f"confidence={self.confidence:.4f}>"
        )
