from unittest.mock import MagicMock

from epub_pipeline.search.book_finder import find_book
from epub_pipeline.search.providers.google import GoogleBooksProvider


def test_find_book_waterfall_fallback(mocker):
    # Setup providers: Google fails, but we want to check if it tries different strategies
    # Logic in find_book:
    # 1. ISBN Search (Priority 1)
    # 2. Text Search (Priority 2) with various relaxations

    # Mock get_providers to return a controllable mock provider
    mock_provider = MagicMock(spec=GoogleBooksProvider)
    mock_provider.name = "MockProvider"

    # Scenario: ISBN fails, Text search succeeds on second attempt
    mock_provider.get_by_isbn.return_value = (None, 0)

    # search_by_text side effects:
    # 1. Full context -> None
    # 2. No publisher -> Match!
    mock_provider.search_by_text.side_effect = [
        (None, 0),
        ({"title": "Found", "authors": ["Me"]}, 1),
    ]

    mocker.patch("epub_pipeline.search.book_finder.get_providers", return_value=[mock_provider])

    meta = {"title": "Test", "author": "Me", "isbn": "978123"}

    result, conf, strategy = find_book(meta)

    assert result["title"] == "Found"
    assert "Text MockProvider" in strategy
    # Ensure ISBN was called
    mock_provider.get_by_isbn.assert_called()
    # Ensure text search was called multiple times
    assert mock_provider.search_by_text.call_count == 2
