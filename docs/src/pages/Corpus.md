# Corpus Page Documentation

## Overview

The Corpus page provides read-only access to works that have completed both heading and content chunking. These works are ready for vectorization and RAG operations. The corpus represents the final stage of document processing before they can be used in retrieval-augmented generation.

### Pages

- **Main Page**: `/corpus` - Lists all corpus works with statistics
- **Work Viewer**: `/corpus/[id]` - Displays sanitized markdown content for a specific work

### User Workflow

1. View corpus statistics (total works, chunk vectorization status)
2. Browse list of works ready for vectorization
3. Click on a work to view its sanitized markdown content
4. Content is read-only (viewing only)

## API Calls

### GET `/corpus/stats`

**Called By**: Main page (`/corpus`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "total_works": 10,
  "chunk_stats": {
    "no_vec": 150,
    "to_vec": 200,
    "vec": 500,
    "vec_err": 5
  }
}
```

**Purpose**: Get overview statistics for corpus works and their chunk vectorization status.

### GET `/corpus/works`

**Called By**: Main page (`/corpus`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "works": [
    {
      "id": 1,
      "title": "Introduction to Psychology",
      "authors": "Smith, J.",
      "sanitized_path": "/path/to/work.sanitized.md"
    }
  ],
  "total": 10
}
```

**Purpose**: List all works in the corpus (sorted by ID descending, newest first).

### GET `/corpus/work/{work_id}`

**Called By**: Work detail page (if needed for metadata)

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "id": 1,
  "title": "Introduction to Psychology",
  "authors": "Smith, J.",
  "year": 2020,
  "publisher": "Academic Press",
  "sanitized_path": "/path/to/work.sanitized.md",
  "sanitized_hash": "abc123..."
}
```

**Purpose**: Get detailed information about a specific corpus work.

### GET `/corpus/work/{work_id}/content`

**Called By**: Work viewer page (`/corpus/[id]`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "content": "# Chapter 1\n\nContent here...",
  "filename": "work.sanitized.md",
  "work_id": 1,
  "work_title": "Introduction to Psychology"
}
```

**Purpose**: Retrieve the sanitized markdown file content for viewing.

## API Implementation Details

### GET `/corpus/stats`

**Router**: `src/vulcanlab_api/routers/corpus.py` → `get_corpus_stats()`

**Processing Steps**:

1. **Get Corpus Works**: Calls `_get_corpus_works(session)` which:
   - Queries all `Work` objects from database
   - Filters works in Python (due to JSON field complexity):
     - Must have `processing_status` JSON field
     - `processing_status["content_chunks"] == "completed"`
     - `processing_status["heading_chunks"] == "completed"`
     - Must have `files["sanitized"]` entry
   - Returns list of `Work` objects

2. **Get Chunk Statistics**: Calls `_get_chunk_vector_stats(session, corpus_work_ids)` which:
   - Queries `Chunk` table filtered by `work_id IN (corpus_work_ids)`
   - Groups by `vector_status` and counts chunks
   - Returns dict with counts: `{"no_vec": 0, "to_vec": 0, "vec": 0, "vec_err": 0}`

3. **Return Response**: Combines work count and chunk statistics

**Database Queries**:
- `SELECT * FROM works` (all works, filtered in Python)
- `SELECT vector_status, COUNT(id) FROM chunks WHERE work_id IN (...) GROUP BY vector_status`

**Tables Accessed**: `works`, `chunks`

### GET `/corpus/works`

**Router**: `src/vulcanlab_api/routers/corpus.py` → `list_corpus_works()`

**Processing Steps**:

1. **Get Corpus Works**: Same as `/corpus/stats` - calls `_get_corpus_works(session)`

2. **Build Work List Items**: For each corpus work:
   - Extracts `id`, `title`, `authors`
   - Gets `sanitized_path` from `work.files["sanitized"]["path"]`
   - Creates `CorpusWorkListItem` objects

3. **Sort**: Sorts by ID descending (newest first)

4. **Return Response**: Returns list with total count

**Database Queries**:
- `SELECT * FROM works` (all works, filtered in Python)

**Tables Accessed**: `works`

### GET `/corpus/work/{work_id}`

**Router**: `src/vulcanlab_api/routers/corpus.py` → `get_corpus_work_detail(work_id)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`

2. **Validate Corpus Membership**: Calls `_is_corpus_work(work)` to verify:
   - Work has `processing_status`
   - Both `content_chunks` and `heading_chunks` are "completed"
   - Work has `files["sanitized"]` entry

3. **Extract File Info**: Gets sanitized file path and hash from `work.files["sanitized"]`

4. **Return Response**: Returns work details with sanitized file info

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**Tables Accessed**: `works`

### GET `/corpus/work/{work_id}/content`

**Router**: `src/vulcanlab_api/routers/corpus.py` → `get_sanitized_content(work_id)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`

2. **Validate Sanitized File**: Checks `work.files["sanitized"]` exists

3. **Read File**: Uses `Path(work.files["sanitized"]["path"]).read_text(encoding="utf-8")`

4. **Return Response**: Returns file content with metadata

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**File System Access**: Reads sanitized markdown file from disk

**Tables Accessed**: `works`

## Modules Used

### `vulcanLab.data.database`

**Purpose**: Database connection and session management

**Key Functions**:
- `get_session()`: Context manager for database sessions
  - Creates SQLAlchemy session
  - Handles rollback on exceptions
  - Closes session in finally block

**Usage**: All corpus endpoints use `with get_session() as session:` pattern

### `vulcanLab.data.models.work`

**Purpose**: Work model definition

**Key Classes**:
- `Work`: SQLAlchemy model representing bibliographic works
  - Fields: `id`, `title`, `authors`, `year`, `publisher`, `files` (JSON), `processing_status` (JSON)
  - `files` JSON structure: `{"sanitized": {"path": "...", "hash": "..."}, ...}`
  - `processing_status` JSON structure: `{"content_chunks": "completed", "heading_chunks": "completed"}`

**Usage**: Queried to find corpus works and extract file metadata

### `vulcanLab.data.models.chunk`

**Purpose**: Chunk model definition

**Key Classes**:
- `Chunk`: SQLAlchemy model representing document chunks
  - Fields: `id`, `work_id`, `vector_status`, `level`, `content`, `embedding`
  - `vector_status`: One of `"no_vec"`, `"to_vec"`, `"vec"`, `"vec_err"`

**Usage**: Queried to get chunk vectorization statistics grouped by status

## Database Tables

### `works`

**Schema**:
- `id` (INTEGER, PRIMARY KEY)
- `title` (VARCHAR(500), NOT NULL, INDEXED)
- `authors` (VARCHAR(1000), NULLABLE)
- `year` (INTEGER, NULLABLE, INDEXED)
- `publisher` (VARCHAR(255), NULLABLE)
- `files` (JSON, NULLABLE) - Stores file paths and hashes
- `processing_status` (JSON, NULLABLE) - Tracks chunking completion status
- `content_hash` (VARCHAR(64), NULLABLE, INDEXED)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Usage in Corpus**:
- Queried to find works with completed chunking
- `files["sanitized"]` contains path to sanitized markdown file
- `processing_status` checked to verify both chunking types are completed

**Filtering Logic**:
- Corpus works must have:
  - `processing_status["content_chunks"] == "completed"`
  - `processing_status["heading_chunks"] == "completed"`
  - `files["sanitized"]` entry exists

### `chunks`

**Schema**:
- `id` (INTEGER, PRIMARY KEY)
- `work_id` (INTEGER, FOREIGN KEY → works.id, INDEXED)
- `vector_status` (VARCHAR(10), NOT NULL, INDEXED)
- `level` (VARCHAR(20), NOT NULL, INDEXED)
- `content` (TEXT, NOT NULL)
- `embedding` (VECTOR(768), NULLABLE)
- `start_line` (INTEGER, NOT NULL)
- `end_line` (INTEGER, NOT NULL)
- `parent_id` (INTEGER, FOREIGN KEY → chunks.id, NULLABLE)

**Usage in Corpus**:
- Queried to count chunks by `vector_status` for corpus works
- Statistics show: `no_vec`, `to_vec`, `vec`, `vec_err` counts

**Query Pattern**:
```sql
SELECT vector_status, COUNT(id) 
FROM chunks 
WHERE work_id IN (corpus_work_ids) 
GROUP BY vector_status
```

## Helper Functions

### `_is_corpus_work(work: Work) -> bool`

**Location**: `src/vulcanlab_api/routers/corpus.py`

**Purpose**: Check if a work qualifies as a corpus work

**Logic**:
1. Check `work.processing_status` exists
2. Verify `processing_status["content_chunks"] == "completed"`
3. Verify `processing_status["heading_chunks"] == "completed"`
4. Verify `work.files["sanitized"]` exists
5. Return `True` if all conditions met

### `_get_corpus_works(session) -> list[Work]`

**Location**: `src/vulcanlab_api/routers/corpus.py`

**Purpose**: Get all works that are in the corpus

**Logic**:
1. Query all works: `session.query(Work).all()`
2. Filter in Python using `_is_corpus_work()` for each work
3. Return filtered list

**Note**: Filtering done in Python due to JSON field complexity in SQLAlchemy

### `_get_chunk_vector_stats(session, corpus_work_ids: list[int]) -> dict[str, int]`

**Location**: `src/vulcanlab_api/routers/corpus.py`

**Purpose**: Get chunk statistics grouped by vector_status

**Logic**:
1. Query chunks: `session.query(Chunk.vector_status, func.count(Chunk.id))`
2. Filter: `.filter(Chunk.work_id.in_(corpus_work_ids))`
3. Group: `.group_by(Chunk.vector_status)`
4. Initialize result dict with all statuses set to 0
5. Populate with actual counts from query results
6. Return statistics dict

