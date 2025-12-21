import difflib
import re
import unicodedata

def get_similarity(s1, s2):
    """Calcule la similarité entre deux chaînes (0.0 à 1.0)."""
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def sanitize_filename(value):
    """
    Nettoie une chaîne pour qu'elle soit utilisable comme nom de fichier.
    Remplace les caractères interdits et supprime les accents.
    """
    if not value:
        return "Unknown"
    
    # Normalisation Unicode (NFD pour séparer les accents)
    value = unicodedata.normalize('NFD', value).encode('ascii', 'ignore').decode('ascii')
    
    # Remplacement des caractères non-alphanumériques (sauf - _ .)
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value) # Remplace les espaces multiples par un tiret
    
    return value
