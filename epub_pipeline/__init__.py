__version__ = "0.1.0-alpha.1"

# Utils
from .pipeline.cover_manager import CoverManager
from .pipeline.drive_uploader import DriveUploader

# Pipeline
from .pipeline.epub_manager import EpubManager
from .pipeline.kepub_handler import KepubHandler

# Search
from .search.book_finder import find_book
from .search.confidence import ConfidenceScorer
from .search.provider import MetadataProvider
from .utils.formatter import Formatter
from .utils.isbn_utils import (
    clean_isbn_string,
    convert_isbn10_to_13,
    extract_isbn_from_filename,
    is_valid_isbn,
)
from .utils.logger import Logger
from .utils.text_utils import get_similarity, sanitize_filename

__all__ = [
    # Utils
    "Logger",
    "Formatter",
    "sanitize_filename",
    "get_similarity",
    "clean_isbn_string",
    "extract_isbn_from_filename",
    "is_valid_isbn",
    "convert_isbn10_to_13",
    # Pipeline
    "EpubManager",
    "CoverManager",
    "KepubHandler",
    "DriveUploader",
    # Search
    "find_book",
    "ConfidenceScorer",
    "MetadataProvider",
]
