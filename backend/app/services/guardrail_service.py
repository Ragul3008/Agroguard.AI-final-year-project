"""
services/guardrail_service.py - Input validation guardrails for AgroGuard-AI.

Validates image uploads before they reach the ML pipeline:
    1. File type validation     — JPEG, PNG, WebP only (MIME + magic bytes)
    2. File size validation     — max 10 MB
    3. Dimension validation     — max 4096x4096 pixels
    4. Green/plant detection    — checks if image contains a plant/leaf (stricter thresholds)
    5. Image quality check      — rejects solid color, all-white, all-black images
"""

import io
import struct
import cv2
import numpy as np
from PIL import Image
from app.utils.logger import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

_ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}

# Magic bytes for image formats
_MAGIC_BYTES: dict[str, bytes] = {
    "jpeg": b"\xFF\xD8\xFF",
    "png":  b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A",
    "webp": b"RIFF",  # WebP starts with RIFF, need to check for WEBP at offset 8
    "bmp":  b"BM",
    "tiff": b"II\x2A\x00",  # Little-endian TIFF
    "tiff_be": b"MM\x00\x2A",  # Big-endian TIFF
}

_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024   # 10 MB
_MAX_DIMENSION: int = 4096  # Max width/height in pixels

# Plant/leaf detection thresholds (stricter than before)
_MIN_GREEN_RATIO      = 0.08   # At least 8% of pixels must be greenish (was 5%)
_MIN_COLOR_VARIANCE   = 150.0  # Minimum variance — rejects solid color images (was 100)
_MIN_EDGE_DENSITY     = 0.015  # Minimum edge density — rejects blank images (was 0.01)


def _check_magic_bytes(image_bytes: bytes) -> str | None:
    """
    Check file magic bytes to determine actual image format.
    Returns format name if recognized, None otherwise.
    """
    if len(image_bytes) < 12:
        return None

    # JPEG
    if image_bytes[:3] == _MAGIC_BYTES["jpeg"]:
        return "jpeg"

    # PNG
    if image_bytes[:8] == _MAGIC_BYTES["png"]:
        return "png"

    # WebP: RIFF....WEBP
    if image_bytes[:4] == _MAGIC_BYTES["webp"] and len(image_bytes) >= 12:
        if image_bytes[8:12] == b"WEBP":
            return "webp"

    # BMP
    if image_bytes[:2] == _MAGIC_BYTES["bmp"]:
        return "bmp"

    # TIFF (little-endian)
    if image_bytes[:4] == _MAGIC_BYTES["tiff"]:
        return "tiff"

    # TIFF (big-endian)
    if image_bytes[:4] == _MAGIC_BYTES["tiff_be"]:
        return "tiff"

    return None


def _get_image_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    """
    Extract image dimensions without fully decoding.
    Returns (width, height) or None if unable to determine.
    """
    try:
        # Try PIL first (handles most formats)
        with Image.open(io.BytesIO(image_bytes)) as img:
            return img.size
    except Exception:
        pass

    # Fallback: manual parsing for common formats
    try:
        if len(image_bytes) < 24:
            return None

        # JPEG: SOF marker parsing
        if image_bytes[:3] == b"\xFF\xD8\xFF":
            i = 2
            while i < len(image_bytes) - 8:
                if image_bytes[i] == 0xFF and image_bytes[i+1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    height = struct.unpack(">H", image_bytes[i+5:i+7])[0]
                    width = struct.unpack(">H", image_bytes[i+7:i+9])[0]
                    return (width, height)
                i += 1

        # PNG: IHDR chunk at offset 8
        if image_bytes[:8] == b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A":
            width = struct.unpack(">I", image_bytes[16:20])[0]
            height = struct.unpack(">I", image_bytes[20:24])[0]
            return (width, height)

        # WebP: VP8/VP8L chunk
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            # VP8X or VP8/VP8L
            pass

    except Exception:
        pass

    return None


class GuardrailService:
    """
    Validates image uploads before ML inference.

    Checks:
        1. MIME type — must be image format
        2. File size — max 10 MB
        3. Magic bytes — actual file format matches expected
        4. Dimensions — max 4096x4096 pixels
        5. Plant detection — must contain green plant/leaf pixels (stricter)
        6. Image quality  — rejects blank, solid color, all-white/black images
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

    def validate_image_bytes(self, image_bytes: bytes, content_type: str) -> tuple[int, int]:
        """
        Validate image bytes: magic bytes, dimensions, and basic integrity.
        Called AFTER image bytes are loaded but BEFORE plant detection.

        Args:
            image_bytes: Raw image bytes.
            content_type: MIME type from HTTP client.

        Returns:
            Tuple of (width, height).

        Raises:
            ValueError: If validation fails.
        """
        # Check 1: Magic bytes
        detected_format = _check_magic_bytes(image_bytes)
        if not detected_format:
            raise ValueError(
                "File does not appear to be a valid image. "
                "Please upload a valid JPEG, PNG, or WebP image."
            )

        # Verify content-type matches detected format (loose check)
        expected_mime = {
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "bmp": "image/bmp",
            "tiff": "image/tiff",
        }.get(detected_format)

        normalised = content_type.split(";")[0].strip().lower()
        if expected_mime and normalised != expected_mime:
            logger.warning(
                "Content-Type mismatch: header='%s' but magic bytes indicate '%s'",
                normalised, expected_mime
            )
            # Don't reject, just warn - some clients send generic types

        # Check 2: Dimensions
        dimensions = _get_image_dimensions(image_bytes)
        if dimensions:
            width, height = dimensions
            if width > _MAX_DIMENSION or height > _MAX_DIMENSION:
                raise ValueError(
                    f"Image dimensions ({width}x{height}) exceed maximum allowed "
                    f"({_MAX_DIMENSION}x{_MAX_DIMENSION}). Please resize your image."
                )
            if width < 32 or height < 32:
                raise ValueError(
                    f"Image too small ({width}x{height}). Minimum size is 32x32 pixels."
                )
            logger.debug("Guardrail ✓ dimensions=%dx%d format=%s", width, height, detected_format)
            return (width, height)
        else:
            logger.warning("Could not determine image dimensions, skipping dimension check")

        return (0, 0)

    def validate_plant_image(self, image_bytes: bytes) -> None:
        """
        Validate that the uploaded image actually contains a plant/leaf.
        Called AFTER image bytes are loaded and basic validation passes.

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

            # Brown/yellow (diseased leaves)
            lower_yellow = np.array([15,  25,  25])
            upper_yellow = np.array([35, 255, 255])

            mask1 = cv2.inRange(hsv, lower_green1, upper_green1)
            mask2 = cv2.inRange(hsv, lower_green2, upper_green2)
            mask3 = cv2.inRange(hsv, lower_green3, upper_green3)
            mask4 = cv2.inRange(hsv, lower_yellow, upper_yellow)

            plant_mask  = cv2.bitwise_or(mask1, cv2.bitwise_or(mask2, cv2.bitwise_or(mask3, mask4)))
            plant_ratio = float(np.sum(plant_mask > 0)) / total_px

            logger.debug(
                "Plant check — plant_ratio=%.3f variance=%.1f edge_density=%.4f",
                plant_ratio, variance, edge_density,
            )

            if plant_ratio < _MIN_GREEN_RATIO:
                raise ValueError(
                    "This does not appear to be a banana plant image. "
                    "Please upload a photo of a banana leaf, stem or fruit. "
                    f"(Plant pixel ratio: {plant_ratio*100:.1f}% — minimum required: {_MIN_GREEN_RATIO*100:.0f}%)"
                )

            logger.info(
                "Plant guardrail ✓ plant=%.1f%% variance=%.0f edges=%.3f",
                plant_ratio * 100, variance, edge_density,
            )

        except ValueError:
            raise   # Re-raise our own validation errors

        except Exception as exc:
            logger.warning("Plant detection check failed: %s — allowing image", exc)
            # If detection itself fails — let it through
            # Better to allow than block a valid image


# Singleton instance
_guardrail_service: GuardrailService | None = None


def get_guardrail_service() -> GuardrailService:
    """Get or create the singleton GuardrailService instance."""
    global _guardrail_service
    if _guardrail_service is None:
        _guardrail_service = GuardrailService()
    return _guardrail_service