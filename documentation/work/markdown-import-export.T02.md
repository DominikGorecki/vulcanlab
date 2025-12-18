# Ticket: markdown-import-export.T02 - Export Core Logic and API Endpoint

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement core export logic to retrieve markdown from Work and write to exports folder
- Create API endpoint for exporting individual works
- Support intelligent markdown sourcing (DB for simple conversion, folder for advanced)

## Scope
### In scope
- Core function: export_work(work_id: int, session: Session) -> str in markdown_export module
- Core function: get_markdown_source(work: Work) -> tuple[str, str] to retrieve markdown content
- Helper: generate_export_filename(title: str) -> str for slugification
- Helper: create_frontmatter(title: str, author: str, year: int) -> str for YAML generation
- API router: POST /api/v1/markdown/export/{work_id}
- Error handling for missing markdown

### Out of scope
- Frontend UI components
- Batch export operations
- Export history tracking
- File versioning or overwrite handling (overwrite by default)

## Dependencies
- Depends on: T01
- Unblocks: T05

## Implementation plan
1. Create src/vulcanlab/markdown_export/export.py with core functions:
   - get_markdown_source(work: Work) -> tuple[str, str]:
     - If work.file_type is SIMPLE_CONVERSION, return (work.sanitized_markdown, "db")
     - Else check for sanitized markdown file in output folder using work.files JSON
     - Return (content, source) or raise ValueError if not found
   - generate_export_filename(title: str) -> str:
     - Convert to lowercase, replace spaces with hyphens
     - Remove special characters (keep only alphanumeric and hyphens)
     - Limit to 100 characters, add .md extension
   - create_frontmatter(title: str, author: str, year: int) -> str:
     - Generate YAML frontmatter with triple-dash delimiters
     - Format: "---\ntitle: {title}\nauthor: {author}\nyear: {year}\n---\n"
   - export_work(work_id: int, session: Session) -> str:
     - Query work by ID, raise HTTPException(404) if not found
     - Call get_markdown_source(work)
     - Generate filename using generate_export_filename(work.title)
     - Create full markdown with frontmatter + content
     - Write to exports_dir / filename
     - Log export operation
     - Return export path as string
2. Create src/vulcanlab_api/routers/markdown.py:
   - Define router with prefix configured in main.py
   - POST /export/{work_id} endpoint:
     - Get database session
     - Call export_work(work_id, session)
     - Return { "success": true, "export_path": path }
     - Handle errors: 404 (work not found), 400 (markdown unavailable), 500 (write failed)
3. Register router in src/vulcanlab_api/main.py:
   - app.include_router(markdown_router, prefix="/api/v1/markdown")
4. Patterns to apply:
   - Three-tier architecture: Core logic in vulcanlab module, API in vulcanlab_api
   - Session management: Pass session explicitly to export_work()
   - API versioning: /api/v1/markdown prefix
   - Error handling: Raise HTTPException for API errors
   - Configuration: Use get_exports_dir() from T01
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - generate_export_filename() with various titles (spaces, special chars, long titles)
  - create_frontmatter() generates valid YAML with correct format
  - get_markdown_source() returns DB content for simple conversion works
  - get_markdown_source() reads from output folder for advanced conversion works
  - get_markdown_source() raises ValueError when markdown unavailable
  - export_work() successfully writes file with frontmatter
  - export_work() raises 404 for non-existent work_id
  - export_work() raises 400 when markdown unavailable
  - API endpoint returns correct response format
  - API endpoint handles errors correctly
- Suggested locations:
  - tests/unit/test_markdown_export.py
  - tests/unit/test_markdown_export_api.py
- Mocking/fakes needed:
  - Mock database session and Work query
  - Mock file I/O (Path.write_text)
  - Mock get_exports_dir()
  - Mock logger for log verification

## Acceptance criteria (checklist)
- [ ] export_work() creates markdown file with YAML frontmatter in exports folder
- [ ] Exported filename is slugified version of work title
- [ ] Frontmatter includes title, author, and year fields
- [ ] Export intelligently sources from DB or output folder based on work type
- [ ] API endpoint POST /api/v1/markdown/export/{work_id} returns success response
- [ ] API returns 404 for non-existent work
- [ ] API returns 400 for work without available markdown
- [ ] Export operation is logged with work ID and path
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Create a test work in database with sanitized markdown
  2. Call API: POST /api/v1/markdown/export/{work_id}
  3. Check exports folder for generated file
  4. Verify file has YAML frontmatter with correct metadata
  5. Verify file content matches work's sanitized markdown
  6. Try exporting work without markdown, verify 400 error
- Expected results:
  - Export file created at {output_dir}/exports/{slugified-title}.md
  - File contains valid YAML frontmatter
  - File content matches source markdown
  - Appropriate errors returned for invalid requests

## Notes
- Filename slugification should handle Unicode characters gracefully (transliterate or remove)
- If multiple works have same title, later exports will overwrite (acceptable for now, Q2 in spec)
- YAML frontmatter must use standard YAML syntax (string values in quotes if they contain special chars)
- For advanced conversion, look for sanitized markdown file path in work.files JSON structure
- Consider max file size check (warn if > 10MB) but don't block export
