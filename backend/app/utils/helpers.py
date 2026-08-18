"""
utils/helpers.py - General-purpose helper functions for AgroGuard-AI.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def format_confidence(value: float) -> float:
    """Round a confidence score to 4 decimal places."""
    return round(float(value), 4)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp *value* to the range [min_val, max_val]."""
    return max(min_val, min(max_val, value))
