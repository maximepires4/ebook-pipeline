#!/usr/bin/env python3
import sys
import os
import argparse

# Ensure project root is in path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.epub_manager import EpubManager
from src.search.book_finder import find_book
from src.utils.formatter import Formatter
from src.utils.logger import Logger
from src.utils.text_utils import sanitize_filename


def process_file(file_path):
    Logger.info(f"🚀 DRY RUN Pipeline for: {file_path}")
    print("-" * 60)

    # 1. Extraction
    manager = EpubManager(file_path)
    meta = manager.get_curated_metadata()
    if not meta:
        Logger.error("Failed to extract metadata.")
        return

    Logger.info("1. [Extraction] OK")
    print(f"   - Title: {meta['title']}")
    print(f"   - Author: {meta['author']}")

    # 2. Search
    data, score, strategy, _ = find_book(meta)

    if data:
        Logger.info(f"2. [Search] Match Found ({score}%) via {strategy}")
        Formatter.print_comparison(meta, data)

        # 3. Update Simulation
        Logger.info("3. [Update] WOULD update metadata in file.")
        if data.get("imageLinks"):
            Logger.info("   - WOULD download and set new cover.")

        # Prepare mock updated meta for renaming check
        meta["title"] = data["title"]
        meta["author"] = str(data["authors"][0])
        meta["date"] = data.get("publishedDate")
    else:
        Logger.warning("2. [Search] No match found.")
        Logger.info("3. [Update] Skipped.")

    # 4. Conversion Simulation
    Logger.info("4. [Conversion] WOULD convert to KEPUB.")
    kepub_path = file_path.replace(".epub", ".kepub.epub")
    print(f"   - Output: {kepub_path}")

    # 5. Renaming Simulation
    title = sanitize_filename(meta["title"])
    author = sanitize_filename(meta["author"])
    date_str = str(meta.get("date", ""))[:4]
    if not date_str or date_str == "None":
        date_str = "Unknown"

    new_filename = f"{title}-{author}-{date_str}.kepub.epub"
    Logger.info("5. [Renaming] WOULD rename to:")
    print(f"   - {new_filename}")

    # 6. Upload Simulation
    Logger.info("6. [Upload] WOULD upload to Drive/Output.")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Simulate the pipeline without modifying files."
    )
    parser.add_argument(
        "path", nargs="?", default="data", help="Path to EPUB file or directory."
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        Logger.error(f"File or directory not found: {args.path}")
        sys.exit(1)

    if os.path.isdir(args.path):
        files = [f for f in os.listdir(args.path) if f.lower().endswith(".epub")]
        if not files:
            Logger.warning(f"No EPUB files found in {args.path}")
            return

        Logger.info(f"📂 Simulating pipeline for {len(files)} files in {args.path}...")
        for f in files:
            print("=" * 60)
            process_file(os.path.join(args.path, f))
    else:
        process_file(args.path)


if __name__ == "__main__":
    main()
