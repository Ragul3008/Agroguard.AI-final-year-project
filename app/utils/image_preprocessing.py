"""
utils/image_preprocessing.py - Advanced image preprocessing for AgroGuard-AI.

Techniques applied:
    1. Blur Detection       — Laplacian variance, reject blurry images
    2. Leaf Segmentation    — GrabCut algorithm, isolate leaf from background
    3. Affected Area Crop   — Contour detection, crop diseased region
    4. CLAHE Enhancement    — Contrast Limited Adaptive Histogram Equalization
    5. Green Channel Boost  — Enhance leaf-specific features
    6. Resize & Normalize   — 224x224, ImageNet stats for ConvNeXt Small
"""

import io
import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
IMG_SIZE            = 224
BLUR_THRESHOLD      = 80.0    # Laplacian variance below this = blurry
MIN_LEAF_AREA_RATIO = 0.05    # Leaf must cover at least 5% of image
CLAHE_CLIP_LIMIT    = 2.5     # CLAHE clip limit
CLAHE_GRID_SIZE     = (8, 8)  # CLAHE tile grid size

# ImageNet normalization stats (same as training notebook Cell 4)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

# Final transform — matches val_transforms in training notebook
_to_tensor_and_normalize = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — BLUR DETECTION
# Laplacian variance — blurry images have low edge variance
# ─────────────────────────────────────────────────────────────────────────────
def detect_blur(image_bgr: np.ndarray) -> tuple[bool, float]:
    """
    Detect if image is blurry using Laplacian variance method.

    Args:
        image_bgr: OpenCV BGR image array.

    Returns:
        (is_blurry, blur_score) — lower score means more blurry.
    """
    gray       = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blurry  = blur_score < BLUR_THRESHOLD
    return is_blurry, round(float(blur_score), 2)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — LEAF SEGMENTATION (GrabCut)
# Isolates the banana leaf from the background
# ─────────────────────────────────────────────────────────────────────────────
def segment_leaf(image_bgr: np.ndarray) -> np.ndarray:
    """
    Segment the leaf from background using GrabCut algorithm.
    Returns leaf on white background.

    Args:
        image_bgr: OpenCV BGR image array.

    Returns:
        Segmented leaf image with white background.
    """
    try:
        h, w    = image_bgr.shape[:2]
        margin  = int(min(h, w) * 0.10)
        rect    = (margin, margin, w - 2 * margin, h - 2 * margin)

        mask    = np.zeros((h, w), np.uint8)
        bgd_mdl = np.zeros((1, 65), np.float64)
        fgd_mdl = np.zeros((1, 65), np.float64)

        cv2.grabCut(image_bgr, mask, rect, bgd_mdl, fgd_mdl, 5, cv2.GC_INIT_WITH_RECT)

        # Foreground + probable foreground
        fg_mask    = np.where(
            (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0
        ).astype(np.uint8)

        # Check leaf area is sufficient
        leaf_ratio = np.sum(fg_mask > 0) / (h * w)
        if leaf_ratio < MIN_LEAF_AREA_RATIO:
            logger.debug("GrabCut leaf too small (%.2f) — skipping", leaf_ratio)
            return image_bgr

        # Clean mask with morphological operations
        kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN,  kernel, iterations=1)

        # Apply mask — background becomes white
        result               = image_bgr.copy()
        result[fg_mask == 0] = [255, 255, 255]

        logger.debug("Leaf segmented — area ratio: %.2f", leaf_ratio)
        return result

    except Exception as exc:
        logger.warning("Leaf segmentation failed: %s — using original", exc)
        return image_bgr


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — AFFECTED AREA CROP
# Detects disease spots using HSV thresholding and crops the most affected region
# ─────────────────────────────────────────────────────────────────────────────
def crop_affected_area(image_bgr: np.ndarray) -> np.ndarray:
    """
    Detect and crop the most diseased region of the leaf.
    Uses HSV thresholding to find brown/yellow/dark disease spots.

    Args:
        image_bgr: OpenCV BGR image array.

    Returns:
        Cropped region with disease area, or original if not found.
    """
    try:
        h, w = image_bgr.shape[:2]
        hsv  = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # Brown spots — anthracnose, panama, sigatoka lesions
        lower_brown = np.array([5,  50,  50])
        upper_brown = np.array([25, 255, 200])

        # Yellow spots — yellow sigatoka, chlorosis
        lower_yellow = np.array([20, 80,  80])
        upper_yellow = np.array([40, 255, 255])

        # Dark spots — black sigatoka
        lower_dark = np.array([0,   0,  0])
        upper_dark = np.array([180, 50, 60])

        # Combine all disease color masks
        mask_brown  = cv2.inRange(hsv, lower_brown,  upper_brown)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_dark   = cv2.inRange(hsv, lower_dark,   upper_dark)
        mask        = cv2.bitwise_or(mask_brown, cv2.bitwise_or(mask_yellow, mask_dark))

        # Clean mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)

        # Find disease contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            logger.debug("No disease contours found — using original")
            return image_bgr

        # Find largest disease contour
        largest = max(contours, key=cv2.contourArea)
        area    = cv2.contourArea(largest)

        if area < (h * w) * 0.01:
            logger.debug("Disease area too small (%.0f px) — using original", area)
            return image_bgr

        # Get bounding box with 30% padding
        x, y, cw, ch = cv2.boundingRect(largest)
        pad_x = int(cw * 0.30)
        pad_y = int(ch * 0.30)
        x1    = max(0, x - pad_x)
        y1    = max(0, y - pad_y)
        x2    = min(w, x + cw + pad_x)
        y2    = min(h, y + ch + pad_y)

        # Ensure crop is meaningful
        if (x2 - x1) * (y2 - y1) / (h * w) < 0.05:
            return image_bgr

        cropped = image_bgr[y1:y2, x1:x2]
        logger.debug(
            "Affected area cropped — region: (%d,%d,%d,%d)",
            x1, y1, x2, y2,
        )
        return cropped

    except Exception as exc:
        logger.warning("Affected area crop failed: %s — using original", exc)
        return image_bgr


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — CLAHE ENHANCEMENT
# Improves contrast in poor lighting conditions from field photos
# Applied to L channel in LAB color space — preserves color info
# ─────────────────────────────────────────────────────────────────────────────
def apply_clahe(image_bgr: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE to improve contrast — especially useful for dark field photos.

    Args:
        image_bgr: OpenCV BGR image.

    Returns:
        Contrast-enhanced BGR image.
    """
    try:
        # BGR → LAB
        lab     = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE only to L (lightness) channel
        clahe      = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=CLAHE_GRID_SIZE,
        )
        l_enhanced   = clahe.apply(l)
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        enhanced     = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        logger.debug("CLAHE applied")
        return enhanced

    except Exception as exc:
        logger.warning("CLAHE failed: %s — using original", exc)
        return image_bgr


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — GREEN CHANNEL BOOST
# Enhances leaf-specific features for better disease detection
# ─────────────────────────────────────────────────────────────────────────────
def boost_green_channel(image_bgr: np.ndarray, factor: float = 1.15) -> np.ndarray:
    """
    Boost green channel to enhance leaf tissue features.

    Args:
        image_bgr: OpenCV BGR image.
        factor:    Multiplier for green channel (1.15 = 15% boost).

    Returns:
        Green-boosted BGR image.
    """
    try:
        b, g, r   = cv2.split(image_bgr.astype(np.float32))
        g_boosted = np.clip(g * factor, 0, 255).astype(np.uint8)
        result    = cv2.merge([b.astype(np.uint8), g_boosted, r.astype(np.uint8)])
        logger.debug("Green channel boosted by %.2fx", factor)
        return result

    except Exception as exc:
        logger.warning("Green boost failed: %s — using original", exc)
        return image_bgr


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PREPROCESSING PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """
    Full preprocessing pipeline for AgroGuard-AI inference.

    Pipeline steps:
        1. Decode image bytes → PIL → OpenCV BGR
        2. Blur detection     → raise ValueError if blurry
        3. Leaf segmentation  → GrabCut isolates leaf from background
        4. Affected area crop → crops most diseased region using contours
        5. CLAHE enhancement  → improves contrast for field photos
        6. Green channel boost→ enhances leaf tissue features
        7. Resize to 224x224  → ConvNeXt Small input size
        8. ToTensor + Normalize → ImageNet stats (matches training Cell 4)
        9. Add batch dim      → shape [1, 3, 224, 224]

    Args:
        image_bytes: Raw image bytes from uploaded file.

    Returns:
        Preprocessed tensor of shape [1, 3, 224, 224].

    Raises:
        ValueError: If image is blurry, unreadable or too small.
    """

    # ── Step 1: Decode ───────────────────────────────────────────────────────
    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot read image file: {exc}") from exc

    # PIL RGB → OpenCV BGR
    image_bgr      = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    original_shape = image_bgr.shape
    logger.debug("Image decoded — shape: %s", original_shape)

    # ── Step 2: Blur Detection ───────────────────────────────────────────────
    is_blurry, blur_score = detect_blur(image_bgr)
    logger.debug("Blur score: %.2f (threshold: %.2f)", blur_score, BLUR_THRESHOLD)

    if is_blurry:
        raise ValueError(
            f"Image is too blurry (score: {blur_score:.1f}). "
            f"Please take a clearer photo of the banana leaf in good lighting."
        )

    # ── Step 3: Leaf Segmentation ────────────────────────────────────────────
    image_bgr = segment_leaf(image_bgr)

    # ── Step 4: Affected Area Crop ───────────────────────────────────────────
    image_bgr = crop_affected_area(image_bgr)

    # ── Step 5: CLAHE Enhancement ────────────────────────────────────────────
    image_bgr = apply_clahe(image_bgr)

    # ── Step 6: Green Channel Boost ──────────────────────────────────────────
    image_bgr = boost_green_channel(image_bgr)

    # ── Step 7: Resize to 224x224 ────────────────────────────────────────────
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_final = Image.fromarray(image_rgb).resize(
        (IMG_SIZE, IMG_SIZE), Image.LANCZOS
    )

    # ── Step 8: ToTensor + Normalize (matches val_transforms in notebook) ────
    tensor = _to_tensor_and_normalize(pil_final)

    # ── Step 9: Add batch dimension ──────────────────────────────────────────
    tensor = tensor.unsqueeze(0)

    logger.debug(
        "Preprocessing done — input: %s output: %s",
        original_shape, tuple(tensor.shape),
    )
    return tensor


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC HELPER — Blur score API
# ─────────────────────────────────────────────────────────────────────────────
def get_blur_score(image_bytes: bytes) -> dict:
    """
    Returns blur analysis — useful for giving feedback to farmers.

    Returns:
        {
          "is_blurry": bool,
          "blur_score": float,
          "threshold": float,
          "message": str
        }
    """
    try:
        pil_image        = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_bgr        = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        is_blurry, score = detect_blur(image_bgr)
        return {
            "is_blurry":  is_blurry,
            "blur_score": score,
            "threshold":  BLUR_THRESHOLD,
            "message": (
                "Image too blurry — please retake in better lighting"
                if is_blurry
                else "Image sharpness is good"
            ),
        }
    except Exception as exc:
        return {
            "is_blurry":  True,
            "blur_score": 0.0,
            "threshold":  BLUR_THRESHOLD,
            "message":    f"Could not analyse image: {exc}",
        }