# Ebook Metadata Guide (EPUB)

This document details the standard metadata (Dublin Core) and specific metadata (OPF/Calibre) used by **Epub Pipeline** to build a perfectly sorted and identified digital library.

## 1. Unique Identification
These metadata serve to link the file to a unique book record (to retrieve cover, summary, etc.).

| Field | XML Tag (OPF) | Importance | Description |
| :--- | :--- | :--- | :--- |
| **Identifier** | `dc:identifier` | **CRITICAL** | The unique fingerprint of the book. |
| *Type* | `opf:scheme="ISBN"` | **CRITICAL** | ISBN-13 (e.g., `9782226494887`) is the absolute standard for identification. |
| **Publisher** | `dc:publisher` | High | Helps distinguish editions (e.g., "Penguin" vs "Oxford"). |

---

## 2. Sorting and Organization
These metadata determine the display order in lists.

### Authors (Creators)
*   **Tag**: `dc:creator`
    *   *Example*: `Yuval Noah Harari`
*   **Sort Attribute**: `opf:file-as`
    *   *Example*: `Harari, Yuval Noah`
    *   *Role*: Allows sorting by Last Name.
*   **Multiple Authors**: The pipeline supports multiple `dc:creator` tags for a single book.

### Title
*   **Tag**: `dc:title`
    *   *Example*: `The Miserables`
*   **Sort Attribute**: `opf:file-as` (Optional)
    *   *Example*: `Miserables, The`
    *   *Role*: Allows ignoring definite/indefinite articles during sorting.

---

## 3. Discovery and Navigation

| Field | XML Tag | Description |
| :--- | :--- | :--- |
| **Subjects** | `dc:subject` | Multiple keywords (e.g., "History", "Science", "Anthropology"). |
| **Language** | `dc:language` | ISO Code (e.g., `fr`, `en-US`). Essential for filtering API results. |
| **Date** | `dc:date` | Publication date (YYYY-MM-DD or YYYY). |
| **Description** | `dc:description` | The summary or blurb. |

---

## Pipeline Logic

When analyzing an EPUB file, `epub-pipeline` follows this priority:

1.  **ISBN Extraction**:
    *   Looks for `dc:identifier` with `scheme="ISBN"`.
    *   Looks for `978...` pattern in `dc:identifier` values.
    *   Looks for `978...` pattern in the **filename**.
2.  **Author Normalization**:
    *   Extracts all `dc:creator` tags.
    *   Generates `file-as` attributes automatically if missing (e.g. "Name Surname" -> "Surname, Name").
3.  **Search Strategy**:
    *   Uses ISBN if found (High Confidence).
    *   Falls back to Text Search (Title + First Author + Publisher) if ISBN fails.
