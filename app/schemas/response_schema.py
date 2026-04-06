"""
schemas/response_schema.py - Production response schemas for AgroGuard-AI.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Nearby Centre Schema
# ─────────────────────────────────────────────────────────────────────────────
class Nearbycentre(BaseModel):
    """Single nearby horticulture or agriculture office."""

    name:     str = Field(..., description="Name of the office or centre.")
    address:  str = Field(..., description="Full address of the centre.")
    distance: str = Field(..., description="Distance from farmer e.g. '12.4 km'.")
    phone:    str = Field(default="", description="Contact phone number.")
    type:     str = Field(default="", description="Type: ICAR / Horticulture / KVK etc.")
    summary:  str = Field(..., description="One-line summary with name, address, distance.")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Main Predict Response
# ─────────────────────────────────────────────────────────────────────────────
class PredictResponse(BaseModel):
    """Full production response from POST /predict."""

    # ── Core prediction ───────────────────────────────────────────────────────
    disease:        str   = Field(..., description="Detected banana disease name.")
    confidence:     float = Field(..., ge=0.0, le=1.0, description="Model confidence [0-1].")
    confidence_pct: str   = Field(..., description="Confidence as percentage e.g. '99.78%'.")
    severity:       str   = Field(..., description="Severity: Low, Medium, High, or None.")

    # ── Advisory ─────────────────────────────────────────────────────────────
    advisory: str = Field(..., description="ICAR-aligned bullet-point treatment advisory.")

    # ── Location — full list of nearby centres ────────────────────────────────
    nearest_center:  str                  = Field(
        ...,
        description="Nearest centre as string — backward compatible.",
    )
    nearby_centres:  list[Nearbycentre]   = Field(
        default_factory=list,
        description="All nearby horticulture and agriculture offices sorted by distance.",
    )

    # ── Production flags ─────────────────────────────────────────────────────
    is_confident:     bool             = Field(..., description="True if confidence >= threshold.")
    is_banana_image:  bool             = Field(..., description="True if image is a banana plant.")
    rejection_reason: Optional[str]    = Field(None, description="Reason if prediction rejected.")
    all_probabilities:dict[str, float] = Field(..., description="Probability for all 7 classes.")

    # ── Metadata ─────────────────────────────────────────────────────────────
    timestamp:     datetime = Field(..., description="UTC timestamp of prediction.")
    model_version: str      = Field(default="2.0.0", description="Model version.")
    language:      str      = Field(default="english", description="Advisory language used.")

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Health Response
# ─────────────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Response from GET /health."""
    status:       str  = Field(default="ok")
    version:      str  = Field(default="2.0.0")
    model_loaded: bool = Field(default=True)

    model_config = {"protected_namespaces": ()}


# ─────────────────────────────────────────────────────────────────────────────
# Error Response
# ─────────────────────────────────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    """Standard error envelope."""
    detail:    str
    code:      Optional[int] = None
    timestamp: datetime      = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Nearby Centres Response (for GET /nearby-centres endpoint)
# ─────────────────────────────────────────────────────────────────────────────
class NearbyCentresResponse(BaseModel):
    """Response from GET /nearby-centres."""
    latitude:    float              = Field(..., description="Farmer GPS latitude.")
    longitude:   float              = Field(..., description="Farmer GPS longitude.")
    total_found: int                = Field(..., description="Total centres found.")
    centres:     list[Nearbycentre] = Field(..., description="List of nearby centres.")