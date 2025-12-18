# Ticket: markdown-import-export.T04 - Import Unsanitized Markdown Path

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement import logic for unsanitized markdown that requires sanitization
- Integrate with simple_conversion sanitization pipeline
- Support both sanitized and unsanitized workflows

## Scope
### In scope
- Core function: import_unsanitized_markdown(file_path: str, metadata: Metadata, session: Session) -> Work
- Integration with simple_conversion.sanitize_small or sanitize_large based on size
- Store original markdown, then sanitized version
- Reuse existing sanitization logic

### Out of scope
- Creating new sanitization logic (reuse existing)
- API endpoints (covered in T07)
- Frontend UI components
- Token classification logic (reuse from simple_conversion)

## Dependencies
- Depends on: T03
- Unblocks: T07

## Implementation plan
1. Extend src/vulcanlab/markdown_import/import_flow.py:
   - Implement import_unsanitized_markdown(file_path: str, metadata: Metadata, session: Session) -> Work:
     - Create Work record with FileType.MARKDOWN_IMPORT
     - Set title, authors, publication_year from metadata
     - Read markdown content (strip frontmatter if present)
     - Store in work.converted_markdown field (original unsanitized)
     - Store file info in work.files JSON
     - Commit work to DB
     - Count tokens in markdown using tiktoken (same as parse_classify module)
     - If token count < threshold: call sanitize_small.sanitize_small_document()
     - If token count >= threshold: call sanitize_large.sanitize_large_document()
     - Store sanitized result in work.sanitized_markdown field
     - Update work record in DB
     - Call chunk_simple.chunk_headings(work, session)
     - Call chunk_simple.chunk_content(work, session)
     - Set all chunks to ChunkVectorStatus.TO_VEC
     - Log import and sanitization operations
     - Return created work
2. Add helper function: determine_sanitization_method(content: str) -> str:
   - Count tokens using tiktoken (reuse from simple_conversion.parse_classify)
   - Compare to threshold from config
   - Return "small" or "large"
3. Patterns to apply:
   - Reuse existing sanitization: Import and call sanitize_small/sanitize_large from simple_conversion
   - Configuration: Use get_token_threshold() from conversion_config
   - Session management: Pass session explicitly
   - Error handling: Handle sanitization failures gracefully
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - determine_sanitization_method() returns "small" for content below threshold
  - determine_sanitization_method() returns "large" for content above threshold
  - import_unsanitized_markdown() creates Work with MARKDOWN_IMPORT type
  - import_unsanitized_markdown() stores original content in converted_markdown
  - import_unsanitized_markdown() calls appropriate sanitization function
  - import_unsanitized_markdown() stores sanitized content in sanitized_markdown
  - import_unsanitized_markdown() calls chunking after sanitization
  - import_unsanitized_markdown() sets chunks to TO_VEC status
  - import_unsanitized_markdown() handles sanitization errors
  - Token counting matches parse_classify behavior
- Suggested locations:
  - tests/unit/test_markdown_import.py (extend existing file)
  - tests/unit/test_markdown_import_unsanitized.py
- Mocking/fakes needed:
  - Mock database session and Work model
  - Mock sanitize_small.sanitize_small_document()
  - Mock sanitize_large.sanitize_large_document()
  - Mock chunk_simple functions
  - Mock tiktoken.get_encoding()
  - Mock config loader for token threshold

## Acceptance criteria (checklist)
- [ ] import_unsanitized_markdown() creates Work with FileType.MARKDOWN_IMPORT
- [ ] Original markdown stored in converted_markdown field
- [ ] Token count determines small vs large sanitization method
- [ ] Appropriate sanitization function called based on token count
- [ ] Sanitized markdown stored in sanitized_markdown field
- [ ] Chunking called after sanitization completes
- [ ] All chunks set to TO_VEC status
- [ ] Sanitization errors logged and handled gracefully
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Create small unsanitized markdown file (< 15000 tokens) in input folder
  2. Call import_unsanitized_markdown() with file path and metadata
  3. Verify sanitize_small was called (check logs)
  4. Query work from DB, verify converted_markdown and sanitized_markdown fields
  5. Verify chunks were created
  6. Create large unsanitized markdown file (> 15000 tokens)
  7. Call import_unsanitized_markdown() with large file
  8. Verify sanitize_large was called (check logs)
- Expected results:
  - Small files use sanitize_small
  - Large files use sanitize_large
  - Both original and sanitized markdown stored
  - Chunks created successfully

## Notes
- Token counting should use same encoding as simple_conversion (cl100k_base)
- Threshold should come from vulcanlab.config.json conversion.token_threshold
- Sanitization may modify markdown structure significantly; this is expected
- If sanitization fails completely, log error but don't leave work in broken state
- Consider adding sanitization status field to Work model (future enhancement, not required)
- Sanitization functions may call LLM; ensure proper error handling for API failures
