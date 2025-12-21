from src import config
from src.utils.logger import Logger

class Formatter:
    @staticmethod
    def print_metadata(manager, full=False):
        """Affiche les métadonnées d'un livre (local)."""
        if not manager.book:
            return

        Logger.info(f"📘 File: {manager.filename}")
        
        if full:
            raw = manager.get_raw_metadata()
            if not raw:
                Logger.warning("No metadata found.", indent=2)
            for key, items in raw.items():
                for item in items:
                    attr_str = f" {item['attrs']}" if item['attrs'] else ""
                    print(f"  {key:25}: {item['value']}{attr_str}")
        else:
            curated = manager.get_curated_metadata()
            print(f"  Title:     {curated['title']}")
            print(f"  Author:    {curated['author']}")
            print(f"  ISBN:      {curated['isbn'] if curated['isbn'] else '❌ Not Found'}")
            print(f"  Publisher: {curated['publisher'] if curated['publisher'] else 'Unknown'}")
            print(f"  Language:  {curated['language'] if curated['language'] else 'Unknown'}")
            print(f"  Date:      {curated['date'] if curated['date'] else 'Unknown'}")
            
            if curated['series']:
                index_str = f" (Tome {curated['series_index']})" if curated['series_index'] else ""
                print(f"  Series:    {curated['series']}{index_str}")
            
            if curated['subjects']:
                tags = ", ".join(curated['subjects'][:5])
                if len(curated['subjects']) > 5: tags += "..."
                print(f"  Tags:      {tags}")
        
        print("-" * 60)

    @staticmethod
    def print_search_result(data, score, strategy, hits):
        """Affiche le résultat enrichi d'une recherche en ligne."""
        if not data:
            Logger.error("No match found online.")
            print("-" * 60)
            return

        color = "🟢" if score > config.CONFIDENCE_THRESHOLD_HIGH else \
                "🟡" if score > config.CONFIDENCE_THRESHOLD_MEDIUM else "🔴"
        
        Logger.info(f"{color} MATCH FOUND (Score: {score}%) via {strategy}", indent=4)
        
        # Champs de base
        Logger.info(f"Title:     {data.get('title', 'N/A')}", indent=7)
        
        if config.SHOW_SUBTITLE and data.get('subtitle'):
            Logger.info(f"Subtitle:  {data['subtitle']}", indent=7)
            
        Logger.info(f"Authors:   {', '.join(data.get('authors', ['N/A']))}", indent=7)
        Logger.info(f"Publisher: {data.get('publisher', 'N/A')}", indent=7)
        Logger.info(f"Date:      {data.get('publishedDate', 'N/A')}", indent=7)

        # Champs enrichis
        if config.SHOW_PAGE_COUNT and data.get('pageCount'):
            Logger.info(f"Pages:     {data['pageCount']}", indent=7)

        if config.SHOW_CATEGORIES and data.get('categories'):
            cats = ", ".join(data['categories'])
            Logger.info(f"Genres:    {cats}", indent=7)
            
        if config.SHOW_IDENTIFIERS and data.get('industryIdentifiers'):
            # On formatte joliment les ISBNs trouvés
            ids = [f"{i['type'].replace('_', '')}:{i['identifier']}" for i in data['industryIdentifiers'] if 'ISBN' in i['type']]
            if ids:
                Logger.info(f"IDs:       {', '.join(ids)}", indent=7)

        if config.SHOW_RATING and data.get('averageRating'):
            stars = "★" * int(data['averageRating'])
            Logger.info(f"Rating:    {data['averageRating']}/5 {stars} ({data.get('ratingsCount', 0)} votes)", indent=7)

        if config.SHOW_DESCRIPTION and data.get('description'):
            desc = data['description'].replace('\n', ' ')
            if len(desc) > 150:
                desc = desc[:150] + "..."
            Logger.info(f"Summary:   {desc}", indent=7)
            
        if config.SHOW_LINKS:
            link = data.get('previewLink') or data.get('infoLink') or data.get('canonicalVolumeLink')
            if link:
                Logger.info(f"Link:      {link}", indent=7)
            
        if config.SHOW_COVER_LINK and data.get('imageLinks'):
            cover = data['imageLinks'].get('thumbnail') or data['imageLinks'].get('smallThumbnail')
            if cover:
                Logger.info(f"Cover:     {cover}", indent=7)

        # Infos techniques
        if config.VERBOSE and hits > 1:
            Logger.info(f"Google Hits: {hits}", indent=7)
                
        print("-" * 60)