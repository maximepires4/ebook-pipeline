from unittest.mock import MagicMock, patch

from epub_pipeline import config
from epub_pipeline.utils.formatter import Formatter
from epub_pipeline.utils.isbn_utils import is_valid_isbn
from epub_pipeline.utils.logger import Logger
from epub_pipeline.utils.text_utils import truncate


class TestLogger:
    def test_logger_methods(self, capsys):
        # Force config values
        config.VERBOSE = True
        config.FULL_OUTPUT = True

        Logger.info("Info message")
        Logger.verbose("Verbose message")
        Logger.success("Success message")
        Logger.warning("Warning message")
        Logger.error("Error message")
        Logger.full_json({"key": "value"})

        captured = capsys.readouterr()
        assert "Info message" in captured.out
        assert "Verbose message" in captured.out
        assert "Success message" in captured.out
        assert "Warning message" in captured.out
        assert "Error message" in captured.out
        assert '{"key": "value"}' in captured.out

    def test_logger_silent(self, capsys):
        config.VERBOSE = False
        config.FULL_OUTPUT = False

        Logger.verbose("Hidden")
        Logger.full_json({})

        captured = capsys.readouterr()
        assert "Hidden" not in captured.out


class TestFormatter:
    def test_print_metadata(self, capsys):
        mock_manager = MagicMock()
        mock_manager.filename = "test.epub"
        mock_manager.book = True
        mock_manager.get_curated_metadata.return_value = {
            "title": "Title",
            "authors": ["Author"],
            "isbn": "123",
            "publisher": "Pub",
            "language": "en",
            "date": "2023",
        }

        Formatter.print_metadata(mock_manager, full=False)
        captured = capsys.readouterr()
        assert "Title:     Title" in captured.out

        # Test full mode (raw metadata)
        mock_manager.get_raw_metadata.return_value = {"DC:title": [{"value": "Raw Title", "attrs": {}}]}
        Formatter.print_metadata(mock_manager, full=True)
        captured = capsys.readouterr()
        assert "Raw Title" in captured.out

    def test_print_search_result(self, capsys):
        data = {
            "title": "Found Book",
            "subtitle": "Sub",
            "authors": ["Auth"],
            "publisher": "Pub",
            "publishedDate": "2022",
            "categories": ["Fiction"],
            "description": "Long desc",
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "999"}],
            "imageLinks": {"thumbnail": "http://img.jpg"},
            "previewLink": "http://link",
        }
        # Enable all show flags
        with patch.multiple(
            config,
            SHOW_SUBTITLE=True,
            SHOW_DESCRIPTION=True,
            SHOW_CATEGORIES=True,
            SHOW_COVER_LINK=True,
            SHOW_LINKS=True,
            SHOW_IDENTIFIERS=True,
        ):
            Formatter.print_search_result(data, 90, "ISBN")

        captured = capsys.readouterr()
        assert "Found Book" in captured.out
        assert "90%" in captured.out
        assert "Sub" in captured.out
        assert "Fiction" in captured.out

    def test_print_comparison(self, capsys):
        local = {"title": "Old", "authors": ["OldAuth"]}
        remote = {"title": "New", "authors": ["NewAuth"]}
        Formatter.print_comparison(local, remote)
        captured = capsys.readouterr()
        assert "Old" in captured.out
        assert "New" in captured.out


class TestUtilsExtras:
    def test_truncate(self):
        assert truncate("hello", 3) == "hel..."
        assert truncate("hello", 10) == "hello"

    def test_isbn_edge_cases(self):
        assert is_valid_isbn(None) is False
        assert is_valid_isbn("123") is False
