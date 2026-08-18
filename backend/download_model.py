import os
import gdown
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The target directory and file
MODEL_DIR = "saved_models"
MODEL_PATH = os.path.join(MODEL_DIR, "agroguard_banana_convnext_v3.pth")

# The Google Drive File ID (Provided as an environment variable in Render)
# E.g., if link is https://drive.google.com/file/d/1ABCXYZ/view, the ID is 1ABCXYZ
DRIVE_FILE_ID = os.environ.get("MODEL_DRIVE_ID")

def main():
    if not DRIVE_FILE_ID:
        logger.warning("No MODEL_DRIVE_ID environment variable found. Skipping model download.")
        return

    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(MODEL_PATH):
        logger.info(f"Model already exists at {MODEL_PATH}. Skipping download.")
        return

    logger.info(f"Downloading model from Google Drive (ID: {DRIVE_FILE_ID})...")
    try:
        # Use gdown to download the file by ID
        url = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'
        gdown.download(url, MODEL_PATH, quiet=False, fuzzy=True)
        logger.info("Model download complete!")
    except Exception as e:
        logger.error(f"Failed to download model: {e}")

if __name__ == "__main__":
    main()
