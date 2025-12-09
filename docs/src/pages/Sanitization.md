# Sanitization Page Documentation

## Overview

The Sanitization page manages the process of cleaning and structuring markdown content. Users extract headings, get AI-suggested improvements to heading hierarchy, and apply changes to create sanitized markdown files ready for chunking.

### Pages

- **Main Page**: `/sanitization` - Lists all works with sanitization status
- **Add Sanitized**: `/sanitization/add` - Add pre-sanitized markdown directly (skip conversion workflow)
- **Work Workflow**: `/sanitization/[id]` - Sanitization workflow for a specific work
- **View Titles**: `/sanitization/[id]/titles` - View and edit extracted titles file
- **View Title Changes**: `/sanitization/[id]/title-changes` - View and edit title change suggestions
- **Generate Title Changes**: `/sanitization/[id]/gen-title-changes` - Generate title changes using LLM

### User Workflow

1. View list of works needing sanitization
2. Select a work to begin sanitization workflow
3. Extract titles from original markdown (required step)
4. Optionally generate AI-suggested title changes
5. Review and edit title changes if needed
6. Apply title changes to create sanitized markdown, or skip-apply to copy original
7. Sanitized file is ready for chunking

## API Calls

### GET `/sanitization/works`

**Called By**: Main page (`/sanitization`) on component mount

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
      "work_type": "book",
      "has_sanitized": false,
      "has_original_markdown": true
    }
  ],
  "total": 10,
  "needs_sanitization": 5
}
```

**Purpose**: List all works with their sanitization status.

### GET `/sanitization/work/{work_id}`

**Called By**: Work workflow page (`/sanitization/[id]`) on component mount and after operations

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "id": 1,
  "title": "Introduction to Psychology",
  "authors": "Smith, J.",
  "year": 2020,
  "work_type": "book",
  "original_markdown": {
    "exists": true,
    "path": "/path/to/work.md",
    "hash": "abc123...",
    "hash_match": true,
    "error": null
  },
  "titles": {
    "exists": true,
    "path": "/path/to/work.titles.md",
    "hash": "def456...",
    "hash_match": true,
    "error": null
  },
  "title_changes": {
    "exists": false,
    "path": null,
    "hash": null,
    "hash_match": null,
    "error": null
  },
  "sanitized": {
    "exists": false,
    "path": null,
    "hash": null,
    "hash_match": null,
    "error": null
  }
}
```

**Purpose**: Get detailed work information with file status validation (existence and hash matching).

### POST `/sanitization/work/{work_id}/extract-titles`

**Called By**: Work workflow page when user clicks "Generate" for titles

**Request**:
```json
{
  "source_key": "original_markdown",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.titles.md",
  "message": "Titles extracted successfully to work.titles.md"
}
```

**Purpose**: Extract all headings from a work's markdown file and create `.titles.md` file.

### POST `/sanitization/work/{work_id}/suggest-title-changes`

**Called By**: Generate title changes page (`/sanitization/[id]/gen-title-changes`) when user runs LLM

**Request**:
```json
{
  "source_key": "original_markdown",
  "use_full_model": false,
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.title_changes.md",
  "message": "Title changes suggested successfully to work.title_changes.md"
}
```

**Purpose**: Use AI to suggest heading hierarchy improvements and create `.title_changes.md` file.

### POST `/sanitization/work/{work_id}/apply-title-changes`

**Called By**: Work workflow page when user clicks "Apply Title Changes"

**Request**:
```json
{
  "source_key": "original_markdown",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.sanitized.md",
  "message": "Title changes applied successfully to work.sanitized.md"
}
```

**Purpose**: Apply title changes to create sanitized markdown file.

### POST `/sanitization/work/{work_id}/skip-apply`

**Called By**: Work workflow page when user clicks "Skip Apply (Copy Original)"

**Request**:
```json
{
  "source_key": "original_markdown",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.sanitized.md",
  "message": "Original copied to sanitized: work.sanitized.md"
}
```

**Purpose**: Skip sanitization and copy original markdown to sanitized version.

### POST `/sanitization/work/{work_id}/verify-title-changes`

**Called By**: Work workflow page when user clicks "Verify" button

**Request**:
```json
{
  "source_key": "original_markdown"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Title changes verified and hash updated",
  "errors": []
}
```

**Purpose**: Verify title changes file integrity and update hash if valid.

### GET `/sanitization/work/{work_id}/titles/content`

**Called By**: View titles page (`/sanitization/[id]/titles`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "content": "# Heading 1\n## Heading 2\n...",
  "filename": "work.titles.md",
  "hash": "def456..."
}
```

**Purpose**: Get the content of a work's titles file for viewing/editing.

### PUT `/sanitization/work/{work_id}/titles/content`

**Called By**: View titles page when user saves edits

**Request**:
```json
{
  "content": "# Updated Heading 1\n## Updated Heading 2\n...",
  "hash": "def456..."
}
```

**Response**: Same as GET, with updated content and new hash

**Purpose**: Update the content of a work's titles file and update its hash in database.

### GET `/sanitization/work/{work_id}/title-changes/content`

**Called By**: View title changes page (`/sanitization/[id]/title-changes`) on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "content": "123: # New Title\n124: ***MISSING***\n...",
  "filename": "work.title_changes.md",
  "hash": "ghi789..."
}
```

**Purpose**: Get the content of a work's title_changes file for viewing/editing.

### PUT `/sanitization/work/{work_id}/title-changes/content`

**Called By**: View title changes page when user saves edits

**Request**:
```json
{
  "content": "123: # Updated Title\n124: ***MISSING***\n...",
  "hash": "ghi789..."
}
```

**Response**: Same as GET, with updated content and new hash

**Purpose**: Update the content of a work's title_changes file and update its hash in database.

### GET `/sanitization/work/{work_id}/title-changes/table`

**Called By**: View title changes page (interactive table mode)

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "work_id": 1,
  "source_file": "./work.md",
  "rows": [
    {
      "line_number": 123,
      "original_heading": "# Old Title",
      "suggested_action": "CHANGE",
      "suggested_title": "# New Title"
    }
  ],
  "filename": "work.title_changes.md",
  "hash": "ghi789..."
}
```

**Purpose**: Get title changes as structured table data (all headings merged with suggestions).

### PUT `/sanitization/work/{work_id}/title-changes/table`

**Called By**: View title changes page when user saves table edits

**Request**:
```json
{
  "rows": [
    {
      "line_number": 123,
      "original_heading": "# Old Title",
      "suggested_action": "CHANGE",
      "suggested_title": "# New Title"
    }
  ]
}
```

**Response**: Same as GET, with updated rows and new hash

**Purpose**: Save table data back to title_changes file (only actual changes saved).

### GET `/sanitization/work/{work_id}/prompt`

**Called By**: Generate title changes page to show prompt before running

**Request**: Query parameters: `source_key` (default: "original_markdown"), `force` (default: false)

**Response**:
```json
{
  "prompt": "You are an expert...",
  "work_title": "Introduction to Psychology",
  "work_authors": "Smith, J."
}
```

**Purpose**: Get the LLM prompt for suggesting title changes without executing it.

### POST `/sanitization/work/{work_id}/manual-title-changes`

**Called By**: Generate title changes page when user pastes manual LLM response

**Request**:
```json
{
  "source_key": "original_markdown",
  "llm_response": "Here are the suggested changes...",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "output_path": "/path/to/work.title_changes.md",
  "message": "Title changes saved successfully to work.title_changes.md"
}
```

**Purpose**: Save title changes from a manually executed LLM response.

### POST `/sanitization/add-sanitized`

**Called By**: Add sanitized page (`/sanitization/add`) when user submits form

**Request**:
```json
{
  "filename": "work1",
  "content": "# Full markdown content...",
  "title": "Introduction to Psychology",
  "authors": "Smith, J.",
  "year": 2020,
  "publisher": "Academic Press"
}
```

**Response**:
```json
{
  "success": true,
  "work_id": 42,
  "output_path": "/path/to/work1.sanitized.md",
  "message": "Work created successfully with ID 42"
}
```

**Purpose**: Create a new work with pre-sanitized markdown content directly (skips conversion workflow).

## API Implementation Details

### GET `/sanitization/works`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `list_works()`

**Processing Steps**:

1. **Query All Works**: `session.query(Work).order_by(Work.id.desc()).all()`
2. **Build Work Items**: For each work:
   - Checks `work.files["sanitized"]` exists → `has_sanitized`
   - Checks `work.files["original_markdown"]` exists → `has_original_markdown`
   - Counts works needing sanitization (has original but no sanitized)
3. **Return Response**: Returns work list with statistics

**Database Queries**:
- `SELECT * FROM works ORDER BY id DESC`

**Tables Accessed**: `works`

### GET `/sanitization/work/{work_id}`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `get_work_detail(work_id)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Check File Status**: For each file key (`original_markdown`, `titles`, `title_changes`, `sanitized`):
   - Calls `_check_file_status(work, file_key)`:
     - Checks if file exists in `work.files[file_key]`
     - Gets path and stored hash
     - Checks if file exists on disk
     - Computes current hash using `compute_file_hash()`
     - Compares hashes
     - Returns `FileStatusInfo` with existence, path, hash, hash_match, error
3. **Return Response**: Returns work details with file statuses

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**File System Operations**: Checks file existence and computes hashes

**Tables Accessed**: `works`

### POST `/sanitization/work/{work_id}/extract-titles`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `extract_titles_from_work_endpoint(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `extract_titles_from_work()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source file path from `work.files[source_key]["path"]`
   - Validates file hash matches database (unless `force=True`)
   - Reads markdown file
   - Extracts headings using `extract_titles()` function
   - Writes headings to `<base>.titles.md` file
   - Computes file hash
   - Updates `work.files["titles"]` with path and hash
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

**File System Operations**: Reads markdown file, writes titles file

**Tables Accessed**: `works`

### POST `/sanitization/work/{work_id}/suggest-title-changes`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `suggest_title_changes_endpoint(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `suggest_heading_changes_from_work()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source file and titles file paths from `work.files`
   - Validates file hashes match (unless `force=True`)
   - Builds LLM prompt using `build_prompt_for_work()`:
     - Loads template from database (function_tag: "heading_improvement")
     - Includes work title, authors, TOC, and titles content
     - Formats prompt with template variables
   - Calls LLM (LIGHT or FULL model based on `use_full_model`)
   - Parses LLM response to extract title changes
   - Writes changes to `<base>.title_changes.md` file
   - Computes file hash
   - Updates `work.files["title_changes"]` with path and hash
   - Sets file to read-only
   - Commits database changes
3. **Return Response**: Returns success status and output path

**Modules Called**:
- `vulcanLab.sanitization.suggest_heading_changes_from_work()`
- `vulcanLab.sanitization.build_prompt_for_work()`
- `vulcanLab.data.template_loader.load_template()`
- `vulcanLab.ai.llm_factory.create_langchain_chat()`

**External API Calls**: LLM API (OpenAI or Gemini)

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `SELECT * FROM prompt_meta WHERE function_tag = 'heading_improvement'` (template loading)
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Reads markdown and titles files, writes title_changes file

**Tables Accessed**: `works`, `prompt_meta`

### POST `/sanitization/work/{work_id}/apply-title-changes`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `apply_title_changes_endpoint(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `apply_title_changes_from_work()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source file and title_changes file paths from `work.files`
   - Validates file hashes match (unless `force=True`)
   - Parses title_changes file:
     - Format: `"line_num: new_title"` per line
     - Special formats: `***MISSING***` (skip), `-` (remove markers), `--` (blank line)
   - Reads source markdown file
   - Applies changes line by line:
     - Replaces headings at specified line numbers
     - Handles special cases (missing, remove, blank)
   - Writes sanitized content to `<base>.sanitized.md` file
   - Computes file hash
   - Updates `work.files["sanitized"]` with path and hash
   - Sets file to read-only
   - Commits database changes
3. **Return Response**: Returns success status and output path

**Modules Called**:
- `vulcanLab.sanitization.apply_title_changes_from_work()`
- `vulcanLab.sanitization.apply_title_changes.parse_title_changes()`
- `vulcanLab.utils.file_utils.compute_file_hash()`
- `vulcanLab.utils.file_utils.set_file_readonly()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Reads source and title_changes files, writes sanitized file

**Tables Accessed**: `works`

### POST `/sanitization/work/{work_id}/skip-apply`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `skip_apply_endpoint(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `skip_apply_from_work()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source file path from `work.files[source_key]["path"]`
   - Validates file hash matches (unless `force=True`)
   - Copies source file to `<base>.sanitized.md`
   - Computes file hash
   - Updates `work.files["sanitized"]` with path and hash
   - Sets file to read-only
   - Commits database changes
3. **Return Response**: Returns success status and output path

**Modules Called**:
- `vulcanLab.sanitization.skip_apply_from_work()`
- `vulcanLab.utils.file_utils.compute_file_hash()`
- `vulcanLab.utils.file_utils.set_file_readonly()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Copies markdown file

**Tables Accessed**: `works`

### POST `/sanitization/work/{work_id}/verify-title-changes`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `verify_title_changes(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `verify_title_changes_integrity()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets titles, title_changes, and source markdown file paths
   - Validates titles file hash matches database
   - Checks every line in title_changes exists in titles file
   - Checks every line in titles file has a corresponding heading in markdown
   - If all checks pass, updates title_changes hash in database
3. **Return Response**: Returns verification result with any errors

**Modules Called**:
- `vulcanLab.sanitization.verify_title_changes_integrity()`
- `vulcanLab.utils.file_utils.compute_file_hash()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Reads titles, title_changes, and markdown files

**Tables Accessed**: `works`

### GET `/sanitization/work/{work_id}/titles/content`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `get_titles_content(work_id)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Validate Titles File**: Checks `work.files["titles"]` exists
3. **Read File**: Reads titles file from disk using path in `work.files["titles"]["path"]`
4. **Compute Hash**: Computes current hash of file
5. **Return Response**: Returns content, filename, and hash

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**File System Operations**: Reads titles file from disk

**Tables Accessed**: `works`

### PUT `/sanitization/work/{work_id}/titles/content`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `update_titles_content(work_id, request)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Validate Titles File**: Checks `work.files["titles"]` exists and file exists on disk
3. **Make File Writable**: Calls `set_file_writable()` to allow editing
4. **Write Content**: Writes new content to titles file
5. **Set Read-Only**: Calls `set_file_readonly()` to protect file
6. **Compute New Hash**: Computes hash of updated file
7. **Update Database**: Updates `work.files["titles"]["hash"]` with new hash
8. **Commit**: Commits database changes
9. **Return Response**: Returns updated content and new hash

**Modules Called**:
- `vulcanLab.utils.file_utils.set_file_writable()`
- `vulcanLab.utils.file_utils.set_file_readonly()`
- `vulcanLab.utils.file_utils.compute_file_hash()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Writes titles file, updates file permissions

**Tables Accessed**: `works`

### GET `/sanitization/work/{work_id}/title-changes/content`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `get_title_changes_content(work_id)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Validate Title Changes File**: Checks `work.files["title_changes"]` exists
3. **Read File**: Reads title_changes file from disk
4. **Compute Hash**: Computes current hash of file
5. **Return Response**: Returns content, filename, and hash

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**File System Operations**: Reads title_changes file from disk

**Tables Accessed**: `works`

### PUT `/sanitization/work/{work_id}/title-changes/content`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `update_title_changes_content(work_id, request)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Validate Title Changes File**: Checks `work.files["title_changes"]` exists and file exists on disk
3. **Make File Writable**: Calls `set_file_writable()` to allow editing
4. **Write Content**: Writes new content to title_changes file
5. **Set Read-Only**: Calls `set_file_readonly()` to protect file
6. **Compute New Hash**: Computes hash of updated file
7. **Update Database**: Updates `work.files["title_changes"]["hash"]` with new hash
8. **Commit**: Commits database changes
9. **Return Response**: Returns updated content and new hash

**Modules Called**:
- `vulcanLab.utils.file_utils.set_file_writable()`
- `vulcanLab.utils.file_utils.set_file_readonly()`
- `vulcanLab.utils.file_utils.compute_file_hash()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Writes title_changes file, updates file permissions

**Tables Accessed**: `works`

### GET `/sanitization/work/{work_id}/title-changes/table`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `get_title_changes_table(work_id)`

**Processing Steps**:

1. **Call Module Function**: Calls `get_title_changes_table_data()` from `vulcanLab.sanitization.title_changes_interactive`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source markdown and title_changes file paths
   - Reads source markdown and extracts all headings with line numbers
   - Reads title_changes file and parses suggestions
   - Merges headings with suggestions:
     - Headings in title_changes: use suggested action/title
     - Headings NOT in title_changes: default to original (NO_CHANGE)
   - Returns all headings as table rows
3. **Get File Info**: Gets title_changes file hash and filename from database
4. **Return Response**: Returns table data with all headings

**Modules Called**:
- `vulcanLab.sanitization.title_changes_interactive.get_title_changes_table_data()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`

**File System Operations**: Reads markdown and title_changes files

**Tables Accessed**: `works`

### PUT `/sanitization/work/{work_id}/title-changes/table`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `update_title_changes_table(work_id, request)`

**Processing Steps**:

1. **Query Work**: `session.query(Work).filter(Work.id == work_id).first()`
2. **Call Module Function**: Calls `reconstruct_title_changes_markdown()` from `vulcanLab.sanitization.title_changes_interactive`
3. **Module Processing**:
   - Filters rows to only include actual changes (suggested_action != original_heading OR suggested_title != original_title)
   - Converts table rows back to markdown format:
     - Format: `"line_num: new_title"` per line
     - Only includes changed headings
4. **Write File**: Writes reconstructed markdown to title_changes file
5. **Set Read-Only**: Sets file to read-only
6. **Compute Hash**: Computes new hash
7. **Update Database**: Updates `work.files["title_changes"]["hash"]`
8. **Commit**: Commits database changes
9. **Return Response**: Returns updated table data

**Modules Called**:
- `vulcanLab.sanitization.title_changes_interactive.reconstruct_title_changes_markdown()`
- `vulcanLab.utils.file_utils.set_file_writable()`
- `vulcanLab.utils.file_utils.set_file_readonly()`
- `vulcanLab.utils.file_utils.compute_file_hash()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Writes title_changes file

**Tables Accessed**: `works`

### GET `/sanitization/work/{work_id}/prompt`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `get_prompt_for_work(work_id, source_key, force)`

**Processing Steps**:

1. **Call Module Function**: Calls `build_prompt_for_work()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source file and titles file paths
   - Validates file hashes (unless `force=True`)
   - Loads template from database (function_tag: "heading_improvement")
   - Builds prompt with work metadata and titles content
   - Returns prompt string (does not call LLM)
3. **Return Response**: Returns prompt, work title, and authors

**Modules Called**:
- `vulcanLab.sanitization.build_prompt_for_work()`
- `vulcanLab.data.template_loader.load_template()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `SELECT * FROM prompt_meta WHERE function_tag = 'heading_improvement'`

**File System Operations**: Reads markdown and titles files

**Tables Accessed**: `works`, `prompt_meta`

### POST `/sanitization/work/{work_id}/manual-title-changes`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `save_manual_title_changes(work_id, request)`

**Processing Steps**:

1. **Call Module Function**: Calls `save_title_changes_from_response()` from `vulcanLab.sanitization`
2. **Module Processing**:
   - Gets `Work` by ID
   - Gets source file path
   - Parses LLM response text to extract title changes
   - Writes changes to `<base>.title_changes.md` file
   - Computes file hash
   - Updates `work.files["title_changes"]` with path and hash
   - Sets file to read-only
   - Commits database changes
3. **Return Response**: Returns success status and output path

**Modules Called**:
- `vulcanLab.sanitization.save_title_changes_from_response()`
- `vulcanLab.utils.file_utils.compute_file_hash()`
- `vulcanLab.utils.file_utils.set_file_readonly()`

**Database Queries**:
- `SELECT * FROM works WHERE id = ?`
- `UPDATE works SET files = ? WHERE id = ?`

**File System Operations**: Writes title_changes file

**Tables Accessed**: `works`

### POST `/sanitization/add-sanitized`

**Router**: `src/vulcanlab_api/routers/sanitization.py` → `add_sanitized_markdown(request)`

**Processing Steps**:

1. **Validate Filename**: Checks filename contains only alphanumeric, underscores, hyphens
2. **Get Output Directory**: Gets output directory from config
3. **Create File Path**: Builds path as `<filename>.sanitized.md`
4. **Check Duplicate**: Checks if file already exists
5. **Write File**: Writes sanitized content to file
6. **Compute Hash**: Computes SHA-256 content hash
7. **Set Read-Only**: Sets file to read-only
8. **Check Duplicate Content**: Queries database for existing work with same `content_hash`
9. **Create Work**: Creates `Work` object:
   - Sets `files`: `{"sanitized": {"path": "...", "hash": "..."}}`
   - Sets `toc`: `[]` (empty, since sanitization skipped)
   - Sets bibliographic metadata from request
10. **Insert Database**: Inserts work into database
11. **Return Response**: Returns success status and work ID

**Modules Called**:
- `vulcanLab.utils.file_utils.compute_file_hash()`
- `vulcanLab.utils.file_utils.set_file_readonly()`
- `vulcanLab.utils.file_utils.set_file_writable()`

**Database Queries**:
- `SELECT * FROM works WHERE content_hash = ?` (duplicate check)
- `INSERT INTO works (...) VALUES (...)`

**File System Operations**: Writes sanitized markdown file

**Tables Accessed**: `works`

## Modules Used

### `vulcanLab.sanitization.extract_titles`

**Purpose**: Extract headings/titles from markdown files

**Key Functions**:
- `extract_titles(md_path)`: Extract all headings from markdown file
  - Parses ATX-style headings (# through ######)
  - Returns list of heading strings
- `extract_titles_from_work(work_id, source_key, force, verbose)`: Extract titles from work
  - Gets work from database
  - Gets source file path from `work.files[source_key]`
  - Validates file hash matches database (unless `force=True`)
  - Extracts headings and writes to `<base>.titles.md`
  - Updates `work.files["titles"]` with path and hash
  - Returns output file path

**Database Tables**: `works`

**File System Operations**: Reads markdown file, writes titles file

### `vulcanLab.sanitization.suggest_heading_changes`

**Purpose**: Generate AI-suggested heading improvements

**Key Functions**:
- `suggest_heading_changes_from_work(work_id, source_key, use_full_model, force, verbose)`: Generate suggestions
  - Gets work and file paths
  - Validates file hashes
  - Builds LLM prompt using template
  - Calls LLM (LIGHT or FULL model)
  - Parses response to extract title changes
  - Writes to `<base>.title_changes.md`
  - Updates database
- `build_prompt_for_work(work_id, source_key, force)`: Build prompt without executing
  - Loads template from database
  - Formats prompt with work metadata and titles
  - Returns prompt string
- `save_title_changes_from_response(work_id, source_key, llm_response, force)`: Save manual response
  - Parses LLM response text
  - Writes title_changes file
  - Updates database

**External API Calls**: LLM API (OpenAI or Gemini)

**Database Tables**: `works`, `prompt_meta`

**File System Operations**: Reads markdown and titles files, writes title_changes file

### `vulcanLab.sanitization.apply_title_changes`

**Purpose**: Apply title changes to create sanitized markdown

**Key Functions**:
- `apply_title_changes_from_work(work_id, source_key, force, verbose)`: Apply changes
  - Gets work and file paths
  - Validates file hashes
  - Parses title_changes file
  - Reads source markdown
  - Applies changes line by line
  - Writes sanitized markdown to `<base>.sanitized.md`
  - Updates database
- `parse_title_changes(changes_file)`: Parse title changes file
  - Parses format: `"line_num: new_title"`
  - Handles special formats: `***MISSING***`, `-`, `--`
  - Returns list of change dictionaries

**Database Tables**: `works`

**File System Operations**: Reads source and title_changes files, writes sanitized file

### `vulcanLab.sanitization.skip_apply`

**Purpose**: Skip sanitization and copy original to sanitized

**Key Functions**:
- `skip_apply_from_work(work_id, source_key, force, verbose)`: Copy original to sanitized
  - Gets work and source file path
  - Validates file hash
  - Copies source file to `<base>.sanitized.md`
  - Updates database

**Database Tables**: `works`

**File System Operations**: Copies markdown file

### `vulcanLab.sanitization.update_content_hash`

**Purpose**: Verify and update file hashes

**Key Functions**:
- `verify_title_changes_integrity(work_id, source_key, verbose)`: Verify integrity
  - Validates titles file hash matches database
  - Checks every line in title_changes exists in titles file
  - Checks every line in titles has corresponding heading in markdown
  - Updates title_changes hash if all checks pass
  - Returns verification result with errors

**Database Tables**: `works`

**File System Operations**: Reads titles, title_changes, and markdown files

### `vulcanLab.sanitization.title_changes_interactive`

**Purpose**: Interactive table editing for title changes

**Key Functions**:
- `get_title_changes_table_data(work_id, source_key)`: Get table data
  - Reads source markdown and extracts all headings
  - Reads title_changes file and parses suggestions
  - Merges headings with suggestions (all headings included)
  - Returns table rows with original and suggested values
- `reconstruct_title_changes_markdown(source_file, rows)`: Reconstruct markdown
  - Filters rows to only actual changes
  - Converts table rows back to markdown format
  - Returns markdown string

**Database Tables**: `works`

**File System Operations**: Reads markdown and title_changes files

### `vulcanLab.utils.file_utils`

**Purpose**: File system utility functions

**Key Functions**:
- `compute_file_hash(file_path)`: Compute SHA-256 hash of file
- `set_file_readonly(file_path)`: Set file permissions to read-only
- `set_file_writable(file_path)`: Set file permissions to writable
- `is_file_readonly(file_path)`: Check if file is read-only

**File System Operations**: File permission and hash operations

### `vulcanLab.data.template_loader`

**Purpose**: Load prompt templates from database

**Key Functions**:
- `load_template(function_tag, fallback_builder)`: Load template
  - Queries `prompt_meta` table by `function_tag`
  - Falls back to file-based template if not in database
  - Returns `LCPromptTemplate` object

**Database Tables**: `prompt_meta`

## Database Tables

### `works`

**Schema**: See Corpus documentation for full schema

**Usage in Sanitization**:
- `files["original_markdown"]`: Path and hash of original markdown file
- `files["titles"]`: Path and hash of extracted titles file
- `files["title_changes"]`: Path and hash of title changes suggestions file
- `files["sanitized"]`: Path and hash of sanitized markdown file
- File hashes used for integrity validation (prevents editing files outside system)

**Query Patterns**:
- `SELECT * FROM works WHERE id = ?` (get work by ID)
- `SELECT * FROM works ORDER BY id DESC` (list all works)
- `UPDATE works SET files = ? WHERE id = ?` (update file metadata)

### `prompt_meta`

**Schema**:
- `id` (INTEGER, PRIMARY KEY)
- `function_tag` (VARCHAR, NOT NULL, UNIQUE, INDEXED) - e.g., "heading_improvement"
- `template` (TEXT, NOT NULL) - Prompt template content
- `description` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Usage in Sanitization**:
- Stores prompt templates for LLM operations
- `function_tag="heading_improvement"` used for title changes suggestions
- Templates include variables like `{work_title}`, `{titles_content}`, `{toc_content}`

**Query Patterns**:
- `SELECT * FROM prompt_meta WHERE function_tag = ?` (load template)

## File Naming Conventions

Files created during sanitization:

- `<base>.titles.md` - Extracted headings from original markdown
- `<base>.title_changes.md` - AI-suggested heading changes (format: `"line_num: new_title"`)
- `<base>.sanitized.md` - Final sanitized markdown (after applying changes or copying original)

Where `<base>` is derived from the original markdown filename (e.g., "work1" from "work1.md").

## Hash Validation

All sanitization files use hash validation to ensure integrity:

- **Stored Hash**: Hash stored in `work.files[file_key]["hash"]` in database
- **Current Hash**: Hash computed from file on disk using `compute_file_hash()`
- **Validation**: Hashes must match before operations (unless `force=True`)
- **Update**: Hash updated in database after file modifications
- **Read-Only Protection**: Files set to read-only after creation/modification to prevent external edits

