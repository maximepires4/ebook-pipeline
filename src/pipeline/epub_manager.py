import os
import argparse
from typing import Optional, List, Any, Dict

from ebooklib import epub

from src.utils.isbn_utils import clean_isbn_string, extract_isbn_from_filename
from src.models import BookMetadata
from src.utils.logger import Logger


class EpubManager:
    """
    Manages reading and writing metadata for an EPUB file using EbookLib.
    It abstracts away the complexity of Dublin Core (DC) and custom OPF metadata.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.book = None

        try:
            # Attempt to read the EPUB file structure
            self.book = epub.read_epub(filepath)
        except Exception as e:
            # Log parsing errors (often due to DRM or corrupted ZIPs)
            Logger.error(f"Error reading EPUB: {e}")
            pass

    def get_raw_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extracts ALL metadata available in the OPF, including custom namespaces.
        Useful for debugging to see exactly what tags exist.
        """
        if not self.book:
            return {}
        raw_data: Dict[str, List[Dict[str, Any]]] = {}
        for namespace, name_dict in self.book.metadata.items():
            # Simplifies namespace URLs to prefixes (e.g., 'DC' or 'OPF')
            ns_prefix = namespace.split("/")[-1].split("#")[-1]
            if "elements/1.1" in namespace:
                ns_prefix = "DC"
            for name, items in name_dict.items():
                key = f"{ns_prefix}:{name}"
                raw_data[key] = []
                for value, attrs in items:
                    raw_data[key].append({"value": value, "attrs": attrs})
        return raw_data

    def get_curated_metadata(self) -> Optional[BookMetadata]:
        """
        Extracts essential metadata (Title, Author, ISBN, etc.) into a normalized structure.
        Implements fallback strategies for finding ISBNs (metadata vs filename).
        """
        if not self.book:
            return None

        # Basic Dublin Core fields
        titles = self.book.get_metadata("DC", "title")
        title = titles[0][0] if titles else "Unknown"
        creators = self.book.get_metadata("DC", "creator")
        author = creators[0][0] if creators else "Unknown"

        # ISBN Extraction Strategy:
        # 1. Look for 'identifier' tags with scheme="ISBN"
        # 2. Look for identifiers that look like ISBNs (10 or 13 digits, starting with 978/979)
        isbn = None
        identifiers = self.book.get_metadata("DC", "identifier")
        for value, attrs in identifiers:
            c_val = clean_isbn_string(value)
            scheme = ""
            for k, v in attrs.items():
                if "scheme" in k.lower():
                    scheme = v.lower()
                    break
            if "isbn" in scheme or (
                c_val.isdigit()
                and len(c_val) in [10, 13]
                and c_val.startswith(("978", "979", ""))
            ):
                if len(c_val) in [10, 13]:
                    isbn = c_val
                    break

        # Fallback: Check filename for ISBN pattern
        if not isbn:
            isbn = extract_isbn_from_filename(self.filename)

        publishers = self.book.get_metadata("DC", "publisher")
        publisher = publishers[0][0] if publishers else None

        langs = self.book.get_metadata("DC", "language")
        language = langs[0][0] if langs else None

        pub_dates = self.book.get_metadata("DC", "date")
        date = pub_dates[0][0] if pub_dates else None

        # Custom Metadata (Calibre Series)
        # These are stored in the default namespace, not Dublin Core
        series = None
        series_index = None

        for _, name_dict in self.book.metadata.items():
            for name, items in name_dict.items():
                if name == "series":
                    series = items[0][0]
                elif name == "series_index":
                    try:
                        if items and items[0][0] is not None:
                            series_index = float(items[0][0])
                    except (ValueError, TypeError):
                        pass

        subjects = []
        subj_items = self.book.get_metadata("DC", "subject")
        for s, _ in subj_items:
            subjects.append(s)

        return BookMetadata(
            filename=self.filename,
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            language=language,
            date=str(date) if date else None,
            series=series,
            series_index=series_index,
            tags=subjects,
        )

    def _clear_metadata(self, namespace, name):
        """Helper to remove specific metadata entries directly from the internal dict."""
        if namespace in self.book.metadata and name in self.book.metadata[namespace]:
            del self.book.metadata[namespace][name]

    def update_metadata(self, new_data: dict):
        """
        Overwrites existing metadata with new data from search results.
        Clears old Dublin Core entries first to avoid duplicates.
        """
        if not self.book:
            return

        # Explicitly clear old DC fields
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "title")
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "creator")
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "publisher")
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "date")
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "description")
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "subject")

        if new_data.get("title"):
            self.book.set_title(new_data["title"])

        authors = new_data.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]
        for auth in authors:
            self.book.add_author(auth)

        # Using add_metadata because set_metadata is not standard in EbookLib
        if new_data.get("publisher"):
            self.book.add_metadata("DC", "publisher", new_data["publisher"])

        if new_data.get("publishedDate"):
            self.book.add_metadata("DC", "date", new_data["publishedDate"])

        if new_data.get("description"):
            self.book.add_metadata("DC", "description", new_data["description"])

        if new_data.get("categories"):
            for tag in new_data["categories"]:
                self.book.add_metadata("DC", "subject", tag)

    def set_cover(self, image_data):
        """Sets the cover image. EbookLib handles the manifest item creation."""
        if not self.book or not image_data:
            return
        self.book.set_cover("cover.jpg", image_data)

    def save(self, output_path=None):
        """Writes the modified EPUB to disk."""
        if not self.book:
            return
        if not output_path:
            output_path = self.filepath
        epub.write_epub(output_path, self.book, {})


if __name__ == "__main__":
    from src.utils.formatter import Formatter

    parser = argparse.ArgumentParser(description="Standalone EPUB Metadata Inspector.")
    parser.add_argument("path", nargs="?", default="data", help="File path.")
    parser.add_argument("--full", action="store_true", help="Print raw metadata.")
    args = parser.parse_args()

    if os.path.isfile(args.path):
        Formatter.print_metadata(EpubManager(args.path), args.full)
    else:
        print("Invalid path or file not found.")
