class MetadataProvider:
    """
    Abstract Base Class (Interface) for all metadata providers (Google, OpenLibrary, etc.).
    Enforces a consistent API for the BookFinder to use.
    """

    @property
    def name(self):
        """Returns the display name of the provider."""
        raise NotImplementedError

    def get_by_isbn(self, isbn):
        """
        Fetches metadata using a specific ISBN.
        Returns: (SearchResult | None, total_hits: int)
        """
        raise NotImplementedError

    def search_by_text(self, meta, context):
        """
        Searches using loose text criteria (Title, Author, etc.).
        Args:
            meta: Local BookMetadata object.
            context: Dictionary defining which fields to use in the query (e.g. {'pub': True}).
        Returns: (SearchResult | None, total_hits: int)
        """
        raise NotImplementedError
