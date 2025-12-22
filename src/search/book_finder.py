from typing import List, Optional, Tuple

from src import config
from src.search.provider import MetadataProvider
from src.utils.logger import Logger
from src.search.confidence import ConfidenceScorer
from src.utils.isbn_utils import convert_isbn10_to_13
from src.models import BookMetadata, SearchResult

from src.search.providers.google import GoogleBooksProvider
from src.search.providers.openlibrary import OpenLibraryProvider


def get_providers() -> List[MetadataProvider]:
    """Initializes the metadata providers based on configuration."""
    providers: List[MetadataProvider] = []
    if config.API_SOURCE in ["all", "google"]:
        providers.append(GoogleBooksProvider())
    if config.API_SOURCE in ["all", "openlibrary"]:
        providers.append(OpenLibraryProvider())
    return providers


def find_book(meta: BookMetadata) -> Tuple[Optional[SearchResult], float, str]:
    """
    Core logic for finding a book online using a 'Waterfall' strategy.

    1. ISBN Strategy: High confidence, fast. Tries ISBN-13 and ISBN-10.
    2. Text Relaxation Strategy: Used if ISBN fails. Tries progressively looser queries:
       - Full Context (Title + Author + Publisher + Year)
       - No Publisher
       - No Year
       - Basic (Title + Author)

    Returns:
        tuple: (Best Match Data, Confidence Score, Strategy Name, Total Hits)
    """
    providers = get_providers()

    # --- 1. ISBN Strategy (Priority 1) ---
    # ISBNs are unique identifiers, so if we match one, confidence is naturally high (90+).
    isbn = meta.get("isbn")
    if isbn:
        Logger.verbose(f"Strategy: ISBN ({isbn})")
        variants = [isbn]
        # Always try to generate the ISBN-13 equivalent for better hit rates
        if len(isbn) == 10:
            v13 = convert_isbn10_to_13(isbn)
            if v13:
                variants.append(v13)

        for provider in providers:
            for v_isbn in variants:
                data, total = provider.get_by_isbn(v_isbn)
                Logger.verbose(f"Hits: {total}")
                if data:
                    conf, reasons = ConfidenceScorer.calculate(
                        "ISBN", meta, data, total
                    )
                    for r in reasons:
                        Logger.verbose(f"   - {r}")
                    Logger.full_json(data)
                    return data, conf, f"ISBN ({provider.name})"
            Logger.verbose(f"{provider.name}: ISBN not found.")

    # --- 2. Text Relaxation Strategy (Priority 2) ---
    # If ISBN fails, we fall back to text search.
    # We start with strict constraints to find the specific edition, then relax them
    # to find at least the correct work.
    Logger.verbose("Strategy: Text search with relaxation")
    if meta.get("title") == "Unknown":
        return None, 0, "None"

    attempts = [
        {"name": "Full context", "pub": True, "year": True},
        {"name": "No publisher", "pub": False, "year": True},
        {"name": "No year", "pub": False, "year": False},
        {"name": "Basic", "pub": False, "year": False},
    ]

    for provider in providers:
        for attempt in attempts:
            Logger.verbose(f"{provider.name} Trying ({attempt['name']})")

            data, total = provider.search_by_text(meta, attempt)
            Logger.verbose(f"Hits: {total}")

            if data:
                conf, reasons = ConfidenceScorer.calculate("Text", meta, data, total)

                # Early exit if we find a decent match (> 40%)
                if conf > config.CONFIDENCE_THRESHOLD_LOW:
                    for r in reasons:
                        Logger.verbose(f"   - {r}")
                    Logger.full_json(data)
                    return (
                        data,
                        conf,
                        f"Text {provider.name} ({attempt['name']})",
                    )
                else:
                    Logger.verbose(f"Low confidence ({conf}%). Continuing...")

    return None, 0, "None"
