"""
models/model_loader.py - Thread-safe singleton model loader for AgroGuard-AI.

Loads the fine-tuned ResNet-50 banana disease classifier once at startup
and reuses the same instance for every inference request.

Banana Disease Classes (7) - Alphabetical order matching ImageFolder:
    0  anthracnose
    1  black sigatoka
    2  bunchy top virus
    3  healthy
    4  panama
    5  pseudostem Wevil
    6  yellow sigatoka
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
# IMPORTANT: Must match alphabetical folder order used by ImageFolder during training
# ---------------------------------------------------------------------------
DISEASE_CLASSES: list[str] = [
    "Banana - Anthracnose",
    "Banana - Black Sigatoka",
    "Banana - Bunchy Top Virus (BBTV)",
    "Banana - Healthy",
    "Banana - Panama Disease (Fusarium Wilt)",
    "Banana - Pseudostem Weevil Infestation",
    "Banana - Yellow Sigatoka",
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
        Build ResNet-50 with custom classification head matching training architecture.
        """
        net = models.resnet50(weights=None)
        in_features = net.fc.in_features  # 2048 for ResNet-50
        net.fc = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Linear(512, NUM_CLASSES)
        )
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

            # Support checkpoint dict saved by training notebook
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            elif isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]

            net.load_state_dict(state)
            logger.info(
                "Banana disease model loaded successfully (%d classes).", NUM_CLASSES
            )
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