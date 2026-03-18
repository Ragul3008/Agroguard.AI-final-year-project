"""
services/prediction_service.py - Production prediction orchestrator with JWT farmer tracking.
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
from app.schemas.response_schema import PredictResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PredictionService:
    """Production prediction service — full 8-step pipeline with farmer tracking."""

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
        """Full production prediction pipeline with farmer tracking and language support."""
        logger.info(
            "── Prediction Pipeline START (farmer_id=%s, language=%s) ──",
            farmer_id, language,
        )

        # Step 1: Validate image
        self._guardrail_service.validate_image(content_type, len(image_bytes))
        logger.info("Step 1 ✓ Image validated")

        # Step 2: Preprocess image
        tensor = preprocess_image(image_bytes)
        logger.info("Step 2 ✓ Preprocessed → %s", tuple(tensor.shape))

        # Step 3: Classify disease
        result = self._classifier.predict(tensor)
        logger.info(
            "Step 3 ✓ Disease='%s' Confidence=%.4f is_confident=%s is_banana=%s",
            result.disease_name, result.confidence,
            result.is_confident, result.is_banana_image,
        )

        # Step 4: Estimate severity
        severity = (
            self._severity_estimator.estimate(result.disease_name, result.confidence)
            if result.is_banana_image else "Unknown"
        )
        logger.info("Step 4 ✓ Severity=%s", severity)

        # Step 5: Generate advisory (Gemini LLM) in requested language
        if result.is_confident:
            advisory = self._advisory_service.get_advisory(
                disease_name=result.disease_name,
                severity=severity,
                language=language,
            )
            logger.info(
                "Step 5 ✓ Advisory generated (%d chars) in language='%s'",
                len(advisory), language,
            )
        else:
            advisory = result.rejection_reason or "Please upload a clearer image."
            logger.info("Step 5 ✓ Advisory skipped — low confidence")

        # Step 6: Find nearest horticulture centre
        nearest_center = self._location_service.get_nearest_centre(latitude, longitude)
        logger.info("Step 6 ✓ Nearest centre: %s", nearest_center)

        confidence_pct = f"{result.confidence * 100:.2f}%"

        # Step 7: Persist to DB with farmer_id and language
        await create_prediction(
            db=db,
            farmer_id=farmer_id,
            disease=result.disease_name,
            confidence=result.confidence,
            confidence_pct=confidence_pct,
            severity=severity,
            advisory=advisory,
            is_confident=result.is_confident,
            is_banana_image=result.is_banana_image,
            rejection_reason=result.rejection_reason,
            latitude=latitude,
            longitude=longitude,
            nearest_center=nearest_center,
        )
        logger.info("Step 7 ✓ Saved to database")

        # Step 8: Return response
        response = PredictResponse(
            disease=result.disease_name,
            confidence=result.confidence,
            confidence_pct=confidence_pct,
            severity=severity,
            advisory=advisory,
            nearest_center=nearest_center,
            is_confident=result.is_confident,
            is_banana_image=result.is_banana_image,
            rejection_reason=result.rejection_reason,
            all_probabilities=result.all_probabilities,
            timestamp=datetime.now(timezone.utc),
            model_version="2.0.0",
        )
        logger.info(
            "── Prediction Pipeline COMPLETE → %s | %s | %s | lang=%s ──",
            result.disease_name, severity, confidence_pct, language,
        )
        return response