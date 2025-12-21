import os
import subprocess
import shutil
from src.utils.logger import Logger

class KepubHandler:
    """Gère la conversion EPUB -> KEPUB via l'outil externe 'kepubify'."""
    
    BINARY_NAME = "kepubify"

    @staticmethod
    def get_binary_path():
        """Cherche le binaire kepubify (PATH ou local)."""
        # 1. Vérifier dans le PATH système (Recommandé)
        path_bin = shutil.which(KepubHandler.BINARY_NAME)
        if path_bin:
            return path_bin
            
        # 2. Vérifier dans le dossier courant (Legacy/Dev)
        local_bin = os.path.join(os.getcwd(), KepubHandler.BINARY_NAME)
        if os.path.exists(local_bin) and os.access(local_bin, os.X_OK):
            return local_bin
            
        return None

    @staticmethod
    def convert_to_kepub(input_path, output_path=None):
        """
        Convertit un fichier EPUB en KEPUB.
        Nécessite que 'kepubify' soit installé et accessible dans le PATH.
        """
        binary = KepubHandler.get_binary_path()
        if not binary:
            Logger.error("❌ 'kepubify' not found in PATH.", indent=4)
            Logger.info("   Please install it from: https://github.com/pgaskin/kepubify", indent=4)
            Logger.info("   Or ensure it is in your system PATH.", indent=4)
            return False

        if not output_path:
            # Par défaut : fichier.kepub.epub
            if input_path.lower().endswith('.epub'):
                output_path = input_path[:-5] + '.kepub.epub'
            else:
                output_path = input_path + '.kepub.epub'

        # Commande: kepubify input_path -o output_path
        cmd = [binary, input_path, "-o", output_path]
        
        try:
            # Logger.verbose(f"Executing: {' '.join(cmd)}", indent=4)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            Logger.success(f"Converted to KEPUB: {os.path.basename(output_path)}", indent=4)
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"kepubify failed: {e.stderr.strip()}", indent=4)
            return False
        except Exception as e:
            Logger.error(f"Conversion error: {e}", indent=4)
            return False