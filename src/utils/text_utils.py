import difflib
import re
import unicodedata


def get_similarity(s1, s2):
    """
    Calculates the Levenshtein similarity ratio between two strings.
    Returns a float between 0.0 (no match) and 1.0 (perfect match).
    Case-insensitive.
    """
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def sanitize_filename(value):
    """
    Converts a string into a safe filename:
    1. Normalizes unicode characters (e.g., é -> e).
    2. Removes non-alphanumeric characters (except - and _).
    3. Replaces whitespace with hyphens.
    4. Converts to lowercase.

    Example: "L'Étranger!" -> "letranger"
    """
    if not value:
        return "Unknown"

    # Normalize unicode to ASCII (NFD split -> drop non-spacing mark)
    value = (
        unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode("ascii")
    )

    # Remove unwanted characters (keep alphanumeric, space, hyphen)
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    # Replace spaces (including tabs, non-breaking) and multiple hyphens with single hyphen
    value = re.sub(r"[-\s]+", "-", value)
    
    # Final safety check to remove any remaining spaces
    return value.replace(" ", "-")


def format_author_sort(author_name):
    """
    Converts 'First Last' to 'Last, First' for sorting purposes.
    Simple heuristic: assumes the last word is the surname.
    """
    if not author_name or "," in author_name:
        return author_name

    parts = author_name.strip().split()
    if len(parts) > 1:
        # "Frank Herbert" -> "Herbert, Frank"
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return author_name
