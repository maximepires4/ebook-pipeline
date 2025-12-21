import requests
import time
from typing import Optional, Tuple
from src import config
from src.utils.logger import Logger
from src.search.provider import MetadataProvider
from src.models import SearchResult, BookMetadata

class GoogleBooksProvider(MetadataProvider):
    @property
    def name(self):
        return "Google Books"

    def get_by_isbn(self, isbn: str) -> Tuple[Optional[SearchResult], int]:
        return self._fetch(f"isbn:{isbn}")

    def search_by_text(self, meta: BookMetadata, context: dict) -> Tuple[Optional[SearchResult], int]:
        query = self._build_query(meta, context)
        # Filtre langue
        lang = meta.get('language') if config.FILTER_BY_LANGUAGE else None
        
        return self._fetch(query, lang_restrict=lang)

    def _fetch(self, query: str, lang_restrict: str = None) -> Tuple[Optional[SearchResult], int]:
        if not query: return None, 0
        
        params = {'q': query}
        if lang_restrict: params['langRestrict'] = lang_restrict

        for attempt in range(config.MAX_RETRIES):
            try:
                response = requests.get(config.GOOGLE_API_URL, params=params, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                if "items" in data and len(data["items"]) > 0:
                    return self._normalize(data["items"][0]), data.get("totalItems", 0)
                else:
                    return None, 0
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [500, 502, 503, 504, 429]:
                    time.sleep(2 ** attempt)
                else:
                    Logger.verbose(f"[Google] HTTP Error: {e}", indent=4)
                    return None, 0
            except Exception as e:
                Logger.verbose(f"[Google] Connection error: {e}", indent=4)
                return None, 0
        return None, 0

    def _build_query(self, meta: BookMetadata, context: dict) -> str:
        use_pub = context.get("pub", False) and config.USE_PUBLISHER_IN_SEARCH and meta.get('publisher')
        use_year = context.get("year", False) and config.USE_YEAR_IN_SEARCH and meta.get('year')
        use_series = context.get("series", False) and config.USE_SERIES_IN_SEARCH and meta.get('series')

        title = meta.get('title', '')
        if not title: return ""
        clean_title = title.split('(')[0].split(':')[0].strip()
        parts = [f"intitle:{clean_title}"]
        
        if meta.get('author') and meta['author'] != "Unknown": 
            parts.append(f"inauthor:{meta['author']}")
        
        if use_pub: 
            clean_pub = meta['publisher'].replace('Editions', '').strip()
            parts.append(f"inpublisher:{clean_pub}")
        
        keywords = []
        if use_series and meta.get('series'): keywords.append(meta['series'].split('(')[0].strip())
        if use_year and meta.get('year'): keywords.append(str(meta['year']))
        
        query = " ".join(parts)
        if keywords: query += " " + " ".join(keywords)
        return query

    def _normalize(self, item: dict) -> SearchResult:
        data = item.get('volumeInfo', {})
        return SearchResult(
            title=data.get('title', 'Unknown'),
            authors=data.get('authors', ['Unknown']),
            publisher=data.get('publisher', 'Unknown'),
            publishedDate=data.get('publishedDate', 'Unknown'),
            description=data.get('description', ''),
            pageCount=data.get('pageCount', 0),
            categories=data.get('categories', []),
            imageLinks=data.get('imageLinks', {}),
            industryIdentifiers=data.get('industryIdentifiers', []),
            link=data.get('infoLink', ''),
            language=data.get('language', 'en'),
            provider_id=item.get('id', '')
        )
