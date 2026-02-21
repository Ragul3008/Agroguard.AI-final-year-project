"""
services/guardrail_service.py - Input validation guardrails for AgroGuard-AI.

Validates image uploads before they reach the ML pipeline, failing fast on
bad inputs to avoid wasting compute resources.
"""

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

# Maximum file size: 10 MB
_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024


class GuardrailService:
    """Validates image uploads and request parameters before ML inference."""

    def validate_image(self, content_type: str, file_size: int) -> None:
        """
        Validate uploaded image MIME type and file size.

        Args:
            content_type: MIME type reported by the HTTP client.
            file_size:    Size of the upload in bytes.

        Raises:
            ValueError: If any validation check fails.
        """
        if not content_type:
            raise ValueError("Content-Type header is missing from the uploaded file.")

        # Normalise content type (strip parameters like ; charset=...)
        normalised = content_type.split(";")[0].strip().lower()

        if normalised not in _ALLOWED_CONTENT_TYPES:
            msg = (
                f"Unsupported file type '{content_type}'. "
                f"Allowed types: JPEG, PNG, WebP, BMP, TIFF."
            )
            logger.warning("Guardrail rejected upload: %s", msg)
            raise ValueError(msg)

        if file_size == 0:
            raise ValueError("Uploaded file is empty (0 bytes).")

        if file_size > _MAX_FILE_SIZE_BYTES:
            msg = (
                f"File too large ({file_size / (1024 * 1024):.1f} MB). "
                f"Maximum allowed size is {_MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )
            logger.warning("Guardrail rejected upload: %s", msg)
            raise ValueError(msg)

        logger.debug(
            "Guardrail passed: type=%s size=%d bytes", content_type, file_size
        )
