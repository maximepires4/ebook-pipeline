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
            Logger.warning(
                f"Standard parsing failed ({e}). Switching to filename fallback."
            )
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
            return self._extract_from_filename()

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

    def _extract_from_filename(self) -> BookMetadata:
        """
        Fallback parser for filenames formatted like:
        'Title -- Author -- Series -- Publisher -- ISBN -- ... .epub'
        """
        # Remove extension
        name = os.path.splitext(self.filename)[0]

        # Split by ' -- ' (standard Calibre export format?)
        parts = name.split(" -- ")

        title = parts[0] if len(parts) > 0 else "Unknown"
        author = parts[1] if len(parts) > 1 else "Unknown"

        # Clean up Author (Surname, Name -> Name Surname if needed, or keep as is)
        # Here we just take the first part of "Surname, Name" if it looks like that
        if ";" in author:
            author = author.split(";")[0].strip()

        isbn = extract_isbn_from_filename(self.filename)

        # Try to guess other fields based on position if standard format
        # This is a best-effort guess
        publisher = parts[3] if len(parts) > 3 else None

        return BookMetadata(
            filename=self.filename,
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            language=None,
            date=None,
            series=None,
            series_index=None,
            tags=[],
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
        self._clear_metadata("http://purl.org/dc/elements/1.1/", "language")
        self._clear_metadata(
            "http://purl.org/dc/elements/1.1/", "identifier"
        )  # Careful with ID

        # 1. Title
        if new_data.get("title"):
            self.book.set_title(new_data["title"])

        # 2. Authors (with Sort Name)
        authors = new_data.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]

        for auth in authors:
            sort_name = format_author_sort(auth)
            # Add author with file-as attribute for proper sorting
            self.book.add_author(auth, file_as=sort_name, role="aut")

        # 3. Publisher
        if new_data.get("publisher"):
            self.book.add_metadata("DC", "publisher", new_data["publisher"])

        # 4. Date
        if new_data.get("publishedDate"):
            self.book.add_metadata("DC", "date", new_data["publishedDate"])

        # 5. Language
        if new_data.get("language"):
            self.book.set_language(new_data["language"])

        # 6. Description
        if new_data.get("description"):
            self.book.add_metadata("DC", "description", new_data["description"])

        # 7. Tags / Subjects
        if new_data.get("categories"):
            for tag in new_data["categories"]:
                self.book.add_metadata("DC", "subject", tag)

        # 8. ISBN / Identifier
        # We try to extract ISBN-13 from industryIdentifiers
        if new_data.get("industryIdentifiers"):
            for ident in new_data["industryIdentifiers"]:
                # Google Books format: {'type': 'ISBN_13', 'identifier': '...'}
                if ident.get("type") == "ISBN_13":
                    self.book.set_identifier(ident["identifier"])
                    break

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
