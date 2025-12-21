import os
from ebooklib import epub
import warnings

# On ignore les avertissements de la librairie EbookLib
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def print_all_metadata(epub_path):
    try:
        book = epub.read_epub(epub_path)
        print(f"📖 Fichier : {os.path.basename(epub_path)}")

        # book.metadata est un dictionnaire structuré par namespace
        # On itère sur tout pour ne rien rater
        has_metadata = False
        for namespace, name_dict in book.metadata.items():
            # Simplification du nom du namespace pour la lisibilité
            ns_prefix = namespace.split("/")[-1].split("#")[-1]
            if "elements/1.1" in namespace:
                ns_prefix = "DC"

            for name, items in name_dict.items():
                for value, attrs in items:
                    has_metadata = True
                    label = f"{ns_prefix}:{name}"
                    # On affiche la valeur, et les attributs s'ils existent (comme file-as ou scheme)
                    attr_str = f" {attrs}" if attrs else ""
                    print(f"  {label:25}: {value}{attr_str}")

        if not has_metadata:
            print("  ❌ Aucune métadonnée trouvée.")

        print("-" * 60)

    except Exception as e:
        print(f"❌ Erreur lors de la lecture de {os.path.basename(epub_path)}: {e}")


def main():
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Le dossier '{data_dir}' n'existe pas.")
        return

    files = [f for f in os.listdir(data_dir) if f.lower().endswith(".epub")]

    if not files:
        print(f"Aucun fichier .epub trouvé dans '{data_dir}/'.")
        return

    print(f"📚 Analyse de {len(files)} livre(s) en cours...\n")
    for f in files:
        path = os.path.join(data_dir, f)
        print_all_metadata(path)


if __name__ == "__main__":
    main()
