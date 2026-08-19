"""
models/model_loader.py - Thread-safe singleton model loader for AgroGuard-AI.
ConvNeXt Small architecture - 99.78% accuracy
"""

import os
import threading
from typing import Optional

import torch
import torch.nn as nn
from torchvision import models

# Drastically reduce CPU memory usage
torch.set_num_threads(1)
torch.set_grad_enabled(False)

from app.utils.logger import get_logger

logger = get_logger(__name__)

DISEASE_CLASSES: list[str] = [
    "Banana - Anthracnose",
    "Banana - Black Sigatoka",
    "Banana - Bunchy Top Virus (BBTV)",
    "Banana - Healthy",
    "Banana - Panama Disease (Fusarium Wilt)",
    "Banana - Pseudostem Weevil Infestation",
    "Banana - Yellow Sigatoka",
]

NUM_CLASSES: int = len(DISEASE_CLASSES)


class ModelLoader:
    _instance: Optional["ModelLoader"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: nn.Module = self._load_model()

    @classmethod
    def get_instance(
        cls,
        model_path: str = "saved_models/agroguard_banana_convnext_small.pth",
    ) -> "ModelLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    logger.info("Creating ModelLoader singleton (path=%s)", model_path)
                    cls._instance = cls(model_path)
        return cls._instance

    def _build_architecture(self) -> nn.Module:
        net = models.convnext_small(weights=None)
        in_features = net.classifier[2].in_features
        net.classifier[2] = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 512),
            nn.GELU(),
            nn.Dropout(p=0.3),
            nn.Linear(512, NUM_CLASSES)
        )
        return net

    def _load_model(self) -> nn.Module:
        net = self._build_architecture()

        if os.path.isfile(self.model_path):
            logger.info(
                "Loading banana model weights from '%s' on %s",
                self.model_path,
                self.device,
            )
            # Use mmap=True to map weights to disk and avoid large RAM spikes during loading
            state = torch.load(self.model_path, map_location=self.device, mmap=True)

            if isinstance(state, dict) and "model_state_dict" in state:
                state_dict = state["model_state_dict"]
            elif isinstance(state, dict) and "state_dict" in state:
                state_dict = state["state_dict"]
            else:
                state_dict = state

            net.load_state_dict(state_dict)
            
            # Explicitly free memory to survive Render's 512MB RAM limit
            del state
            del state_dict
            import gc
            gc.collect()
            
            logger.info("Banana disease model loaded successfully (%d classes).", NUM_CLASSES)
        else:
            logger.warning(
                "Checkpoint not found at '%s'. Using RANDOM weights.",
                self.model_path,
            )

        net.to(self.device)
        net.eval()
        return net 