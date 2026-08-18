"""
schemas/response_schema.py - Production response schemas for AgroGuard-AI.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Advisory Section Schema
# ─────────────────────────────────────────────────────────────────────────────
class AdvisorySection(BaseModel):
    """Structured advisory section with title and content."""

    title:   str = Field(..., description="Section title (e.g., 'Immediate Actions').")
    content: str = Field(..., description="Section content as markdown or plain text.")
    icon:    Optional[str] = Field(None, description="Optional emoji icon for the section.")


class AdvisoryResponse(BaseModel):
    """Structured advisory response broken into sections."""

    summary:     str = Field(..., description="One-sentence plain-language summary.")
    sections:    list[AdvisorySection] = Field(default_factory=list, description="Advisory sections.")
    full_text:   str = Field(..., description="Complete advisory text for TTS/accessibility.")


# ─────────────────────────────────────────────────────────────────────────────
# Confidence Label
# ─────────────────────────────────────────────────────────────────────────────
class ConfidenceLabel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


def get_confidence_label(confidence: float) -> ConfidenceLabel:
    """Convert numeric confidence to human-readable label."""
    if confidence >= 0.9:
        return ConfidenceLabel.HIGH
    elif confidence >= 0.75:
        return ConfidenceLabel.MEDIUM
    elif confidence >= 0.5:
        return ConfidenceLabel.LOW
    else:
        return ConfidenceLabel.VERY_LOW


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
    disease:            str          = Field(..., description="Detected banana disease name.")
    disease_display:    Optional[str] = Field(None, description="Localized display name for the disease.")
    confidence:         float        = Field(..., ge=0.0, le=1.0, description="Model confidence [0-1].")
    confidence_pct:     str          = Field(..., description="Confidence as percentage e.g. '99.78%'.")
    confidence_label:   ConfidenceLabel = Field(..., description="Human-readable confidence label.")
    severity:           str          = Field(..., description="Severity: Low, Medium, High, or None.")

    # ── Advisory ─────────────────────────────────────────────────────────────
    advisory:           AdvisoryResponse = Field(..., description="Structured advisory with sections.")
    advisory_legacy:    str          = Field(..., description="Full advisory text for backward compatibility.")

    # ── Location — full list of nearby centres ────────────────────────────────
    nearest_center:     str                  = Field(
        ...,
        description="Nearest centre as string — backward compatible.",
    )
    nearby_centres:     list[Nearbycentre]   = Field(
        default_factory=list,
        description="All nearby horticulture and agriculture offices sorted by distance.",
    )

    # ── Production flags ─────────────────────────────────────────────────────
    is_confident:       bool             = Field(..., description="True if confidence >= threshold.")
    is_banana_image:    bool             = Field(..., description="True if image is a banana plant.")
    rejection_reason:   Optional[str]    = Field(None, description="Reason if prediction rejected.")
    all_probabilities:  dict[str, float] = Field(..., description="Probability for all 7 classes.")

    # ── Metadata ─────────────────────────────────────────────────────────────
    timestamp:          datetime       = Field(..., description="UTC timestamp of prediction.")
    model_version:      str            = Field(default="3.0.0", description="Model version.")
    language:           str            = Field(default="english", description="Advisory language used.")
    inference_latency_ms: Optional[int] = Field(None, description="Model inference latency in milliseconds.")

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
        "use_enum_values": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Health Response
# ─────────────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Response from GET /health."""
    status:         str  = Field(default="ok")  # ok, degraded, down
    version:        str  = Field(default="2.0.0")
    model_loaded:   bool = Field(default=False)
    database:       str  = Field(default="unknown")  # connected, disconnected

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