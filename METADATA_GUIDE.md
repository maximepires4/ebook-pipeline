# Ebook Metadata Guide (EPUB)

This document details the standard metadata (Dublin Core) and specific metadata (OPF/Calibre) required to build a perfectly sorted and identified digital library.

## 1. Unique Identification (The Key)
These metadata serve to link the file to a unique book record (to retrieve cover, summary, etc.).

| Field | XML Tag (OPF) | Importance | Description |
| :--- | :--- | :--- | :--- |
| **Identifier** | `dc:identifier` | **CRITICAL** | The unique fingerprint of the book. |
| *Type* | `opf:scheme="ISBN"` | **CRITICAL** | ISBN-13 (e.g., `9782226494887`) is the absolute standard for identification. |
| **Publisher** | `dc:publisher` | High | Helps distinguish editions (e.g., "Penguin" vs "Oxford"). |

---

## 2. Sorting and Organization (The Ranking)
These metadata determine the display order in lists. Without them, "Victor Hugo" might be sorted under **V**.

### Author (Creator)
*   **Display**: `dc:creator`
    *   *Value*: `Yuval Noah Harari`
*   **Sort**: `opf:file-as` (Attribute)
    *   *Value*: `Harari, Yuval Noah`
    *   *Role*: Allows sorting by Last Name.

### Title (Title)
*   **Display**: `dc:title`
    *   *Value*: `The Miserables`
*   **Sort**: `opf:file-as` (Attribute - optional but recommended)
    *   *Value*: `Miserables, The`
    *   *Role*: Allows ignoring definite/indefinite articles during sorting.

### Series (Sagas)
The Dublin Core standard does not natively handle series. Custom `<meta>` tags (de facto Calibre standard) are often used.
*   **Series Name**: `<meta name="calibre:series" content="Harry Potter"/>`
*   **Index**: `<meta name="calibre:series_index" content="1.0"/>`

---

## 3. Discovery and Navigation
For search, filtering, and user experience.

| Field | XML Tag | Description |
| :--- | :--- | :--- |
| **Subjects / Tags** | `dc:subject` | Multiple keywords (e.g., "History", "Science", "Anthropology"). |
| **Language** | `dc:language` | ISO Code (e.g., `fr`, `en-US`). Essential for filtering by language. |
| **Date** | `dc:date` | Publication date (often just the year or YYYY-MM-DD). |
| **Description** | `dc:description` | The summary or blurb. |

---

## Technical Summary for Implementation

When analyzing an EPUB file, the extraction priority should be:

1.  **Retrieve `dc:identifier` where `scheme="ISBN"`** -> This is the source of truth.
2.  **Retrieve `dc:creator` AND its attribute `opf:file-as`** -> To build a clean author index.
3.  **Retrieve `meta name="calibre:series"`** -> To group volumes.