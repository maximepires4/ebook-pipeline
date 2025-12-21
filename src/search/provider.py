class MetadataProvider:
    """Interface abstraite pour les fournisseurs de métadonnées."""
    
    @property
    def name(self):
        """Nom du provider (ex: 'Google Books')."""
        raise NotImplementedError

    def get_by_isbn(self, isbn):
        """
        Cherche par ISBN.
        Retourne (data, total_items) ou (None, 0).
        """
        raise NotImplementedError

    def search_by_text(self, meta, context):
        """
        Cherche par texte en utilisant le contexte (title, author, etc.)
        Retourne (data, total_items) ou (None, 0).
        """
        raise NotImplementedError
