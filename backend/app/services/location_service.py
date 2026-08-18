"""
services/location_service.py - Hybrid GPS Location Service for AgroGuard-AI.

Multi-layer architecture:
1. Primary Source: Verified curated database of 104+ block & village level extension offices (AEC/ADA),
   Horticulture depots, KVKs, ICAR institutes, and agricultural universities (e.g. Chidambaram, Panruti, Cuddalore).
2. Secondary Source 1: Geoapify Places API v2 + Geoapify Live Geocoding API.
3. Secondary Source 2 (Backup): Google Places Text Search API (New).

Combines verified local offices with live API POI discoveries, deduplicates,
calculates Haversine distance, and returns live Google Maps directions coordinates.
"""

import asyncio
import json
import math
import time
from pathlib import Path
from typing import Optional
import httpx
from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# Constants & API Endpoints
# ─────────────────────────────────────────────────────────────────────────────
_MAX_RESULTS     = 5
_MAX_DISTANCE_KM = 75.0   # initial radius preference
_REQUEST_TIMEOUT = 10.0   # seconds for API requests

# Geoapify API Endpoints
_GEOAPIFY_PLACES_URL  = "https://api.geoapify.com/v2/places"
_GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
_GEOAPIFY_FETCH_LIMIT = 50
_GEOAPIFY_RADIUS_STEPS = [25_000, 50_000, 75_000]

_GEOAPIFY_CATEGORIES = ",".join([
    "office.government",
    "office.research",
    "office",
    "education.university",
    "education.college",
])

# Google Places Text Search API (New)
_GOOGLE_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
_GOOGLE_SEARCH_RADIUS = 50000
_GOOGLE_SEARCH_QUERIES = [
    "Agricultural Extension Centre",
    "Agriculture office",
    "Horticulture office",
    "Krishi Vigyan Kendra",
]

# Agriculture validation keywords for live API results
_AGRI_KEYWORDS = [
    "agricultur", "horticultur", "icar", "kvk", "krishi vigyan",
    "krishi", "agri", "farming", "farm", "kissan", "kisan",
    "plant protection", "soil", "crop", "tnau", "angrau",
    "uhas", "kau ", "jnkvv", "seed", "fertiliz", "extension",
    "ada office", "depot", "vivasaya", "virivakka", "paccs",
    "raitha", "rythu", "rsk", "rbk", "block agricultural",
    "district agricultural", "horticultural", "faculty",
]

# ─────────────────────────────────────────────────────────────────────────────
# Load curated agriculture centres database
# ─────────────────────────────────────────────────────────────────────────────
_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "agriculture_centres.json"
_CURATED_CENTRES: list[dict] = []

try:
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        _CURATED_CENTRES = json.load(f)
    logger.info(
        "Loaded %d curated agriculture centres from %s",
        len(_CURATED_CENTRES), _DATA_FILE.name,
    )
except FileNotFoundError:
    logger.error("Agriculture centres database not found: %s", _DATA_FILE)
except json.JSONDecodeError as exc:
    logger.error("Failed to parse agriculture centres database: %s", exc)

# ─────────────────────────────────────────────────────────────────────────────
# Cache: 7-day TTL, keyed by rounded lat/lng (~100m precision)
# ─────────────────────────────────────────────────────────────────────────────
_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
_CACHE_PRECISION = 3
_geo_cache: dict[str, tuple[float, list[dict]]] = {}


def _cache_key(lat: float, lng: float) -> str:
    return f"{round(lat, _CACHE_PRECISION)},{round(lng, _CACHE_PRECISION)}"


def _get_cached(lat: float, lng: float) -> list[dict] | None:
    key = _cache_key(lat, lng)
    if key in _geo_cache:
        timestamp, results = _geo_cache[key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            logger.debug("Location cache hit for %s", key)
            return results
        else:
            del _geo_cache[key]
    return None


def _set_cached(lat: float, lng: float, results: list[dict]) -> None:
    key = _cache_key(lat, lng)
    _geo_cache[key] = (time.time(), results)
    logger.debug("Location cache set for %s (%d results)", key, len(results))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R    = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    a    = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
            + math.cos(phi1) * math.cos(phi2)
            * math.sin(math.radians(lng2 - lng1) / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _format_centre(
    name: str, address: str, distance: float,
    phone: str = "", centre_type: str = "",
    lat: Optional[float] = None, lon: Optional[float] = None,
) -> dict:
    return {
        "name":      name,
        "address":   address,
        "distance":  f"{distance:.1f} km",
        "phone":     phone,
        "type":      centre_type,
        "latitude":  lat,
        "longitude": lon,
        "summary":   (
            f"{name} — {address} ({distance:.1f} km away)"
            + (f" | {phone}" if phone else "")
        ),
    }


def _search_curated_database(
    latitude: float, longitude: float, max_distance: float = _MAX_DISTANCE_KM,
) -> list[dict]:
    """Search the curated database for centres, sorted by distance."""
    all_results = []
    for centre in _CURATED_CENTRES:
        dist = _haversine(latitude, longitude, centre["lat"], centre["lon"])
        all_results.append(_format_centre(
            name        = centre["name"],
            address     = centre["address"],
            distance    = dist,
            phone       = centre.get("phone", ""),
            centre_type = centre.get("type", "Agriculture Centre"),
            lat         = centre["lat"],
            lon         = centre["lon"],
        ))
    all_results.sort(key=lambda c: float(c["distance"].replace(" km", "")))
    
    within_radius = [c for c in all_results if float(c["distance"].replace(" km", "")) <= max_distance]
    return within_radius if within_radius else all_results[:5]


def _is_agriculture_related(name: str, address: str) -> bool:
    text = (name + " " + address).lower()
    return any(kw in text for kw in _AGRI_KEYWORDS)


def _classify_centre_type(categories: list[str], name: str) -> str:
    name_lower = name.lower()
    if "university" in name_lower or any("university" in c for c in categories):
        return "Agricultural University"
    if "kvk" in name_lower or "krishi vigyan" in name_lower:
        return "Krishi Vigyan Kendra (KVK)"
    if "icar" in name_lower or "research" in name_lower:
        return "Research Institute"
    if "horticultur" in name_lower:
        return "Horticulture Office"
    if "extension" in name_lower or "ada office" in name_lower or "aec" in name_lower:
        return "Block Agricultural Office (ADA)"
    if "agricultur" in name_lower:
        return "Agriculture Office"
    return "Agriculture Centre"


def _parse_geoapify_feature(feature: dict, user_lat: float, user_lon: float) -> dict | None:
    """Parse a Geoapify feature; return None if not agriculture-related."""
    props = feature.get("properties", {})
    name  = props.get("name", "").strip()
    if not name:
        return None

    place_lat = props.get("lat", user_lat)
    place_lon = props.get("lon", user_lon)
    dist_km   = _haversine(user_lat, user_lon, place_lat, place_lon)

    addr_parts = [
        props.get("address_line2", ""),
        props.get("district", ""),
        props.get("city", props.get("county", "")),
        props.get("state", ""),
        props.get("postcode", ""),
    ]
    address = ", ".join(p for p in addr_parts if p) or props.get("formatted", "")

    if not _is_agriculture_related(name, address):
        return None

    raw   = props.get("datasource", {}).get("raw", {})
    phone = raw.get("phone", raw.get("contact:phone", ""))
    cats  = props.get("categories", [])
    ctype = _classify_centre_type(cats, name)

    return _format_centre(
        name        = name,
        address     = address,
        distance    = dist_km,
        phone       = str(phone) if phone else "",
        centre_type = ctype,
        lat         = place_lat,
        lon         = place_lon,
    )


def _parse_google_place(place: dict, user_lat: float, user_lon: float) -> dict | None:
    """Parse a Google Places result; return None if not agriculture-related."""
    name = (place.get("displayName", {}).get("text", "")
            or place.get("name", "")).strip()
    if not name:
        return None

    location = place.get("location", {})
    place_lat = location.get("latitude", user_lat)
    place_lon = location.get("longitude", user_lon)
    dist_km = _haversine(user_lat, user_lon, place_lat, place_lon)

    address = place.get("formattedAddress", "")
    if not _is_agriculture_related(name, address):
        return None

    phone = place.get("internationalPhoneNumber",
                      place.get("nationalPhoneNumber", ""))
    types = place.get("types", [])
    centre_type = _classify_centre_type(types, name)

    return _format_centre(
        name=name, address=address, distance=dist_km,
        phone=str(phone) if phone else "", centre_type=centre_type,
        lat=place_lat, lon=place_lon,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Location Service
# ─────────────────────────────────────────────────────────────────────────────
class LocationService:
    """
    Hybrid multi-source location service for AgroGuard-AI:
    - Primary: Verified curated database of 104+ block & village extension offices
    - Secondary 1: Geoapify Places API v2 + Geocoding API
    - Secondary 2 (Backup): Google Places Text Search API (New)
    """

    async def geocode_address(self, address: str) -> tuple[float, float] | None:
        """Geocode an address string (e.g. 'Chidambaram, Cuddalore, Tamil Nadu') to (lat, lng)."""
        api_key = settings.GEOAPIFY_API_KEY
        if not api_key or not address.strip():
            return None
        params = {"text": address, "apiKey": api_key, "limit": 1, "format": "json"}
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                resp = await client.get(_GEOAPIFY_GEOCODE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if results:
                    lat = results[0].get("lat")
                    lon = results[0].get("lon")
                    if lat is not None and lon is not None:
                        return float(lat), float(lon)
        except Exception as exc:
            logger.debug("Geocoding failed for '%s': %s", address, exc)
        return None

    async def get_nearest_centre(
        self,
        latitude:  Optional[float],
        longitude: Optional[float],
    ) -> str:
        centres = await self.get_all_nearby_centres(latitude, longitude)
        return centres[0]["summary"] if centres else "No nearby agriculture center found."

    async def get_all_nearby_centres(
        self,
        latitude:    Optional[float],
        longitude:   Optional[float],
        max_results: int = _MAX_RESULTS,
    ) -> list[dict]:
        """
        Return nearby agriculture centres combining curated verified database
        with live Geoapify and Google Places API discoveries.
        """
        if latitude is None or longitude is None:
            return []

        # Check in-memory cache first
        cached = _get_cached(latitude, longitude)
        if cached:
            logger.info(
                "Returning %d cached agriculture centres for (%.4f, %.4f)",
                len(cached[:max_results]), latitude, longitude,
            )
            return cached[:max_results]

        logger.info(
            "Searching nearby agriculture centres for lat=%.4f, lng=%.4f...",
            latitude, longitude,
        )

        # ── Step 1: Search verified curated database ──
        curated = _search_curated_database(latitude, longitude)

        # ── Step 2: Query live APIs concurrently ──
        geoapify_key = settings.GEOAPIFY_API_KEY
        google_key   = settings.GOOGLE_MAPS_API_KEY

        geo_task    = self._geoapify_places_search(latitude, longitude, geoapify_key) if geoapify_key else asyncio.sleep(0, result=[])
        google_task = self._google_places_search(latitude, longitude, google_key) if google_key else asyncio.sleep(0, result=[])

        geoapify_results, google_results = await asyncio.gather(geo_task, google_task, return_exceptions=True)

        if isinstance(geoapify_results, Exception):
            logger.debug("Geoapify live search error: %s", geoapify_results)
            geoapify_results = []

        if isinstance(google_results, Exception):
            logger.debug("Google Places live search error: %s", google_results)
            google_results = []

        # ── Step 3: Merge + Deduplicate (Curated verified first, then APIs) ──
        seen_names: set[str] = set()
        merged: list[dict] = []

        for c in curated + geoapify_results + google_results:
            norm = c["name"].strip().lower()
            if norm not in seen_names:
                seen_names.add(norm)
                merged.append(c)

        # Sort by distance (nearest first)
        merged.sort(key=lambda c: float(c["distance"].replace(" km", "")))

        final = merged[:max(max_results, 10)]
        _set_cached(latitude, longitude, final)

        logger.info(
            "Returning %d nearby agriculture centres for (%.4f, %.4f)",
            len(final[:max_results]), latitude, longitude,
        )
        return final[:max_results]

    # ── Geoapify Places API Live Search ───────────────────────────────────────

    async def _geoapify_places_search(
        self,
        latitude:  float,
        longitude: float,
        api_key:   str,
    ) -> list[dict]:
        """Call Geoapify Places API v2 across expanding radius steps."""
        seen: set[str] = set()
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            for radius in _GEOAPIFY_RADIUS_STEPS:
                params = {
                    "categories": _GEOAPIFY_CATEGORIES,
                    "filter":     f"circle:{longitude},{latitude},{radius}",
                    "bias":       f"proximity:{longitude},{latitude}",
                    "limit":      _GEOAPIFY_FETCH_LIMIT,
                    "apiKey":     api_key,
                }

                try:
                    resp = await client.get(_GEOAPIFY_PLACES_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    features = data.get("features", [])
                    for feature in features:
                        centre = _parse_geoapify_feature(feature, latitude, longitude)
                        if centre and centre["name"].lower() not in seen:
                            seen.add(centre["name"].lower())
                            results.append(centre)
                except Exception as exc:
                    logger.debug("Geoapify Places API error at radius %dm: %s", radius, exc)
                    break

        return results

    # ── Google Places Text Search API (New) Live Search ──────────────────────

    async def _google_places_search(
        self,
        latitude:  float,
        longitude: float,
        api_key:   str,
    ) -> list[dict]:
        """Call Google Places Text Search API (New) for queries live."""
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.displayName,"
                "places.formattedAddress,"
                "places.location,"
                "places.internationalPhoneNumber,"
                "places.nationalPhoneNumber,"
                "places.types"
            ),
        }

        results = []
        seen: set[str] = set()

        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            for query in _GOOGLE_SEARCH_QUERIES:
                body = {
                    "textQuery": query,
                    "locationBias": {
                        "circle": {
                            "center": {"latitude": latitude, "longitude": longitude},
                            "radius": _GOOGLE_SEARCH_RADIUS,
                        }
                    },
                    "languageCode": "en",
                    "maxResultCount": 10,
                }

                try:
                    resp = await client.post(_GOOGLE_PLACES_URL, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()

                    places = data.get("places", [])
                    for place in places:
                        centre = _parse_google_place(place, latitude, longitude)
                        if centre and centre["name"].lower() not in seen:
                            seen.add(centre["name"].lower())
                            results.append(centre)
                except Exception as exc:
                    logger.debug("Google Places API error for '%s': %s", query, exc)
                    continue

        return results