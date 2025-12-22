import pytest

from epub_pipeline.search.providers.openlibrary import OpenLibraryProvider


class TestOpenLibrary:
    @pytest.fixture
    def provider(self):
        return OpenLibraryProvider()

    def test_get_by_isbn(self, provider, requests_mock):
        isbn = "978123"
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"

        # Success
        requests_mock.get(
            url,
            json={
                f"ISBN:{isbn}": {
                    "title": "OL Book",
                    "authors": [{"name": "OL Auth"}],
                    "publishers": [{"name": "OL Pub"}],
                    "publish_date": "2020",
                    "identifiers": {"isbn_13": ["978123"]},
                    "cover": {"medium": "url"},
                }
            },
        )
        res, hits = provider.get_by_isbn(isbn)
        assert res["title"] == "OL Book"
        assert hits == 1

        # Not found / Empty
        requests_mock.get(url, json={})
        res, hits = provider.get_by_isbn(isbn)
        assert res is None

    def test_search_by_text(self, provider, requests_mock):
        meta = {"title": "Dune", "author": "Herbert", "publisher": "Ace"}
        # Search by title + author + pub
        requests_mock.get(
            "https://openlibrary.org/search.json",
            json={
                "numFound": 5,
                "docs": [
                    {
                        "title": "Dune",
                        "author_name": ["Frank Herbert"],
                        "first_publish_year": 1965,
                        "cover_i": 12345,
                        "key": "/works/OL123",
                    }
                ],
            },
        )

        res, hits = provider.search_by_text(meta, {"pub": True})
        assert res["title"] == "Dune"
        assert res["imageLinks"]["thumbnail"] is not None
        assert hits == 5

    def test_search_errors(self, provider, requests_mock):
        requests_mock.get("https://openlibrary.org/search.json", status_code=500)
        res, _ = provider.search_by_text({"title": "A"}, {})
        assert res is None
