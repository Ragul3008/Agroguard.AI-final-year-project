"""
models/severity_estimator.py - Banana disease severity estimation.

Severity is derived from model confidence and disease type.

Rules:
    ┌──────────────────────────────┬───────────────────────────────────┐
    │ Condition                    │ Severity                          │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ Healthy plant                │ None                              │
    │ Panama Disease (any conf.)   │ Always High (incurable, urgent)   │
    │ Bunchy Top Virus (any conf.) │ Always High (no cure)             │
    │ confidence >= 0.85           │ High                              │
    │ confidence >= 0.60           │ Medium                            │
    │ confidence < 0.60            │ Low                               │
    └──────────────────────────────┴───────────────────────────────────┘
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)

_HIGH_THRESHOLD   = 0.85
_MEDIUM_THRESHOLD = 0.60

# Diseases that are always critical regardless of confidence score
_ALWAYS_HIGH: list[str] = ["panama", "bunchy top virus", "bbtv"]


class SeverityEstimator:
    """Estimates severity level for a detected banana disease."""

    def estimate(self, disease_name: str, confidence: float) -> str:
        """
        Determine severity level.

        Args:
            disease_name: Human-readable disease label from DiseaseClassifier.
            confidence:   Model confidence in [0, 1].

        Returns:
            One of "Low", "Medium", "High", or "None" (healthy plant).
        """
        disease_lower = disease_name.lower()

        # Healthy plant — no severity
        if "healthy" in disease_lower:
            logger.info("Banana plant is healthy — no severity assigned.")
            return "None"

        # Incurable diseases — always critical
        if any(keyword in disease_lower for keyword in _ALWAYS_HIGH):
            logger.info(
                "Disease '%s' is always treated as High severity.", disease_name
            )
            return "High"

        # Confidence-based thresholds
        if confidence >= _HIGH_THRESHOLD:
            severity = "High"
        elif confidence >= _MEDIUM_THRESHOLD:
            severity = "Medium"
        else:
            severity = "Low"

        logger.info(
            "Severity estimated → %s (disease='%s', confidence=%.4f)",
            severity,
            disease_name,
            confidence,
        )
        return severity
