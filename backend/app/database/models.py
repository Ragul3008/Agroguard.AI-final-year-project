"""
database/models.py - Production ORM models for AgroGuard-AI.
Includes: Farmer (user) model + Prediction model.
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class AuthProvider(PyEnum):
    """Authentication provider enum."""
    PASSWORD = "password"
    GOOGLE = "google"


class Farmer(Base):
    """
    Farmer user account.
    Stores registration details and authentication credentials.
    """

    __tablename__ = "farmers"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(255), nullable=False)
    phone        = Column(String(20),  nullable=True, unique=True, index=True)
    email        = Column(String(255), nullable=True,  unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for Google-only accounts
    google_id    = Column(String(255), nullable=True, unique=True, index=True)
    auth_provider = Column(Enum(AuthProvider), nullable=False, default=AuthProvider.PASSWORD)
    village      = Column(String(255), nullable=True)
    district     = Column(String(255), nullable=True)
    state        = Column(String(255), nullable=True, default="Tamil Nadu")
    is_active    = Column(Boolean,     nullable=False, default=True)
    created_at   = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship to predictions
    predictions = relationship("Prediction", back_populates="farmer", lazy="select")

    def __repr__(self) -> str:
        return f"<Farmer id={self.id} name='{self.name}' phone='{self.phone}' provider='{self.auth_provider.value}'>"


class PasswordReset(Base):
    """
    Password reset OTP storage.
    Stores hashed OTP with expiry and attempt tracking.
    """

    __tablename__ = "password_resets"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    email        = Column(String(255), nullable=False, index=True)
    otp_hash     = Column(String(255), nullable=False)  # bcrypt hash of the 6-digit OTP
    attempts     = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    expires_at   = Column(DateTime(timezone=True), nullable=False, index=True)
    used         = Column(Boolean, nullable=False, default=False)
    created_at   = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<PasswordReset id={self.id} email='{self.email}' used={self.used}>"


class Prediction(Base):
    """Stores each banana disease prediction with full production metadata."""

    __tablename__ = "predictions"

    id               = Column(Integer,     primary_key=True, autoincrement=True)
    farmer_id        = Column(Integer,     ForeignKey("farmers.id"), nullable=True)
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

    # Relationship to farmer
    farmer = relationship("Farmer", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} disease='{self.disease}' "
            f"severity='{self.severity}' confidence={self.confidence:.4f}>"
        )