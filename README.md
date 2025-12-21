# 📚 Ebook Super Pipeline

Un outil d'automatisation complet pour gérer votre bibliothèque d'ebooks (EPUB). Il extrait les métadonnées, enrichit les informations via des APIs en ligne, convertit les fichiers pour Kobo (KEPUB) et peut les publier directement sur Google Drive.

## 🚀 Fonctionnalités Clés

*   **Enrichissement de Métadonnées** : Recherche intelligente sur **Google Books** et **OpenLibrary** (fallback automatique si l'ISBN échoue).
*   **Gestion des Couvertures** : Télécharge et redimensionne automatiquement les meilleures couvertures disponibles.
*   **Optimisation Kobo** : Conversion automatique au format **KEPUB** via [kepubify](https://github.com/pgaskin/kepubify).
*   **Standardisation** : Renommage propre des fichiers (`Titre - Auteur - Année`).
*   **Drive & KoboCloud** : Upload natif via l'API Google Drive ou copie locale pour synchronisation tierce.

## 🛠️ Installation

### 1. Prérequis Système
Ce projet nécessite l'outil `kepubify` pour la conversion Kobo. Pour des raisons de sécurité, le téléchargement automatique est désactivé.

1.  Téléchargez la dernière version depuis [pgaskin/kepubify](https://github.com/pgaskin/kepubify/releases).
2.  Placez le binaire dans votre `PATH` système (recommandé) ou à la racine de ce projet.
3.  Renommez-le simplement `kepubify` (ou `kepubify.exe` sur Windows) et rendez-le exécutable (`chmod +x kepubify`).

### 2. Installation Python
```bash
git clone https://github.com/votre-repo/ebook-metadata.git
cd ebook-metadata
pip install -r requirements.txt
```

### 3. Configuration (.env)
Copiez le modèle :
```bash
cp .env.example .env
```

## 🐳 Utilisation avec Docker (Recommandé)

L'image Docker contient déjà toutes les dépendances, y compris `kepubify`. C'est la méthode la plus simple et la plus propre.

1.  **Préparer les fichiers**
    *   Placez vos `.epub` dans le dossier `data/`.
    *   Configurez votre `.env` et vos `credentials.json` à la racine.

2.  **Lancer le pipeline**
    ```bash
    docker-compose up --build
    ```

Le conteneur va traiter les livres, les uploader (si configuré) ou les déposer dans `output/`, puis s'arrêter.

## ☁️ Intégration KoboCloud

Ce projet est le compagnon idéal de [KoboCloud](https://github.com/fsantini/KoboCloud). Voici le flux de travail automatisé :

1.  **Le "Feeder" (Ce projet)** :
    *   Vous déposez un livre brut dans `data/`.
    *   Le script nettoie les métadonnées, télécharge la couverture HD et convertit en **KEPUB**.
    *   Il upload le résultat final dans un dossier Google Drive dédié (ex: `Ebooks/Processed`).

2.  **Le "Reader" (Votre Kobo)** :
    *   Installez KoboCloud sur votre liseuse (voir leur documentation).
    *   Dans le fichier de configuration KoboCloud (`kobocloudrc`), ajoutez le lien de partage public de votre dossier Google Drive `Ebooks/Processed`.

**Résultat** : Vos livres apparaissent automatiquement sur votre liseuse, avec des couvertures parfaites, des résumés complets et le format rapide KEPUB, sans jamais brancher de câble USB.

## ☁️ Configuration Google Drive (Optionnel)

L'outil propose deux modes de fonctionnement pour l'export :

### Mode A : API Google Drive (Recommandé)
Upload direct via l'API officielle. Nécessite une configuration OAuth2.

1.  Activez l'API **Google Drive** dans la [Google Cloud Console](https://console.cloud.google.com/).
2.  Créez des identifiants **OAuth 2.0 Client ID** (Type: Desktop App).
3.  Téléchargez le fichier JSON, renommez-le `credentials.json` et placez-le à la racine du projet.
4.  Dans `.env`, mettez `ENABLE_DRIVE_UPLOAD=True`.

### Mode B : Copie Locale (Par défaut)
Les fichiers traités sont copiés dans le dossier `output/` du projet.
Utile si vous utilisez déjà un client de synchro (Google Drive Desktop, rclone, Syncthing).

## 🎮 Utilisation

### Mode Pipeline Automatique
Traite tout un dossier : enrichit, convertit, renomme et exporte.

```bash
python main.py data
```

La première fois (en Mode A), une fenêtre s'ouvrira pour autoriser l'accès à votre Drive.

### Options de Ligne de Commande

| Argument | Description |
| :--- | :--- |
| `directory` | Dossier contenant les EPUBs (défaut: `data`). |
| `--no-kepub` | Désactive la conversion KEPUB. |
| `--no-rename` | Désactive le renommage. |
| `--auto` | Sauvegarde automatique sans confirmation (confiance > 90%). |
| `-s, --source` | Force une API (`google`, `openlibrary`). |
| `-v` | Mode verbeux (debug). |

## 📦 Architecture

*   `src/pipeline/` : Orchestration et manipulations (EpubManager, KepubHandler, DriveUploader).
*   `src/search/` : Moteur de recherche (BookFinder) et connecteurs API.
*   `src/utils/` : Outils transverses.
*   `src/config.py` : Configuration centralisée.
*   `src/models.py` : Définitions de types et structures de données.

## 🔒 Sécurité

*   **Vérification Binaire** : Le téléchargement de binaires externes est désactivé pour éviter les attaques supply-chain.
*   **Gestion des Secrets** : Les tokens OAuth2 sont stockés localement (`token.json`) et ne doivent pas être committés.

## 🔗 Crédits

*   **Kepubify** : [pgaskin/kepubify](https://github.com/pgaskin/kepubify)
*   **APIs** : Google Books API & OpenLibrary.
