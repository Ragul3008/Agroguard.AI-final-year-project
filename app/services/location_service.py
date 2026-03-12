"""
services/location_service.py - Google Maps API location service for AgroGuard-AI.

Architecture:
    Primary  → Google Maps Places API (real nearby agriculture offices)
    Fallback → Hardcoded ICAR centre coordinates (if Maps API fails)

Finds the nearest banana farming / horticulture / agriculture support
centre for the farmer based on their GPS coordinates.
"""

import httpx
from typing import Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Google Maps Places API endpoint
# ---------------------------------------------------------------------------
_PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# Search keywords for agriculture offices near farmer
_SEARCH_KEYWORDS = [
    "horticulture office",
    "agriculture office",
    "krishi vigyan kendra",
    "ICAR",
]

# Search radius in metres (50 km)
_SEARCH_RADIUS = 50000


# ---------------------------------------------------------------------------
# Hardcoded fallback centres
# ---------------------------------------------------------------------------
import math

_FALLBACK_CENTRES: list[dict] = [
    {"name": "ICAR-NRCB (National Research Centre for Banana), Trichy",  "lat": 10.8254, "lng": 78.6856, "type": "ICAR Research Centre"},
    {"name": "Theni District Horticulture Office (Banana Hub)",           "lat": 10.0104, "lng": 77.4770, "type": "State Horticulture Office"},
    {"name": "Trichy District Horticulture Office",                       "lat": 10.7905, "lng": 78.7047, "type": "State Horticulture Office"},
    {"name": "Erode Banana Farmers Support Centre",                       "lat": 11.3410, "lng": 77.7172, "type": "Farmer Support Centre"},
    {"name": "Coimbatore Agriculture and Horticulture Office",            "lat": 11.0168, "lng": 76.9558, "type": "State Agriculture Office"},
    {"name": "Salem District Horticulture Office",                        "lat": 11.6643, "lng": 78.1460, "type": "State Horticulture Office"},
    {"name": "Dindigul District Horticulture Office",                     "lat": 10.3673, "lng": 77.9803, "type": "State Horticulture Office"},
    {"name": "Tirunelveli Horticulture Office",                           "lat":  8.7139, "lng": 77.7567, "type": "State Horticulture Office"},
    {"name": "Madurai District Agriculture Office",                       "lat":  9.9252, "lng": 78.1198, "type": "State Agriculture Office"},
    {"name": "KVK Theni — Banana Crop Advisory Centre",                   "lat":  9.9601, "lng": 77.4794, "type": "Krishi Vigyan Kendra"},
    {"name": "KVK Trichy — ICAR Liaison Office",                          "lat": 10.8050, "lng": 78.6930, "type": "Krishi Vigyan Kendra"},
    {"name": "Davangere Horticulture Department, Karnataka",              "lat": 14.4644, "lng": 75.9218, "type": "State Horticulture Office"},
]


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate great-circle distance in km between two GPS coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class LocationService:
    """
    Google Maps-powered location service.

    Primary:  Google Maps Places API → real nearby agriculture offices
    Fallback: Hardcoded ICAR centres → reliable static fallback
    """

    def get_nearest_centre(
        self,
        latitude:  Optional[float],
        longitude: Optional[float],
    ) -> str:
        """
        Find nearest banana farming support centre using Google Maps API.

        Args:
            latitude:  Farmer's GPS latitude.
            longitude: Farmer's GPS longitude.

        Returns:
            Name and distance of nearest centre.
        """
        if latitude is None or longitude is None:
            logger.info("No GPS coordinates — returning default ICAR-NRCB centre.")
            return (
                "ICAR-NRCB (National Research Centre for Banana), Trichy — "
                "Contact: 0431-2616214 | nrcb@icar.gov.in"
            )

        # Try Google Maps API first
        result = self._get_google_maps_centre(latitude, longitude)
        if result:
            logger.info("Google Maps centre found: %s", result)
            return result

        # Fallback to hardcoded centres
        logger.warning("Google Maps API failed — using fallback centres.")
        return self._get_fallback_centre(latitude, longitude)

    def _get_google_maps_centre(
        self,
        latitude:  float,
        longitude: float,
    ) -> str | None:
        """Query Google Maps Places API for nearby agriculture offices."""
        api_key = settings.GOOGLE_MAPS_API_KEY

        if not api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set — skipping Maps API.")
            return None

        for keyword in _SEARCH_KEYWORDS:
            try:
                params = {
                    "location": f"{latitude},{longitude}",
                    "radius":   _SEARCH_RADIUS,
                    "keyword":  keyword,
                    "key":      api_key,
                }

                response = httpx.get(
                    _PLACES_NEARBY_URL,
                    params=params,
                    timeout=5.0,
                )
                data = response.json()

                if data.get("status") == "OK" and data.get("results"):
                    place    = data["results"][0]
                    name     = place.get("name", "Agriculture Office")
                    vicinity = place.get("vicinity", "")

                    # Calculate distance
                    place_loc = place.get("geometry", {}).get("location", {})
                    place_lat = place_loc.get("lat", latitude)
                    place_lng = place_loc.get("lng", longitude)
                    distance  = _haversine(latitude, longitude, place_lat, place_lng)

                    result = f"{name} — {vicinity} ({distance:.1f} km away)"
                    logger.info("Google Maps found: %s", result)
                    return result

            except Exception as exc:
                logger.error("Google Maps API error for keyword='%s': %s", keyword, exc)
                continue

        return None

    def _get_fallback_centre(self, latitude: float, longitude: float) -> str:
        """Return nearest hardcoded ICAR centre."""
        nearest  = min(
            _FALLBACK_CENTRES,
            key=lambda c: _haversine(latitude, longitude, c["lat"], c["lng"]),
        )
        distance = _haversine(latitude, longitude, nearest["lat"], nearest["lng"])
        result   = f"{nearest['name']} ({nearest['type']}) — {distance:.1f} km away"
        logger.info("Fallback centre: %s", result)
        return result