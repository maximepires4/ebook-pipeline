import pytest

from epub_pipeline.search.providers.google import GoogleBooksProvider


class TestGoogleBooksProvider:
    @pytest.fixture
    def provider(self):
        return GoogleBooksProvider()

    def test_get_by_isbn_found(self, provider, requests_mock):
        isbn = "9780441172719"
        mock_response = {
            "totalItems": 1,
            "items": [
                {
                    "id": "123",
                    "volumeInfo": {
                        "title": "Dune",
                        "authors": ["Frank Herbert"],
                        "publishedDate": "1965",
                        "industryIdentifiers": [{"type": "ISBN_13", "identifier": isbn}],
                    },
                }
            ],
        }

        requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=mock_response)

        result, total = provider.get_by_isbn(isbn)
        assert result is not None
        assert result["title"] == "Dune"
        assert result["authors"] == ["Frank Herbert"]
        assert total == 1

    def test_get_by_isbn_not_found(self, provider, requests_mock):
        requests_mock.get("https://www.googleapis.com/books/v1/volumes", json={"totalItems": 0})
        result, total = provider.get_by_isbn("0000000000")
        assert result is None
        assert total == 0

    def test_search_by_text(self, provider, requests_mock):
        meta = {"title": "Dune", "authors": ["Frank Herbert"]}
        context = {"pub": False, "year": False}

        mock_response = {
            "totalItems": 10,
            "items": [{"volumeInfo": {"title": "Dune", "authors": ["Frank Herbert"]}}],
        }

        requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=mock_response)

        result, total = provider.search_by_text(meta, context)
        assert result["title"] == "Dune"
        assert total == 10
