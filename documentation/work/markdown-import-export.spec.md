# Title: Markdown Import/Export

## Summary
- Add a new "MD Import/Export" navigation item with two separate pages: Export and Import
- Export page lists all corpus works and allows exporting their sanitized markdown to an `exports` subfolder with YAML frontmatter metadata
- Import page lists all markdown files from input folder and database, allowing users to import them into the corpus
- Import workflow supports both sanitized and unsanitized markdown, following the simple conversion pipeline
- Integration with existing Work model, corpus display, and vectorization queue

## Problem / Context
- Users currently cannot easily export corpus works as standalone markdown files with metadata
- There is no way to import existing markdown documents into the RAG system without converting from PDF/EPUB
- Users with pre-existing markdown content (notes, articles, documentation) cannot leverage the RAG capabilities
- Exporting processed works would enable sharing, backup, and external editing workflows

## Goals
- Enable export of corpus works as markdown files with metadata to `exports` subfolder
- Enable import of arbitrary markdown files into the corpus pipeline
- Maintain compatibility with existing simple conversion and vectorization workflows
- Provide clear UX for metadata entry and sanitization decisions during import
- Support duplicate detection to prevent accidental re-imports

## Non-goals (Strict)
- Advanced markdown editing capabilities within the UI
- Version control or diff tracking for exported/imported markdown
- Bulk import/export operations with batch processing
- Support for non-markdown text formats during import
- Automatic metadata extraction from markdown content using LLMs

## Scope
### In scope
- Export functionality that writes markdown files with YAML frontmatter to `exports` subfolder
- Import functionality that reads markdown from input folder and creates Work records
- Metadata entry UI for title, author, and publication year
- Modal for user to indicate if markdown is sanitized
- Integration with simple conversion sanitization pipeline
- Duplicate detection based on title/author
- Status page redirection for import progress monitoring
- Two separate pages under `/markdown` route with tab navigation
- Navigation item always visible (not dependent on advanced mode)

### Out of scope
- Editing markdown content within the UI
- Exporting works that don't have markdown available
- Importing non-markdown file formats
- Automated metadata extraction or inference
- Custom metadata field configuration
- Export scheduling or automation

## Requirements (Functional)
- R1: Export page must list all corpus works (both simple and advanced conversion) in a unified table
- R2: Clicking a work on export page must copy its sanitized markdown to `{output_dir}/exports/{filename}.md`
- R3: Exported markdown must include YAML frontmatter with title, author, and year fields
- R4: Export must intelligently source markdown from DB (simple conversion) or output folder (advanced conversion)
- R5: If markdown is unavailable for a work, show error and prevent export
- R6: Import page must list all `.md` files from input folder and markdown works from database
- R7: When user selects a markdown file for import, prompt for metadata (title, author, year)
- R8: If metadata exists in YAML frontmatter, pre-populate the entry form
- R9: After metadata entry, show modal asking if markdown is sanitized
- R10: If user indicates "sanitized", save to DB as sanitized_markdown and proceed to chunking
- R11: If user indicates "not sanitized", save to DB as original markdown and run sanitization
- R12: After sanitization/chunking, redirect to status page (similar to simple conversion)
- R13: Import must create Work record with FileType.MARKDOWN_IMPORT (or similar enum value)
- R14: After chunking, set chunks to TO_VEC status for manual vectorization
- R15: Before import, check for duplicate works with same title/author and warn user
- R16: Duplicate warning must allow user to proceed or cancel
- R17: Add "MD Import/Export" navigation item always visible in nav bar
- R18: Route structure must be `/markdown/export` and `/markdown/import` with tab navigation between them

## Requirements (Non-functional)
- Performance:
  - Export operation must complete in < 2 seconds for typical markdown files (< 1MB)
  - Import file listing must load in < 1 second
  - Metadata form validation must be instant (< 100ms)
- Reliability:
  - Export must not corrupt or modify source markdown content
  - Import must validate markdown syntax before processing
  - Failed imports must not leave partial Work records in database
  - All database operations must be transactional
- Security / Privacy:
  - Validate file paths to prevent directory traversal attacks
  - Sanitize user-provided metadata to prevent injection attacks
  - Restrict export to configured output directory only
  - Restrict import to configured input directory only
- Observability:
  - Log all export operations with work ID and destination path
  - Log all import operations with filename and metadata
  - Log sanitization decisions (sanitized vs not sanitized)
  - Track import errors and sanitization failures

## Proposed Solution (High-level)
- Add new navigation item "MD Import/Export" to nav-bar.tsx with FileImport icon
- Create `/markdown/export` page component for export functionality
- Create `/markdown/import` page component for import functionality
- Add shared tab navigation component to switch between export and import pages
- Export page queries corpus API and displays works in a table
- Export button triggers API call to `/api/v1/markdown/export/{work_id}` which writes file to exports subfolder
- Import page queries new endpoint `/api/v1/markdown/files` to list available markdown files
- Import button opens metadata entry modal with form validation
- After metadata entry, show sanitization decision modal
- Import API endpoint `/api/v1/markdown/import` creates Work record and triggers pipeline
- Reuse existing sanitization logic from simple_conversion module
- Reuse existing chunking logic from simple_conversion module
- Status page monitoring reuses simple conversion status infrastructure

## Interfaces / APIs / Contracts

### API Endpoints (all under `/api/v1/markdown`)

**GET /api/v1/markdown/files**
- Returns list of available markdown files for import
- Response: `{ files: [{ filename: string, file_path: string, has_metadata: boolean, metadata?: { title: string, author: string, year: number } }] }`

**POST /api/v1/markdown/export/{work_id}**
- Exports work's sanitized markdown to exports subfolder
- Request body: None
- Response: `{ success: boolean, export_path: string }` or error
- Errors: 404 (work not found), 400 (markdown not available), 500 (write failed)

**POST /api/v1/markdown/import**
- Imports markdown file and creates Work record
- Request body: `{ filename: string, title: string, author: string, year: number, is_sanitized: boolean }`
- Response: `{ work_id: number, status: string }` or error
- Errors: 400 (invalid metadata, duplicate work), 404 (file not found), 500 (processing failed)

**GET /api/v1/markdown/check-duplicate**
- Checks if work with title/author already exists
- Query params: `title`, `author`
- Response: `{ exists: boolean, work_id?: number, work_title?: string }`

### Database Changes
- Add new FileType enum value: `MARKDOWN_IMPORT`
- No schema changes required; use existing Work model files JSON structure
- Store markdown in `converted_markdown` or `sanitized_markdown` fields based on workflow

### Core Module Functions
- `vulcanlab.markdown_import.list_markdown_files() -> list[MarkdownFile]`
- `vulcanlab.markdown_import.extract_metadata(file_path: str) -> Optional[Metadata]`
- `vulcanlab.markdown_import.import_markdown(file_path: str, metadata: Metadata, is_sanitized: bool, session: Session) -> Work`
- `vulcanlab.markdown_export.export_work(work_id: int, session: Session) -> str` (returns export path)
- `vulcanlab.markdown_export.get_markdown_source(work: Work) -> tuple[str, str]` (returns content and source)

## Data Model / Storage
- Leverage existing Work model with files JSON structure
- Add FileType.MARKDOWN_IMPORT enum value to enums.py
- For sanitized imports: `{ "original_file": { "path": "/path/to/file.md", "type": "markdown" }, "sanitized_markdown": "content" }`
- For unsanitized imports: `{ "original_file": { "path": "/path/to/file.md", "type": "markdown" }, "converted_markdown": "original", "sanitized_markdown": "after_sanitization" }`
- Export reads from `sanitized_markdown` field or falls back to output folder for advanced conversions

## UX / Workflows

### Export Workflow
1. User navigates to `/markdown/export`
2. System displays table of all corpus works (ID, Title, Authors)
3. User clicks "Export" button for a work
4. System validates markdown availability
5. If unavailable, show error modal
6. If available, write markdown with frontmatter to `{output_dir}/exports/{work_title_slug}.md`
7. Show success toast with export path
8. User can click work row to view in corpus detail page (existing functionality)

### Import Workflow
1. User navigates to `/markdown/import`
2. System displays list of all markdown files from input folder and DB
3. User selects a markdown file and clicks "Import"
4. System checks for existing metadata in frontmatter
5. Show metadata entry modal with pre-populated fields if available
6. User fills in title, author, year (required fields)
7. User submits metadata
8. System checks for duplicate work with same title/author
9. If duplicate exists, show warning modal with "Proceed" and "Cancel" options
10. If user cancels, return to file list
11. If user proceeds, show sanitization decision modal: "Is this markdown sanitized?"
12. If "Yes (sanitized)": Save as sanitized_markdown, skip to chunking
13. If "No (needs sanitization)": Save as original, run sanitization, then chunking
14. Redirect to status page (like simple conversion) showing progress
15. After completion, chunks are set to TO_VEC status
16. User can navigate to Vectorization page to complete embedding

## Testing Plan
- Unit tests:
  - Test markdown file listing from input folder
  - Test metadata extraction from YAML frontmatter
  - Test export path generation and file writing
  - Test duplicate detection logic
  - Test sanitization decision branching
  - Test Work record creation with correct FileType
  - Mock database sessions and file I/O operations
- Integration tests:
  - Test full import workflow with sanitized markdown
  - Test full import workflow with unsanitized markdown
  - Test export of simple conversion work
  - Test export of advanced conversion work
  - Test error handling for missing markdown
  - Test duplicate warning and user decision flow
  - Not required for ticket unless explicitly requested
- Manual test plan:
  - Export a simple conversion work and verify frontmatter format
  - Export an advanced conversion work and verify content correctness
  - Import a markdown file with frontmatter and verify metadata pre-population
  - Import a markdown file without frontmatter and manually enter metadata
  - Import unsanitized markdown and verify sanitization runs
  - Import sanitized markdown and verify it skips to chunking
  - Attempt to import duplicate work and verify warning appears
  - Proceed with duplicate import and verify work is created
  - Cancel duplicate import and verify no work is created
  - Navigate between export and import pages using tabs
  - Verify navigation item is always visible
  - Monitor import progress on status page
  - Verify imported work appears in corpus
  - Queue imported work for vectorization and verify TO_VEC status

## Acceptance Criteria (Checklist)
- [ ] "MD Import/Export" navigation item appears in nav bar and is always visible
- [ ] Export page displays all corpus works in a unified table
- [ ] Clicking "Export" button writes markdown with YAML frontmatter to exports subfolder
- [ ] Export intelligently sources markdown from DB or output folder based on conversion type
- [ ] Export shows error if markdown is unavailable for a work
- [ ] Import page lists all markdown files from input folder and database
- [ ] Clicking "Import" opens metadata entry modal
- [ ] Metadata form pre-populates if YAML frontmatter exists
- [ ] After metadata entry, sanitization decision modal appears
- [ ] Sanitized markdown skips sanitization and proceeds to chunking
- [ ] Unsanitized markdown runs through sanitization before chunking
- [ ] Import redirects to status page showing progress
- [ ] Duplicate detection warns user before import
- [ ] User can proceed or cancel when duplicate is detected
- [ ] Imported works appear in corpus with correct metadata
- [ ] Imported chunks are set to TO_VEC status
- [ ] Tab navigation works between export and import pages
- [ ] All API endpoints return correct responses and error codes
- [ ] Unit tests pass for all core module functions

## Rollout / Migration Plan
- Add FileType.MARKDOWN_IMPORT enum value to enums.py (no migration needed, enum is in code)
- No database schema changes required
- Deploy backend API endpoints first
- Deploy frontend pages and navigation updates
- Test with sample markdown files in staging environment
- Document export/import workflows in user guide
- No data migration needed as this is a new feature

## Risks and Alternatives
- Risks:
  - Large markdown files (> 10MB) may cause performance issues during import/export
  - Sanitization may alter markdown content unexpectedly if user misclassifies as "not sanitized"
  - Duplicate detection based only on title/author may miss true duplicates with slight variations
  - Export folder may accumulate many files without cleanup mechanism
- Alternatives considered:
  - Alternative 1: Single page with tabs instead of separate routes
    - Rejected: Separate routes provide better URL structure and bookmarking
  - Alternative 2: Automatic metadata extraction using LLMs
    - Rejected: Adds complexity and LLM cost, better to require user input
  - Alternative 3: In-place editing of markdown before import
    - Rejected: Out of scope, users can edit externally before import
  - Alternative 4: Support multiple file formats (TXT, DOCX, etc.)
    - Rejected: Markdown-only keeps scope manageable, other formats can be converted externally

## Patterns and Standards Alignment (from documentation/patterns.md)
- Patterns applied:
  - Three-tier architecture: Core module in `src/vulcanlab/markdown_import` and `src/vulcanlab/markdown_export`, API layer in `src/vulcanlab_api/routers/markdown.py`, Frontend in `vulcanlab_ui/src/app/markdown/`
  - Database session management: Pass session explicitly to core module functions
  - API versioning: All endpoints under `/api/v1/markdown` prefix
  - Error handling: Use HTTPException for API errors, let global handler catch unhandled exceptions
  - Configuration: Use `vulcanlab.config.json` for paths.output_dir and paths.input_dir
  - Frontend: Next.js App Router, client components for interactivity, Shadcn/Radix UI for modals and forms
  - Naming: snake_case in Python, camelCase in TypeScript, kebab-case for routes
- Deviations (if any):
  - None: This feature follows all established patterns

## Implementation Notes (Non-binding)
- Reuse existing `ConversionSettingsContext` pattern for any configuration needs
- Export filename should be slugified version of work title (lowercase, hyphens, remove special chars)
- Consider using existing `ConfirmDeleteModal` pattern for duplicate warning modal
- Status page for import can reuse existing simple conversion status page component structure
- YAML frontmatter should use triple-dash delimiters and follow standard YAML syntax
- Metadata validation should enforce non-empty strings for title/author and valid integer for year
- Consider adding export count to work table in UI (bonus feature, not required)
- May want to add "last exported" timestamp to work record (future enhancement)
- Export folder should be created automatically if it doesn't exist
- Consider logging export/import operations to separate log file for audit trail

## Open Questions
- Q1: Should there be a limit on markdown file size for import (e.g., 10MB max)?
- Q2: Should export overwrite existing files in exports folder or create versioned filenames?
- Q3: Should the system automatically clean up old exports or leave that to user/admin?
- Q4: Should imported works be distinguishable in the corpus UI (e.g., icon or badge)?
- Q5: Should there be a way to re-export a work that was previously exported (e.g., after updates)?
