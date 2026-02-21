"""
services/prediction_service.py - Orchestrates the full banana disease prediction pipeline.

8-Step Pipeline:
    1. Validate image (GuardrailService)
    2. Preprocess image bytes → tensor (image_preprocessing)
    3. Classify banana disease (DiseaseClassifier)
    4. Estimate severity (SeverityEstimator)
    5. Generate ICAR-aligned advisory (AdvisoryService)
    6. Resolve nearest banana farming support centre (LocationService)
    7. Persist prediction to PostgreSQL (CRUD)
    8. Return structured PredictResponse
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
    """
    High-level service that wires all domain components together
    to deliver a complete banana crop disease prediction.
    """

    def __init__(self) -> None:
        loader = ModelLoader.get_instance()

        self._classifier        = DiseaseClassifier(model_loader=loader)
        self._severity_estimator = SeverityEstimator()
        self._advisory_service  = AdvisoryService()
        self._location_service  = LocationService()
        self._guardrail_service = GuardrailService()

    async def predict(
        self,
        image_bytes:  bytes,
        content_type: str,
        latitude:     Optional[float],
        longitude:    Optional[float],
        db:           AsyncSession,
    ) -> PredictResponse:
        """
        Execute the full 8-step prediction pipeline.

        Args:
            image_bytes:  Raw bytes of the uploaded banana plant image.
            content_type: MIME type of the uploaded file.
            latitude:     Optional GPS latitude of the farm.
            longitude:    Optional GPS longitude of the farm.
            db:           Async database session injected by FastAPI.

        Returns:
            PredictResponse populated with all prediction fields.

        Raises:
            ValueError:   If image validation or preprocessing fails.
            RuntimeError: If the ML inference step fails unexpectedly.
        """
        logger.info("── Banana Prediction Pipeline START ──")

        # ── Step 1: Validate input ─────────────────────────────────────────
        self._guardrail_service.validate_image(content_type, len(image_bytes))
        logger.info("Step 1 ✓ Image validated")

        # ── Step 2: Preprocess image ───────────────────────────────────────
        tensor = preprocess_image(image_bytes)
        logger.info("Step 2 ✓ Image preprocessed → %s", tuple(tensor.shape))

        # ── Step 3: Classify disease ───────────────────────────────────────
        disease_name, confidence = self._classifier.predict(tensor)
        logger.info("Step 3 ✓ Disease: '%s'  Confidence: %.4f", disease_name, confidence)

        # ── Step 4: Estimate severity ──────────────────────────────────────
        severity = self._severity_estimator.estimate(disease_name, confidence)
        logger.info("Step 4 ✓ Severity: %s", severity)

        # ── Step 5: Generate ICAR advisory ────────────────────────────────
        advisory = self._advisory_service.get_advisory(disease_name, severity)
        logger.info("Step 5 ✓ Advisory generated (%d chars)", len(advisory))

        # ── Step 6: Nearest banana support centre ─────────────────────────
        nearest_center = self._location_service.get_nearest_centre(latitude, longitude)
        logger.info("Step 6 ✓ Nearest centre: %s", nearest_center)

        # ── Step 7: Persist to PostgreSQL ─────────────────────────────────
        await create_prediction(
            db=db,
            disease=disease_name,
            confidence=confidence,
            severity=severity,
            advisory=advisory,
            latitude=latitude,
            longitude=longitude,
        )
        logger.info("Step 7 ✓ Prediction saved to database")

        # ── Step 8: Build and return response ─────────────────────────────
        response = PredictResponse(
            disease=disease_name,
            confidence=confidence,
            severity=severity,
            advisory=advisory,
            nearest_center=nearest_center,
            timestamp=datetime.now(timezone.utc),
        )

        logger.info("── Banana Prediction Pipeline COMPLETE ──")
        return response
