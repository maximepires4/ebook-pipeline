from typing import TypedDict, List, Optional, Dict, Any

class ImageLinks(TypedDict, total=False):
    smallThumbnail: str
    thumbnail: str
    small: str
    medium: str
    large: str

class BookMetadata(TypedDict, total=False):
    """Structure standardisée des métadonnées internes."""
    title: str
    author: str
    isbn: Optional[str]
    publisher: Optional[str]
    date: Optional[str]  # Format YYYY-MM-DD ou YYYY
    language: Optional[str]
    description: Optional[str]
    series: Optional[str]
    series_index: Optional[float]
    tags: List[str]
    filename: str  # Nom du fichier source

class SearchResult(TypedDict, total=False):
    """Structure normalisée des résultats de recherche (Google/OpenLibrary)."""
    title: str
    authors: List[str]
    publishedDate: str
    description: str
    industryIdentifiers: List[Dict[str, str]]  # [{'type': 'ISBN_13', 'identifier': '...'}]
    pageCount: int
    categories: List[str]
    imageLinks: ImageLinks
    publisher: str
    language: str
    # Champs spécifiques provider
    provider_id: str 
    link: str
