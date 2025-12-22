from unittest.mock import MagicMock, patch

from epub_pipeline.pipeline.cover_manager import CoverManager
from epub_pipeline.pipeline.kepub_handler import KepubHandler


class TestCoverManager:
    @patch("epub_pipeline.pipeline.cover_manager.requests.get")
    def test_download_cover_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"fake_image_data"

        data = CoverManager.download_cover("http://test.com/img.jpg")
        assert data == b"fake_image_data"

    @patch("epub_pipeline.pipeline.cover_manager.requests.get")
    def test_download_cover_failure(self, mock_get):
        mock_get.side_effect = Exception("Boom")
        assert CoverManager.download_cover("http://fail") is None
        assert CoverManager.download_cover(None) is None

    @patch("epub_pipeline.pipeline.cover_manager.Image.open")
    def test_process_image(self, mock_open):
        # Mock PIL Image object
        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_img.width = 3000
        mock_img.height = 4000
        mock_open.return_value = mock_img

        # Simulate convert/save
        mock_img.convert.return_value = mock_img

        res = CoverManager.process_image(b"input")

        mock_img.convert.assert_called_with("RGB")
        mock_img.thumbnail.assert_called()  # Should resize
        assert res is not None  # Returns bytes from BytesIO

    def test_process_image_none(self):
        assert CoverManager.process_image(None) is None


class TestKepubHandler:
    @patch("shutil.which")
    def test_get_binary_path(self, mock_which):
        mock_which.return_value = "/usr/bin/kepubify"
        assert KepubHandler.get_binary_path() == "/usr/bin/kepubify"

    @patch("epub_pipeline.pipeline.kepub_handler.subprocess.run")
    @patch("epub_pipeline.pipeline.kepub_handler.KepubHandler.get_binary_path")
    def test_convert_success(self, mock_path, mock_run):
        mock_path.return_value = "kepubify"

        # Success case
        assert KepubHandler.convert_to_kepub("book.epub") is True
        mock_run.assert_called_once()

        # Already kepub
        assert KepubHandler.convert_to_kepub("book.kepub.epub") is True

    @patch("epub_pipeline.pipeline.kepub_handler.subprocess.run")
    @patch("epub_pipeline.pipeline.kepub_handler.KepubHandler.get_binary_path")
    def test_convert_failure(self, mock_path, mock_run):
        mock_path.return_value = "kepubify"
        mock_run.side_effect = Exception("Fail")
        assert KepubHandler.convert_to_kepub("book.epub") is False

    @patch("epub_pipeline.pipeline.kepub_handler.KepubHandler.get_binary_path")
    def test_convert_no_binary(self, mock_path):
        mock_path.return_value = None
        assert KepubHandler.convert_to_kepub("book.epub") is False
