# Ticket: markdown-import-export.T03 - Import Core Logic (Sanitized Markdown Path)

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement core import logic for sanitized markdown files
- Create Work records with MARKDOWN_IMPORT file type
- Integrate with existing chunking pipeline

## Scope
### In scope
- Core function: list_markdown_files() -> list[MarkdownFile] to scan input folder
- Core function: extract_metadata(file_path: str) -> Optional[Metadata] to parse YAML frontmatter
- Core function: import_sanitized_markdown(file_path: str, metadata: Metadata, session: Session) -> Work
- Integration with chunk_simple module for chunking headings and content
- Setting chunks to TO_VEC status after import

### Out of scope
- Unsanitized markdown import (covered in T04)
- Duplicate detection (covered in T06)
- API endpoints (covered in T07)
- Frontend UI components

## Dependencies
- Depends on: T01
- Unblocks: T04, T07

## Implementation plan
1. Create src/vulcanlab/markdown_import/metadata.py:
   - Define MarkdownFile dataclass: filename, file_path, has_metadata, metadata (optional)
   - Define Metadata dataclass: title, author, year
   - Implement extract_metadata(file_path: str) -> Optional[Metadata]:
     - Read file, parse YAML frontmatter between --- delimiters
     - Extract title, author, year fields
     - Return Metadata or None if not found/invalid
     - Handle YAML parsing errors gracefully
2. Create src/vulcanlab/markdown_import/scanner.py:
   - Implement list_markdown_files() -> list[MarkdownFile]:
     - Load config for paths.input_dir
     - Scan for all .md files in input directory
     - For each file, call extract_metadata()
     - Return list of MarkdownFile objects
3. Create src/vulcanlab/markdown_import/import_flow.py:
   - Implement import_sanitized_markdown(file_path: str, metadata: Metadata, session: Session) -> Work:
     - Create Work record with FileType.MARKDOWN_IMPORT
     - Set title, authors (from metadata.author), publication_year
     - Read markdown content (strip frontmatter if present)
     - Store in work.sanitized_markdown field
     - Store file info in work.files JSON: {"original_file": {"path": file_path, "type": "markdown"}}
     - Commit work to DB
     - Call chunk_simple.chunk_headings(work, session)
     - Call chunk_simple.chunk_content(work, session)
     - Set all chunks to ChunkVectorStatus.TO_VEC
     - Log import operation
     - Return created work
4. Patterns to apply:
   - Core module independence: No FastAPI imports
   - Session management: Pass session explicitly
   - Configuration: Use vulcanlab.config.load_config()
   - Error handling: Raise domain exceptions (ValueError, FileNotFoundError)
   - Reuse: Leverage existing chunk_simple module
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - extract_metadata() with valid YAML frontmatter returns Metadata
  - extract_metadata() with missing frontmatter returns None
  - extract_metadata() with invalid YAML returns None
  - extract_metadata() handles missing title/author/year fields gracefully
  - list_markdown_files() scans input directory correctly
  - list_markdown_files() calls extract_metadata() for each file
  - import_sanitized_markdown() creates Work with MARKDOWN_IMPORT type
  - import_sanitized_markdown() stores metadata correctly
  - import_sanitized_markdown() stores sanitized markdown in correct field
  - import_sanitized_markdown() calls chunking functions
  - import_sanitized_markdown() sets chunks to TO_VEC status
  - import_sanitized_markdown() handles file read errors
- Suggested locations:
  - tests/unit/test_markdown_metadata.py
  - tests/unit/test_markdown_scanner.py
  - tests/unit/test_markdown_import.py
- Mocking/fakes needed:
  - Mock file system (Path.glob, Path.read_text)
  - Mock database session and Work model
  - Mock chunk_simple.chunk_headings() and chunk_content()
  - Mock config loader

## Acceptance criteria (checklist)
- [ ] list_markdown_files() returns all .md files from input directory
- [ ] extract_metadata() correctly parses YAML frontmatter
- [ ] extract_metadata() handles missing/invalid metadata gracefully
- [ ] import_sanitized_markdown() creates Work with FileType.MARKDOWN_IMPORT
- [ ] Work record contains title, author, year from metadata
- [ ] Markdown content stored in work.sanitized_markdown field
- [ ] Chunking functions are called after work creation
- [ ] All chunks set to TO_VEC status
- [ ] Import operation is logged
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Create test markdown file with YAML frontmatter in input folder
  2. Call list_markdown_files() and verify file is listed
  3. Call extract_metadata() on test file, verify metadata extracted
  4. Call import_sanitized_markdown() with file path and metadata
  5. Query database for created work, verify fields
  6. Check that chunks were created with TO_VEC status
- Expected results:
  - Work record created with MARKDOWN_IMPORT type
  - Metadata fields populated correctly
  - Markdown content stored in sanitized_markdown field
  - Chunks created and ready for vectorization

## Notes
- YAML frontmatter must be at the start of file (first line must be ---)
- Content after frontmatter should have leading/trailing whitespace stripped
- If frontmatter parsing fails, treat as file without metadata (don't fail import)
- Year should be validated as integer (reject strings like "2023-01-01")
- Author field should support multiple authors (comma-separated) but store as single string
- Chunking may fail if markdown structure is invalid; handle gracefully and log error
