import os
import argparse
import warnings
from typing import Optional, List, Any, Dict

from src.utils.isbn_utils import clean_isbn_string, extract_isbn_from_filename
from src.utils.text_utils import format_author_sort
from src.models import BookMetadata
from src.utils.logger import Logger

# Suppress annoying ebooklib warnings
# Must be done BEFORE importing ebooklib
warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib")
warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib")

from ebooklib import epub  # type: ignore  # noqa: E402


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
            Logger.error(f"Standard parsing failed ({e}).")
            raise e

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
            print(f"HERE scheme: {scheme}")
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
            tags=subjects,
        )

    def _clear_metadata(self, namespace, name):
        """Helper to remove specific metadata entries directly from the internal dict."""
        if namespace in self.book.metadata and name in self.book.metadata[namespace]:
            del self.book.metadata[namespace][name]

    def update_metadata(self, new_data: dict):
        """
        Overwrites existing metadata with new data from search results.
        Clears old Dublin Core entries ONLY if new data is available to replace them.
        """
        if not self.book:
            return

        # 1. Title (Mandatory)
        if new_data.get("title"):
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "title")
            self.book.set_title(new_data["title"])

        # 2. Authors (Mandatory)
        authors = new_data.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]
        if authors:
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "creator")
            for auth in authors:
                sort_name = format_author_sort(auth)
                self.book.add_author(auth, file_as=sort_name, role="aut")

        # 3. Publisher
        if new_data.get("publisher"):
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "publisher")
            self.book.add_metadata("DC", "publisher", new_data["publisher"])

        # 4. Date
        if new_data.get("publishedDate"):
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "date")
            self.book.add_metadata("DC", "date", new_data["publishedDate"])

        # 5. Language
        if new_data.get("language"):
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "language")
            self.book.set_language(new_data["language"])

        # 6. Description
        if new_data.get("description"):
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "description")
            self.book.add_metadata("DC", "description", new_data["description"])

        # 7. Tags / Subjects
        if new_data.get("categories"):
            self._clear_metadata("http://purl.org/dc/elements/1.1/", "subject")
            for tag in new_data["categories"]:
                self.book.add_metadata("DC", "subject", tag)

        # 8. ISBN / Identifier
        # Strategy: Add new ISBNs but DO NOT delete the primary unique identifier
        # to avoid breaking the OPF structure (which causes "Document is empty").
        if new_data.get("industryIdentifiers"):
            for ident in new_data["industryIdentifiers"]:
                if ident.get("type") == "ISBN_13":
                    # Check if this ISBN already exists to avoid duplicates
                    current_ids = self.book.get_metadata("DC", "identifier")
                    exists = False
                    for val, attr in current_ids:
                        if val == ident["identifier"]:
                            exists = True
                            break

                    if not exists:
                        # Add as a new identifier with scheme attribute
                        self.book.add_metadata(
                            "DC", "identifier", ident["identifier"], {"scheme": "ISBN"}
                        )
                    break  # Only add the first ISBN-13 found

    def set_cover(self, image_data):
        """Sets the cover image. EbookLib handles the manifest item creation."""
        if not self.book or not image_data:
            return
        self.book.set_cover("cover.jpg", image_data)

    def save(self, output_path=None):
        """Writes the modified EPUB to disk with safe metadata cleanup."""
        if not self.book:
            return
        if not output_path:
            output_path = self.filepath

        # Cleanup problematic custom metadata
        for ns in list(self.book.metadata.keys()):
            if not ns:
                continue

            # 1. Cleanup by namespace string
            if "user_metadata" in ns or "calibre" in ns.lower():
                del self.book.metadata[ns]
                continue

            # 2. Cleanup individual keys and safely filter values
            keys_to_del = []
            for key, items in self.book.metadata[ns].items():
                if key and ("user_metadata" in key or "calibre" in key.lower()):
                    keys_to_del.append(key)
                    continue

                new_items = []
                for val, attrs in items:
                    # Keep if value is present OR if attributes are present (important for cover meta)
                    if val is not None or (attrs and len(attrs) > 0):
                        # Ensure attributes don't contain None values
                        clean_attrs = {}
                        if isinstance(attrs, dict):
                            for ak, av in attrs.items():
                                if ak is not None and av is not None:
                                    clean_attrs[ak] = av
                        new_items.append((val, clean_attrs))

                if not new_items:
                    keys_to_del.append(key)
                else:
                    self.book.metadata[ns][key] = new_items

            for k in keys_to_del:
                del self.book.metadata[ns][k]

        try:
            epub.write_epub(output_path, self.book, {})
        except Exception as e:
            Logger.error(f"Failed to write EPUB: {e}")
            raise e


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
