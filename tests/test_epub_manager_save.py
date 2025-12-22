from unittest.mock import MagicMock

from epub_pipeline.pipeline.epub_manager import EpubManager


def test_save_metadata_cleanup(mocker):
    mocker.patch("ebooklib.epub.read_epub")
    mock_write = mocker.patch("ebooklib.epub.write_epub")

    manager = EpubManager("test.epub")
    manager.book = MagicMock()

    # Simulate messy metadata (calibre junk)
    manager.book.metadata = {
        "http://purl.org/dc/elements/1.1/": {"title": [("T", {})]},
        "http://calibre.kovidgoyal.net/2009/metadata": {"series": [("S", {})]},
        "http://www.idpf.org/2007/opf": {
            "meta": [
                ("value", {"name": "calibre:timestamp"}),
                (None, {"name": "calibre:rating"}),
            ]
        },
    }

    manager.save("output.epub")

    # Verify cleanup logic
    # Calibre namespace should be removed
    assert "http://calibre.kovidgoyal.net/2009/metadata" not in manager.book.metadata

    # Verify write called
    mock_write.assert_called_with("output.epub", manager.book, {})
