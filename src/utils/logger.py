from src import config
import json

class Logger:
    @staticmethod
    def info(msg, indent=0):
        print(" " * indent + msg)

    @staticmethod
    def verbose(msg, indent=0):
        if config.VERBOSE:
            print(" " * indent + msg)

    @staticmethod
    def success(msg, indent=0):
        print(" " * indent + f"✅ {msg}")

    @staticmethod
    def warning(msg, indent=0):
        print(" " * indent + f"⚠️  {msg}")

    @staticmethod
    def error(msg, indent=0):
        print(" " * indent + f"❌ {msg}")
        
    @staticmethod
    def full_json(data, indent=0):
        """Affiche le JSON complet si le mode FULL est activé."""
        if config.FULL_OUTPUT:
            json_str = json.dumps(data, indent=4, ensure_ascii=False)
            # On indente chaque ligne du JSON
            indented_lines = [" " * indent + line for line in json_str.split('\n')]
            print(" " * indent + "📦 [FULL OUTPUT] Google API Response:")
            print('\n'.join(indented_lines))