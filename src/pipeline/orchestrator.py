import os
import shutil
import tempfile

from src import config

from src.pipeline.epub_manager import EpubManager
from src.pipeline.cover_manager import CoverManager
from src.pipeline.kepub_handler import KepubHandler
from src.pipeline.drive_uploader import DriveUploader

from src.utils.text_utils import sanitize_filename
from src.utils.logger import Logger
from src.utils.formatter import Formatter

from src.search.book_finder import find_book


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
    ):
        self.auto_save = auto_save
        self.enable_kepub = enable_kepub
        self.enable_rename = enable_rename
        self.interactive_fields = interactive_fields
        self.uploader = DriveUploader()

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
                Logger.error(f"Critical error processing {f}: {e}")
            print("-" * 60)

    def process_file(self, file_path):
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

            manager = EpubManager(working_path)
            if not manager.book:
                Logger.warning(f"Skipping (No Book): {filename}")
                return

            meta = manager.get_curated_metadata()
            if not meta:
                Logger.warning(f"Skipping (No Meta): {filename}")
                return

            Logger.info(
                f"Processing: {meta.get('title', 'Unknown')} ({filename})"
            )

            online_data, confidence, strategy, _ = find_book(meta)

            final_meta = meta
            current_path = working_path

            if online_data:
                Formatter.print_search_result(online_data, confidence, strategy, 1)

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
            else:
                Logger.warning(
                    "No online match. Using local metadata for pipeline.", indent=4
                )

            # --- 4. Renaming ---
            if self.enable_rename:
                current_path = self._handle_renaming(current_path, final_meta)

            # --- 5. Conversion ---
            if self.enable_kepub:
                current_path = self._handle_conversion(current_path)

            self.uploader.process_file(current_path)

    def _should_save(self, confidence):
        if self.auto_save or confidence >= 90:
            return True

        try:
            choice = (
                input(
                    f"   ? Low confidence ({confidence}%). Apply this metadata? [y/N]: "
                )
                .strip()
                .lower()
            )
            return choice == "y"
        except EOFError:
            return False

    def _review_metadata_changes(self, local_meta, remote_data):
        """
        Interactively asks the user to confirm each metadata field change.
        Returns a dict containing ONLY the approved changes.
        """
        print("\n   --- Interactive Metadata Review ---")
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

        for label, l_key, r_key in fields:
            local_val = clean(local_meta.get(l_key)).strip()
            remote_val = clean(remote_data.get(r_key)).strip()

            # Special date handling
            if label == "Date" and len(local_val) >= 4 and len(remote_val) >= 4:
                if local_val[:4] == remote_val[:4]:
                    continue

            if local_val != remote_val and remote_val:
                print(f"   [?] {label}:")
                print(f"      Current: {local_val}")
                print(f"      New:     {remote_val}")
                choice = input("      Apply change? [y/N]: ").strip().lower()
                if choice == "y":
                    approved[r_key] = remote_data[r_key]

        # Author (List vs String)
        local_auth = clean(local_meta.get("author"))
        remote_auths = remote_data.get("authors", [])
        remote_auth_str = (
            ", ".join(remote_auths)
            if isinstance(remote_auths, list) and remote_auths
            else str(remote_auths)
        )

        if local_auth != remote_auth_str and remote_auths:
            print("   [?] Author:")
            print(f"      Current: {local_auth}")
            print(f"      New:     {remote_auth_str}")
            choice = input("      Apply change? [y/N]: ").strip().lower()
            if choice == "y":
                approved["authors"] = remote_auths

        # Cover
        if remote_data.get("imageLinks"):
            print("   [?] Cover found online.")
            choice = input("      Download and update cover? [y/N]: ").strip().lower()
            if choice == "y":
                approved["imageLinks"] = remote_data["imageLinks"]

        print("   -----------------------------------")
        if not approved:
            Logger.info("   No changes applied.")
            return None

        return approved

    def _update_metadata(self, manager, online_data):
        Logger.info("Updating metadata...", indent=4)
        manager.update_metadata(online_data)

        if config.SHOW_COVER_LINK and online_data.get("imageLinks"):
            url = online_data["imageLinks"].get("thumbnail") or online_data[
                "imageLinks"
            ].get("smallThumbnail")
            if url:
                img_bytes = CoverManager.download_cover(url)
                processed_img = CoverManager.process_image(img_bytes)
                if processed_img:
                    manager.set_cover(processed_img)
                    Logger.success("Cover updated.", indent=4)

        manager.save()
        Logger.success("EPUB saved.", indent=4)

    def _get_updated_meta_dict(self, original_meta, online_data):
        new_meta = original_meta.copy()
        
        # Only update keys that are present in online_data (approved changes)
        if "title" in online_data:
            new_meta["title"] = online_data["title"]

        if "authors" in online_data:
            auths = online_data["authors"]
            new_meta["author"] = (
                auths[0] if isinstance(auths, list) and auths else str(auths)
            )

        if "publishedDate" in online_data:
            new_meta["date"] = online_data["publishedDate"]
            
        return new_meta

    def _handle_conversion(self, input_path):
        Logger.info("Converting to KEPUB...", indent=4)
        if not input_path.endswith(".kepub.epub"):
            kepub_path = input_path.replace(".epub", ".kepub.epub")
        else:
            kepub_path = input_path

        if KepubHandler.convert_to_kepub(input_path, kepub_path):
            return kepub_path
        else:
            Logger.warning("Conversion failed. Using standard EPUB.", indent=4)
            return input_path

    def _handle_renaming(self, current_path, meta):
        title = sanitize_filename(meta["title"])
        author = sanitize_filename(meta["author"])
        date_str = str(meta.get("date", ""))[:4]
        if not date_str or date_str == "None":
            date_str = "Unknown"

        if current_path.endswith(".kepub.epub"):
            ext = ".kepub.epub"
        else:
            ext = ".epub"

        new_filename = f"{title}-{author}-{date_str}{ext}"
        new_path = os.path.join(os.path.dirname(current_path), new_filename)

        if new_path != current_path:
            try:
                shutil.move(current_path, new_path)
                Logger.info(f"Renamed to: {new_filename}", indent=4)
                return new_path
            except Exception as e:
                Logger.error(f"Rename failed: {e}", indent=4)

        return current_path