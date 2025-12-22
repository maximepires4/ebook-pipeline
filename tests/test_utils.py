from epub_pipeline.utils.isbn_utils import (
    clean_isbn_string,
    convert_isbn10_to_13,
    extract_isbn_from_filename,
    is_valid_isbn,
)
from epub_pipeline.utils.text_utils import (
    format_author_sort,
    get_similarity,
    sanitize_filename,
)


class TestIsbnUtils:
    def test_clean_isbn(self):
        assert clean_isbn_string("ISBN: 978-0-123") == "9780123"
        assert clean_isbn_string("urn:isbn:9780123") == "9780123"
        assert clean_isbn_string("978-0-12-345678-9") == "9780123456789"

    def test_is_valid_isbn10(self):
        # The Catcher in the Rye
        assert is_valid_isbn("0316769487") is True
        # Invalid checksum
        assert is_valid_isbn("0316769480") is False

    def test_is_valid_isbn13(self):
        # Dune
        assert is_valid_isbn("9780441172719") is True
        # Invalid
        assert is_valid_isbn("9780441172710") is False

    def test_convert_10_to_13(self):
        # 0316769487 -> 9780316769488
        isbn13 = convert_isbn10_to_13("0316769487")
        assert isbn13 == "9780316769488"
        assert is_valid_isbn(isbn13)

    def test_extract_from_filename(self):
        fname = "Dune - Frank Herbert - 9780441172719.epub"
        assert extract_isbn_from_filename(fname) == "9780441172719"

        fname_junk = "My Book 12345.epub"
        assert extract_isbn_from_filename(fname_junk) is None


class TestTextUtils:
    def test_sanitize_filename(self):
        assert sanitize_filename("L'Étranger") == "letranger"
        assert sanitize_filename("Dune: Messiah") == "dune-messiah"
        assert sanitize_filename("  A   B  ") == "a-b"

    def test_get_similarity(self):
        assert get_similarity("Dune", "Dune") == 1.0
        assert get_similarity("Dune", "dune") == 1.0
        assert get_similarity("Harry Potter", "Barry Trotter") > 0.5
        assert get_similarity("A", "Z") == 0.0

    def test_format_author_sort(self):
        assert format_author_sort("Frank Herbert") == "Herbert, Frank"
        assert format_author_sort("Cher") == "Cher"
        assert format_author_sort("Victor Marie Hugo") == "Hugo, Victor Marie"
