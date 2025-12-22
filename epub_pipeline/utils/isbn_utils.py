import re


def clean_isbn_string(value):
    """
    Normalizes an ISBN string by removing common prefixes and separators.
    Example: "urn:isbn:978-0-123-456" -> "9780123456"
    """
    if not value:
        return ""
    cleaned = value.lower().replace("urn:isbn:", "").replace("isbn:", "").replace("-", "").strip()
    return cleaned.upper()


def extract_isbn_from_filename(filename):
    """
    Attempts to find an ISBN-like pattern in a filename.
    Prioritizes ISBN-13 over ISBN-10.
    """
    # TODO: Add support for ISBN-13 with hyphens

    # Regex for ISBN-13 (starts with 978 or 979, followed by 10 digits)
    isbn13_match = re.search(r"\b(97[89]\d{10})\b", filename)
    if isbn13_match:
        return isbn13_match.group(1)

    # Regex for ISBN-10 (9 digits followed by digit or X)
    isbn10_match = re.search(r"\b(\d{9}[\dX])\b", filename.upper())
    if isbn10_match:
        return isbn10_match.group(1).upper()

    return None


def is_valid_isbn(isbn):
    """
    Validates an ISBN (10 or 13) using checksum calculation.
    """
    if not isbn:
        return False

    isbn = clean_isbn_string(isbn)

    if len(isbn) == 10:
        if not re.match(r"^\d{9}[\dX]$", isbn):
            return False
        total = 0
        for i in range(9):
            total += int(isbn[i]) * (10 - i)
        last = 10 if isbn[9] == "X" else int(isbn[9])
        total += last
        return total % 11 == 0

    elif len(isbn) == 13:
        if not re.match(r"^\d{13}$", isbn):
            return False
        total = 0
        for i in range(12):
            val = int(isbn[i])
            total += val if i % 2 == 0 else val * 3
        check = (10 - (total % 10)) % 10
        return check == int(isbn[12])

    return False


def convert_isbn10_to_13(isbn10):
    """
    Converts a valid ISBN-10 to its ISBN-13 equivalent (prefix 978).
    Recalculates the checksum digit.
    """
    isbn10 = clean_isbn_string(isbn10)
    if len(isbn10) != 10:
        return None

    base = "978" + isbn10[:9]

    total = 0
    for i in range(12):
        val = int(base[i])
        total += val if i % 2 == 0 else val * 3
    check = (10 - (total % 10)) % 10

    return base + str(check)
