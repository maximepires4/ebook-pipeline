from epub_pipeline.search.confidence import ConfidenceScorer


class TestConfidenceScorer:
    def test_perfect_isbn_match(self):
        local = {"isbn": "9781234567890", "title": "Test Book", "author": "John Doe"}
        remote = {
            "title": "Test Book",
            "authors": ["John Doe"],
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9781234567890"}],
        }
        score, reasons = ConfidenceScorer.calculate("ISBN", local, remote, 1)

        # Expect high score: 100 base (ISBN) + matches
        assert score == 100
        assert "Matched via ISBN" in reasons[0]

    def test_text_match_high_confidence(self):
        local = {"title": "The Hobbit", "author": "J.R.R. Tolkien"}
        remote = {"title": "The Hobbit", "authors": ["J.R.R. Tolkien"]}

        # Text search (0 base) + Title (50) + Author (40) + Unique (10) = 100
        score, _ = ConfidenceScorer.calculate("Text", local, remote, 1)
        assert score == 100

    def test_text_match_low_confidence(self):
        local = {"title": "Hobbit", "author": "Tolkien"}
        remote = {"title": "The Lord of the Rings", "authors": ["J.R.R. Tolkien"]}

        # Title mismatch penalizes heavily
        score, reasons = ConfidenceScorer.calculate("Text", local, remote, 1)
        assert score < 60

    def test_ambiguous_results(self):
        local = {"title": "History", "author": "Unknown"}
        remote = {"title": "A History", "authors": ["Someone"]}

        # 1000 results -> -10 penalty
        score, reasons = ConfidenceScorer.calculate("Text", local, remote, 1000)
        assert any("Ambiguous" in r for r in reasons)
        assert score < 50
