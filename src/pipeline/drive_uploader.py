import os.path
import pickle
import shutil
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src import config
from src.utils.logger import Logger

# Scopes requis pour lire et écrire sur le Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class DriveUploader:
    """
    Gère l'upload vers Google Drive (API) ou la copie vers un dossier de sortie local.
    """

    def __init__(self):
        self.service = None
        self.creds = None
        
        if config.ENABLE_DRIVE_UPLOAD:
            self._authenticate()

    def _authenticate(self):
        """Gère le flux d'authentification OAuth2."""
        creds = None
        # Chargement du token existant
        if os.path.exists(config.GOOGLE_TOKEN_PATH):
            try:
                with open(config.GOOGLE_TOKEN_PATH, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                Logger.warning(f"Could not load token.json: {e}")

        # Rafraîchissement ou nouvelle connexion
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None # Force re-auth
            
            if not creds:
                if not os.path.exists(config.GOOGLE_CREDENTIALS_PATH):
                    Logger.error(f"❌ Missing '{config.GOOGLE_CREDENTIALS_PATH}'. cannot authenticate with Google Drive.")
                    Logger.info("   Please download OAuth 2.0 Client IDs from Google Cloud Console.")
                    return

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.GOOGLE_CREDENTIALS_PATH, SCOPES)
                    
                    # Tentative 1: Navigateur local (Marche sur Desktop)
                    try:
                        creds = flow.run_local_server(port=0)
                    except Exception:
                        Logger.warning("⚠️  Browser authentication failed (Docker/Headless detected?).", indent=4)
                        Logger.info("   Switching to Console Mode. Please visit this URL to authorize:", indent=4)
                        # Tentative 2: Mode Console (Copier-Coller le code)
                        creds = flow.run_console()

                except Exception as e:
                    Logger.error(f"Authentication failed: {e}")
                    return

            # Sauvegarde du nouveau token
            with open(config.GOOGLE_TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

        self.creds = creds
        try:
            self.service = build('drive', 'v3', credentials=creds)
        except Exception as e:
            Logger.error(f"Failed to build Drive service: {e}")

    def process_file(self, file_path: str):
        """
        Point d'entrée principal.
        Si ENABLE_DRIVE_UPLOAD -> Upload API.
        Sinon -> Copie vers dossier 'output'.
        """
        if config.ENABLE_DRIVE_UPLOAD:
            return self.upload_to_drive(file_path)
        else:
            return self.copy_to_local_output(file_path)

    def upload_to_drive(self, file_path: str):
        """Upload le fichier vers Google Drive."""
        if not self.service:
            Logger.error("Drive service not initialized. Skipping upload.")
            return False

        if not os.path.exists(file_path):
            Logger.error(f"File not found: {file_path}")
            return False

        file_name = os.path.basename(file_path)
        
        # Métadonnées du fichier
        file_metadata = {'name': file_name}
        if config.DRIVE_FOLDER_ID:
            file_metadata['parents'] = [config.DRIVE_FOLDER_ID]

        try:
            Logger.info(f"☁️  Uploading to Drive: {file_name}...", indent=4)
            
            media = MediaFileUpload(file_path, mimetype='application/epub+zip', resumable=True)
            
            request = self.service.files().create(body=file_metadata, media_body=media, fields='id')
            
            # Barre de progression simplifiée
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    Logger.verbose(f"Uploaded {int(status.progress() * 100)}%", indent=6)
            
            Logger.success(f"Upload complete. File ID: {response.get('id')}", indent=4)
            return True

        except Exception as e:
            Logger.error(f"Drive upload failed: {e}", indent=4)
            return False

    def copy_to_local_output(self, file_path: str):
        """Copie le fichier vers le dossier 'output' local."""
        try:
            output_dir = os.path.join(os.getcwd(), 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(output_dir, file_name)
            
            # Éviter de copier sur soi-même si input=output
            if os.path.abspath(file_path) == os.path.abspath(dest_path):
                return True

            Logger.info(f"📂 Copying to output: {dest_path}", indent=4)
            shutil.copy2(file_path, dest_path)
            Logger.success("Copy complete.", indent=4)
            return True
            
        except Exception as e:
            Logger.error(f"Local copy failed: {e}", indent=4)
            return False