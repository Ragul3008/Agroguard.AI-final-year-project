"""
models/model_loader.py - Thread-safe singleton model loader for AgroGuard-AI.

Loads the fine-tuned ResNet-50 banana disease classifier once at startup
and reuses the same instance for every inference request.

Banana Disease Classes (7):
    0  Banana___Panama_Disease
    1  Banana___Black_Sigatoka
    2  Banana___Yellow_Sigatoka
    3  Banana___Pseudostem_Weevil
    4  Banana___Bunchy_Top_Virus
    5  Banana___Anthracnose
    6  Banana___Healthy
"""

import os
import threading
from typing import Optional

import torch
import torch.nn as nn
from torchvision import models

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Banana Disease Class Labels
# These must match the exact class order used when training the model.
# ---------------------------------------------------------------------------
DISEASE_CLASSES: list[str] = [
    "Banana___Panama_Disease",       # Fusarium wilt — most destructive
    "Banana___Black_Sigatoka",       # Mycosphaerella fijiensis fungal leaf disease
    "Banana___Yellow_Sigatoka",      # Mycosphaerella musicola fungal leaf disease
    "Banana___Pseudostem_Weevil",    # Odoiporus longicollis insect pest
    "Banana___Bunchy_Top_Virus",     # BBTV — aphid-transmitted virus
    "Banana___Anthracnose",          # Colletotrichum musae post-harvest fungal disease
    "Banana___Healthy",              # No disease detected
]

NUM_CLASSES: int = len(DISEASE_CLASSES)   # 7


class ModelLoader:
    """
    Thread-safe singleton that holds the loaded ResNet-50 model.

    Usage:
        loader = ModelLoader.get_instance()
        model  = loader.model
    """

    _instance: Optional["ModelLoader"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: nn.Module = self._load_model()

    # ------------------------------------------------------------------
    # Singleton factory
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(
        cls,
        model_path: str = "saved_models/agroguard_banana_resnet50.pth",
    ) -> "ModelLoader":
        """Return (and lazily create) the singleton ModelLoader."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    logger.info("Creating ModelLoader singleton (path=%s)", model_path)
                    cls._instance = cls(model_path)
        return cls._instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_architecture(self) -> nn.Module:
        """
        Build ResNet-50 with a custom classification head for 7 banana disease classes.
        """
        net = models.resnet50(weights=None)
        in_features = net.fc.in_features          # 2048 for ResNet-50
        net.fc = nn.Linear(in_features, NUM_CLASSES)
        return net

    def _load_model(self) -> nn.Module:
        """
        Load weights from disk.
        Falls back to random weights (with a clear warning) when the checkpoint
        is absent so the API can still start during development / CI.
        """
        net = self._build_architecture()

        if os.path.isfile(self.model_path):
            logger.info(
                "Loading banana model weights from '%s' on %s",
                self.model_path,
                self.device,
            )
            state = torch.load(self.model_path, map_location=self.device)

            # Support both raw state-dict and {'state_dict': …} checkpoints
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]

            net.load_state_dict(state)
            logger.info("Banana disease model loaded successfully (%d classes).", NUM_CLASSES)
        else:
            logger.warning(
                "Checkpoint not found at '%s'. "
                "Using RANDOM weights — predictions will be unreliable until "
                "a trained model is placed at this path.",
                self.model_path,
            )

        net.to(self.device)
        net.eval()
        return net
