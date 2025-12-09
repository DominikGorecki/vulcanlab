# Conversion Page Documentation

## Overview

The Conversion page manages the process of converting PDF and EPUB files to markdown format. Users can review conversion artifacts, compare different conversion versions, and add converted files to the database with bibliographic metadata.

### Pages

- **Main Page**: `/conv` - Lists input files and converted files pending review
- **Review Page**: `/conv/[id]` - Review conversion inspection options and readiness
- **Add to Database**: `/conv/[id]/add` - Add converted file to database with metadata
- **Inspect Original MD**: `/conv/[id]/inspect_original_md` - View and edit original markdown
- **Inspect Style vs Hier**: `/conv/[id]/inspect_style_hier` - Compare style.md vs hier.md versions
- **Inspect TOC Titles**: `/conv/[id]/inspect_toc_titles` - View and edit table of contents titles

### User Workflow

1. View input files (PDF/EPUB) ready for conversion
2. Select a file and start conversion (creates markdown artifacts)
3. Review conversion inspection options
4. Inspect and edit conversion artifacts as needed
5. Generate TOC titles if missing
6. Compare style vs hier versions and select better one
7. Verify readiness (base.md and toc_titles.md exist, no errors)
8. Add to database with bibliographic metadata

## API Calls

### GET `/conv/io-folder-data`

**Called By**: Main page (`/conv`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "input_files": ["book1.pdf", "book2.epub"],
  "processed_files": [
    "book1|42|.pdf|.md|.style.md|.hier.md|.toc_titles.md"
  ]
}
```

**Purpose**: Get lists of unprocessed input files and converted files pending database addition.

**Format**: `processed_files` uses pipe-separated format: `basename|io_file_id|variant1|variant2|...`

### POST `/conv/convert-file`

**Called By**: Main page (`/conv`) when user clicks "Start Conversion" in modal

**Request**:
```json
{
  "filename": "book1.pdf"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully converted book1.pdf",
  "input_file": "book1.pdf",
  "output_files": [
    "book1.pdf",
    "book1.style.md",
    "book1.hier.md",
    "book1.toc_titles.md"
  ]
}
```

**Purpose**: Convert a PDF or EPUB file from input directory to markdown format (blocking operation).

### GET `/conv/inspection/{io_file_id}`

**Called By**: Review page (`/conv/[id]`) on component mount

**Request**: Path parameter `io_file_id` (integer)

**Response**:
```json
{
  "items": [
    {
      "name": "inspect_style_hier",
      "available": true,
      "files_checked": ["book1.style.md", "book1.hier.md"]
    },
    {
      "name": "inspect_toc_titles",
      "available": false,
      "files_checked": ["book1.toc_titles.md"]
    },
    {
      "name": "inspect_original_md",
      "available": true,
      "files_checked": ["book1.md"]
    }
  ]
}
```

**Purpose**: Get available inspection options based on what conversion artifacts exist.

### GET `/conv/readiness/{io_file_id}`

**Called By**: Review page (`/conv/[id]`) on component mount and after operations

**Request**: Path parameter `io_file_id` (integer)

**Response**:
```json
{
  "ready": false,
  "reasons": [
    "Table of contents file is missing. Generate it first."
  ],
  "base_name": "book1"
}
```

**Purpose**: Check if converted file is ready to be added to database (validates required files exist and are error-free).

### POST `/conv/generate-toc-titles/{io_file_id}`

**Called By**: Review page (`/conv/[id]`) when user clicks "Generate" for TOC titles

**Request**: No body

**Response**:
```json
{
  "success": true,
  "message": "Successfully generated toc_titles.md from PDF bookmarks (45 lines)",
  "file_created": "book1.toc_titles.md"
}
```

**Purpose**: Generate TOC titles file by extracting bookmarks from source PDF.

### GET `/conv/file-content/{io_file_id}/{file_type}`

**Called By**: Various inspect pages to view file content

**Request**: 
- Path parameter `io_file_id` (integer)
- Path parameter `file_type` (string: "style", "hier", "toc_titles", "base")

**Response**:
```json
{
  "content": "# Heading 1\n\nContent...",
  "filename": "book1.style.md"
}
```

**Purpose**: Get markdown file content. For "style" and "hier", returns extracted titles only. For "toc_titles" and "base", returns raw markdown.

### PUT `/conv/file-content/{io_file_id}/{file_type}`

**Called By**: Inspect pages when user saves edits

**Request**:
```json
{
  "content": "123: # New Title\n124: ***MISSING***"
}
```

**Response**: Same as GET, with updated content

**Purpose**: Update markdown file content. For style/hier: applies title edits in format "line_num: title". For toc_titles: replaces entire file.

### GET `/conv/suggestion/{io_file_id}`

**Called By**: Inspect style vs hier page (`/conv/[id]/inspect_style_hier`) on component mount

**Request**: Path parameter `io_file_id` (integer)

**Response**:
```json
{
  "style_metrics": {
    "total_headings": 150,
    "h1_h2_count": 25,
    "max_depth": 4,
    "final_score": 0.85
  },
  "hier_metrics": {
    "total_headings": 145,
    "h1_h2_count": 22,
    "max_depth": 5,
    "final_score": 0.82
  },
  "winner": "style",
  "score_difference": 0.03
}
```

**Purpose**: Compare style.md and hier.md files and suggest the better one based on structural metrics.

### POST `/conv/select-file/{io_file_id}`

**Called By**: Inspect style vs hier page when user selects a file

**Request**:
```json
{
  "file_type": "style"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully copied book1.style.md to book1.md",
  "output_file": "book1.md"
}
```

**Purpose**: Copy selected file (style.md or hier.md) to `<base>.md` as the main version.

### GET `/conv/original-markdown/{io_file_id}`

**Called By**: Inspect original MD page (`/conv/[id]/inspect_original_md`) on component mount

**Request**: Path parameter `io_file_id` (integer)

**Response**:
```json
{
  "content": "# Full markdown content...",
  "filename": "book1.md"
}
```

**Purpose**: Get the content of the base markdown file (`<base>.md`).

### PUT `/conv/original-markdown/{io_file_id}`

**Called By**: Inspect original MD page when user saves edits

**Request**:
```json
{
  "content": "# Updated markdown content..."
}
```

**Response**: Same as GET, with updated content

**Purpose**: Update the base markdown file content.

### POST `/conv/add-to-database/{io_file_id}`

**Called By**: Add to database page (`/conv/[id]/add`) when user submits form

**Request**:
```json
{
  "title": "Introduction to Psychology",
  "authors": "Smith, J.",
  "year": 2020,
  "publisher": "Academic Press",
  "isbn": "978-0123456789",
  "edition": "3rd Edition",
  "volume": null,
  "issue": null,
  "pages": "1-500",
  "url": null,
  "city": null,
  "institution": null,
  "editor": null
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully added work 'Introduction to Psychology' to database",
  "work_id": 42
}
```

**Purpose**: Create a new work entry in the database with bibliographic metadata.

### DELETE `/conv/delete/{io_file_id}`

**Called By**: Review page (`/conv/[id]`) when user confirms deletion

**Request**: Path parameter `io_file_id` (integer)

**Response**:
```json
{
  "success": true,
  "message": "Successfully deleted conversion",
  "deleted_files": ["book1.pdf", "book1.md", "book1.style.md", "book1.hier.md"],
  "io_file_deleted": true
}
```

**Purpose**: Delete all files associated with a conversion and remove database entry.

### POST `/conv/parse-citation-llm`

**Called By**: Add to database page when user clicks "Parse Citation" button

**Request**:
```json
{
  "citation_text": "Smith, J. (2020). Introduction to Psychology. Academic Press.",
  "citation_format": "apa"
}
```

**Response**:
```json
{
  "success": true,
  "title": "Introduction to Psychology",
  "authors": "Smith, J.",
  "year": 2020,
  "publisher": "Academic Press"
}
```

**Purpose**: Use LLM to parse citation text and extract bibliographic metadata.

## API Implementation Details

### GET `/conv/io-folder-data`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `get_io_folder_data_endpoint()`

**Processing Steps**:

1. **Call Module Function**: Calls `get_io_folder_data()` from `vulcanLab.config.io_folder_data`
2. **Transform Processed Files**: Converts `ProcessedFile` objects to pipe-separated strings:
   - Format: `basename|io_file_id|variant1|variant2|...`
   - Uses `io_file_id` (database ID) from the PDF/EPUB variant
3. **Return Response**: Returns input files list and formatted processed files

**Modules Called**:
- `vulcanLab.config.io_folder_data.get_io_folder_data()`

**Database Queries**: 
- `SELECT * FROM io_files WHERE file_type = 'input'`
- `SELECT * FROM io_files WHERE file_type = 'to_convert'`
- `SELECT * FROM works` (to filter already processed files)

**Tables Accessed**: `io_files`, `works`

### POST `/conv/convert-file`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `convert_file_endpoint(request)`

**Processing Steps**:

1. **Load Config**: Gets input/output directories from `vulcanLab.config.load_config()`
2. **Validate Input File**: Checks file exists in input directory
3. **Determine File Type**: Checks extension (`.pdf` or `.epub`)
4. **Ensure Output Directory**: Creates output directory if needed
5. **Convert File**:
   - **For PDF**: Calls `convert_pdf_to_markdown()` with `compare=True`, `use_gpu=True`
     - Generates: `<base>.pdf`, `<base>.style.md`, `<base>.hier.md`, `<base>.toc_titles.md`
   - **For EPUB**: Calls `convert_epub_to_markdown()`
     - Generates: `<base>.epub`, `<base>.md`, `<base>.toc_titles.md`
6. **List Output Files**: Scans output directory for created files
7. **Return Response**: Returns success status and list of created files

**Modules Called**:
- `vulcanLab.conversions.conv_pdf2md.convert_pdf_to_markdown()`
- `vulcanLab.conversions.conv_epub2md.convert_epub_to_markdown()`

**File System Operations**: 
- Reads PDF/EPUB from input directory
- Writes markdown files to output directory
- Copies source PDF/EPUB to output directory

**Tables Accessed**: None (file operations only)

### GET `/conv/inspection/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `get_inspection_options(io_file_id)`

**Processing Steps**:

1. **Call Module Function**: Calls `get_conversion_inspection(io_file_id)` from `vulcanLab.conversions.inspection`
2. **Query Database**: Gets `IOFile` by ID to extract base name
3. **Check Files**: Scans output directory for conversion artifacts:
   - `inspect_style_hier`: Requires both `<base>.style.md` and `<base>.hier.md`
   - `inspect_toc_titles`: Requires `<base>.toc_titles.md`
   - `inspect_titles`: Requires `<base>.titles.md`
   - `inspect_title_changes`: Requires `<base>.title_changes.md`
   - `inspect_original_md`: Requires `<base>.md`
4. **Return Response**: Returns list of inspection items with availability status

**Modules Called**:
- `vulcanLab.conversions.inspection.get_conversion_inspection()`

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: Checks existence of markdown files in output directory

**Tables Accessed**: `io_files`

### GET `/conv/readiness/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `check_readiness(io_file_id)`

**Processing Steps**:

1. **Query Database**: Gets `IOFile` by ID
2. **Extract Base Name**: Gets base name from filename (before first dot)
3. **Check Required Files**:
   - `<base>.md` must exist
   - `<base>.toc_titles.md` must exist
   - `<base>.toc_titles.md` must not contain `***ERROR***`
4. **Collect Reasons**: Builds list of reasons if not ready
5. **Return Response**: Returns readiness status and reasons

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: Checks file existence and reads TOC file content

**Tables Accessed**: `io_files`

### POST `/conv/generate-toc-titles/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `generate_toc_titles(io_file_id)`

**Processing Steps**:

1. **Query Database**: Gets `IOFile` by ID
2. **Extract Base Name**: Gets base name from filename
3. **Locate Source PDF**: Finds PDF in input directory
4. **Extract Bookmarks**: Calls `extract_bookmarks_to_toc()` from `vulcanLab.conversions.pdf_bookmarks2toc`
   - Uses PyMuPDF (`fitz`) to extract PDF bookmarks
   - Converts to hierarchical markdown headings
5. **Handle Errors**: If extraction fails or no bookmarks found, creates error file with `***ERROR***` marker
6. **Return Response**: Returns success status and file details

**Modules Called**:
- `vulcanLab.conversions.pdf_bookmarks2toc.extract_bookmarks_to_toc()`

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: 
- Reads PDF from input directory
- Writes TOC markdown to output directory

**Tables Accessed**: `io_files`

### GET `/conv/file-content/{io_file_id}/{file_type}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `get_file_content(io_file_id, file_type)`

**Processing Steps**:

1. **Validate File Type**: Must be "style", "hier", "toc_titles", or "base"
2. **Query Database**: Gets `IOFile` by ID
3. **Extract Base Name**: Gets base name from filename
4. **Construct File Path**: Builds path to target file in output directory
5. **Read Content**:
   - **For "style" and "hier"**: Calls `extract_titles()` to get headings only
   - **For "toc_titles" and "base"**: Reads raw markdown content
6. **Return Response**: Returns content and filename

**Modules Called**:
- `vulcanLab.sanitization.extract_titles.extract_titles()` (for style/hier)

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: Reads markdown file from output directory

**Tables Accessed**: `io_files`

### PUT `/conv/file-content/{io_file_id}/{file_type}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `update_file_content(io_file_id, file_type, request)`

**Processing Steps**:

1. **Validate File Type**: Must be "style", "hier", or "toc_titles"
2. **Query Database**: Gets `IOFile` by ID
3. **Extract Base Name**: Gets base name from filename
4. **Update File**:
   - **For "toc_titles"**: Writes raw markdown content directly
   - **For "style" and "hier"**: Calls `apply_title_edits()` to apply line-based edits
     - Format: `"123: # New Title"` - Replace line 123
     - Format: `"123: ***MISSING***"` - Skip (no change)
     - Format: `"123: -"` - Remove heading markers
     - Format: `"123: --"` - Replace with blank line
5. **Extract Updated Titles**: For style/hier, extracts titles after update
6. **Return Response**: Returns updated content

**Modules Called**:
- `vulcanLab.sanitization.apply_title_edits.apply_title_edits()` (for style/hier)
- `vulcanLab.sanitization.extract_titles.extract_titles()` (for style/hier)

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: Reads and writes markdown files in output directory

**Tables Accessed**: `io_files`

### GET `/conv/suggestion/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `get_file_suggestion(io_file_id)`

**Processing Steps**:

1. **Query Database**: Gets `IOFile` by ID
2. **Extract Base Name**: Gets base name from filename
3. **Locate Files**: Finds `<base>.style.md` and `<base>.hier.md` in output directory
4. **Analyze Both Files**:
   - Calls `extract_headings()` for each file
   - Calls `compute_final_score()` for each file with default weights and chunk config
   - Computes metrics: headings count, depth, chunkability, penalties
5. **Determine Winner**: Compares final scores with tie-breaking rules:
   - If scores differ by < 0.01: use chunkability_score, then level_jump_count, then h1_h2_count
   - Otherwise: higher final_score wins
6. **Return Response**: Returns metrics for both files and winner recommendation

**Modules Called**:
- `vulcanLab.conversions.style_v_hier.extract_headings()`
- `vulcanLab.conversions.style_v_hier.compute_final_score()`

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: Reads style.md and hier.md files from output directory

**Tables Accessed**: `io_files`

### POST `/conv/select-file/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `select_file(io_file_id, request)`

**Processing Steps**:

1. **Validate File Type**: Must be "style" or "hier"
2. **Query Database**: Gets `IOFile` by ID
3. **Extract Base Name**: Gets base name from filename
4. **Construct Paths**: Builds source (`<base>.<type>.md`) and target (`<base>.md`) paths
5. **Validate Source Exists**: Checks source file exists
6. **Check Target**: Ensures target doesn't already exist (must delete first)
7. **Copy File**: Uses `shutil.copy2()` to copy source to target
8. **Return Response**: Returns success status

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`

**File System Operations**: Copies markdown file in output directory

**Tables Accessed**: `io_files`

### POST `/conv/add-to-database/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `add_to_database(io_file_id, request)`

**Processing Steps**:

1. **Query Database**: Gets `IOFile` by ID
2. **Extract Base Name**: Gets base name from filename
3. **Locate Markdown File**: Finds `<base>.md` in output directory
4. **Validate File Exists**: Checks markdown file exists
5. **Call Create Function**: Calls `create_new_work()` from `vulcanLab.conversions.new_work`:
   - Computes content hash of markdown file
   - Parses TOC from `<base>.toc_titles.md` if exists
   - Checks for duplicate content_hash if `check_duplicates=True`
   - Creates `Work` object with bibliographic metadata
   - Sets `files` JSON: `{"original_markdown": {"path": "...", "hash": "..."}}`
   - Inserts into database
6. **Return Response**: Returns success status and work ID

**Modules Called**:
- `vulcanLab.conversions.new_work.create_new_work()`

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`
- `SELECT * FROM works WHERE content_hash = ?` (duplicate check)
- `INSERT INTO works (...) VALUES (...)`

**File System Operations**: 
- Reads markdown file to compute hash
- Reads TOC file if exists

**Tables Accessed**: `io_files`, `works`

### DELETE `/conv/delete/{io_file_id}`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `delete_conversion_endpoint(io_file_id)`

**Processing Steps**:

1. **Call Module Function**: Calls `delete_conversion()` from `vulcanLab.sanitization.delete_conversion`
2. **Module Processing**:
   - Gets `IOFile` by ID
   - Extracts base name
   - Finds all files in output directory matching `<base>.*`
   - Deletes all matching files
   - Deletes `IOFile` database entry
3. **Return Response**: Returns deletion details

**Modules Called**:
- `vulcanLab.sanitization.delete_conversion.delete_conversion()`

**Database Queries**:
- `SELECT * FROM io_files WHERE id = ?`
- `DELETE FROM io_files WHERE id = ?`

**File System Operations**: Deletes all files with matching base name in output directory

**Tables Accessed**: `io_files`

### POST `/conv/parse-citation-llm`

**Router**: `src/vulcanlab_api/routers/conversion.py` → `parse_citation_llm(request)`

**Processing Steps**:

1. **Call LLM Parser**: Calls `parse_citation_with_llm()` from `vulcanLab.utils.llm_citation_parser`
2. **LLM Processing**:
   - Uses LIGHT tier LLM
   - Sends citation text with format (APA, MLA, or Chicago)
   - Parses structured response to extract bibliographic fields
3. **Return Response**: Returns extracted fields

**Modules Called**:
- `vulcanLab.utils.llm_citation_parser.parse_citation_with_llm()`

**External API Calls**: LLM API (OpenAI or Gemini) for citation parsing

**Tables Accessed**: None

## Modules Used

### `vulcanLab.config.io_folder_data`

**Purpose**: Manage input/output folder scanning and database synchronization

**Key Functions**:
- `get_io_folder_data()`: Get comprehensive IO folder data
  - Syncs filesystem with `io_files` table
  - Filters input files (removes already processed)
  - Groups converted files by base name with variants
  - Returns `IOFolderData` with input files and processed files
- `sync_files_with_database()`: Sync filesystem files with `io_files` table
  - Scans input and output directories
  - Adds new files to database
  - Updates `last_seen_at` for existing files
  - Removes files from database that no longer exist
- `get_processed_files_from_works()`: Query works table to get processed filenames
  - Checks `work.files["original_file"]["path"]` for each work
  - Returns set of filenames that have been processed

**Database Tables**: `io_files`, `works`

### `vulcanLab.conversions.conv_pdf2md`

**Purpose**: Convert PDF files to markdown format using Docling

**Key Functions**:
- `convert_pdf_to_markdown()`: Main conversion function
  - Uses Docling `DocumentConverter` with PDF format options
  - Supports GPU acceleration (auto-detects)
  - Can generate style-based or hierarchical versions
  - With `compare=True`: generates both `<base>.style.md` and `<base>.hier.md`
  - Copies source PDF to output directory as `<base>.pdf`
  - Returns markdown content(s)

**External Dependencies**: Docling library, PyMuPDF (for PDF operations)

**File System Operations**: Reads PDF, writes markdown files

### `vulcanLab.conversions.conv_epub2md`

**Purpose**: Convert EPUB files to markdown format

**Key Functions**:
- `convert_epub_to_markdown()`: Main conversion function
  - Uses `ebooklib` to extract HTML content from EPUB
  - Uses `markdownify` to convert HTML to markdown
  - Extracts hierarchical navigation structure
  - Generates `<base>.md` and `<base>.toc_titles.md`
  - Returns markdown content

**External Dependencies**: ebooklib, BeautifulSoup, markdownify

**File System Operations**: Reads EPUB, writes markdown files

### `vulcanLab.conversions.inspection`

**Purpose**: Inspect conversion artifacts and determine available options

**Key Functions**:
- `get_conversion_inspection(io_file_id)`: Get inspection options
  - Queries `IOFile` by ID
  - Extracts base name from filename
  - Checks output directory for conversion artifacts
  - Returns list of `InspectionItem` objects with availability status

**Database Tables**: `io_files`

**File System Operations**: Checks file existence in output directory

### `vulcanLab.conversions.pdf_bookmarks2toc`

**Purpose**: Extract PDF bookmarks and convert to markdown TOC

**Key Functions**:
- `extract_bookmarks_to_toc()`: Extract bookmarks from PDF
  - Uses PyMuPDF (`fitz`) to open PDF
  - Calls `doc.get_toc()` to get bookmarks (list of [level, title, page])
  - Converts to hierarchical markdown headings (H1-H6)
  - Writes to `<base>.toc_titles.md` file
  - Returns TOC content as string

**External Dependencies**: PyMuPDF (fitz)

**File System Operations**: Reads PDF, writes TOC markdown file

### `vulcanLab.conversions.style_v_hier`

**Purpose**: Compare style-based and hierarchical markdown conversions

**Key Functions**:
- `extract_headings(md_path)`: Extract all headings from markdown file
  - Parses ATX-style headings (# through ######)
  - Returns list of `Heading` objects with metadata
- `compute_final_score(headings, total_lines, weights, chunk_config)`: Compute structural metrics
  - Calculates hierarchy score (depth, level jumps)
  - Calculates chunkability score (section sizes, target range)
  - Calculates coverage score (heading distribution)
  - Applies penalties (repeated headings, heading runs, imbalance)
  - Returns `StructuralMetrics` with final score
- `compare_and_select()`: Compare two files and select winner (not used in API, but metrics used)

**File System Operations**: Reads markdown files for analysis

### `vulcanLab.conversions.new_work`

**Purpose**: Create new work entries in database

**Key Functions**:
- `create_new_work()`: Create work entry with bibliographic metadata
  - Validates markdown file exists
  - Computes SHA-256 content hash
  - Parses TOC from `<base>.toc_titles.md` if exists
  - Checks for duplicate `content_hash` if `check_duplicates=True`
  - Creates `Work` object with all metadata
  - Sets `files` JSON: `{"original_markdown": {"path": "...", "hash": "..."}}`
  - Inserts into database and returns `Work` object

**Database Tables**: `works`

**File System Operations**: Reads markdown and TOC files, computes file hashes

### `vulcanLab.sanitization.extract_titles`

**Purpose**: Extract headings/titles from markdown files

**Key Functions**:
- `extract_titles(md_path)`: Extract all headings from markdown
  - Parses ATX-style headings
  - Returns list of heading strings (one per line)

**File System Operations**: Reads markdown file

### `vulcanLab.sanitization.apply_title_edits`

**Purpose**: Apply title edits to markdown files

**Key Functions**:
- `apply_title_edits(file_path, edits_content)`: Apply line-based edits
  - Parses edits in format: `"line_num: new_title"`
  - Special formats: `***MISSING***` (skip), `-` (remove markers), `--` (blank line)
  - Modifies specific lines in markdown file
  - Writes updated file

**File System Operations**: Reads and writes markdown file

### `vulcanLab.sanitization.delete_conversion`

**Purpose**: Delete conversion and associated files

**Key Functions**:
- `delete_conversion(io_file_id)`: Delete conversion files
  - Gets `IOFile` by ID
  - Extracts base name
  - Finds all files matching `<base>.*` in output directory
  - Deletes all matching files
  - Deletes `IOFile` database entry
  - Returns deletion details

**Database Tables**: `io_files`

**File System Operations**: Deletes files from output directory

### `vulcanLab.utils.llm_citation_parser`

**Purpose**: Parse citation text using LLM

**Key Functions**:
- `parse_citation_with_llm(citation_text, citation_format)`: Parse citation
  - Uses LIGHT tier LLM
  - Sends citation text with format specification
  - Parses structured response to extract bibliographic fields
  - Returns parsed citation object

**External API Calls**: LLM API (OpenAI or Gemini)

## Database Tables

### `io_files`

**Schema**:
- `id` (INTEGER, PRIMARY KEY)
- `filename` (VARCHAR, NOT NULL, INDEXED)
- `file_type` (ENUM: "input", "to_convert", NOT NULL, INDEXED)
- `file_path` (VARCHAR, NOT NULL, UNIQUE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- `last_seen_at` (TIMESTAMP)

**Usage in Conversion**:
- Tracks files in input and output directories
- `file_type="input"`: Unprocessed PDF/EPUB files in input directory
- `file_type="to_convert"`: Converted files in output directory (PDF, EPUB, MD variants)
- Used to identify files for conversion and inspection
- Base name extracted from filename (everything before first dot)
- Variants grouped by base name

**Query Patterns**:
- `SELECT * FROM io_files WHERE id = ?` (get file by ID)
- `SELECT * FROM io_files WHERE file_type = 'input'` (get input files)
- `SELECT * FROM io_files WHERE file_type = 'to_convert'` (get converted files)
- `DELETE FROM io_files WHERE id = ?` (delete file entry)

### `works`

**Schema**: See Corpus documentation for full schema

**Usage in Conversion**:
- Created when converted file is added to database via `create_new_work()`
- `files["original_markdown"]` stores path and hash of base markdown file
- `content_hash` used for duplicate detection
- `toc` stores parsed table of contents from TOC file

**Query Patterns**:
- `SELECT * FROM works WHERE content_hash = ?` (duplicate check)
- `INSERT INTO works (...) VALUES (...)` (create new work)
- `SELECT * FROM works` (get processed filenames for filtering)

## File Naming Conventions

Files in the output directory follow these naming patterns:

- `<base>.pdf` or `<base>.epub` - Source file copy
- `<base>.md` - Base markdown file (selected from style or hier)
- `<base>.style.md` - Style-based conversion (PDF only)
- `<base>.hier.md` - Hierarchical conversion (PDF only)
- `<base>.toc_titles.md` - Table of contents extracted from bookmarks
- `<base>.titles.md` - Extracted headings (created during sanitization)
- `<base>.title_changes.md` - Title change suggestions (created during sanitization)

Where `<base>` is the filename without extension (e.g., "book1" from "book1.pdf").

