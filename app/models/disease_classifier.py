"""
models/disease_classifier.py - Banana disease inference using ResNet-50.

Runs a forward pass on a preprocessed image tensor and returns the
top predicted banana disease label together with its confidence score.
"""

import torch
import torch.nn.functional as F

from app.models.model_loader import ModelLoader, DISEASE_CLASSES
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Human-readable display names for each class index
_DISPLAY_NAMES: dict[str, str] = {
    "Banana___Panama_Disease":    "Banana - Panama Disease (Fusarium Wilt)",
    "Banana___Black_Sigatoka":    "Banana - Black Sigatoka",
    "Banana___Yellow_Sigatoka":   "Banana - Yellow Sigatoka",
    "Banana___Pseudostem_Weevil": "Banana - Pseudostem Weevil Infestation",
    "Banana___Bunchy_Top_Virus":  "Banana - Bunchy Top Virus (BBTV)",
    "Banana___Anthracnose":       "Banana - Anthracnose",
    "Banana___Healthy":           "Banana - Healthy",
}


class DiseaseClassifier:
    """
    Wraps the singleton ModelLoader and exposes a simple predict() API.
    """

    def __init__(self, model_loader: ModelLoader) -> None:
        self._loader = model_loader

    def predict(self, tensor: torch.Tensor) -> tuple[str, float]:
        """
        Run inference on a preprocessed banana plant image.

        Args:
            tensor: Float tensor of shape (1, 3, 224, 224).

        Returns:
            Tuple of (human_readable_disease_name, confidence_score).
            confidence_score is a float in [0, 1].
        """
        tensor = tensor.to(self._loader.device)

        with torch.no_grad():
            logits       = self._loader.model(tensor)          # (1, 7)
            probabilities = F.softmax(logits, dim=1)           # (1, 7)

        confidence_tensor, class_idx_tensor = probabilities.max(dim=1)
        raw_label        = DISEASE_CLASSES[class_idx_tensor.item()]
        confidence_value = round(confidence_tensor.item(), 4)
        display_name     = _DISPLAY_NAMES.get(raw_label, raw_label)

        logger.info(
            "Banana disease prediction → '%s'  confidence=%.4f",
            display_name,
            confidence_value,
        )
        return display_name, confidence_value
