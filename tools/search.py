#!/usr/bin/env python3
import argparse
import os
import sys

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epub_pipeline import config
from epub_pipeline.pipeline.epub_manager import EpubManager
from epub_pipeline.search.book_finder import find_book
from epub_pipeline.utils.formatter import Formatter
from epub_pipeline.utils.logger import Logger


def process_file(path):
    Logger.info(f"\nSearching metadata for: {path}")
    manager = EpubManager(path)

    meta = manager.get_curated_metadata()
    if not meta:
        Logger.error("Could not extract basic metadata from file.")
        return

    print(f"Extracted: {meta['title']} / {', '.join(meta['authors'])} / {meta['isbn']}")

    data, score, strategy = find_book(meta)

    if data:
        Formatter.print_search_result(data, score, strategy)
    else:
        Logger.warning("No match found.")


def main():
    parser = argparse.ArgumentParser(description="Test metadata search for an EPUB file.")
    parser.add_argument("path", nargs="?", default="data", help="Path to EPUB file or directory.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed search steps.")
    args = parser.parse_args()

    config.VERBOSE = args.verbose

    if not os.path.exists(args.path):
        Logger.error(f"File or directory not found: {args.path}")
        sys.exit(1)

    if os.path.isdir(args.path):
        files = [f for f in os.listdir(args.path) if f.lower().endswith(".epub")]
        if not files:
            Logger.warning(f"No EPUB files found in {args.path}")
            return

        Logger.info(f"Searching for {len(files)} files in {args.path}...")
        for f in files:
            process_file(os.path.join(args.path, f))
    else:
        process_file(args.path)


if __name__ == "__main__":
    main()
