# Markdown Import/Export Page Documentation

## Overview

The Markdown Import/Export feature provides bidirectional workflow for managing markdown content in the corpus system. The Export page allows exporting corpus works as markdown files with embedded metadata, while the Import page allows importing markdown files with metadata collection, duplicate detection, and sanitization decisions.

### Pages

- **Export Page**: `/markdown/export` - Export corpus works as markdown files
- **Import Page**: `/markdown/import` - Import markdown files into the system

### Navigation

Both pages share a common layout with tab navigation to switch between Import and Export modes.

## Export Page

### User Workflow

1. Navigate to `/markdown/export`
2. View table of all corpus works (ID, Title, Authors)
3. Click "Export" button for desired work
4. System writes markdown file to configured export directory
5. Success toast shows export path
6. Optional: Click work row to view in corpus detail page

### Features

- **Works Table**: Displays all works in corpus with basic metadata
- **Individual Export**: Export one work at a time
- **Path Display**: Shows export file path on success
- **Error Handling**: Comprehensive error messages for various failure modes
- **Loading States**: Visual feedback during export operation
- **Navigation**: Click row to view work details

## Import Page

### User Workflow

1. Navigate to `/markdown/import`
2. View table of available markdown files in import directory
3. Click row to select file for import
4. **Metadata Entry Modal**:
   - Enter Title (required)
   - Enter Author (required)
   - Enter Year (optional, 1000-2100)
   - Pre-populated from embedded metadata if available
5. **Duplicate Check**: System checks for existing work with same title/author
6. **Duplicate Warning Modal** (if duplicate found):
   - Shows existing work ID and title
   - Option to proceed anyway or cancel
7. **Sanitization Decision Modal**:
   - Choose: "Yes, it's sanitized" or "No, needs sanitization"
   - Explains sanitization process
8. Submit to import
9. Redirect to `/simple-conversion/automatic/{work_id}` on success

### Features

- **File List**: Table of available markdown files with metadata indicator
- **Metadata Pre-population**: Auto-fill from embedded YAML frontmatter
- **Duplicate Detection**: Warns before creating duplicate works
- **Sanitization Selection**: User decides if content needs sanitization
- **Multi-step Modals**: Guided workflow with clear progression
- **Error Handling**: Detailed error messages for various failure scenarios
- **Loading States**: Visual feedback during async operations

## API Calls

### Export Page API Calls

#### GET `/corpus/works`

**Called By**: Export page on component mount

**Request**: No parameters

**Response**:
```json
{
  "works": [
    {
      "id": 45,
      "title": "Introduction to Psychology",
      "authors": "John Doe"
    },
    {
      "id": 46,
      "title": "Cognitive Science Fundamentals",
      "authors": "Jane Smith"
    }
  ],
  "total": 2
}
```

**Purpose**: Fetch list of all corpus works for export selection.

#### POST `/api/v1/markdown/export/{workId}`

**Called By**: Export page when user clicks "Export" button

**Request**: Path parameter `workId` (integer)

**Response** (Success):
```json
{
  "success": true,
  "message": "Work exported successfully",
  "export_path": "/data/exports/introduction-to-psychology-45.md",
  "work_id": 45
}
```

**Response** (Error - Work Not Found):
```json
{
  "error": "work_not_found",
  "message": "Work not found",
  "detail": "Work with ID 45 does not exist or was deleted"
}
```

**Response** (Error - No Content):
```json
{
  "error": "no_sanitized_content",
  "message": "Cannot export work",
  "detail": "Work has no sanitized markdown content to export"
}
```

**Response** (Error - Disk Full):
```json
{
  "error": "disk_full",
  "message": "Export failed",
  "detail": "Insufficient disk space to write export file"
}
```

**Purpose**: Export a corpus work as markdown file with YAML frontmatter metadata.

**Export Format**:
```markdown
---
title: Introduction to Psychology
author: John Doe
year: 2024
work_id: 45
exported_at: 2024-12-09T15:30:00Z
---

# Introduction to Psychology

## Chapter 1: Foundations

...
```

### Import Page API Calls

#### GET `/api/v1/markdown/files`

**Called By**: Import page on component mount

**Request**: No parameters

**Response**:
```json
{
  "files": [
    {
      "filename": "cognitive-science.md",
      "file_path": "/data/imports/cognitive-science.md",
      "has_metadata": true,
      "metadata": {
        "title": "Cognitive Science Fundamentals",
        "author": "Jane Smith",
        "year": 2023
      }
    },
    {
      "filename": "neuroscience-basics.md",
      "file_path": "/data/imports/neuroscience-basics.md",
      "has_metadata": false,
      "metadata": null
    }
  ]
}
```

**Purpose**: List all markdown files in configured import directory with embedded metadata detection.

**Metadata Detection**: Parses YAML frontmatter if present, otherwise `has_metadata = false`.

#### GET `/api/v1/markdown/check-duplicate`

**Called By**: Import page after user submits metadata, before showing sanitization modal

**Request Parameters**:
- `title` (string, required): Work title
- `author` (string, required): Work author

**Response** (No Duplicate):
```json
{
  "exists": false
}
```

**Response** (Duplicate Found):
```json
{
  "exists": true,
  "work_id": 45,
  "work_title": "Introduction to Psychology"
}
```

**Purpose**: Check if a work with the same title and author already exists in the database.

**Matching Logic**: Case-insensitive match on both title and author fields.

#### POST `/api/v1/markdown/import`

**Called By**: Import page after user confirms sanitization decision

**Request**:
```json
{
  "filename": "cognitive-science.md",
  "title": "Cognitive Science Fundamentals",
  "author": "Jane Smith",
  "year": 2023,
  "is_sanitized": false
}
```

**Response** (Success):
```json
{
  "work_id": 47,
  "status": "imported",
  "duplicate_warning": null
}
```

**Response** (Success with Duplicate Warning):
```json
{
  "work_id": 47,
  "status": "imported",
  "duplicate_warning": "A work with this title and author already exists (ID: 45)"
}
```

**Response** (Error - File Not Found):
```json
{
  "error": "file_not_found",
  "message": "File not found",
  "detail": "File 'cognitive-science.md' does not exist in import directory"
}
```

**Response** (Error - Empty File):
```json
{
  "error": "empty_file",
  "message": "Import failed",
  "detail": "File is empty or contains only whitespace"
}
```

**Response** (Error - No Content):
```json
{
  "error": "no_content",
  "message": "Import failed",
  "detail": "File contains only metadata frontmatter, no actual content"
}
```

**Response** (Error - Encoding):
```json
{
  "error": "encoding_error",
  "message": "Import failed",
  "detail": "File encoding not supported. Please use UTF-8."
}
```

**Response** (Error - Permission Denied):
```json
{
  "error": "permission_denied",
  "message": "Import failed",
  "detail": "Insufficient permissions to read file"
}
```

**Response** (Error - Chunking Failed):
```json
{
  "error": "chunking_failed",
  "message": "Import failed",
  "detail": "Failed to parse markdown structure for chunking"
}
```

**Response** (Error - Sanitization Failed):
```json
{
  "error": "sanitization_failed",
  "message": "Import failed",
  "detail": "Content sanitization process encountered an error"
}
```

**Purpose**: Import markdown file into database, optionally sanitizing content.

**Post-Import Behavior**: Returns work_id which is used to redirect to `/simple-conversion/automatic/{work_id}` for further processing.

## API Implementation

### Backend Modules Used

**Markdown API Router**: `src/vulcanlab/api/markdown.py`
- `list_files()` - List import directory
- `export_work()` - Export work to markdown
- `import_work()` - Import markdown to database
- `check_duplicate()` - Duplicate detection

**Markdown Service**: `src/vulcanlab/services/markdown_service.py`
- `parse_frontmatter()` - YAML metadata extraction
- `format_export()` - Generate export markdown with metadata
- `validate_markdown()` - Content validation
- `write_export_file()` - File I/O for export
- `read_import_file()` - File I/O for import

**Sanitization Service**: `src/vulcanlab/sanitization/sanitizer.py`
- `sanitize_content()` - Clean and normalize markdown
- `extract_structure()` - Parse heading hierarchy

**Chunking Service**: `src/vulcanlab/chunking/chunker.py`
- `chunk_markdown()` - Generate chunks from sanitized content

### Export Implementation

**Process**:
1. Validate work exists and has sanitized content
2. Fetch work metadata from database
3. Format markdown with YAML frontmatter:
   ```yaml
   ---
   title: Work Title
   author: Author Name
   year: 2024
   work_id: 45
   exported_at: 2024-12-09T15:30:00Z
   ---
   ```
4. Append sanitized markdown content
5. Generate filename: `{slugified-title}-{work_id}.md`
6. Write to configured export directory
7. Return export path

**File Naming**:
- Slugify title (lowercase, hyphens, remove special chars)
- Append work ID for uniqueness
- Example: `introduction-to-psychology-45.md`

**Error Handling**:
- Check disk space before writing
- Handle permission errors
- Validate write operation success

### Import Implementation

**Process**:
1. Read file from import directory
2. Parse YAML frontmatter (if present)
3. Extract markdown content (strip frontmatter)
4. Validate content is non-empty
5. Create work record in database
6. If `is_sanitized = True`:
   - Store content as sanitized_md
   - Set status to 'sanitized'
7. If `is_sanitized = False`:
   - Store content as original_md
   - Queue for sanitization workflow
   - Set status to 'needs_sanitization'
8. Return work_id

**YAML Frontmatter Parsing**:
```python
import yaml

def parse_frontmatter(content: str):
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            metadata = yaml.safe_load(parts[1])
            markdown = parts[2].strip()
            return metadata, markdown
    return None, content
```

**Duplicate Detection**:
```sql
SELECT id, title FROM works
WHERE LOWER(title) = LOWER($1)
  AND LOWER(authors) = LOWER($2)
LIMIT 1;
```

### File Listing Implementation

**Process**:
1. Scan configured import directory
2. Filter for `.md` files
3. For each file:
   - Read first 1KB to detect frontmatter
   - Parse YAML if present
   - Extract metadata fields (title, author, year)
4. Return file list with metadata info

**Directory Configuration**: Import/export directories set in application settings.

## Database Tables

### works

**Description**: Stores work records with markdown content

**Key Fields for Import/Export**:
- `id` (INTEGER PRIMARY KEY): Work identifier
- `title` (TEXT): Work title
- `authors` (TEXT): Author name(s)
- `year` (INTEGER): Publication year
- `original_md` (TEXT): Original markdown (before sanitization)
- `sanitized_md` (TEXT): Cleaned markdown (after sanitization)
- `status` (TEXT): Processing status (sanitized, needs_sanitization, etc.)
- `created_at` (TIMESTAMP): Import timestamp

**Usage**:
- Export: Read from `sanitized_md`, format with metadata, write to file
- Import: Write to `original_md` or `sanitized_md` based on user choice

## UI Components

### MarkdownTabs

**Location**: `/src/components/markdown/MarkdownTabs.tsx`

**Purpose**: Tab navigation between Import and Export pages

**Features**:
- Client-side tab component
- Detects active tab from pathname
- Navigates on tab click

### ErrorModal

**Location**: Shared component for both pages

**Purpose**: Display detailed error information

**Features**:
- Shows error title and message
- Optional detail section for technical information
- Close button

### Export Page Components

**WorksTable**:
- Sortable columns (ID, Title, Authors)
- Export button per row with loading state
- Click row to navigate to corpus detail

**EmptyState**: Displayed when no works exist

**ErrorCard**: Displayed when fetch fails, includes retry button

### Import Page Components

**FilesTable**:
- Displays filename and metadata indicator
- Click row to start import workflow

**MetadataEntryModal**:
- Form fields: Title (required), Author (required), Year (optional)
- Pre-populates from file metadata if available
- Validation: Year must be 1000-2100
- Enter key support for submission

**DuplicateWarningModal**:
- Shows existing work ID and title
- "Proceed Anyway" and "Cancel" buttons
- Warning message about duplicate

**SanitizationDecisionModal**:
- Explains what sanitization does
- Two options: "Yes, it's sanitized" or "No, needs sanitization"
- Disabled during import processing
- Shows loading spinner during import

**EmptyState**: Displayed when no files found in import directory

## Key Features

### Export Features

1. **Metadata Embedding**: YAML frontmatter with all bibliographic info
2. **Unique Filenames**: Slugified title + work ID prevents conflicts
3. **Path Display**: Shows user exactly where file was written
4. **Batch Export**: Could be extended to export multiple works
5. **Error Recovery**: Clear error messages for common issues

### Import Features

1. **Metadata Pre-population**: Auto-fill from embedded frontmatter
2. **Duplicate Detection**: Prevents accidental duplicates
3. **Sanitization Choice**: User decides if content needs processing
4. **Multi-step Workflow**: Guided process with clear progression
5. **Validation**: Client and server-side validation
6. **Workflow Integration**: Redirects to processing page on success

### Shared Features

1. **Tab Navigation**: Easy switching between Import/Export
2. **Loading States**: Visual feedback during operations
3. **Error Handling**: Comprehensive error messages
4. **Empty States**: Friendly messages when no data available
5. **Responsive Design**: Mobile and desktop optimized

## Error Handling

### Export Errors

**work_not_found (404)**: Work doesn't exist or was deleted

**no_sanitized_content (400)**: Work has no sanitized content to export

**disk_full**: Insufficient disk space

**permission_denied**: Cannot write to export directory

**read_only**: Export directory is read-only

**file_not_found**: Internal error, work content missing

### Import Errors

**file_not_found (404)**: File doesn't exist in import directory

**empty_file (400)**: File is empty or only whitespace

**no_content (400)**: Only metadata, no actual content

**encoding_error (400)**: Unsupported file encoding (not UTF-8)

**permission_denied (403)**: Cannot read import file

**chunking_failed (500)**: Failed to parse markdown structure

**sanitization_failed (500)**: Sanitization process error

**validation_error (422)**: Invalid metadata or content

### Client-Side Validation

**Export Page**:
- No validation required (export button always enabled for valid works)

**Import Page**:
- Title and Author required (non-empty)
- Year must be numeric, 1000-2100 range (if provided)
- Prevents submission with invalid data

## Technical Implementation

**Framework**: Next.js 13+ App Router

**State Management**: React hooks (useState, useEffect, useCallback)

**Form Handling**: Controlled components with validation

**UI Library**: shadcn/ui (Card, Table, Button, Dialog, Input, Label, Toast)

**Icons**: Lucide React (FileUp, Download, Upload, AlertCircle, Loader2)

**Styling**: Tailwind CSS

**Navigation**: Next.js Link and useRouter

**File Handling**: Backend handles all file I/O

**YAML Parsing**: PyYAML library (backend)

**Toast Notifications**: shadcn/ui toast system

## Configuration

### Settings Required

**Export Directory**: System setting for where to write exported files

**Import Directory**: System setting for where to read import files

**Example Configuration**:
```python
EXPORT_DIR = "/data/exports"
IMPORT_DIR = "/data/imports"
```

### File Permissions

**Export**: Write permissions on export directory

**Import**: Read permissions on import directory and files

## Use Cases

### Export Use Case: Backup

**Goal**: Create backups of corpus works

**Workflow**:
1. Navigate to Export page
2. Export all works one by one
3. Files saved to configured backup directory
4. Files include all metadata for restore

### Export Use Case: Sharing

**Goal**: Share work with collaborators

**Workflow**:
1. Export work to markdown
2. Send file to collaborator
3. Collaborator imports using Import page
4. Metadata preserved in transition

### Import Use Case: Bulk Addition

**Goal**: Add pre-existing markdown documents to corpus

**Workflow**:
1. Copy markdown files to import directory
2. Optional: Add YAML frontmatter with metadata
3. Use Import page to add files
4. Select sanitization option
5. Files processed and ready for RAG

### Import Use Case: Restore from Backup

**Goal**: Restore work from export backup

**Workflow**:
1. Copy export file to import directory
2. Import file (metadata auto-populated from frontmatter)
3. Duplicate warning shown (expected for restore)
4. Proceed anyway if restoring deleted work
5. Work restored with all metadata

## Performance Considerations

**Export Performance**:
- Single file write per operation
- Large files (>10MB) may take seconds
- No concurrent export limit

**Import Performance**:
- Single file read per operation
- Large files parsed incrementally
- Sanitization may take time for large documents

**File Listing**:
- Scans directory on each page load
- Could be optimized with caching
- Frontmatter parsing limited to first 1KB

## Security Considerations

**Path Traversal**: Backend validates filenames to prevent directory traversal attacks

**File Size Limits**: Should implement max file size for imports

**Encoding Validation**: Only UTF-8 supported

**Sanitization**: Import content should be sanitized before storage

**Permissions**: Separate read (import) and write (export) directories for security
