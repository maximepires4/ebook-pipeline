#!/usr/bin/env python3
import argparse
import os
import sys

# Ensure project root is in path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epub_pipeline.pipeline.epub_manager import EpubManager
from epub_pipeline.utils.formatter import Formatter
from epub_pipeline.utils.logger import Logger


def process_file(path, args):
    Logger.info(f"Inspecting: {path}")
    manager = EpubManager(path)

    if not manager.book:
        Logger.error("Failed to read EPUB file.")
        return

    Formatter.print_metadata(manager, full=args.full)


def main():
    parser = argparse.ArgumentParser(description="Inspect EPUB metadata without modifying anything.")
    parser.add_argument("path", nargs="?", default="data", help="Path to EPUB file or directory.")
    parser.add_argument("--full", action="store_true", help="Show raw XML metadata tags.")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        Logger.error(f"File or directory not found: {args.path}")
        sys.exit(1)

    if os.path.isdir(args.path):
        files = [f for f in os.listdir(args.path) if f.lower().endswith(".epub")]
        if not files:
            Logger.warning(f"No EPUB files found in {args.path}")
            return

        Logger.info(f"Processing {len(files)} files in {args.path}...")
        for f in files:
            process_file(os.path.join(args.path, f), args)
    else:
        process_file(args.path, args)


if __name__ == "__main__":
    main()
