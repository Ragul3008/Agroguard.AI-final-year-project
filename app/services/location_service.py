"""
services/location_service.py - Location service for AgroGuard-AI (Banana Edition).

Returns the nearest ICAR / Horticulture / Agriculture help centre for banana
farmers based on GPS coordinates.

Centres are focussed on major banana-growing districts of Tamil Nadu and
surrounding states. Replace with a live PostGIS or Google Maps API query
in production.
"""

import math
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mock database of banana-farming support centres
# Focused on key banana cultivation districts in Tamil Nadu & Karnataka.
# ---------------------------------------------------------------------------
_CENTRES: list[dict] = [
    # ── ICAR / National Research Centres ───────────────────────────────────
    {
        "name": "ICAR-NRCB (National Research Centre for Banana), Trichy",
        "lat": 10.8254,
        "lng": 78.6856,
        "type": "ICAR Research Centre",
    },
    # ── Tamil Nadu Horticulture Department offices ─────────────────────────
    {
        "name": "Theni District Horticulture Office (Banana Hub)",
        "lat": 10.0104,
        "lng": 77.4770,
        "type": "State Horticulture Office",
    },
    {
        "name": "Trichy District Horticulture Office",
        "lat": 10.7905,
        "lng": 78.7047,
        "type": "State Horticulture Office",
    },
    {
        "name": "Erode Banana Farmers Support Centre",
        "lat": 11.3410,
        "lng": 77.7172,
        "type": "Farmer Support Centre",
    },
    {
        "name": "Coimbatore Agriculture and Horticulture Office",
        "lat": 11.0168,
        "lng": 76.9558,
        "type": "State Agriculture Office",
    },
    {
        "name": "Salem District Horticulture Office",
        "lat": 11.6643,
        "lng": 78.1460,
        "type": "State Horticulture Office",
    },
    {
        "name": "Dindigul District Horticulture Office",
        "lat": 10.3673,
        "lng": 77.9803,
        "type": "State Horticulture Office",
    },
    {
        "name": "Tirunelveli Horticulture Office",
        "lat": 8.7139,
        "lng": 77.7567,
        "type": "State Horticulture Office",
    },
    {
        "name": "Madurai District Agriculture Office",
        "lat": 9.9252,
        "lng": 78.1198,
        "type": "State Agriculture Office",
    },
    {
        "name": "Vellore District Agriculture Office",
        "lat": 12.9165,
        "lng": 79.1325,
        "type": "State Agriculture Office",
    },
    # ── Krishi Vigyan Kendras (KVKs) ───────────────────────────────────────
    {
        "name": "KVK Theni — Banana Crop Advisory Centre",
        "lat": 9.9601,
        "lng": 77.4794,
        "type": "Krishi Vigyan Kendra",
    },
    {
        "name": "KVK Trichy — ICAR Liaison Office",
        "lat": 10.8050,
        "lng": 78.6930,
        "type": "Krishi Vigyan Kendra",
    },
    # ── Karnataka (Cavendish-growing belt) ────────────────────────────────
    {
        "name": "Davangere Horticulture Department, Karnataka",
        "lat": 14.4644,
        "lng": 75.9218,
        "type": "State Horticulture Office",
    },
]


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate great-circle distance in kilometres between two GPS coordinates."""
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class LocationService:
    """Returns the nearest banana farming support centre for given coordinates."""

    def get_nearest_centre(
        self,
        latitude:  Optional[float],
        longitude: Optional[float],
    ) -> str:
        """
        Find the nearest registered banana farming support centre.

        Args:
            latitude:  User GPS latitude (may be None if not provided).
            longitude: User GPS longitude (may be None if not provided).

        Returns:
            Name of the nearest centre with its type, or a default message
            if no coordinates were supplied.
        """
        if latitude is None or longitude is None:
            logger.info("No GPS coordinates provided — returning default centre.")
            return (
                "ICAR-NRCB (National Research Centre for Banana), Trichy — "
                "Contact: 0431-2616214 | nrcb@icar.gov.in"
            )

        nearest  = min(
            _CENTRES,
            key=lambda c: _haversine(latitude, longitude, c["lat"], c["lng"]),
        )
        distance = _haversine(latitude, longitude, nearest["lat"], nearest["lng"])

        result = f"{nearest['name']} ({nearest['type']}) — {distance:.1f} km away"
        logger.info("Nearest centre: %s", result)
        return result
