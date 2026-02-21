"""
utils/image_preprocessing.py - Image preprocessing pipeline for AgroGuard-AI.

Converts uploaded banana plant images into normalised tensors compatible
with the ResNet-50 model.

Pipeline:
    1. Decode raw bytes  →  PIL Image (RGB)
    2. Resize            →  224 × 224 px
    3. ToTensor          →  (C, H, W) float in [0, 1]
    4. Normalize         →  ImageNet mean / std
    5. Unsqueeze         →  (1, C, H, W)  batch dimension
"""

from io import BytesIO

import torch
from PIL import Image
from torchvision import transforms

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Standard ImageNet normalisation statistics used during ResNet training
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]

# Build the transform pipeline once at module load (avoids repeated allocation)
_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
])


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """
    Preprocess raw image bytes into a batch tensor ready for inference.

    Args:
        image_bytes: Raw bytes from the uploaded file.

    Returns:
        Float tensor of shape (1, 3, 224, 224).

    Raises:
        ValueError: If the bytes cannot be decoded as a valid image.
    """
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        logger.error("Failed to open image: %s", exc)
        raise ValueError(f"Invalid image data: {exc}") from exc

    tensor = _TRANSFORM(image)      # (3, 224, 224)
    tensor = tensor.unsqueeze(0)    # (1, 3, 224, 224)

    logger.debug("Image preprocessed → shape %s", tensor.shape)
    return tensor
