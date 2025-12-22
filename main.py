import argparse
import os
import sys
import traceback
from src import config
from src.utils.logger import Logger
from src.pipeline.orchestrator import PipelineOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Full Ebook Pipeline.")
    parser.add_argument("path", help="Directory or file to process.")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode.")
    parser.add_argument(
        "-s",
        "--source",
        choices=["all", "google", "openlibrary"],
        default="all",
        help="Metadata Source.",
    )
    parser.add_argument(
        "--no-kepub", action="store_true", help="Disable KEPUB conversion."
    )
    parser.add_argument("--no-rename", action="store_true", help="Disable renaming.")
    parser.add_argument("--no-upload", action="store_true", help="Disable uploading.")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-save metadata (skip confirmation for high confidence).",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode: confirm each metadata field change manually.",
    )
    parser.add_argument(
        "--isbn",
        help="Force a specific ISBN for the search (single file only).",
    )

    args = parser.parse_args()

    config.VERBOSE = args.verbose
    if args.source != "all":
        config.API_SOURCE = args.source

    orchestrator = PipelineOrchestrator(
        auto_save=args.auto,
        enable_kepub=not args.no_kepub,
        enable_rename=not args.no_rename,
        interactive_fields=args.interactive,
        enable_upload=not args.no_upload,
    )

    target_path = args.path

    try:
        if os.path.isfile(target_path):
            orchestrator.process_file(target_path, forced_isbn=args.isbn)
        elif os.path.isdir(target_path):
            if args.isbn:
                Logger.error("--isbn is only supported for single files.")
                sys.exit(1)
            orchestrator.process_directory(target_path)
        else:
            Logger.error(f"Path not found: {target_path}")
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
