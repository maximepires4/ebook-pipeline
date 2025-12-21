import os
import argparse
from typing import Optional, Tuple

from src import config
from src.utils.logger import Logger
from src.search.confidence import calculate_confidence
from src.utils.isbn_utils import convert_isbn10_to_13
from src.pipeline.epub_manager import EpubManager
from src.utils.formatter import Formatter
from src.models import BookMetadata, SearchResult

from src.search.providers.google import GoogleBooksProvider
from src.search.providers.openlibrary import OpenLibraryProvider


def get_providers():
    """Initializes the metadata providers based on configuration."""
    providers = []
    if config.API_SOURCE in ["all", "google"]:
        providers.append(GoogleBooksProvider())
    if config.API_SOURCE in ["all", "openlibrary"]:
        providers.append(OpenLibraryProvider())
    return providers


def find_book(meta: BookMetadata) -> Tuple[Optional[SearchResult], float, str, int]:
    """
    Core logic for finding a book online using a 'Waterfall' strategy.

    1. ISBN Strategy: High confidence, fast. Tries ISBN-13 and ISBN-10.
    2. Text Relaxation Strategy: Used if ISBN fails. Tries progressively looser queries:
       - Full Context (Title + Author + Publisher + Year + Series)
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
        Logger.verbose(f"🔎 Strategy: ISBN ({isbn})", indent=4)
        variants = [isbn]
        # Always try to generate the ISBN-13 equivalent for better hit rates
        if len(isbn) == 10:
            v13 = convert_isbn10_to_13(isbn)
            if v13:
                variants.append(v13)

        for provider in providers:
            for v_isbn in variants:
                data, total = provider.get_by_isbn(v_isbn)
                if data:
                    conf, _ = calculate_confidence("ISBN", meta, data, total)
                    Logger.full_json(data, indent=8)
                    return data, conf, f"ISBN ({provider.name})", total
            Logger.verbose(f"{provider.name}: ISBN not found.", indent=6)

    # --- 2. Text Relaxation Strategy (Priority 2) ---
    # If ISBN fails, we fall back to text search.
    # We start with strict constraints to find the specific edition, then relax them
    # to find at least the correct work.
    Logger.verbose("Strategy: Text Search with Relaxation", indent=4)
    if meta.get("title") == "Unknown":
        return None, 0, "None", 0

    attempts = [
        {"name": "Full Context", "pub": True, "year": True, "series": True},
        {"name": "No Publisher", "pub": False, "year": True, "series": True},
        {"name": "No Year", "pub": False, "year": False, "series": True},
        {"name": "Basic", "pub": False, "year": False, "series": False},
    ]

    for provider in providers:
        for attempt in attempts:
            Logger.verbose(f"👉 {provider.name} Trying ({attempt['name']})", indent=7)

            data, total = provider.search_by_text(meta, attempt)

            if data:
                conf, _ = calculate_confidence("Text", meta, data, total)

                # Early exit if we find a decent match (> 40%)
                # We don't need perfection here, the user (or auto-save threshold) decides later.
                if conf > 40:
                    Logger.full_json(data, indent=8)
                    return (
                        data,
                        conf,
                        f"Text {provider.name} ({attempt['name']})",
                        total,
                    )
                else:
                    Logger.verbose(
                        f"   ⚠️ Low confidence ({conf}%). Continuing...", indent=7
                    )

    return None, 0, "None", 0


if __name__ == "__main__":
    # Standalone execution for debugging purposes
    parser = argparse.ArgumentParser(description="Standalone Book Finder.")
    parser.add_argument("path", help="Path to the EPUB file.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output."
    )
    parser.add_argument("--full", action="store_true", help="Show full JSON response.")
    parser.add_argument(
        "-s",
        "--source",
        choices=["all", "google", "openlibrary"],
        default="all",
        help="API Source.",
    )
    args = parser.parse_args()

    config.VERBOSE = args.verbose
    config.FULL_OUTPUT = args.full
    config.API_SOURCE = args.source

    if not os.path.exists(args.path):
        Logger.error(f"File not found: {args.path}")
        exit(1)

    extractor = EpubManager(args.path)
    Formatter.print_metadata(extractor)

    meta = extractor.get_curated_metadata()
    if meta:
        data, score, strategy, hits = find_book(meta)
        Formatter.print_search_result(data, score, strategy, hits)
