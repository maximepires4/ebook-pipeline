# 📚 Ebook Super Pipeline

A complete automation tool to manage your ebook library (EPUB). It extracts metadata, enriches information via online APIs, converts files for Kobo (KEPUB), and can publish them directly to Google Drive.

## 🚀 Key Features

*   **Metadata Enrichment**: Smart search on **Google Books** and **OpenLibrary** (automatic fallback if ISBN fails).
*   **Interactive Review**: Asks for your confirmation if the match confidence is low (< 90%), so you never overwrite data blindly.
*   **Granular Control**: Use `-i` mode to manually approve each field (Title, Author, Cover...) change individually.
*   **Cover Management**: Automatically downloads and resizes the best available high-quality covers.
*   **Kobo Optimization**: Automatic conversion to **KEPUB** format via [kepubify](https://github.com/pgaskin/kepubify).
*   **Standardization**: Clean renaming of files (`Title - Author - Year`).
*   **Drive & KoboCloud**: Native upload via Google Drive API or local copy for third-party synchronization.

## 🛠️ Installation

### 1. System Prerequisites
This project requires the `kepubify` tool for Kobo conversion.

1.  Download the latest version from [pgaskin/kepubify](https://github.com/pgaskin/kepubify/releases).
2.  Place the binary in your system `PATH` (recommended) or at the root of this project.
3.  Rename it simply to `kepubify` (or `kepubify.exe` on Windows) and make it executable (`chmod +x kepubify`).

### 2. Python Installation
```bash
git clone https://github.com/your-repo/ebook-metadata.git
cd ebook-metadata
pip install -r requirements.txt
```

### 3. Configuration (.env)
Copy the template:
```bash
cp .env.example .env
```

## 🐳 Usage with Docker (Recommended)

The Docker image contains all dependencies (including `kepubify`) and runs securely as a non-root user.

1.  **Prepare files**
    *   Place your `.epub` files in the `data/` directory.
    *   Configure your `.env` and `credentials.json` (if using Drive) at the root.

2.  **Run the pipeline**
    ```bash
    docker-compose up --build
    ```

**Note:** The container is configured with `tty: true` to allow interactive confirmation (`y/n`) for low-confidence matches directly in your terminal.

## ☁️ KoboCloud Integration

This project is the ideal companion for [KoboCloud](https://github.com/fsantini/KoboCloud).

1.  **The "Feeder" (This project)**:
    *   Processes books in `data/`.
    *   Cleans metadata, fetches HD covers, converts to **KEPUB**.
    *   Uploads the result to a specific Google Drive folder.

2.  **The "Reader" (Your Kobo)**:
    *   Install KoboCloud on your device.
    *   Add the public share link of your Drive folder to `kobocloudrc`.

**Result**: Your books appear wirelessly on your Kobo, perfectly formatted.

## ☁️ Google Drive Configuration

### Mode A: Google Drive API (Recommended)
Direct upload via the official API. Requires OAuth2.

1.  Enable **Google Drive API** in [Google Cloud Console](https://console.cloud.google.com/).
2.  Create **OAuth 2.0 Client IDs** (Desktop App).
3.  Save the JSON as `credentials.json` in the project root.
4.  Set `ENABLE_DRIVE_UPLOAD=True` in `.env`.

*On the first run (even in Docker), you will be asked to authenticate via a URL.*

### Mode B: Local Copy (Default)
Files are copied to the `output/` directory. Use this if you sync via Dropbox, Syncthing, or a mounted Drive client.

## 🎮 Usage

### Automatic Pipeline Mode
Processes an entire folder or a single file.
```bash
python main.py data
# OR
python main.py data/my_book.epub
```

### Interactive Mode
By default, the script asks for global confirmation if the confidence score is below 90%.

*   **Granular Review (`-i`)**:
    Review changes field by field (Title, Author, Date, Cover...).
    ```bash
    python main.py data -i
    ```

*   **Force Auto (`--auto`)**:
    Skip all confirmations (Batch mode).
    ```bash
    python main.py data --auto
    ```

### Command Line Options

| Argument | Description |
| :--- | :--- |
| `path` | Directory or file to process (default: `data`). |
| `-i, --interactive` | Granular review mode (confirm each field). |
| `--drive PATH` | Sets the local sync folder (Mode B). |
| `--no-kepub` | Disables KEPUB conversion. |
| `--no-rename` | Disables renaming. |
| `--auto` | **Force auto-save** (skips all confirmation prompts). |
| `-s, --source` | Force a specific API (`google`, `openlibrary`). |
| `-v` | Verbose mode (debug). |

## 🛠️ Debugging Tools

The `tools/` directory contains useful standalone scripts to diagnose issues without modifying your files.
**Note:** Run them as modules (`python -m tools.xxx`) to avoid import errors.

### 1. Inspector
Displays all metadata found in an EPUB.
```bash
python -m tools.inspect "data/book.epub"
# Or check all files in a folder:
python -m tools.inspect data/
```

### 2. Search Tester
Runs the search logic and shows what *would* be found online, including confidence scores.
```bash
python -m tools.search "data/book.epub"
```

### 3. Dry Run
Simulates the full pipeline (Extraction -> Search -> Conversion -> Renaming -> Upload) but stops before writing any changes to disk or cloud.
```bash
python -m tools.dry_run data/
```

## 📦 Architecture

*   `src/pipeline/`: Orchestration (Orchestrator, EpubManager, DriveUploader).
*   `src/search/`: Logic for finding books (Waterfall strategy).
*   `src/models.py`: Type definitions (`BookMetadata`, `SearchResult`).
*   `src/config.py`: Configuration registry.

## 🔒 Security

*   **Binary Verification**: Downloads `kepubify` from a specific version/URL in Docker.
*   **Least Privilege**: Docker container runs as `appuser` (UID 1000).
*   **Secrets**: OAuth tokens are stored locally (`token.json`) and ignored by git.

## 🔗 Credits

*   **Kepubify**: [pgaskin/kepubify](https://github.com/pgaskin/kepubify)
*   **APIs**: Google Books API & OpenLibrary.
