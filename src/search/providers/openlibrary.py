import requests
from typing import Optional, Tuple
from src import config
from src.utils.logger import Logger
from src.search.provider import MetadataProvider
from src.models import SearchResult, BookMetadata

class OpenLibraryProvider(MetadataProvider):
    @property
    def name(self):
        return "OpenLibrary"

    def get_by_isbn(self, isbn: str) -> Tuple[Optional[SearchResult], int]:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        try:
            resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            key = f"ISBN:{isbn}"
            if key in data:
                return self._normalize_isbn(data[key]), 1
        except Exception as e:
            Logger.verbose(f"[OL] ISBN Error: {e}", indent=4)
        return None, 0

    def search_by_text(self, meta: BookMetadata, context: dict) -> Tuple[Optional[SearchResult], int]:
        # OpenLibrary Search API
        title = meta.get('title', '')
        if not title: return None, 0

        t = title.split('(')[0].split(':')[0].strip()
        params = {'title': t}
        
        if meta.get('author') and meta['author'] != "Unknown":
            params['author'] = meta['author']
            
        if context.get("pub", False) and config.USE_PUBLISHER_IN_SEARCH and meta.get('publisher'):
            params['publisher'] = meta['publisher'].replace('Editions', '').strip()
            
        try:
            resp = requests.get("https://openlibrary.org/search.json", params=params, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if data.get('docs'):
                return self._normalize_search(data['docs'][0]), data.get('numFound', 0)
        except Exception as e:
            Logger.verbose(f"[OL] Search Error: {e}", indent=4)
        return None, 0

    def _normalize_isbn(self, data: dict) -> SearchResult:
        desc = data.get('excerpts', [{'text': ''}])[0]['text'] if 'excerpts' in data else ''
        ids = []
        if 'identifiers' in data:
            for k, v in data['identifiers'].items():
                if 'isbn' in k:
                    for i in v: ids.append({'type': k.upper(), 'identifier': i})
        
        # Adaptation des structures OL vers SearchResult
        return SearchResult(
            title=data.get('title', 'Unknown'),
            authors=[a['name'] for a in data.get('authors', [])],
            publisher=data.get('publishers', [{'name': 'Unknown'}])[0]['name'],
            publishedDate=data.get('publish_date', 'Unknown'),
            description=desc,
            pageCount=data.get('number_of_pages', 0),
            categories=[s['name'] for s in data.get('subjects', [])[:5]],
            imageLinks=data.get('cover', {}),
            industryIdentifiers=ids,
            link=data.get('url', ''),
            language='', # OL API n'est pas toujours clair sur la langue principale ici
            provider_id=data.get('key', '')
        )

    def _normalize_search(self, data: dict) -> SearchResult:
        # Normalisation spécifique au format search.json
        cover_id = data.get('cover_i')
        imgs = {}
        if cover_id:
            imgs = {'thumbnail': f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"}

        return SearchResult(
            title=data.get('title', 'Unknown'),
            authors=data.get('author_name', ['Unknown']),
            publisher=data.get('publisher', ['Unknown'])[0] if data.get('publisher') else 'Unknown',
            publishedDate=str(data.get('first_publish_year', 'Unknown')),
            description='', 
            pageCount=data.get('number_of_pages_median', 0),
            categories=data.get('subject', [])[:5],
            imageLinks=imgs,
            industryIdentifiers=[],
            link=f"https://openlibrary.org{data.get('key')}" if data.get('key') else '',
            language=data.get('language', [''])[0],
            provider_id=data.get('key', '')
        )
