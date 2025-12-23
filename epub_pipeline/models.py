from typing import Dict, List, Optional, TypedDict


class ImageLinks(TypedDict, total=False):
    """Standardized structure for image URLs returned by APIs."""

    smallThumbnail: str
    thumbnail: str
    small: str
    medium: str
    large: str


class BookMetadata(TypedDict, total=False):
    """
    Internal representation of a book's metadata.
    Used for both extracted local data (EpubManager) and finalized data.
    """

    title: str
    authors: List[str]
    isbn: Optional[str]
    publisher: Optional[str]
    date: Optional[str]  # Format: YYYY-MM-DD or YYYY
    language: Optional[str]
    description: Optional[str]
    tags: List[str]
    filename: str  # Source filename for reference


class SearchResult(TypedDict, total=False):
    """
    Normalized structure for search results from external providers (Google/OpenLibrary).
    Ensures consistent data access regardless of the source API.
    """

    title: str
    authors: List[str]
    publishedDate: str
    description: str
    industryIdentifiers: List[Dict[str, str]]  # e.g. [{'type': 'ISBN_13', 'identifier': '...'}]
    categories: List[str]
    imageLinks: ImageLinks
    publisher: str
    language: str
    provider_id: str  # Unique ID from the provider (e.g. Google Books ID)
    link: str  # URL to the book's page
