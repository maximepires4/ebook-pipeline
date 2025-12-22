import requests
from typing import Optional, Tuple, cast
from src import config
from src.utils.logger import Logger
from src.search.provider import MetadataProvider
from src.models import SearchResult, BookMetadata, ImageLinks


class OpenLibraryProvider(MetadataProvider):
    """
    Implementation for OpenLibrary.org API.
    Uses two distinct APIs:
    1. 'Books API' for direct ISBN lookup (richer data).
    2. 'Search API' for text queries (search.json).
    """

    @property
    def name(self):
        return "OpenLibrary"

    def get_by_isbn(self, isbn: str) -> Tuple[Optional[SearchResult], int]:
        """Uses the Books API (jscmd=data) to fetch specific book details."""
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        try:
            resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            key = f"ISBN:{isbn}"
            if key in data:
                return self._normalize_isbn(data[key]), 1
        except Exception as e:
            Logger.verbose(f"[OL] ISBN Error: {e}")
        return None, 0

    def search_by_text(
        self, meta: BookMetadata, context: dict
    ) -> Tuple[Optional[SearchResult], int]:
        """Uses the General Search API (search.json)."""
        title = meta.get("title", "")
        if not title:
            return None, 0

        # Clean title for better hit rate
        t = title.split("(")[0].split(":")[0].strip()
        params = {"title": t}

        if meta.get("author") and meta.get("author") != "Unknown":
            params["author"] = meta.get("author") or ""  # TODO: Debug author

        publisher = meta.get("publisher") or ""
        if context.get("pub", False) and config.USE_PUBLISHER_IN_SEARCH and publisher:
            params["publisher"] = publisher.replace("Editions", "").strip()

        try:
            # Note: No retry logic here (OpenLibrary can be slow, but usually works or fails hard)
            resp = requests.get(
                "https://openlibrary.org/search.json",
                params=params,
                timeout=config.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("docs"):
                return self._normalize_search(data["docs"][0]), data.get("numFound", 0)
        except Exception as e:
            Logger.verbose(f"[OL] Search Error: {e}")
        return None, 0

    def _normalize_isbn(self, data: dict) -> SearchResult:
        """Normalizes data from the 'Books API' (ISBN lookup)."""
        desc = (
            data.get("excerpts", [{"text": ""}])[0]["text"]
            if "excerpts" in data
            else ""
        )
        ids = []
        if "identifiers" in data:
            for k, v in data["identifiers"].items():
                if "isbn" in k:
                    for i in v:
                        ids.append({"type": k.upper(), "identifier": i})

        return SearchResult(
            title=data.get("title", "Unknown"),
            authors=[a["name"] for a in data.get("authors", [])],
            # OpenLibrary returns list of publishers, take the first one
            publisher=data.get("publishers", [{"name": "Unknown"}])[0]["name"],
            publishedDate=data.get("publish_date", "Unknown"),
            description=desc,
            categories=[s["name"] for s in data.get("subjects", [])[:5]],
            imageLinks=cast(ImageLinks, data.get("cover", {})),
            industryIdentifiers=ids,
            link=data.get("url", ""),
            language="",  # Books API rarely provides normalized language codes
            provider_id=data.get("key", ""),
        )

    def _normalize_search(self, data: dict) -> SearchResult:
        """
        Normalizes data from the 'Search API' (search.json).
        The structure is flatter and different from Books API.
        """
        cover_id = data.get("cover_i")
        imgs: dict = {}
        if cover_id:
            imgs = {
                "thumbnail": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            }

        return SearchResult(
            title=data.get("title", "Unknown"),
            authors=data.get("author_name", ["Unknown"]),
            publisher=data.get("publisher", ["Unknown"])[0]
            if data.get("publisher")
            else "Unknown",
            publishedDate=str(data.get("first_publish_year", "Unknown")),
            description="",  # Search API doesn't provide descriptions
            categories=data.get("subject", [])[:5],
            imageLinks=cast(ImageLinks, imgs),
            industryIdentifiers=[],
            link=f"https://openlibrary.org{data.get('key')}" if data.get("key") else "",
            language=data.get("language", [""])[0],
            provider_id=data.get("key", ""),
        )
