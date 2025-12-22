from unittest.mock import patch

import pytest

from epub_pipeline.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def orch():
    # Disable upload for test
    return PipelineOrchestrator(auto_save=True, enable_upload=False)


@patch("epub_pipeline.pipeline.orchestrator.EpubManager")
@patch("epub_pipeline.pipeline.orchestrator.find_book")
@patch("epub_pipeline.pipeline.orchestrator.shutil")
@patch("epub_pipeline.pipeline.orchestrator.tempfile")
@patch("epub_pipeline.pipeline.orchestrator.os")
def test_process_file_flow(mock_os, mock_temp, mock_shutil, mock_find, mock_epub_cls, orch):
    # Setup mocks
    mock_os.path.exists.return_value = True
    mock_os.path.basename.return_value = "book.epub"
    mock_os.path.dirname.return_value = "/tmp"

    # Mock join to return a simple string (MagicMocks as path components break things)
    def side_effect_join(*args):
        return "/".join(map(str, args))

    mock_os.path.join.side_effect = side_effect_join

    # Context manager for tempfile
    mock_temp.TemporaryDirectory.return_value.__enter__.return_value = "/tmp/tmpdir"

    # EpubManager setup
    manager = mock_epub_cls.return_value
    manager.get_curated_metadata.return_value = {
        "title": "Title",
        "author": "Author",
        "isbn": "123",
        "date": "2023-01-01",
    }

    # Search setup: Found match!
    mock_find.return_value = ({"title": "New Title", "authors": ["New A"]}, 90, "ISBN")

    # Run
    # Patch KepubHandler to return True (success) and return a new path
    with patch(
        "epub_pipeline.pipeline.orchestrator.KepubHandler.convert_to_kepub",
        return_value=True,
    ):
        # Patch sanitize to be safe
        with patch(
            "epub_pipeline.pipeline.orchestrator.sanitize_filename",
            side_effect=lambda x: x.lower().replace(" ", "_"),
        ):
            orch.process_file("/data/book.epub")

    # Assertions
    # 1. Metadata updated
    manager.update_metadata.assert_called()
    manager.save.assert_called()

    # 2. Renaming
    # Should be called. The filename changes from book.epub to title_author_2023.kepub.epub
    mock_shutil.move.assert_called()


def test_should_save_logic():
    orch = PipelineOrchestrator(auto_save=False)
    assert orch._should_save(90) is True
    with patch("builtins.input", return_value="y"):
        assert orch._should_save(30) is True
    with patch("builtins.input", return_value="n"):
        assert orch._should_save(30) is False


def test_interactive_review(orch):
    orch.interactive_fields = True
    local = {"title": "Old"}
    remote = {"title": "New", "authors": ["NewAuth"]}
    with patch("builtins.input", side_effect=["y", "y"]):
        approved = orch._review_metadata_changes(local, remote)
        assert approved["title"] == "New"
        assert approved["authors"] == ["NewAuth"]
    with patch("builtins.input", side_effect=["n", "n"]):
        approved = orch._review_metadata_changes(local, remote)
        assert approved is None


def test_process_directory(orch):
    with patch(
        "epub_pipeline.pipeline.orchestrator.os.listdir",
        return_value=["a.epub", "b.txt"],
    ):
        with patch("epub_pipeline.pipeline.orchestrator.os.path.exists", return_value=True):
            with patch.object(orch, "process_file") as mock_process:
                orch.process_directory("/data")
                mock_process.assert_called_once()
