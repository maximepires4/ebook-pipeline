from unittest.mock import patch

from epub_pipeline import config
from epub_pipeline.cli import main


def test_cli_file(mocker):
    test_args = ["epubpipe", "book.epub", "-v", "--no-upload"]
    with patch("sys.argv", test_args):
        with patch("epub_pipeline.cli.PipelineOrchestrator") as mock_cls:
            with patch("os.path.isfile", return_value=True):
                main()

                # Check config
                assert config.VERBOSE is True

                # Check Orchestrator init
                mock_cls.assert_called_once()
                args, kwargs = mock_cls.call_args
                assert kwargs["enable_upload"] is False

                # Check execution
                mock_cls.return_value.process_file.assert_called_with("book.epub", forced_isbn=None)


def test_cli_directory(mocker):
    test_args = ["epubpipe", "data/", "--auto"]
    with patch("sys.argv", test_args):
        with patch("epub_pipeline.cli.PipelineOrchestrator") as mock_cls:
            with patch("os.path.isfile", return_value=False):
                with patch("os.path.isdir", return_value=True):
                    main()
                    mock_cls.return_value.process_directory.assert_called_with("data/")


def test_cli_error(mocker):
    # Test file not found
    with patch("sys.argv", ["epubpipe", "ghost.epub"]):
        with patch("os.path.isfile", return_value=False):
            with patch("os.path.isdir", return_value=False):
                with patch("epub_pipeline.cli.Logger.error") as mock_err:
                    main()
                    mock_err.assert_called()
