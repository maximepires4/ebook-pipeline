import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows overriding settings via a local file (for secrets)
load_dotenv()


def get_bool_env(key, default=False):
    """
    Helper to safely parse boolean values from environment variables.
    Handles 'true', '1', 'yes', 'y', 't' (case-insensitive) as True.
    """
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "t", "yes", "y")


# ==============================================
# Configuration Registry
# ==============================================

# --- Google Drive / Upload ---
# Controls the destination of processed files.
# If True, uploads to Google Drive via API.
# If False, copies to local 'output/' directory.
ENABLE_DRIVE_UPLOAD = get_bool_env("ENABLE_DRIVE_UPLOAD", False)

# OAuth2 Credentials paths
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

# Target Drive Folder ID (optional, uploads to root if empty)
# Can be found in the URL of the folder: drive.google.com/drive/folders/<ID>
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# --- Legacy Sync (Deprecated) ---
# Used for older local sync methods (e.g. rclone mount)
DRIVE_SYNC_FOLDER = os.getenv("DRIVE_SYNC_FOLDER")

# --- Metadata Sources ---
# Controls which APIs are queried.
# Options: 'google', 'openlibrary', 'all'
API_SOURCE = os.getenv("API_SOURCE", "all")

# --- Pipeline Features ---
ENABLE_KEPUBIFY = get_bool_env("ENABLE_KEPUBIFY", True)
ENABLE_RENAME = get_bool_env("ENABLE_RENAME", True)
# If True, applies changes automatically without asking, even for low confidence.
AUTO_SAVE = get_bool_env("AUTO_SAVE", False)

# --- Display / Logging ---
VERBOSE = get_bool_env("VERBOSE", False)
FULL_OUTPUT = get_bool_env("FULL_OUTPUT", False)  # Dumps full JSON response

# Toggles for specific fields in the console output
SHOW_SUBTITLE = True
SHOW_DESCRIPTION = get_bool_env("SHOW_DESCRIPTION", True)
SHOW_PAGE_COUNT = True
SHOW_CATEGORIES = True
SHOW_COVER_LINK = True
SHOW_LINKS = True
SHOW_IDENTIFIERS = True

# --- Search Logic Tuning ---
# These flags control the "strictness" of the text search.
USE_PUBLISHER_IN_SEARCH = get_bool_env("USE_PUBLISHER_IN_SEARCH", True)
USE_SERIES_IN_SEARCH = get_bool_env("USE_SERIES_IN_SEARCH", True)
USE_YEAR_IN_SEARCH = get_bool_env("USE_YEAR_IN_SEARCH", True)
# If True, filters API results to match the EPUB's language (reduces noise)
FILTER_BY_LANGUAGE = get_bool_env("FILTER_BY_LANGUAGE", True)

# --- Network Constants ---
GOOGLE_API_URL = "https://www.googleapis.com/books/v1/volumes"
REQUEST_TIMEOUT = 10  # Seconds
MAX_RETRIES = 3  # Exponential backoff attempts

# --- Confidence Thresholds ---
# Scores (0-100) determining the visual indicator (Green/Yellow/Red)
CONFIDENCE_THRESHOLD_HIGH = 80
CONFIDENCE_THRESHOLD_MEDIUM = 50
