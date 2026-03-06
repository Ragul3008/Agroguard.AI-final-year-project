"""
schemas/response_schema.py - Production response schemas for AgroGuard-AI.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    """Full production response from POST /predict."""

    # Core prediction
    disease:          str   = Field(..., description="Detected banana disease name.")
    confidence:       float = Field(..., ge=0.0, le=1.0, description="Model confidence [0-1].")
    confidence_pct:   str   = Field(..., description="Confidence as percentage e.g. '94.23%'.")
    severity:         str   = Field(..., description="Severity: Low, Medium, High, or None.")

    # Advisory & location
    advisory:         str   = Field(..., description="ICAR-aligned treatment advisory.")
    nearest_center:   str   = Field(..., description="Nearest banana farming support centre.")

    # Production fields
    is_confident:      bool             = Field(..., description="True if confidence is sufficient.")
    is_banana_image:   bool             = Field(..., description="True if image is a banana plant.")
    rejection_reason:  Optional[str]    = Field(None, description="Reason if prediction rejected.")
    all_probabilities: dict[str, float] = Field(..., description="Probability for all 7 classes.")

    # Metadata
    timestamp:      datetime = Field(..., description="UTC timestamp of prediction.")
    model_version:  str      = Field(default="1.1.0", description="Model version.")

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class HealthResponse(BaseModel):
    """Response from GET /health."""
    status:       str  = Field(default="ok")
    version:      str  = Field(default="1.1.0")
    model_loaded: bool = Field(default=True)

    model_config = {
        "protected_namespaces": ()
    }


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    detail:    str
    code:      Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)