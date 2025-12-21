from src.utils.text_utils import get_similarity

class ConfidenceScorer:
    @staticmethod
    def calculate(search_type, local_meta, remote_meta, total_results):
        """
        Orchestre le calcul du score de confiance.
        """
        score = 0
        reasons = []

        # 1. Score de base selon la méthode
        base_score, base_reason = ConfidenceScorer._get_base_score(search_type)
        score += base_score
        reasons.append(base_reason)

        # 2. Similarité du Titre
        title_score, title_reason = ConfidenceScorer._score_title(
            local_meta.get('title', ''), 
            remote_meta.get('title', ''),
            is_isbn=(search_type == "ISBN")
        )
        score += title_score
        reasons.append(title_reason)

        # 3. Similarité de l'Auteur
        author_score, author_reason = ConfidenceScorer._score_author(
            local_meta.get('author', ''),
            remote_meta.get('authors', []),
            is_isbn=(search_type == "ISBN")
        )
        score += author_score
        reasons.append(author_reason)

        # 4. Unicité et Volume de résultats
        uniqueness_score, uniqueness_reason = ConfidenceScorer._score_uniqueness(
            total_results, 
            is_isbn=(search_type == "ISBN")
        )
        score += uniqueness_score
        reasons.append(uniqueness_reason)

        return max(0, min(100, score)), reasons

    @staticmethod
    def _get_base_score(search_type):
        if search_type == "ISBN":
            return 90, "Matched via ISBN (+90)"
        return 0, "Matched via Text Search (Start at 0)"

    @staticmethod
    def _score_title(local, remote, is_isbn):
        sim = get_similarity(local, remote)
        if is_isbn:
            if sim < 0.2:
                return -40, f"Title Mismatch (-40)"
            return 0, "Title match validated"
        else:
            points = int(sim * 50)
            return points, f"Title Similarity {int(sim*100)}% (+{points})"

    @staticmethod
    def _score_author(local, remote_list, is_isbn):
        best_sim = 0
        for r_auth in remote_list:
            s = get_similarity(local, r_auth)
            if s > best_sim:
                best_sim = s
        
        if is_isbn:
            return 0, "Author match validated" # ISBN fait foi
        else:
            points = int(best_sim * 40)
            return points, f"Author Similarity {int(best_sim*100)}% (+{points})"

    @staticmethod
    def _score_uniqueness(total_results, is_isbn):
        if total_results == 1:
            return 10, "Unique result (+10)"
        if total_results > 100 and not is_isbn:
            return -10, "Ambiguous results (-10)"
        return 0, ""

# Alias pour compatibilité avec le code existant
def calculate_confidence(*args, **kwargs):
    return ConfidenceScorer.calculate(*args, **kwargs)