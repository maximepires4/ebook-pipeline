from unittest.mock import MagicMock

from epub_pipeline.pipeline.epub_manager import EpubManager


def test_update_metadata_logic(mocker):
    # Mock ebooklib
    mocker.patch("ebooklib.epub.read_epub")

    manager = EpubManager("test.epub")
    manager.book = MagicMock()
    # Helper to simulate metadata dict
    manager.book.metadata = {"http://purl.org/dc/elements/1.1/": {}}

    # New data to apply
    new_data = {
        "title": "New Title",
        "authors": ["New Author"],
        "description": "New Desc",
        "categories": ["SciFi"],
        "industryIdentifiers": [{"type": "ISBN_13", "identifier": "999999"}],
    }

    manager.update_metadata(new_data)

    # Verify calls
    manager.book.set_title.assert_called_with("New Title")
    manager.book.add_author.assert_called()
    manager.book.set_language.assert_not_called()  # Not provided

    # Check if add_metadata was called for description
    manager.book.add_metadata.assert_any_call("DC", "description", "New Desc")
    # Check if add_metadata was called for subject
    manager.book.add_metadata.assert_any_call("DC", "subject", "SciFi")
    # Check ISBN addition
    manager.book.add_metadata.assert_any_call("DC", "identifier", "999999", {"scheme": "ISBN"})
