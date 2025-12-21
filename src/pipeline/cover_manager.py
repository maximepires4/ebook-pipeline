import requests
import io
from PIL import Image
from src.utils.logger import Logger

class CoverManager:
    """Gère le téléchargement et le redimensionnement des couvertures."""
    
    # Taille max standard pour une liseuse moderne (ex: Kobo Libra 2 est ~1264x1680)
    # On prend une marge de sécurité haute qualité.
    MAX_SIZE = (1600, 2400)
    
    @staticmethod
    def download_cover(url):
        """Télécharge une image depuis une URL et retourne les bytes."""
        if not url:
            return None
            
        try:
            Logger.verbose(f"Downloading cover from {url}...", indent=4)
            headers = {'User-Agent': 'Mozilla/5.0'} # Pour éviter les blocages basiques
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            Logger.warning(f"Failed to download cover: {e}", indent=4)
            return None

    @staticmethod
    def process_image(image_bytes):
        """
        Redimensionne et convertit en JPEG optimisé pour liseuse.
        Retourne l'objet bytes de l'image traitée.
        """
        if not image_bytes:
            return None
            
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Conversion en RGB (si PNG transparent ou palette)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionnement si nécessaire (conserve le ratio)
            if img.width > CoverManager.MAX_SIZE[0] or img.height > CoverManager.MAX_SIZE[1]:
                img.thumbnail(CoverManager.MAX_SIZE, Image.Resampling.LANCZOS)
                
            # Export en JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            Logger.warning(f"Failed to process cover image: {e}", indent=4)
            return None