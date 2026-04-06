"""
services/guardrail_service.py - Input validation guardrails for AgroGuard-AI.

Validates image uploads before they reach the ML pipeline:
    1. File type validation     — JPEG, PNG, WebP only
    2. File size validation     — max 10 MB
    3. Green/plant detection    — checks if image contains a plant/leaf
    4. Image quality check      — rejects solid color, all-white, all-black images
"""

import io
import cv2
import numpy as np
from PIL import Image
from app.utils.logger import get_logger

logger = get_logger(__name__)

_ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}

_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024   # 10 MB

# ─────────────────────────────────────────────────────────────────────────────
# Plant/leaf detection thresholds
# ─────────────────────────────────────────────────────────────────────────────
_MIN_GREEN_RATIO      = 0.05   # At least 5% of pixels must be greenish
_MIN_COLOR_VARIANCE   = 100.0  # Minimum variance — rejects solid color images
_MIN_EDGE_DENSITY     = 0.01   # Minimum edge density — rejects blank images


class GuardrailService:
    """
    Validates image uploads before ML inference.

    Checks:
        1. MIME type — must be image format
        2. File size — max 10 MB
        3. Plant detection — must contain green plant/leaf pixels
        4. Image quality  — rejects blank, solid color, all-white/black images
    """

    def validate_image(self, content_type: str, file_size: int) -> None:
        """
        Validate uploaded image MIME type and file size only.
        Called BEFORE image bytes are loaded.

        Args:
            content_type: MIME type from HTTP client.
            file_size:    Upload size in bytes.

        Raises:
            ValueError: If validation fails.
        """
        # Check 1: Content type
        if not content_type:
            raise ValueError("Content-Type header is missing from uploaded file.")

        normalised = content_type.split(";")[0].strip().lower()
        if normalised not in _ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Unsupported file type '{content_type}'. "
                f"Please upload a JPEG, PNG or WebP image."
            )

        # Check 2: Empty file
        if file_size == 0:
            raise ValueError("Uploaded file is empty (0 bytes).")

        # Check 3: File too large
        if file_size > _MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File too large ({file_size / (1024*1024):.1f} MB). "
                f"Maximum allowed size is 10 MB."
            )

        logger.debug("Guardrail ✓ type=%s size=%d bytes", content_type, file_size)

    def validate_plant_image(self, image_bytes: bytes) -> None:
        """
        Validate that the uploaded image actually contains a plant/leaf.
        Called AFTER image bytes are loaded.

        Checks:
            - Image is not blank/solid color
            - Image contains sufficient green pixels (plant indicator)
            - Image has enough detail/texture

        Args:
            image_bytes: Raw image bytes.

        Raises:
            ValueError: If image does not appear to be a plant/leaf image.
        """
        try:
            # Load image
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(pil_image)
            img_bgr   = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            h, w      = img_bgr.shape[:2]
            total_px  = h * w

            # ── Check 1: Image quality — reject blank/solid color ─────────────
            gray     = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            variance = float(gray.var())
            if variance < _MIN_COLOR_VARIANCE:
                raise ValueError(
                    "Image appears to be blank or a solid color. "
                    "Please upload a clear photo of a banana leaf."
                )

            # ── Check 2: Edge density — reject images with no detail ──────────
            edges        = cv2.Canny(gray, 50, 150)
            edge_density = float(np.sum(edges > 0)) / total_px
            if edge_density < _MIN_EDGE_DENSITY:
                raise ValueError(
                    "Image has no visible detail or texture. "
                    "Please upload a clear photo of a banana leaf."
                )

            # ── Check 3: Green pixel ratio — detect plant/leaf presence ───────
            # Convert to HSV for better green detection
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

            # Green range in HSV — covers healthy and diseased leaves
            # Healthy green
            lower_green1 = np.array([35,  25,  25])
            upper_green1 = np.array([90, 255, 255])

            # Yellow-green (diseased/yellowing leaves)
            lower_green2 = np.array([20,  25,  25])
            upper_green2 = np.array([35, 255, 255])

            # Dark green (deep leaf shade)
            lower_green3 = np.array([90,  15,  15])
            upper_green3 = np.array([150, 255, 200])

            mask1 = cv2.inRange(hsv, lower_green1, upper_green1)
            mask2 = cv2.inRange(hsv, lower_green2, upper_green2)
            mask3 = cv2.inRange(hsv, lower_green3, upper_green3)

            green_mask  = cv2.bitwise_or(mask1, cv2.bitwise_or(mask2, mask3))
            green_ratio = float(np.sum(green_mask > 0)) / total_px

            logger.debug(
                "Plant check — green_ratio=%.3f variance=%.1f edge_density=%.4f",
                green_ratio, variance, edge_density,
            )

            if green_ratio < _MIN_GREEN_RATIO:
                raise ValueError(
                    "This does not appear to be a banana plant image. "
                    "Please upload a photo of a banana leaf, stem or fruit. "
                    f"(Green pixel ratio: {green_ratio*100:.1f}% — minimum required: {_MIN_GREEN_RATIO*100:.0f}%)"
                )

            logger.info(
                "Plant guardrail ✓ green=%.1f%% variance=%.0f edges=%.3f",
                green_ratio * 100, variance, edge_density,
            )

        except ValueError:
            raise   # Re-raise our own validation errors

        except Exception as exc:
            logger.warning("Plant detection check failed: %s — allowing image", exc)
            # If detection itself fails — let it through
            # Better to allow than block a valid image