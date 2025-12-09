# Chunking Page Documentation

## Overview

The Chunking page manages the process of splitting sanitized documents into semantic chunks for vectorization. Users extract sanitized titles, generate AI suggestions for which headings to vectorize, and apply heading-based and content-based chunking.

### Pages

- **Main Page**: `/chunk` - Lists works ready for chunking (have sanitized files)
- **Work Workflow**: `/chunk/[id]` - Chunking workflow for a specific work
- **View Sanitized**: `/chunk/[id]/sanitized` - View and edit sanitized markdown file
- **View Sanitized Titles**: `/chunk/[id]/san-titles` - View and edit sanitized titles file
- **View Vec Suggestions**: `/chunk/[id]/vec-suggestions` - View and edit vectorization suggestions
- **Generate Vec Suggestions**: `/chunk/[id]/gen-vec-sugg` - Generate vec suggestions using LLM

### User Workflow

1. View list of works with sanitized files ready for chunking
2. Select a work to begin chunking workflow
3. Extract sanitized titles (if not already done)
4. Generate vectorization suggestions (which headings to vectorize)
5. Review and edit vec suggestions if needed
6. Apply heading chunks (creates chunk records for headings)
7. Apply content chunks (creates paragraph-level chunks for vectorization)
8. Work is ready for vectorization

## API Calls

### GET `/chunk/works`

**Called By**: Main page (`/chunk`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "works": [
    {
      "id": 1,
      "title": "Introduction to Psychology",
      "authors": "Smith, J.",
      "year": 2020,
      "has_sanitized": true,
      "heading_chunks": "completed",
      "content_chunks": "pending"
    }
  ],
  "total": 10,
  "stats": {
    "heading_completed": 5,
    "content_completed": 3,
    "pending": 2
  }
}
```

**Purpose**: List all works with sanitized files, showing chunking status.

### GET `/chunk/work/{work_id}`

**Called By**: Work workflow page (`/chunk/[id]`) on component mount and after operations

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "id": 1,
  "title": "Introduction to Psychology",
  "authors": "Smith, J.",
  "year": 2020,
  "sanitized": {
    "exists": true,
    "path": "/path/to/work.sanitized.md",
    "hash": "abc123...",
    "hash_match": true
  },
  "san_titles": {
    "exists": true,
    "path": "/path/to/work.san_titles.md",
    "hash": "def456...",
    "hash_match": true
  },
  "vec_suggestions": {
    "exists": true,
    "path": "/path/to/work.vec_sugg.md",
    "hash": "ghi789...",
    "hash_match": true
  },
  "processing_status": {
    "heading_chunks": "completed",
    "content_chunks": "pending"
  }
}
```

**Purpose**: Get detailed work information with file status and chunking progress.

### GET `/chunk/work/{work_id}/sanitized/content`

**Called By**: View sanitized page (`/chunk/[id]/sanitized`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "content": "# Full sanitized markdown content...",
  "filename": "work.sanitized.md",
  "hash": "abc123..."
}
```

**Purpose**: Get the content of a work's sanitized markdown file for viewing/editing.

### PUT `/chunk/work/{work_id}/sanitized/content`

**Called By**: View sanitized page when user saves edits

**Request**:
```json
{
  "content": "# Updated sanitized markdown content...",
  "hash": "abc123..."
}
```

**Response**: Same as GET, with updated content and new hash

**Purpose**: Update the content of a work's sanitized markdown file and update its hash.

### POST `/chunk/work/{work_id}/extract-sanitized-titles`

**Called By**: Work workflow page when user clicks "Extract Sanitized Titles"

**Request**:
```json
{
  "source_key": "sanitized",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.san_titles.md",
  "message": "Sanitized titles extracted successfully"
}
```

**Purpose**: Extract headings from sanitized markdown and create `.san_titles.md` file.

### GET `/chunk/work/{work_id}/san-titles/content`

**Called By**: View sanitized titles page (`/chunk/[id]/san-titles`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "content": "# Heading 1\n## Heading 2\n...",
  "filename": "work.san_titles.md",
  "hash": "def456..."
}
```

**Purpose**: Get the content of a work's sanitized titles file for viewing/editing.

### PUT `/chunk/work/{work_id}/san-titles/content`

**Called By**: View sanitized titles page when user saves edits

**Request**:
```json
{
  "content": "# Updated Heading 1\n## Updated Heading 2\n...",
  "hash": "def456..."
}
```

**Response**: Same as GET, with updated content and new hash

**Purpose**: Update the content of a work's sanitized titles file and update its hash.

### GET `/chunk/work/{work_id}/vec-suggestions/content`

**Called By**: View vec suggestions page (`/chunk/[id]/vec-suggestions`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "content": "# CHANGES TO HEADINGS\n```\n123: VECTORIZE\n124: SKIP\n...\n```",
  "filename": "work.vec_sugg.md",
  "hash": "ghi789..."
}
```

**Purpose**: Get the content of a work's vec suggestions file for viewing/editing.

### PUT `/chunk/work/{work_id}/vec-suggestions/content`

**Called By**: View vec suggestions page when user saves edits

**Request**:
```json
{
  "content": "# CHANGES TO HEADINGS\n```\n123: VECTORIZE\n124: SKIP\n...\n```",
  "hash": "ghi789..."
}
```

**Response**: Same as GET, with updated content and new hash

**Purpose**: Update the content of a work's vec suggestions file and update its hash.

### GET `/chunk/work/{work_id}/vec-suggestions/table`

**Called By**: View vec suggestions page (interactive table mode)

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "work_id": 1,
  "rows": [
    {
      "line_number": 123,
      "heading": "# Chapter 1",
      "decision": "VECTORIZE"
    },
    {
      "line_number": 124,
      "heading": "## Section 1.1",
      "decision": "SKIP"
    }
  ],
  "filename": "work.vec_sugg.md",
  "hash": "ghi789..."
}
```

**Purpose**: Get vec suggestions as structured table data (all headings with decisions).

### PUT `/chunk/work/{work_id}/vec-suggestions/table`

**Called By**: View vec suggestions page when user saves table edits

**Request**:
```json
{
  "rows": [
    {
      "line_number": 123,
      "heading": "# Chapter 1",
      "decision": "VECTORIZE"
    }
  ]
}
```

**Response**: Same as GET, with updated rows and new hash

**Purpose**: Save table data back to vec suggestions file.

### GET `/chunk/work/{work_id}/vec-suggestions/prompt`

**Called By**: Generate vec suggestions page (`/chunk/[id]/gen-vec-sugg`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "prompt": "You are an expert...",
  "work_title": "Introduction to Psychology",
  "work_authors": "Smith, J."
}
```

**Purpose**: Get the LLM prompt for generating vec suggestions without executing it.

### POST `/chunk/work/{work_id}/vec-suggestions/manual`

**Called By**: Generate vec suggestions page when user pastes manual LLM response

**Request**:
```json
{
  "llm_response": "Here are the suggestions...",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.vec_sugg.md",
  "message": "Vec suggestions saved successfully"
}
```

**Purpose**: Save vec suggestions from a manually executed LLM response.

### POST `/chunk/work/{work_id}/vec-suggestions/run`

**Called By**: Generate vec suggestions page when user clicks "Run LLM"

**Request**:
```json
{
  "use_full_model": false,
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.vec_sugg.md",
  "message": "Vec suggestions generated successfully"
}
```

**Purpose**: Generate vec suggestions using LLM (LIGHT or FULL model).

### POST `/chunk/work/{work_id}/apply-heading-chunks`

**Called By**: Work workflow page when user clicks "Apply Heading Chunks"

**Request**:
```json
{
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "chunks_created": 25,
  "message": "Successfully created 25 heading chunks"
}
```

**Purpose**: Create chunk records in database for headings marked for vectorization.

### POST `/chunk/work/{work_id}/apply-content-chunks`

**Called By**: Work workflow page when user clicks "Apply Content Chunks"

**Request**:
```json
{
  "force": false,
  "min_chunk_words": 50
}
```

**Response**:
```json
{
  "success": true,
  "chunks_created": 150,
  "message": "Successfully created 150 content chunks"
}
```

**Purpose**: Create paragraph-level chunk records in database for vectorization.

### GET `/chunk/work/{work_id}/chunks/count`

**Called By**: Work workflow page (for debugging/display)

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "count": 175,
  "work_id": 1
}
```

**Purpose**: Get the total number of chunks for a work.

## API Implementation Details

### GET `/chunk/works`

**Router**: `src/vulcanlab_api/routers/chunking.py` → `list_works()`

**Processing Steps**:

1. **Query All Works**: `session.query(Work).order_by(Work.id.desc()).all()`
2. **Filter Works**: Filters works that have `work.files["sanitized"]` exists
3. **Build Work Items**: For each work:
   - Checks `work.processing_status["heading_chunks"]` → `heading_chunks` status
   - Checks `work.processing_status["content_chunks"]` → `content_chunks` status
   - Extracts basic work info (id, title, authors, year)
4. **Calculate Statistics**: Counts works by chunking status
5. **Return Response**: Returns work list with statistics

**Database Queries**:
- `SELECT * FROM works ORDER BY id DESC`

**Tables Accessed**: `works`

### GET `/chunk/work/{work_id}`

**Router**: `src/vulcanlab_api/routers/chunking.py` → `get_work_detail(work_id)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Check File Status**: For each file key (`sanitized`, `san_titles`, `vec_suggestions`):
   - Checks if file exists in `work.files[file_key]`
   - Gets path and stored hash
   - Checks if file exists on disk
   - Computes current hash using `compute_file_hash()`
   - Compares hashes
   - Returns `FileStatusInfo` with existence, path, hash, hash_match
3. **Get Processing Status**: Extracts `work.processing_status` (heading_chunks, content_chunks)
4. **Return Response**: Returns work details with file statuses and processing status

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**File System Operations**: Checks file existence and computes hashes

**Tables Accessed**: `works`

### POST `/chunk/work/{work_id}/extract-sanitized-titles`

**Router**: `src/vulcanlab_api/routers/chunking.py` → `extract_sanitized_titles(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `extract_titles_from_work()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets sanitized file path from `work.files[source_key]["path"]`
   - Validates file hash matches database (unless `force=True`)
   - Reads sanitized markdown file
   - Extracts headings using `extract_titles()` function
   - Writes headings to `<base>.san_titles.md` file
   - Computes file hash
   - Updates `work.files["san_titles"]` with path and hash
   - Sets file to read-only
   - Commits database changes
3. **Return Response**: Returns success status and output path

**Modules Called**:
- `vulcanLab.sanitization.extract_titles_from_work()`
- `vulcanLab.sanitization.extract_titles.extract_titles()`
- `vulcanLab.utils.file_utils.compute_file_hash()`
- `vulcanLab.utils.file_utils.set_file_readonly()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Reads sanitized markdown file, writes san_titles file

**Tables Accessed**: `works`

### POST `/chunk/work/{work_id}/vec-suggestions/run`

**Router**: `src/vulcanlab_api/routers/chunking.py` → `run_vec_suggestions(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `suggest_chunks_from_work()` from `vulcanLab.chunking`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets sanitized file path from `work.files["sanitized"]`
   - Validates file hash matches database (unless `force=True`)
   - Extracts sanitized titles (if not already done)
   - Builds LLM prompt with titles and bibliographic info
   - Calls LLM (LIGHT or FULL model based on `use_full_model`)
   - Parses LLM response to extract decisions (VECTORIZE/SKIP)
   - Applies hierarchy rules (parent headings must be VECTORIZE if child is)
   - Writes decisions to `<base>.vec_sugg.md` file
   - Computes file hash
   - Updates `work.files["vec_suggestions"]` with path and hash
   - Sets file to read-only
   - Commits database changes
3. **Return Response**: Returns success status and output path

**Modules Called**:
- `vulcanLab.chunking.suggest_chunks_from_work()`
- `vulcanLab.chunking.suggested_chunks.suggest_chunks()`
- `vulcanLab.ai.llm_factory.create_langchain_chat()`

**External API Calls**: LLM API (OpenAI or Gemini)

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Reads sanitized markdown and titles files, writes vec_suggestions file

**Tables Accessed**: `works`

### POST `/chunk/work/{work_id}/apply-heading-chunks`

**Router**: `src/vulcanlab_api/routers/chunking.py` → `apply_heading_chunks(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `chunk_headings()` from `vulcanLab.chunking`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets sanitized file and vec_suggestions file paths from `work.files`
   - Validates file hashes match database (unless `force=True`)
   - Parses vec_suggestions file to get decisions (line_num → VECTORIZE/SKIP)
   - Reads sanitized markdown file
   - Extracts headings with line numbers
   - Filters headings to only those marked VECTORIZE
   - For each heading:
     - Builds heading breadcrumb (parent hierarchy)
     - Creates `Chunk` record:
       - `work_id`: work ID
       - `level`: heading level (H1-H5)
       - `content`: heading text
       - `heading_breadcrumbs`: breadcrumb string
       - `start_line`: heading line number
       - `end_line`: heading line number
       - `vector_status`: "to_vec"
       - `parent_id`: NULL (top-level chunks)
   - Inserts chunks into database
   - Updates `work.processing_status["heading_chunks"] = "completed"`
   - Commits database changes
3. **Return Response**: Returns success status and chunk count

**Modules Called**:
- `vulcanLab.chunking.chunk_headings.chunk_headings()`
- `vulcanLab.utils.file_utils.compute_file_hash()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `INSERT INTO chunks (...) VALUES (...)` (multiple inserts)
- `UPDATE works SET processing_status = ? WHERE id = ?`

**File System Operations**: Reads sanitized markdown and vec_suggestions files

**Tables Accessed**: `works`, `chunks`

### POST `/chunk/work/{work_id}/apply-content-chunks`

**Router**: `src/vulcanlab_api/routers/chunking.py` → `apply_content_chunks(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `chunk_content()` from `vulcanLab.chunking.content_chunking`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets sanitized file path from `work.files["sanitized"]`
   - Validates file hash matches database (unless `force=True`)
   - Reads sanitized markdown file
   - Parses markdown structure:
     - Extracts headings with line numbers and levels
     - Extracts paragraphs with start/end lines
     - Extracts tables and figures
     - Builds heading hierarchy (breadcrumbs)
   - Creates paragraph chunks:
     - Groups paragraphs under their headings
     - Combines paragraphs until reaching TARGET_WORDS (200) or MAX_WORDS (300)
     - Creates chunks with breadcrumbs, start/end lines
   - Creates table chunks (one per table)
   - Creates figure chunks (one per figure)
   - Merges small chunks to meet minimum word count
   - For each chunk:
     - Creates `Chunk` record:
       - `work_id`: work ID
       - `level`: "chunk" (for content chunks)
       - `content`: chunk text (without breadcrumb)
       - `heading_breadcrumbs`: breadcrumb string
       - `start_line`: first paragraph start line
       - `end_line`: last paragraph end line
       - `vector_status`: "to_vec"
       - `parent_id`: NULL (or parent heading chunk ID if linking)
   - Inserts chunks into database
   - Updates `work.processing_status["content_chunks"] = "completed"`
   - Commits database changes
3. **Return Response**: Returns success status and chunk count

**Modules Called**:
- `vulcanLab.chunking.content_chunking.chunk_content()`
- `vulcanLab.utils.file_utils.compute_file_hash()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `INSERT INTO chunks (...) VALUES (...)` (multiple inserts)
- `UPDATE works SET processing_status = ? WHERE id = ?`

**File System Operations**: Reads sanitized markdown file

**Tables Accessed**: `works`, `chunks`

## Modules Used

### `vulcanLab.chunking.chunk_headings`

**Purpose**: Create chunk records for headings marked for vectorization

**Key Functions**:
- `chunk_headings(work_id, force, verbose)`: Create heading chunks
  - Gets work and file paths
  - Validates file hashes
  - Parses vec_suggestions file to get decisions
  - Extracts headings from sanitized markdown
  - Filters headings marked VECTORIZE
  - Creates `Chunk` records for each heading
  - Updates `work.processing_status["heading_chunks"]`
  - Returns number of chunks created

**Database Tables**: `works`, `chunks`

**File System Operations**: Reads sanitized markdown and vec_suggestions files

### `vulcanLab.chunking.content_chunking`

**Purpose**: Create paragraph-level chunks for vectorization

**Key Functions**:
- `chunk_content(work_id, verbose, min_chunk_words)`: Create content chunks
  - Gets work and sanitized file path
  - Validates file hash
  - Parses markdown structure (headings, paragraphs, tables, figures)
  - Builds heading hierarchy (breadcrumbs)
  - Creates paragraph chunks (combines paragraphs under headings)
  - Creates table chunks (one per table)
  - Creates figure chunks (one per figure)
  - Merges small chunks to meet minimum word count
  - Creates `Chunk` records for all chunks
  - Updates `work.processing_status["content_chunks"]`
  - Returns number of chunks created

**External Dependencies**: spaCy (`en_core_web_sm`) for sentence tokenization

**Database Tables**: `works`, `chunks`

**File System Operations**: Reads sanitized markdown file

### `vulcanLab.chunking.suggested_chunks`

**Purpose**: Generate AI suggestions for which headings to vectorize

**Key Functions**:
- `suggest_chunks_from_work(work_id, use_full_model, force, verbose)`: Generate suggestions
  - Gets work and sanitized file path
  - Validates file hash
  - Extracts sanitized titles (if not already done)
  - Builds LLM prompt with titles and bibliographic info
  - Calls LLM (LIGHT or FULL model)
  - Parses response to extract decisions
  - Applies hierarchy rules (parent must be VECTORIZE if child is)
  - Writes to `<base>.vec_sugg.md` file
  - Updates database
- `build_prompt_for_vec_suggestions(work_id, force, verbose)`: Build prompt without executing
  - Gets work and sanitized file path
  - Extracts sanitized titles
  - Builds prompt with titles and bibliographic info
  - Returns prompt string
- `save_vec_suggestions_from_response(work_id, response_text, force, verbose)`: Save manual response
  - Parses LLM response text
  - Applies hierarchy rules
  - Writes vec_suggestions file
  - Updates database

**External API Calls**: LLM API (OpenAI or Gemini)

**Database Tables**: `works`

**File System Operations**: Reads sanitized markdown and titles files, writes vec_suggestions file

### `vulcanLab.sanitization.extract_titles`

**Purpose**: Extract headings from markdown files (reused from sanitization)

**Key Functions**: See Sanitization documentation

**Database Tables**: `works`

**File System Operations**: Reads markdown file, writes titles file

### `vulcanLab.utils.file_utils`

**Purpose**: File system utility functions

**Key Functions**: See Sanitization documentation

**File System Operations**: File permission and hash operations

## Database Tables

### `works`

**Schema**: See Corpus documentation for full schema

**Usage in Chunking**:
- `files["sanitized"]`: Path and hash of sanitized markdown file
- `files["san_titles"]`: Path and hash of sanitized titles file
- `files["vec_suggestions"]`: Path and hash of vectorization suggestions file
- `processing_status["heading_chunks"]`: Status ("pending", "completed")
- `processing_status["content_chunks"]`: Status ("pending", "completed")

**Query Patterns**:
- `SELECT * FROM works WHERE id = ?` (get work by ID)
- `SELECT * FROM works ORDER BY id DESC` (list all works)
- `UPDATE works SET files = ? WHERE id = ?` (update file metadata)
- `UPDATE works SET processing_status = ? WHERE id = ?` (update chunking status)

### `chunks`

**Schema**: See Corpus documentation for full schema

**Usage in Chunking**:
- Created for headings marked VECTORIZE (heading chunks)
- Created for paragraph-level content (content chunks)
- `level`: "H1" through "H5" for heading chunks, "chunk" for content chunks
- `heading_breadcrumbs`: Breadcrumb trail (e.g., "H1 > H2 > H3")
- `vector_status`: Set to "to_vec" (ready for vectorization)
- `parent_id`: NULL for top-level chunks (can link to parent heading chunks)

**Query Patterns**:
- `INSERT INTO chunks (...) VALUES (...)` (create chunk records)
- `SELECT COUNT(*) FROM chunks WHERE work_id = ?` (count chunks for work)
- `SELECT * FROM chunks WHERE work_id = ? AND vector_status = 'to_vec'` (get chunks ready for vectorization)

## File Naming Conventions

Files created during chunking:

- `<base>.san_titles.md` - Extracted headings from sanitized markdown
- `<base>.vec_sugg.md` - Vectorization suggestions (format: `"line_num: VECTORIZE|SKIP"`)

Where `<base>` is derived from the sanitized markdown filename (e.g., "work1" from "work1.sanitized.md").

## Chunking Strategy

### Heading Chunks

- Created for headings marked VECTORIZE in vec_suggestions file
- Level corresponds to heading level (H1-H5)
- Content is just the heading text
- Used for hierarchical grouping and context augmentation
- Not vectorized for semantic search (used for structure)

### Content Chunks

- Created from paragraphs, tables, and figures
- Target size: 200 words (TARGET_WORDS)
- Maximum size: 300 words (MAX_WORDS)
- Minimum size: 50 words (MIN_CHUNK_WORDS)
- Paragraphs combined under same heading until reaching target/max
- Includes heading breadcrumbs for context
- Vectorized for semantic search

### Hierarchy Rules

- If a child heading is marked VECTORIZE, its parent must also be VECTORIZE
- Ensures consistent hierarchy in heading chunks
- Applied automatically when generating vec suggestions

