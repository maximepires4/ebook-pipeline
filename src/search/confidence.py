from src.utils.text_utils import get_similarity


class ConfidenceScorer:
    """
    Calculates a confidence score (0-100) representing how likely a search result
    matches the input metadata.

    The score is based on:
    1. Strategy used (ISBN matches start high).
    2. Text similarity (Levenshtein ratio) for Title and Author.
    3. Result uniqueness (penalizes common terms with thousands of hits).
    """

    @staticmethod
    def calculate(search_type, local_meta, remote_meta, total_results):
        score = 0
        reasons = []
        is_isbn = search_type == "ISBN"

        # 1. Base Score (Strategy)
        base_score, base_reason = ConfidenceScorer._get_base_score(search_type)
        score += base_score
        reasons.append(base_reason)

        # 2. Title Similarity
        title_score, title_reason = ConfidenceScorer._score_title(
            local_meta.get("title", ""),
            remote_meta.get("title", ""),
            is_isbn=is_isbn,
        )
        score += title_score
        reasons.append(title_reason)

        # 3. Author Similarity
        # TODO: check multiple authors
        print("HERE -- check multiple authors", local_meta.get("author", ""))
        author_score, author_reason = ConfidenceScorer._score_author(
            local_meta.get("author", ""),
            remote_meta.get("authors", []),
            is_isbn=is_isbn,
        )
        score += author_score
        reasons.append(author_reason)

        # 4. Uniqueness / Ambiguity
        if not is_isbn:
            uniqueness_score, uniqueness_reason = ConfidenceScorer._score_uniqueness(
                total_results
            )
            score += uniqueness_score
            reasons.append(uniqueness_reason)

        # Clamp between 0 and 100
        return max(0, min(100, score)), reasons

    @staticmethod
    def _get_base_score(search_type):
        if search_type == "ISBN":
            return 100, "Matched via ISBN (+90)"
        return 0, "Matched via Text Search (0)"

    @staticmethod
    def _score_title(local, remote, is_isbn):
        sim = get_similarity(local, remote)
        if is_isbn:
            # Even with ISBN, if title is completely different, it's suspicious (bad metadata on provider side)
            if sim < 0.2:
                return -40, "Title mismatch (-40)"
            return 0, "Title match validated"
        else:
            # For text search, title similarity contributes up to 50 points
            points = int(sim * 50)
            return points, f"Title Similarity {int(sim * 100)}% (+{points})"

    @staticmethod
    def _score_author(local, remote_list, is_isbn):
        # Check against all authors listed in the remote result
        best_sim = 0
        for r_auth in remote_list:
            s = get_similarity(local, r_auth)
            if s > best_sim:
                best_sim = s

        if is_isbn:
            # Even with ISBN, if author is completely different, it's suspicious (bad metadata on provider side)
            if best_sim < 0.2:
                return -40, "Author mismatch (-40)"
            return 0, "Author match validated"
        else:
            # For text search, author similarity contributes up to 40 points
            points = int(best_sim * 40)
            return points, f"Author Similarity {int(best_sim * 100)}% (+{points})"

    @staticmethod
    def _score_uniqueness(total_results):
        # If we find exactly one result, it's a strong signal
        if total_results == 1:
            return 10, "Unique result (+10)"
        # If we find thousands of results for a text search, it's likely a generic match
        if total_results > 100:
            return -10, "Ambiguous results (-10)"
        return 0, ""
