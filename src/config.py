import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_bool_env(key, default=False):
    """Helper to read boolean values from env."""
    val = os.getenv(key, str(default)).lower()
    return val in ('true', '1', 't', 'yes', 'y')

# ==============================================
# Configuration
# ==============================================

# --- Google Drive / Upload ---
# Si True, utilise l'API Google Drive. Si False, copie vers le dossier 'output' local.
ENABLE_DRIVE_UPLOAD = get_bool_env("ENABLE_DRIVE_UPLOAD", False)

# Identifiants OAuth2 pour l'API Drive
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
# ID du dossier sur le Drive (laisser vide pour la racine, mais déconseillé)
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# --- Legacy Sync (Deprecated mais supporté comme fallback manuel) ---
DRIVE_SYNC_FOLDER = os.getenv("DRIVE_SYNC_FOLDER")

# --- Sources ---
API_SOURCE = os.getenv("API_SOURCE", "all") # 'google', 'openlibrary', 'all'

# --- Pipeline ---
ENABLE_KEPUBIFY = get_bool_env("ENABLE_KEPUBIFY", True)
ENABLE_RENAME = get_bool_env("ENABLE_RENAME", True)
AUTO_SAVE = get_bool_env("AUTO_SAVE", False)

# --- Display ---
VERBOSE = get_bool_env("VERBOSE", False)
FULL_OUTPUT = get_bool_env("FULL_OUTPUT", False)

SHOW_SUBTITLE = True
SHOW_DESCRIPTION = get_bool_env("SHOW_DESCRIPTION", True)
SHOW_PAGE_COUNT = True
SHOW_CATEGORIES = True
SHOW_RATING = False
SHOW_COVER_LINK = True
SHOW_LINKS = True
SHOW_IDENTIFIERS = True

# --- Search Logic ---
USE_PUBLISHER_IN_SEARCH = get_bool_env("USE_PUBLISHER_IN_SEARCH", True)
USE_SERIES_IN_SEARCH = get_bool_env("USE_SERIES_IN_SEARCH", True)
USE_YEAR_IN_SEARCH = get_bool_env("USE_YEAR_IN_SEARCH", True)
FILTER_BY_LANGUAGE = get_bool_env("FILTER_BY_LANGUAGE", True)

# --- API Constants ---
GOOGLE_API_URL = "https://www.googleapis.com/books/v1/volumes"
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# --- Confidence Thresholds ---
CONFIDENCE_THRESHOLD_HIGH = 80
CONFIDENCE_THRESHOLD_MEDIUM = 50