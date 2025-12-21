import os
import argparse
import warnings
import re
from typing import Optional, List, Any
from ebooklib import epub

from src.utils.isbn_utils import clean_isbn_string, extract_isbn_from_filename
from src.models import BookMetadata

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

class EpubManager:
    """Gère la lecture ET l'écriture des métadonnées EPUB."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.book = None
        try:
            self.book = epub.read_epub(filepath)
        except Exception as e:
            # En production, utiliser le logger via l'appelant
            pass

    def get_raw_metadata(self) -> dict:
        """Retourne un dictionnaire complet des métadonnées brutes."""
        if not self.book: return {}
        raw_data = {}
        for namespace, name_dict in self.book.metadata.items():
            ns_prefix = namespace.split('/')[-1].split('#')[-1]
            if 'elements/1.1' in namespace: ns_prefix = 'DC'
            for name, items in name_dict.items():
                key = f"{ns_prefix}:{name}"
                raw_data[key] = []
                for value, attrs in items:
                    raw_data[key].append({'value': value, 'attrs': attrs})
        return raw_data

    def get_curated_metadata(self) -> Optional[BookMetadata]:
        """Retourne les métadonnées essentielles."""
        if not self.book: return None

        titles = self.book.get_metadata('DC', 'title')
        title = titles[0][0] if titles else "Unknown"
        creators = self.book.get_metadata('DC', 'creator')
        author = creators[0][0] if creators else "Unknown"

        isbn = None
        identifiers = self.book.get_metadata('DC', 'identifier')
        for value, attrs in identifiers:
            c_val = clean_isbn_string(value)
            scheme = ''
            for k, v in attrs.items():
                if 'scheme' in k.lower(): scheme = v.lower(); break
            if 'isbn' in scheme or (c_val.isdigit() and len(c_val) in [10, 13] and c_val.startswith(('978', '979', ''))):
                if len(c_val) in [10, 13]:
                    isbn = c_val; break
        
        if not isbn:
            isbn = extract_isbn_from_filename(self.filename)

        publishers = self.book.get_metadata('DC', 'publisher')
        publisher = publishers[0][0] if publishers else None
        
        langs = self.book.get_metadata('DC', 'language')
        language = langs[0][0] if langs else None

        pub_dates = self.book.get_metadata('DC', 'date')
        date = pub_dates[0][0] if pub_dates else None
        # Normalisation optionnelle de l'année si besoin
        
        series = None
        series_index = None
        # Recherche naive dans les métadonnées custom (calibre souvent)
        for namespace, name_dict in self.book.metadata.items():
            for name, items in name_dict.items():
                if name == 'series': series = items[0][0]
                elif name == 'series_index': 
                    try:
                        series_index = float(items[0][0])
                    except ValueError:
                        pass

        subjects = []
        subj_items = self.book.get_metadata('DC', 'subject')
        for s, _ in subj_items: subjects.append(s)

        return BookMetadata(
            filename=self.filename,
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            language=language,
            date=str(date) if date else None,
            series=series,
            series_index=series_index,
            tags=subjects
        )

    def update_metadata(self, new_data: dict):
        """Met à jour les métadonnées en mémoire.
        Args:
            new_data: Données issues de SearchResult (approximativement).
        """
        if not self.book: return

        self.book.reset_metadata('DC', 'title')
        self.book.reset_metadata('DC', 'creator')
        self.book.reset_metadata('DC', 'publisher')
        self.book.reset_metadata('DC', 'date')
        self.book.reset_metadata('DC', 'description')
        
        if new_data.get('title'):
            self.book.set_title(new_data['title'])
        
        authors = new_data.get('authors', [])
        if isinstance(authors, str): authors = [authors]
        for auth in authors:
            self.book.add_author(auth)
            
        if new_data.get('publisher'):
            self.book.set_metadata('DC', 'publisher', new_data['publisher'])
            
        if new_data.get('publishedDate'):
            self.book.set_metadata('DC', 'date', new_data['publishedDate'])
            
        if new_data.get('description'):
            self.book.set_metadata('DC', 'description', new_data['description'])

        if new_data.get('categories'):
            self.book.reset_metadata('DC', 'subject')
            for tag in new_data['categories']:
                self.book.set_metadata('DC', 'subject', tag)

    def set_cover(self, image_data):
        """Remplace ou définit l'image de couverture."""
        if not self.book or not image_data: return
        self.book.set_cover('cover.jpg', image_data)

    def save(self, output_path=None):
        """Écrit le fichier sur le disque."""
        if not self.book: return
        if not output_path: output_path = self.filepath
        epub.write_epub(output_path, self.book, {})

if __name__ == "__main__":
    from src.utils.formatter import Formatter
    parser = argparse.ArgumentParser(description="Standalone EPUB Metadata Inspector.")
    parser.add_argument('path', nargs='?', default='data', help="File path.")
    parser.add_argument('--full', action='store_true', help="Print raw metadata.")
    args = parser.parse_args()
    
    if os.path.isfile(args.path):
        Formatter.print_metadata(EpubManager(args.path), args.full)
    else:
        print("Invalid path or file not found.")