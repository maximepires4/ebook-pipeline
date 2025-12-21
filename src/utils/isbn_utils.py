import re

def clean_isbn_string(value):
    """Nettoie une chaîne pour ne garder que les chiffres (et X pour ISBN-10)."""
    if not value:
        return ""
    # On nettoie d'abord en minuscule pour les préfixes "urn:isbn:"
    cleaned = value.lower().replace('urn:isbn:', '').replace('isbn:', '').replace('-', '').strip()
    # On retourne en MAJUSCULE pour garantir que 'x' devienne 'X'
    return cleaned.upper()

def extract_isbn_from_filename(filename):
    """Tente de trouver un ISBN dans le nom du fichier."""
    # ISBN-13 (978/979)
    isbn13_match = re.search(r'\b(97[89]\d{10})\b', filename)
    if isbn13_match:
        return isbn13_match.group(1)
    
    # ISBN-10
    isbn10_match = re.search(r'\b(\d{9}[\dX])\b', filename.upper())
    if isbn10_match:
        return isbn10_match.group(1).upper()
    
    return None

def is_valid_isbn(isbn):
    """Vérifie la validité mathématique (checksum) d'un ISBN-10 ou ISBN-13."""
    if not isbn:
        return False
        
    isbn = clean_isbn_string(isbn)
    
    if len(isbn) == 10:
        # Validation ISBN-10
        if not re.match(r'^\d{9}[\dX]$', isbn):
            return False
        total = 0
        for i in range(9):
            total += int(isbn[i]) * (10 - i)
        last = 10 if isbn[9] == 'X' else int(isbn[9])
        total += last
        return total % 11 == 0
        
    elif len(isbn) == 13:
        # Validation ISBN-13
        if not re.match(r'^\d{13}$', isbn):
            return False
        total = 0
        for i in range(12):
            val = int(isbn[i])
            total += val if i % 2 == 0 else val * 3
        check = (10 - (total % 10)) % 10
        return check == int(isbn[12])
        
    return False

def convert_isbn10_to_13(isbn10):
    """Convertit un ISBN-10 en ISBN-13 (format 978...)."""
    isbn10 = clean_isbn_string(isbn10)
    if len(isbn10) != 10:
        return None
        
    # On prend les 9 premiers chiffres et on ajoute 978 au début
    base = "978" + isbn10[:9]
    
    # Calcul du nouveau checksum ISBN-13
    total = 0
    for i in range(12):
        val = int(base[i])
        total += val if i % 2 == 0 else val * 3
    check = (10 - (total % 10)) % 10
    
    return base + str(check)
