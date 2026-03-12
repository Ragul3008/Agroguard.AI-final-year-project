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
    ) -> PredictResponse:
        """Full production prediction pipeline with farmer tracking."""

        logger.info("── Prediction Pipeline START (farmer_id=%s) ──", farmer_id)

        # Step 1: Validate
        self._guardrail_service.validate_image(content_type, len(image_bytes))
        logger.info("Step 1 ✓ Image validated")

        # Step 2: Preprocess
        tensor = preprocess_image(image_bytes)
        logger.info("Step 2 ✓ Preprocessed → %s", tuple(tensor.shape))

        # Step 3: Classify
        result = self._classifier.predict(tensor)
        logger.info("Step 3 ✓ Disease='%s' Confidence=%.4f is_confident=%s is_banana=%s",
                    result.disease_name, result.confidence,
                    result.is_confident, result.is_banana_image)

        # Step 4: Severity
        severity = (
            self._severity_estimator.estimate(result.disease_name, result.confidence)
            if result.is_banana_image else "Unknown"
        )
        logger.info("Step 4 ✓ Severity=%s", severity)

        # Step 5: Advisory (Gemini LLM)
        advisory = (
            self._advisory_service.get_advisory(result.disease_name, severity)
            if result.is_confident
            else (result.rejection_reason or "Please upload a clearer image.")
        )
        logger.info("Step 5 ✓ Advisory generated (%d chars)", len(advisory))

        # Step 6: Nearest centre (Google Maps)
        nearest_center = self._location_service.get_nearest_centre(latitude, longitude)
        logger.info("Step 6 ✓ Nearest centre: %s", nearest_center)

        confidence_pct = f"{result.confidence * 100:.2f}%"

        # Step 7: Persist to DB with farmer_id
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
            model_version="1.1.0",
        )

        logger.info("── Prediction Pipeline COMPLETE → %s | %s | %s ──",
                    result.disease_name, severity, confidence_pct)
        return response