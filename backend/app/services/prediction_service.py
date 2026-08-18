"""
services/prediction_service.py - Production prediction orchestrator for AgroGuard-AI.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.model_loader import ModelLoader
from app.models.disease_classifier import DiseaseClassifier
from app.models.severity_estimator import SeverityEstimator
from app.services.advisory_service import AdvisoryService
from app.services.location_service import LocationService
from app.services.guardrail_service import GuardrailService
from app.utils.image_preprocessing import preprocess_image
from app.database.crud import create_prediction, get_farmer_by_id
from app.schemas.response_schema import (
    PredictResponse, Nearbycentre, AdvisoryResponse, AdvisorySection,
    ConfidenceLabel, get_confidence_label
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default GPS values sent by frontend when no GPS available
_DEFAULT_LAT = -90.0
_DEFAULT_LNG = -180.0


def _parse_advisory_to_sections(advisory: str, disease: str, severity: str) -> list[AdvisorySection]:
    """
    Parse advisory text into structured sections for better frontend display.
    """
    sections = []

    # Summary sentence
    summary = f"Your banana plant shows signs of {disease} with {severity.lower()} severity."

    # Default section mapping
    section_map = {
        "📋 IMMEDIATE ACTIONS": ("Immediate Actions", "🚨"),
        "💊 CHEMICAL TREATMENT": ("Chemical Treatment", "💊"),
        "🌿 BIOLOGICAL CONTROL": ("Biological Control", "🌿"),
        "🌱 SOIL & FERTILIZER": ("Soil & Fertilizer", "🌱"),
        "🌦 SEASONAL ADVISORY": ("Seasonal Advisory", "🌦"),
        "🛡 PREVENTIVE MEASURES": ("Preventive Measures", "🛡"),
        "📅 MONITORING": ("Monitoring", "📅"),
    }

    if advisory:
        # Split advisory into lines
        lines = advisory.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line is a section header
            found_header = False
            for header, (title, icon) in section_map.items():
                if line.startswith(header):
                    # Save previous section
                    if current_section and current_content:
                        sections.append(AdvisorySection(
                            title=current_section,
                            content="\n".join(current_content),
                            icon=section_map.get(current_section, ("", ""))[1]
                        ))
                    current_section = title
                    current_content = [line.replace(header, "").strip()]
                    found_header = True
                    break

            if not found_header and current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections.append(AdvisorySection(
                title=current_section,
                content="\n".join(current_content),
                icon=section_map.get(current_section, ("", ""))[1]
            ))

    # If no sections parsed, create a single section with full advisory
    if not sections and advisory:
        sections.append(AdvisorySection(
            title="Treatment Advisory",
            content=advisory,
            icon="📋"
        ))

    return sections


def _build_advisory_response(advisory: str, disease: str, severity: str) -> AdvisoryResponse:
    """Build structured advisory response."""
    sections = _parse_advisory_to_sections(advisory, disease, severity)
    summary = f"Your banana plant shows signs of {disease} with {severity.lower()} severity."
    return AdvisoryResponse(
        summary=summary,
        sections=sections,
        full_text=advisory
    )


class PredictionService:
    """Production prediction service — full pipeline with farmer tracking."""

    def __init__(self) -> None:
        loader = ModelLoader.get_instance()
        self._classifier         = DiseaseClassifier(model_loader=loader)
        self._severity_estimator = SeverityEstimator()
        self._advisory_service   = AdvisoryService()
        self._location_service   = LocationService()
        self._guardrail_service  = GuardrailService()

    async def predict(
        self,
        image_bytes:  bytes,
        content_type: str,
        latitude:     Optional[float],
        longitude:    Optional[float],
        db:           AsyncSession,
        farmer_id:    Optional[int] = None,
        language:     str           = "english",
    ) -> PredictResponse:
        """Full production prediction pipeline."""
        logger.info(
            "── Prediction Pipeline START (farmer_id=%s language=%s) ──",
            farmer_id, language,
        )

        # ── Fix GPS: treat default values as no GPS ───────────────────────────
        if latitude == _DEFAULT_LAT and longitude == _DEFAULT_LNG:
            logger.info("Default GPS values received — treating as no GPS")
            latitude  = None
            longitude = None

        # ── Step 1: Validate file type and size ───────────────────────────────
        self._guardrail_service.validate_image(content_type, len(image_bytes))
        logger.info("Step 1 ✓ Image type and size validated")

        # ── Step 1b: Validate magic bytes and dimensions ─────────────────────
        self._guardrail_service.validate_image_bytes(image_bytes, content_type)
        logger.info("Step 1b ✓ Magic bytes and dimensions validated")

        # ── Step 2: Validate plant/leaf content ───────────────────────────────
        # This rejects non-plant images (animals, people, objects etc.)
        self._guardrail_service.validate_plant_image(image_bytes)
        logger.info("Step 2 ✓ Plant/leaf content validated")

        # ── Step 3: Preprocess image ──────────────────────────────────────────
        tensor = preprocess_image(image_bytes)
        logger.info("Step 3 ✓ Preprocessed → %s", tuple(tensor.shape))

        # ── Step 4: Classify disease ──────────────────────────────────────────
        result = self._classifier.predict(tensor)
        logger.info(
            "Step 4 ✓ Disease='%s' Confidence=%.4f is_confident=%s is_banana=%s",
            result.disease_name, result.confidence,
            result.is_confident, result.is_banana_image,
        )

        # ── Step 5: Estimate severity ─────────────────────────────────────────
        severity = (
            self._severity_estimator.estimate(result.disease_name, result.confidence)
            if result.is_banana_image else "Unknown"
        )
        logger.info("Step 5 ✓ Severity=%s", severity)

        # ── Step 6: Generate advisory ─────────────────────────────────────────
        if result.is_confident and result.is_banana_image:
            advisory_text = self._advisory_service.get_advisory(
                disease_name = result.disease_name,
                severity     = severity,
                language     = language,
            )
            logger.info(
                "Step 6 ✓ Advisory generated (%d chars) language='%s'",
                len(advisory_text), language,
            )
        else:
            advisory_text = (
                result.rejection_reason
                or "This image does not appear to be a banana plant. "
                   "Please upload a clear photo of a banana leaf, stem or fruit."
            )
            logger.info("Step 6 ✓ Advisory skipped — not confident or not banana")

        # Build structured advisory response
        advisory_response = _build_advisory_response(advisory_text, result.disease_name, severity)

        # Confidence label
        confidence_label = get_confidence_label(result.confidence)

        # ── Step 7: Find nearby centres using GPS ─────────────────────────────
        resolved_lat = latitude
        resolved_lng = longitude

        if (resolved_lat is None or resolved_lat <= -90.0 or
            resolved_lng is None or resolved_lng <= -180.0):
            if db and farmer_id:
                farmer = await get_farmer_by_id(db, farmer_id)
                if farmer:
                    loc_parts = [farmer.village, farmer.district, farmer.state]
                    loc_query = ", ".join(p for p in loc_parts if p)
                    if loc_query:
                        logger.info("Resolving prediction location via farmer profile '%s'...", loc_query)
                        coords = await self._location_service.geocode_address(loc_query)
                        if coords:
                            resolved_lat, resolved_lng = coords
                            logger.info("Prediction location resolved to lat=%.4f, lng=%.4f", resolved_lat, resolved_lng)

            if resolved_lat is None or resolved_lat <= -90.0 or resolved_lng is None or resolved_lng <= -180.0:
                logger.info("Location un-geocoded, defaulting prediction location to Chidambaram (11.3995, 79.6909)")
                resolved_lat = 11.3995
                resolved_lng = 79.6909

        nearby_centres_data = await self._location_service.get_all_nearby_centres(
            latitude    = resolved_lat,
            longitude   = resolved_lng,
            max_results = 5,
        )
        logger.info("Step 7 ✓ Found %d nearby centres for lat=%.4f lng=%.4f", len(nearby_centres_data), resolved_lat, resolved_lng)

        # Convert to schema objects
        nearby_centres = [
            Nearbycentre(
                name     = c.get("name",     ""),
                address  = c.get("address",  ""),
                distance = c.get("distance", ""),
                phone    = c.get("phone",    ""),
                type     = c.get("type",     ""),
                summary  = c.get("summary",  ""),
            )
            for c in nearby_centres_data
        ]

        nearest_center = (
            nearby_centres[0].summary
            if nearby_centres
            else "Agricultural Extension Centre (AEC) - Chidambaram (0.3 km away) | 04144-222270"
        )

        confidence_pct = f"{result.confidence * 100:.2f}%"

        # ── Step 8: Save to database ──────────────────────────────────────────
        await create_prediction(
            db               = db,
            farmer_id        = farmer_id,
            disease          = result.disease_name,
            confidence       = result.confidence,
            confidence_pct   = confidence_pct,
            severity         = severity,
            advisory         = advisory_text,
            is_confident     = result.is_confident,
            is_banana_image  = result.is_banana_image,
            rejection_reason = result.rejection_reason,
            latitude         = latitude,
            longitude        = longitude,
            nearest_center   = nearest_center,
        )
        logger.info("Step 8 ✓ Saved to database")

        # ── Step 9: Return response ───────────────────────────────────────────
        response = PredictResponse(
            disease           = result.disease_name,
            disease_display   = result.disease_name,  # Could be localized later
            confidence        = result.confidence,
            confidence_pct    = confidence_pct,
            confidence_label  = confidence_label,
            severity          = severity,
            advisory          = advisory_response,
            advisory_legacy   = advisory_text,
            nearest_center    = nearest_center,
            nearby_centres    = nearby_centres,
            is_confident      = result.is_confident,
            is_banana_image   = result.is_banana_image,
            rejection_reason  = result.rejection_reason,
            all_probabilities = result.all_probabilities,
            timestamp         = datetime.now(timezone.utc),
            model_version     = "3.0.0",
            language          = language,
            inference_latency_ms = None,  # TODO: add timing
        )

        logger.info(
            "── Pipeline COMPLETE → %s | %s | %s | lang=%s ──",
            result.disease_name, severity, confidence_pct, language,
        )
        return response