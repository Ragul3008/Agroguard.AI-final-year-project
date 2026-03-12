"""
utils/rate_limiter.py - Rate limiting for AgroGuard-AI using SlowAPI.

Limits:
    /predict        → 10 requests per minute per IP (heavy ML endpoint)
    /auth/register  → 5 requests per minute per IP (prevent spam accounts)
    /auth/login     → 10 requests per minute per IP (prevent brute force)
    /speech/*       → 10 requests per minute per IP
    General API     → 60 requests per minute per IP
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Limiter singleton — keyed by client IP address
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)