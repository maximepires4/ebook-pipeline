import os
import shutil
import tempfile

import termcolor

from epub_pipeline import config
from epub_pipeline.pipeline.cover_manager import CoverManager
from epub_pipeline.pipeline.drive_uploader import DriveUploader
from epub_pipeline.pipeline.epub_manager import EpubManager
from epub_pipeline.pipeline.kepub_handler import KepubHandler
from epub_pipeline.search.book_finder import find_book
from epub_pipeline.utils.formatter import Formatter
from epub_pipeline.utils.logger import Logger
from epub_pipeline.utils.text_utils import sanitize_filename, truncate


class PipelineOrchestrator:
    """
    Central controller for the ebook processing pipeline.
    It manages the lifecycle of a book file from extraction to final upload.
    """

    def __init__(
        self,
        auto_save=False,
        enable_kepub=True,
        enable_rename=True,
        interactive_fields=False,
        enable_upload=True,
    ):
        self.auto_save = auto_save
        self.enable_kepub = enable_kepub
        self.enable_rename = enable_rename
        self.interactive_fields = interactive_fields
        self.uploader = DriveUploader(enable_upload)

    def process_directory(self, directory):
        """Batch processes all EPUB files in a given directory."""
        if not os.path.exists(directory):
            Logger.error(f"Directory '{directory}' does not exist.")
            return

        files = [f for f in os.listdir(directory) if f.lower().endswith(".epub")]

        if not files:
            Logger.warning(f"No standard .epub files found in '{directory}/'.")
            return

        Logger.info(f"Starting Pipeline on {len(files)} files in '{directory}'...")
        print("-" * 60)

        for f in files:
            path = os.path.join(directory, f)
            try:
                self.process_file(path)
            except Exception as e:
                raise e
            print("-" * 60)

    def process_file(self, file_path, forced_isbn=None):
        """
        Runs the full pipeline securely using a temporary workspace.
        Ensures the source file is never modified.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.basename(file_path)
            working_path = os.path.join(temp_dir, filename)

            # Secure Copy
            try:
                shutil.copy2(file_path, working_path)
            except Exception as e:
                Logger.error(f"Failed to copy file to temp dir: {e}")
                return

            try:
                manager = EpubManager(working_path)
            except Exception:
                Logger.warning(f"Skipping (No Book): {filename}")
                return

            meta = manager.get_curated_metadata()
            if not meta:
                Logger.warning(f"Skipping (No Meta): {filename}")
                return

            if forced_isbn:
                Logger.info(f"Using Forced ISBN: {forced_isbn}")
                meta["isbn"] = forced_isbn

            Logger.info(f"Processing: {meta.get('title', 'Unknown')} ({truncate(filename)})")

            online_data, confidence, strategy = find_book(meta)

            final_meta = meta
            current_path = working_path

            if online_data:
                Formatter.print_search_result(online_data, confidence, strategy)

                approved_data = None

                if self.interactive_fields:
                    # Granular manual review
                    approved_data = self._review_metadata_changes(meta, online_data)
                else:
                    # Automatic or Boolean check
                    Formatter.print_comparison(meta, online_data)
                    if self._should_save(confidence):
                        approved_data = online_data

                if approved_data:
                    self._update_metadata(manager, approved_data)
                    final_meta = self._get_updated_meta_dict(meta, approved_data)
                elif self.interactive_fields:
                    Logger.info("No metadata changes selected. Continuing with local metadata.")
                else:
                    Logger.warning("Skipping file (Metadata update rejected by user).")
                    return
            else:
                Logger.warning("No online match. Using local metadata for pipeline.")

            # --- 4. Renaming ---
            if self.enable_rename:
                current_path = self._handle_renaming(current_path, final_meta)

            # --- 5. Conversion ---
            if self.enable_kepub:
                current_path = self._handle_conversion(current_path)

            # --- 6. Upload ---
            self.uploader.process_file(current_path)

    def _should_save(self, confidence):
        if self.auto_save or confidence >= config.CONFIDENCE_THRESHOLD_HIGH:
            return True

        try:
            choice = input(f"   [?] Low confidence ({confidence}%). Apply this metadata? [y/N]: ").strip().lower()
            return choice == "y"
        except EOFError:
            return False

    def _review_metadata_changes(self, local_meta, remote_data):
        """
        Interactively asks the user to confirm each metadata field change.
        Returns a dict containing ONLY the approved changes.
        """
        print("\n   --- Interactive Metadata Review ---")
        print("y = apply change, e = edit value, else skip\n")
        approved = {}

        def clean(v):
            return str(v) if v else ""

        # Fields map: (Label, Local Key, Remote Key)
        fields = [
            ("Title", "title", "title"),
            ("Publisher", "publisher", "publisher"),
            ("Date", "date", "publishedDate"),
            ("Language", "language", "language"),
            ("Description", "description", "description"),
        ]

        # TODO: Multiple authors

        for label, l_key, r_key in fields:
            local_val = clean(local_meta.get(l_key)).strip()
            remote_val = clean(remote_data.get(r_key)).strip()

            # Special date handling
            if label == "Date" and len(local_val) >= 4 and len(remote_val) >= 4:
                if local_val[:4] == remote_val[:4]:
                    continue

            if local_val != remote_val and remote_val:
                print(
                    f"   [?] ({label})",
                    termcolor.colored(f"{local_val or 'N/A'}", attrs=["bold"]),
                    "->",
                    termcolor.colored(f"{remote_val or 'N/A'}", attrs=["bold"]),
                    end=" ",
                )
                choice = input("[y/e/N]: ").strip().lower()
                if choice == "y":
                    approved[r_key] = remote_data[r_key]
                elif choice == "e":
                    new_val = input("   Edit value: ").strip()
                    approved[r_key] = new_val

        # TODO: Clean for multiple authors
        # Author (List vs String)
        local_auth = clean(local_meta.get("author"))
        remote_auths = remote_data.get("authors", [])
        remote_auth_str = (
            ", ".join(remote_auths) if isinstance(remote_auths, list) and remote_auths else str(remote_auths)
        )

        if local_auth != remote_auth_str and remote_auths:
            print("   [?] Author:")
            print(f"      Current: {local_auth}")
            print(f"      New:     {remote_auth_str}")
            choice = input("      Apply change? [y/N]: ").strip().lower()
            if choice == "y":
                approved["authors"] = remote_auths

        # Cover
        if config.UPDATE_COVER and remote_data.get("imageLinks"):
            choice = input("    [?] Cover found online, download and update? [y/N]: ").strip().lower()
            if choice == "y":
                approved["imageLinks"] = remote_data["imageLinks"]

        if not approved:
            return None

        return approved

    def _update_metadata(self, manager, online_data):
        Logger.info("Updating metadata...")
        manager.update_metadata(online_data)

        if True:
            # TODO: Fix cover update
            Logger.warning("DEBUG: Skipping cover update.")
        elif config.UPDATE_COVER and online_data.get("imageLinks"):
            url = online_data["imageLinks"].get("thumbnail") or online_data["imageLinks"].get("smallThumbnail")
            if url:
                img_bytes = CoverManager.download_cover(url)
                processed_img = CoverManager.process_image(img_bytes)
                if processed_img:
                    manager.set_cover(processed_img)
                    Logger.success("Cover updated.", indent=4)

        manager.save()
        Logger.success("EPUB saved.")

    def _get_updated_meta_dict(self, original_meta, online_data):
        new_meta = original_meta.copy()

        # Only update keys that are present in online_data (approved changes)
        if "title" in online_data:
            new_meta["title"] = online_data["title"]

        if "authors" in online_data:
            auths = online_data["authors"]
            new_meta["author"] = auths[0] if isinstance(auths, list) and auths else str(auths)

        if "publishedDate" in online_data:
            new_meta["date"] = online_data["publishedDate"]

        return new_meta

    def _handle_conversion(self, input_path):
        Logger.info("Converting to KEPUB...")
        if not input_path.endswith(".kepub.epub"):
            kepub_path = input_path.replace(".epub", ".kepub.epub")
        else:
            kepub_path = input_path

        if KepubHandler.convert_to_kepub(input_path, kepub_path):
            return kepub_path
        else:
            Logger.warning("Conversion failed. Using standard EPUB.")
            return input_path

    def _handle_renaming(self, current_path, meta):
        title = sanitize_filename(meta["title"])
        author = sanitize_filename(meta["author"])
        date_str = str(meta.get("date", ""))[:4]

        if current_path.endswith(".kepub.epub"):
            ext = ".kepub.epub"
        else:
            ext = ".epub"

        if not date_str or date_str == "None":
            new_filename = f"{title}_{author}{ext}"
        else:
            new_filename = f"{title}_{author}_{date_str}{ext}"
        new_path = os.path.join(os.path.dirname(current_path), new_filename)

        if new_path != current_path:
            try:
                shutil.move(current_path, new_path)
                Logger.info(f"Renamed to: {new_filename}")
                return new_path
            except Exception as e:
                Logger.error(f"Rename failed: {e}")

        return current_path
