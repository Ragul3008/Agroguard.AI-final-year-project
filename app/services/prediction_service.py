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
from app.database.crud import create_prediction
from app.schemas.response_schema import PredictResponse, Nearbycentre
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default GPS values sent by frontend when no GPS available
_DEFAULT_LAT = -90.0
_DEFAULT_LNG = -180.0


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
            advisory = self._advisory_service.get_advisory(
                disease_name = result.disease_name,
                severity     = severity,
                language     = language,
            )
            logger.info(
                "Step 6 ✓ Advisory generated (%d chars) language='%s'",
                len(advisory), language,
            )
        else:
            advisory = (
                result.rejection_reason
                or "This image does not appear to be a banana plant. "
                   "Please upload a clear photo of a banana leaf, stem or fruit."
            )
            logger.info("Step 6 ✓ Advisory skipped — not confident or not banana")

        # ── Step 7: Find nearby centres using GPS ─────────────────────────────
        nearby_centres_data = self._location_service.get_all_nearby_centres(
            latitude    = latitude,
            longitude   = longitude,
            max_results = 5,
        )
        logger.info("Step 7 ✓ Found %d nearby centres", len(nearby_centres_data))

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
            else "ICAR-NRCB, Trichy — 0431-2616214"
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
            advisory         = advisory,
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
            confidence        = result.confidence,
            confidence_pct    = confidence_pct,
            severity          = severity,
            advisory          = advisory,
            nearest_center    = nearest_center,
            nearby_centres    = nearby_centres,
            is_confident      = result.is_confident,
            is_banana_image   = result.is_banana_image,
            rejection_reason  = result.rejection_reason,
            all_probabilities = result.all_probabilities,
            timestamp         = datetime.now(timezone.utc),
            model_version     = "3.0.0",
            language          = language,
        )

        logger.info(
            "── Pipeline COMPLETE → %s | %s | %s | lang=%s ──",
            result.disease_name, severity, confidence_pct, language,
        )
        return response