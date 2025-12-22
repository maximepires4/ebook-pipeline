import requests
import io
from PIL import Image
from src.utils.logger import Logger


class CoverManager:
    """
    Utilities for downloading and processing book covers.
    Ensures images are optimized for e-readers (JPEG, reasonable resolution).
    """

    # Standard high-quality resolution target for e-ink screens
    MAX_SIZE = (1600, 2400)

    @staticmethod
    def download_cover(url):
        """Downloads image data from a URL with basic error handling."""
        if not url:
            return None

        try:
            Logger.verbose(f"Downloading cover from {url}...")
            # User-Agent is important to avoid 403 Forbidden from some CDNs
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            Logger.warning(f"Failed to download cover: {e}")
            return None

    @staticmethod
    def process_image(image_bytes):
        """
        Processes raw image bytes:
        1. Converts to RGB (removes alpha channel if PNG).
        2. Resizes if larger than MAX_SIZE (maintaining aspect ratio).
        3. Compresses to optimized JPEG.
        """
        if not image_bytes:
            return None

        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Convert CMYK or RGBA to RGB for JPEG compatibility
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if too large (High-quality downsampling)
            if (
                img.width > CoverManager.MAX_SIZE[0]
                or img.height > CoverManager.MAX_SIZE[1]
            ):
                img.thumbnail(CoverManager.MAX_SIZE, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            Logger.warning(f"Failed to process cover image: {e}")
            return None
