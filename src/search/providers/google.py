import requests
import time
from typing import Optional, Tuple
from src import config
from src.utils.logger import Logger
from src.search.provider import MetadataProvider
from src.models import SearchResult, BookMetadata


class GoogleBooksProvider(MetadataProvider):
    """
    Implementation of the MetadataProvider for the Google Books API v1.
    Includes built-in retry logic (exponential backoff) and query construction.
    """

    @property
    def name(self):
        return "Google Books"

    def get_by_isbn(self, isbn: str) -> Tuple[Optional[SearchResult], int]:
        """Direct lookup using the specific 'isbn:' keyword."""
        return self._fetch(f"isbn:{isbn}")

    def search_by_text(
        self, meta: BookMetadata, context: dict
    ) -> Tuple[Optional[SearchResult], int]:
        """Constructs a complex query string and fetches results."""
        query = self._build_query(meta, context)
        # Apply language filtering if enabled in config to reduce false positives
        lang = meta.get("language") if config.FILTER_BY_LANGUAGE else None

        return self._fetch(query, lang_restrict=lang)

    def _fetch(
        self, query: str, lang_restrict: Optional[str] = None
    ) -> Tuple[Optional[SearchResult], int]:
        """
        Executes the HTTP request to Google API.
        Handles:
        - Network errors
        - Rate limiting (429/503) with exponential backoff
        - JSON parsing
        """
        if not query:
            return None, 0

        params = {"q": query}
        if lang_restrict:
            params["langRestrict"] = lang_restrict

        for attempt in range(config.MAX_RETRIES):
            try:
                response = requests.get(
                    config.GOOGLE_API_URL, params=params, timeout=config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()

                if "items" in data and len(data["items"]) > 0:
                    # We only care about the first (best) result
                    return self._normalize(data["items"][0]), data.get("totalItems", 0)
                else:
                    return None, 0

            except requests.exceptions.HTTPError as e:
                # Retry on server errors or rate limits
                if e.response.status_code in [500, 502, 503, 504, 429]:
                    time.sleep(2**attempt)
                else:
                    Logger.verbose(f"[Google] HTTP Error: {e}")
                    return None, 0
            except Exception as e:
                Logger.verbose(f"[Google] Connection error: {e}")
                return None, 0
        return None, 0

    def _build_query(self, meta: BookMetadata, context: dict) -> str:
        """
        Constructs a targeted query string (e.g., 'intitle:Dune inauthor:Herbert').
        Uses 'context' flags to decide which fields to include (Relaxation Strategy).
        """
        publisher = meta.get("publisher") or ""
        use_pub = (
            context.get("pub", False) and config.USE_PUBLISHER_IN_SEARCH and publisher
        )

        # Extract year from date string (YYYY-MM-DD -> YYYY)
        date_str = meta.get("date") or ""
        year = date_str[:4] if len(date_str) >= 4 and date_str[:4].isdigit() else ""

        use_year = context.get("year", False) and config.USE_YEAR_IN_SEARCH and year

        title = meta.get("title", "")
        if not title:
            return ""

        # Clean up title (remove subtitles inside parenthesis/colons for better search)
        clean_title = title.split("(")[0].split(":")[0].strip()
        parts = [f"intitle:{clean_title}"]

        if meta.get("author") and meta.get("author") != "Unknown":
            parts.append(f"inauthor:{meta.get('author')}")

        if use_pub:
            clean_pub = publisher.replace("Editions", "").strip()
            parts.append(f"inpublisher:{clean_pub}")

        keywords = []
        if use_year:
            keywords.append(year)

        query = " ".join(parts)
        if keywords:
            query += " " + " ".join(keywords)
        return query

    def _normalize(self, item: dict) -> SearchResult:
        """Converts raw Google API response to our standardized SearchResult."""
        data = item.get("volumeInfo", {})
        return SearchResult(
            title=data.get("title", "Unknown"),
            authors=data.get("authors", ["Unknown"]),
            publisher=data.get("publisher", "Unknown"),
            publishedDate=data.get("publishedDate", "Unknown"),
            description=data.get("description", ""),
            categories=data.get("categories", []),
            imageLinks=data.get("imageLinks", {}),
            industryIdentifiers=data.get("industryIdentifiers", []),
            link=data.get("infoLink", ""),
            language=data.get("language", "en"),
            provider_id=item.get("id", ""),
        )
