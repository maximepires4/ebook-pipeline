# 📚 Ebook Super Pipeline

**The ultimate automated tool for curating your Ebook library.**

This pipeline extracts metadata from your EPUB files, attempts to find better metadata online (Google Books, OpenLibrary), standardizes filenames, converts to KEPUB (for Kobo e-readers), and uploads the results to Google Drive or a local folder.

## 🚀 Key Features

*   **Smart Metadata Enrichment**:
    *   **Waterfall Search Strategy**: Prioritizes ISBN lookups (high precision) but falls back to a "relaxed" text search (Title/Author/Publisher) if no ISBN is found.
    *   **Confidence Scoring**: Calculates a reliability score (0-100%) for each match based on title similarity, author overlap, and result uniqueness.
*   **Safety First**:
    *   **Interactive Review**: By default, low-confidence matches require your confirmation.
    *   **Granular Control (`-i`)**: Optionally review every single field change (Title, Author, Description, etc.) before applying.
    *   **Non-Destructive**: Processes files in a temporary workspace; original files are never modified in place unless output to the same directory.
*   **Media Management**:
    *   **High-Res Covers**: Automatically downloads and optimizes covers for e-ink screens (resizing to max 1600x2400, grayscale optimized JPEG).
*   **Kobo Optimization**:
    *   Native integration with **[kepubify](https://github.com/pgaskin/kepubify)** to convert EPUBs to KEPUB for faster page turns and better formatting on Kobo devices.
*   **Cloud Sync**:
    *   Direct upload to **Google Drive** (ideal for use with **[KoboCloud](https://github.com/fsantini/KoboCloud)**).
    *   Resumable uploads for large files.

## 🛠️ Installation

### 1. Prerequisites
*   **Python 3.12+**
*   **Kepubify**: Required for Kobo conversion.
    1.  Download the binary from [pgaskin/kepubify](https://github.com/pgaskin/kepubify/releases).
    2.  Place it in your system `PATH` or in the root of this project.
    3.  Rename it to `kepubify` (Windows: `kepubify.exe`) and `chmod +x kepubify`.

### 2. Setup
```bash
git clone https://github.com/your-repo/ebook-metadata.git
cd ebook-metadata
pip install -r requirements.txt
cp .env.example .env
```

### 3. Google Drive (Optional)
To enable Cloud Upload:
1.  Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Google Drive API**.
3.  Create **OAuth 2.0 Client IDs** (Desktop App).
4.  Download the JSON, rename it to `credentials.json`, and place it in the project root.
5.  Set `GOOGLE_CREDENTIALS_PATH=credentials.json` in `.env`.

## ⚙️ Configuration (`.env`)

Configure the pipeline behavior via the `.env` file:

| Variable | Default | Description |
| :--- | :--- | :--- |
| **UPLOAD** | | |
| `GOOGLE_CREDENTIALS_PATH` | `credentials.json` | Path to OAuth client ID JSON. |
| `DRIVE_FOLDER_ID` | *None* | ID of the destination folder on Drive (from URL). If empty, uploads to root. |
| **PIPELINE** | | |
| `ENABLE_KEPUBIFY` | `True` | Convert EPUB to KEPUB. |
| `ENABLE_RENAME` | `True` | Rename files to `Title - Author - Year.epub`. |
| `UPDATE_COVER` | `True` | Download and replace cover images. |
| `AUTO_SAVE` | `False` | Skip confirmation prompts (risky for batch processing). |
| **SEARCH** | | |
| `API_SOURCE` | `all` | `google`, `openlibrary`, or `all`. |
| `FILTER_BY_LANGUAGE` | `True` | Filter API results to match the EPUB's language tag. |
| `USE_PUBLISHER_IN_SEARCH` | `True` | Include publisher name in text search queries. |
| `USE_YEAR_IN_SEARCH` | `True` | Include publication year in text search queries. |
| `CONFIDENCE_THRESHOLD_HIGH` | `80` | Score above which auto-save applies (if enabled). |
| **DEBUG** | | |
| `VERBOSE` | `False` | Show detailed search steps and HTTP logs. |
| `FULL_OUTPUT` | `False` | Dump full JSON responses from APIs. |

## 🎮 Usage

### Basic Usage
Process a single file or an entire directory.
```bash
# Process all .epub files in the data/ folder
python main.py data/

# Process a specific file
python main.py data/dune.epub
```

### CLI Options

| Flag | Description |
| :--- | :--- |
| `-i`, `--interactive` | **Granular Review Mode**: Ask for confirmation for *each field* (Title, Date, Cover...) that differs. |
| `--auto` | **Batch Mode**: Automatically accept changes if confidence > 80%, skip others. |
| `--no-kepub` | Disable KEPUB conversion for this run. |
| `--no-rename` | Keep original filenames. |
| `--no-upload` | Process locally only (files remain in `output/` or temp). |
| `--isbn <ISBN>` | Force a specific ISBN for the search (works only with single file). |
| `-v`, `--verbose` | Enable debug logs. |
| `-s <source>` | Limit search to `google` or `openlibrary`. |

### Examples

**1. Interactive Review (Recommended for new books)**
```bash
python main.py data/new_books/ -i
```

**2. Force specific ISBN**
Useful if the automatic search finds the wrong edition.
```bash
python main.py data/unknown_book.epub --isbn 9780441172719
```

**3. Offline / Local Only**
Just clean metadata, rename, and convert, without uploading.
```bash
python main.py data/ --no-upload --no-kepub
```

## 🛠️ Debugging Tools

The `tools/` directory contains standalone scripts to diagnose issues without running the full pipeline.

*   **Inspector**: See exactly what metadata exists inside a file.
    ```bash
    python -m tools.inspect data/book.epub --full
    ```
*   **Search Tester**: Test the search logic and see confidence scores without changing files.
    ```bash
    python -m tools.search data/book.epub
    ```
*   **Dry Run**: Simulate the whole process (including renaming/conversion logic) without writing to disk.
    ```bash
    python -m tools.dry_run data/
    ```

## 📦 Architecture

*   **`src/pipeline/`**:
    *   `Orchestrator`: Manages the flow (Extract -> Search -> Update -> Convert -> Upload).
    *   `EpubManager`: Handles `EbookLib` interactions (reading/writing OPF/DC metadata).
    *   `DriveUploader`: Handles Google Drive OAuth2 and resumable uploads.
*   **`src/search/`**:
    *   `BookFinder`: Implements the "Waterfall" strategy.
    *   `ConfidenceScorer`: The logic engine for rating match quality.

## 🔗 Credits
*   [kepubify](https://github.com/pgaskin/kepubify) by pgaskin.
*   Google Books API & OpenLibrary API.