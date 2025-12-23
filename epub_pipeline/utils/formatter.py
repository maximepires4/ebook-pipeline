import termcolor

from epub_pipeline import config
from epub_pipeline.utils.logger import Logger


class Formatter:
    """
    Presentation layer for the application.
    Handles formatting of metadata and search results for the console.
    """

    @staticmethod
    def print_metadata(manager, full=False):
        """
        Prints local file metadata.
        Args:
            manager (EpubManager): The file manager instance.
            full (bool): If True, dumps raw XML metadata (debug mode).
        """
        if not manager.book:
            return

        Logger.info(f"File: {manager.filename}")

        if full:
            # Debug view: Raw XML tags
            raw = manager.get_raw_metadata()
            if not raw:
                Logger.warning("No metadata found.")
            for key, items in raw.items():
                for item in items:
                    attr_str = f" {item['attrs']}" if item["attrs"] else ""
                    print(f"  {key:25}: {item['value']}{attr_str}")
        else:
            # User view: Cleaned metadata
            curated = manager.get_curated_metadata()
            print(f"  Title:     {curated['title']}")
            print(f"  Author:    {', '.join(curated['authors'])}")
            print(f"  ISBN:      {curated['isbn'] if curated['isbn'] else '❌ Not Found'}")
            print(f"  Publisher: {curated['publisher'] if curated['publisher'] else 'Unknown'}")
            print(f"  Language:  {curated['language'] if curated['language'] else 'Unknown'}")
            print(f"  Date:      {curated['date'] if curated['date'] else 'Unknown'}")

        print("-" * 60)

    @staticmethod
    def print_search_result(data, score, strategy):
        """
        Prints the result of an online search with a visual confidence indicator.
        """
        if not data:
            Logger.error("No match found online.")
            return

        Logger.info(f"MATCH FOUND (Score: {score}%) via {strategy}")

        Logger.info(f"Title:     {data.get('title', 'N/A')}")

        if config.SHOW_SUBTITLE and data.get("subtitle"):
            Logger.info(f"Subtitle:  {data['subtitle']}")

        Logger.info(f"Authors:   {', '.join(data.get('authors', ['N/A']))}")
        Logger.info(f"Publisher: {data.get('publisher', 'N/A')}")
        Logger.info(f"Date:      {data.get('publishedDate', 'N/A')}")

        if config.SHOW_CATEGORIES and data.get("categories"):
            cats = ", ".join(data["categories"])
            Logger.info(f"Genres:    {cats}")

        if config.SHOW_IDENTIFIERS and data.get("industryIdentifiers"):
            ids = [
                f"{i['type'].replace('_', '')}:{i['identifier']}"
                for i in data["industryIdentifiers"]
                if "ISBN" in i["type"]
            ]
            if ids:
                Logger.info(f"IDs:       {', '.join(ids)}")

        if config.SHOW_DESCRIPTION and data.get("description"):
            desc = data["description"].replace("\n", " ")
            if len(desc) > 150:
                desc = desc[:150] + "..."
            Logger.info(f"Summary:   {desc}")

        if config.SHOW_LINKS:
            link = data.get("previewLink") or data.get("infoLink") or data.get("canonicalVolumeLink")
            if link:
                Logger.info(f"Link:      {link}")

        if config.SHOW_COVER_LINK and data.get("imageLinks"):
            cover = data["imageLinks"].get("thumbnail") or data["imageLinks"].get("smallThumbnail")
            if cover:
                Logger.info(f"Cover:     {cover}")

    @staticmethod
    def print_comparison(local_meta, remote_data):
        """
        Displays a side-by-side comparison of current vs new metadata.
        """
        print(f"   {'FIELD':<12} | {'CURRENT':<35} | {'NEW (PROPOSED)'}")
        print("   " + "-" * 80)

        # TODO: Other changes like description

        # Helpers
        def trunc(s, w=35):
            s = str(s)
            return (s[: w - 2] + "..") if len(s) > w else s

        # Fields to compare
        fields = [
            ("Title", local_meta.get("title"), remote_data.get("title")),
            (
                "Author",
                ", ".join(local_meta.get("authors", [])),
                ", ".join(remote_data.get("authors", [])),
            ),
            ("Publisher", local_meta.get("publisher"), remote_data.get("publisher")),
            (
                "Date",
                str(local_meta.get("date"))[:10],
                remote_data.get("publishedDate"),
            ),
            ("Language", local_meta.get("language"), remote_data.get("language")),
        ]

        # TODO: Better handle ISBN
        new_isbn = "N/A"
        if remote_data.get("industryIdentifiers"):
            for i in remote_data["industryIdentifiers"]:
                if i["type"] == "ISBN_13":
                    new_isbn = i["identifier"]
                    break
        fields.append(("ISBN", local_meta.get("isbn"), new_isbn))

        # TODO: Better handle empty values
        for label, old, new in fields:
            old_str = trunc(old or "N/A")
            new_str = trunc(new or "N/A")

            if old_str != new_str and new_str != "N/A":
                print(
                    termcolor.colored(
                        f" {label:<12} | {old_str:<35} | {new_str}",
                        attrs=["bold"],
                    )
                )
            else:
                print(f" {label:<12} | {old_str:<35} | {new_str}")
        print("   " + "-" * 80)
