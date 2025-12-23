# 📚 Epub Pipeline

[![PyPI Version](https://img.shields.io/pypi/v/epub-pipeline?color=blue&style=flat-square)](https://pypi.org/project/epub-pipeline/)
[![Python Version](https://img.shields.io/pypi/pyversions/epub-pipeline?style=flat-square)](https://pypi.org/project/epub-pipeline/)
[![License](https://img.shields.io/github/license/your-username/epub-pipeline?style=flat-square)](LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/your-username/epub-pipeline/ci.yml?branch=main&style=flat-square)](https://github.com/your-username/epub-pipeline/actions)
[![Code Style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**The ultimate automated tool for curating your Ebook library.**

This pipeline extracts metadata from your EPUB files, attempts to find better metadata online (Google Books, OpenLibrary), standardizes filenames, converts to KEPUB (for Kobo e-readers), and uploads the results to Google Drive or a local folder.

## Key Features

*   **Smart Metadata Enrichment**:
    *   **Waterfall Search Strategy**: Prioritizes ISBN lookups (high precision) but falls back to a "relaxed" text search (Title/Author/Publisher) if no ISBN is found.
    *   **Confidence Scoring**: Calculates a reliability score (0-100%) for each match based on title similarity, author overlap, and result uniqueness.
*   **Safety First**:
    *   **Interactive Review**: By default, low-confidence matches require your confirmation.
    *   **Granular Control (-i)**: Optionally review every single field change (Title, Author, Description, etc.) before applying.
    *   **Non-Destructive**: Processes files in a temporary workspace; original files are never modified in place unless output to the same directory.
*   **Media Management**:
    *   **High-Res Covers**: Automatically downloads and optimizes covers for e-ink screens (resizing to max 1600x2400, grayscale optimized JPEG).
*   **Kobo Optimization**:
    *   Native integration with **[kepubify](https://github.com/pgaskin/kepubify)** to convert EPUBs to KEPUB for faster page turns and better formatting on Kobo devices.
*   **Cloud Sync**:
    *   Direct upload to **Google Drive** (ideal for use with **[KoboCloud](https://github.com/fsantini/KoboCloud)**).
    *   Resumable uploads for large files.

## Installation

### 1. Prerequisites
*   **Python 3.12+**
*   **Kepubify**: Required for Kobo conversion.
    1.  Download the binary from [pgaskin/kepubify](https://github.com/pgaskin/kepubify/releases).
    2.  Place it in your system `PATH` (recommended).
    3.  Rename it to `kepubify` (Windows: `kepubify.exe`) and ensure it is executable.

### 2. Install Package
Clone the repository and install it in editable mode:

```bash
git clone https://github.com/your-repo/epub-pipeline.git
cd epub-pipeline
pip install -e .
```
This will install the `epubpipe` command globally in your Python environment.

### 3. Configuration (.env)
Copy the template and edit your settings:
```bash
cp .env.example .env
```
*Note: The tool looks for `.env` in the directory where you run the command.*

### 4. Google Drive (Optional)
To enable Cloud Upload:
1.  Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Google Drive API**.
3.  Create **OAuth 2.0 Client IDs** (Desktop App).
4.  Download the JSON, rename it to `credentials.json`, and place it in your working directory.
5.  Set `GOOGLE_CREDENTIALS_PATH=credentials.json` in `.env`.

## Usage

### Basic Usage
Process a single file or an entire directory using the CLI command:
```bash
# Process all .epub files in the data/ folder
epubpipe data/

# Process a specific file
epubpipe data/dune.epub
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
epubpipe data/new_books/ -i
```

**2. Force specific ISBN**
Useful if the automatic search finds the wrong edition.
```bash
epubpipe data/unknown_book.epub --isbn 9780441172719
```

**3. Offline / Local Only**
Just clean metadata, rename, and convert, without uploading.
```bash
epubpipe data/ --no-upload --no-kepub
```

## Debugging Tools

The `tools/` directory contains standalone scripts to diagnose issues. You can run them as modules from the project root:

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
*   **Manual Upload**: Upload a file or folder to Google Drive immediately.
    ```bash
    python -m tools.upload data/book.epub
    ```

## Development

### Setup
```bash
# Install in editable mode with dev dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
pytest
```

### Manual Linting
```bash
ruff check .
mypy .
```

## Credits
*   **[kepubify](https://github.com/pgaskin/kepubify)** by pgaskin.
*   Google Books API & OpenLibrary API.
