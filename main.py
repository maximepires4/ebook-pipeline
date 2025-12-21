import argparse
import os
import sys
from src import config
from src.utils.logger import Logger
from src.pipeline.orchestrator import PipelineOrchestrator

def main():
    parser = argparse.ArgumentParser(description="Full Ebook Pipeline.")
    parser.add_argument('directory', nargs='?', help="Directory containing ebook files.")
    
    # Options
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose mode.")
    parser.add_argument('-s', '--source', choices=['all', 'google', 'openlibrary'], default='all', help="Metadata Source.")
    parser.add_argument('--no-kepub', action='store_true', help="Disable KEPUB conversion.")
    parser.add_argument('--no-rename', action='store_true', help="Disable renaming.")
    parser.add_argument('--drive', help="Path to Google Drive sync folder.")
    parser.add_argument('--auto', action='store_true', help="Auto-save metadata (skip confirmation for high confidence).")

    args = parser.parse_args()

    # --- 1. Configuration ---
    # Injection des arguments CLI dans la configuration globale
    config.VERBOSE = args.verbose
    if args.source != 'all': 
        config.API_SOURCE = args.source
    
    # --- 2. Initialisation ---
    # On délègue la logique métier à l'orchestrateur
    orchestrator = PipelineOrchestrator(
        auto_save=args.auto,
        enable_kepub=not args.no_kepub,
        enable_rename=not args.no_rename,
        drive_folder=args.drive
    )

    # --- 3. Sélection du dossier ---
    data_dir = args.directory
    if not data_dir:
        # Interaction simple si aucun argument fourni
        try:
            print(f"Current working directory: {os.getcwd()}")
            default_dir = os.path.join(os.getcwd(), 'data')
            user_input = input(f"Enter directory to analyze [default: {default_dir}]: ").strip()
            data_dir = user_input if user_input else default_dir
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return

    # --- 4. Exécution ---
    try:
        orchestrator.process_directory(data_dir)
    except KeyboardInterrupt:
        print("\n🛑 Process stopped by user.")
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()