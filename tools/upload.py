#!/usr/bin/env python3
import argparse
import os
import sys

# Ensure project root is in path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epub_pipeline import config
from epub_pipeline.pipeline.drive_uploader import DriveUploader
from epub_pipeline.utils.logger import Logger


def upload_path(path, uploader):
    if os.path.isfile(path):
        Logger.info(f"📤 Uploading file: {os.path.basename(path)}")
        uploader.upload_to_drive(path)

    elif os.path.isdir(path):
        files = [f for f in os.listdir(path) if not f.startswith(".")]
        Logger.info(f"📂 Uploading folder content: {path} ({len(files)} files)")
        print("-" * 60)

        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path):
                Logger.info(f"   📄 {f}")
                uploader.upload_to_drive(full_path)
            else:
                Logger.warning(f"   ⚠️ Skipping subfolder: {f} (Recursive upload not supported)")


def main():
    parser = argparse.ArgumentParser(description="Manually upload files to the configured Google Drive folder.")
    parser.add_argument("path", help="File or directory to upload.")
    args = parser.parse_args()

    # Force enable drive upload for this tool
    config.ENABLE_DRIVE_UPLOAD = True

    if not os.path.exists(args.path):
        Logger.error(f"Path not found: {args.path}")
        sys.exit(1)

    uploader = DriveUploader()
    if not uploader.service:
        Logger.error("Failed to initialize Drive service. Check credentials.")
        sys.exit(1)

    if not config.DRIVE_FOLDER_ID:
        Logger.warning("No DRIVE_FOLDER_ID set. Files will be uploaded to the root of your Drive.")
        try:
            input("Press Enter to continue or Ctrl+C to cancel...")
        except KeyboardInterrupt:
            sys.exit(0)

    upload_path(args.path, uploader)
    Logger.success("Done.")


if __name__ == "__main__":
    main()
