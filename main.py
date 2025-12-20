import os
import ebooklib
from ebooklib import epub
import warnings

# Suppress warnings from ebooklib regarding recent xml libraries if any
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def get_metadata(epub_path):
    try:
        book = epub.read_epub(epub_path)
        
        # Title
        # get_metadata returns a list of tuples (value, attributes)
        titles = book.get_metadata('DC', 'title')
        title_str = titles[0][0] if titles else "Unknown Title"
        
        # Author
        creators = book.get_metadata('DC', 'creator')
        author_str = creators[0][0] if creators else "Unknown Author"

        # Language
        langs = book.get_metadata('DC', 'language')
        lang_str = langs[0][0] if langs else "Unknown Language"

        print(f"File: {os.path.basename(epub_path)}")
        print(f"  Title:    {title_str}")
        print(f"  Author:   {author_str}")
        print(f"  Language: {lang_str}")
        print("-" * 40)

    except Exception as e:
        print(f"Error reading {os.path.basename(epub_path)}: {e}")

def main():
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory '{data_dir}'.")

    files = [f for f in os.listdir(data_dir) if f.lower().endswith('.epub')]
    
    if not files:
        print(f"No .epub files found in '{data_dir}/'.")
        print("Please place an .epub file in the 'data' folder and run this script again.")
        return

    print(f"Found {len(files)} epub file(s) in '{data_dir}':\n")
    for f in files:
        path = os.path.join(data_dir, f)
        get_metadata(path)

if __name__ == "__main__":
    main()
