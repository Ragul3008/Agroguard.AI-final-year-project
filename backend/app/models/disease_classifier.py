"""
models/disease_classifier.py - Production banana disease classifier.

Production features added:
    - Confidence threshold  → rejects uncertain predictions
    - Not-banana detection  → rejects non-banana images
    - Full probability map  → returns all 7 class probabilities
"""

import torch
import torch.nn.functional as F

from app.models.model_loader import ModelLoader, DISEASE_CLASSES
from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

_DISPLAY_NAMES: dict[str, str] = {
    "Banana___Panama_Disease":    "Banana - Panama Disease (Fusarium Wilt)",
    "Banana___Black_Sigatoka":    "Banana - Black Sigatoka",
    "Banana___Yellow_Sigatoka":   "Banana - Yellow Sigatoka",
    "Banana___Pseudostem_Weevil": "Banana - Pseudostem Weevil Infestation",
    "Banana___Bunchy_Top_Virus":  "Banana - Bunchy Top Virus (BBTV)",
    "Banana___Anthracnose":       "Banana - Anthracnose",
    "Banana___Healthy":           "Banana - Healthy",
}


class PredictionResult:
    """Structured prediction result with full production metadata."""

    def __init__(
        self,
        disease_name:      str,
        confidence:        float,
        is_confident:      bool,
        is_banana_image:   bool,
        all_probabilities: dict,
        rejection_reason:  str = None,
    ) -> None:
        self.disease_name      = disease_name
        self.confidence        = confidence
        self.is_confident      = is_confident
        self.is_banana_image   = is_banana_image
        self.all_probabilities = all_probabilities
        self.rejection_reason  = rejection_reason


class DiseaseClassifier:
    """Production banana disease classifier with confidence filtering."""

    def __init__(self) -> None:
        self._conf_threshold       = settings.MODEL_CONFIDENCE_THRESHOLD
        self._not_banana_threshold = settings.MODEL_NOT_BANANA_THRESHOLD

    def predict(self, tensor: torch.Tensor) -> PredictionResult:
        """
        Run inference with production confidence checks.

        Args:
            tensor: Float tensor of shape (1, 3, 224, 224).

        Returns:
            PredictionResult with full metadata.
        """
        loader = ModelLoader.get_instance()
        tensor = tensor.to(loader.device)

        with torch.no_grad():
            logits        = loader.model(tensor)
            probabilities = F.softmax(logits, dim=1)

        confidence_tensor, class_idx_tensor = probabilities.max(dim=1)
        raw_label        = DISEASE_CLASSES[class_idx_tensor.item()]
        confidence_value = round(confidence_tensor.item(), 4)
        display_name     = _DISPLAY_NAMES.get(raw_label, raw_label)

        # Full probability distribution for all 7 classes
        all_probs = {
            _DISPLAY_NAMES.get(DISEASE_CLASSES[i], DISEASE_CLASSES[i]):
            round(probabilities[0][i].item(), 4)
            for i in range(len(DISEASE_CLASSES))
        }

        # Production check 1: Not a banana image
        if confidence_value < self._not_banana_threshold:
            logger.warning(
                "Non-banana image rejected (confidence=%.4f < threshold=%.4f)",
                confidence_value, self._not_banana_threshold,
            )
            return PredictionResult(
                disease_name      = "Unknown",
                confidence        = confidence_value,
                is_confident      = False,
                is_banana_image   = False,
                all_probabilities = all_probs,
                rejection_reason  = (
                    "The uploaded image does not appear to be a banana plant. "
                    "Please upload a clear image of a banana leaf, stem, or fruit."
                ),
            )

        # Production check 2: Low confidence prediction
        if confidence_value < self._conf_threshold:
            logger.warning(
                "Low confidence prediction rejected (confidence=%.4f < threshold=%.4f)",
                confidence_value, self._conf_threshold,
            )
            return PredictionResult(
                disease_name      = display_name,
                confidence        = confidence_value,
                is_confident      = False,
                is_banana_image   = True,
                all_probabilities = all_probs,
                rejection_reason  = (
                    f"Low confidence ({confidence_value:.0%}). "
                    "Please upload a clearer, well-lit image of the affected area."
                ),
            )

        logger.info("Prediction → '%s' confidence=%.4f ✓", display_name, confidence_value)
        return PredictionResult(
            disease_name      = display_name,
            confidence        = confidence_value,
            is_confident      = True,
            is_banana_image   = True,
            all_probabilities = all_probs,
        )