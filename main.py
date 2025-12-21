import argparse
import os
import sys
from src import config
from src.utils.logger import Logger
from src.pipeline.orchestrator import PipelineOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Full Ebook Pipeline.")
    parser.add_argument(
        "path", nargs="?", help="Directory or file to process."
    )

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
    parser.add_argument("--drive", help="Path to Google Drive sync folder.")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-save metadata (skip confirmation for high confidence).",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode: confirm each metadata field change manually."
    )

    args = parser.parse_args()

    config.VERBOSE = args.verbose
    if args.source != "all":
        config.API_SOURCE = args.source

    if args.drive:
        config.DRIVE_SYNC_FOLDER = args.drive

    orchestrator = PipelineOrchestrator(
        auto_save=args.auto,
        enable_kepub=not args.no_kepub,
        enable_rename=not args.no_rename,
        interactive_fields=args.interactive
    )

    target_path = args.path
    if not target_path:
        try:
            print(f"Current working directory: {os.getcwd()}")
            default_dir = os.path.join(os.getcwd(), "data")
            user_input = input(
                f"Enter file or directory to analyze [default: {default_dir}]: "
            ).strip()
            target_path = user_input if user_input else default_dir
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return

    try:
        if os.path.isfile(target_path):
            Logger.info(f"🚀 Starting Pipeline on single file: {target_path}")
            orchestrator.process_file(target_path)
        elif os.path.isdir(target_path):
            orchestrator.process_directory(target_path)
        else:
            Logger.error(f"Path not found: {target_path}")
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()