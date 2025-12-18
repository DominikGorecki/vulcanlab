# Ticket: rag-parent-chunk-enrichment.T01 - Core Helper Functions for Content Processing

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement pure helper functions for sentence boundary detection, heading identification, and word counting
- Create the `truncate_to_word_limit()` function for sliding window truncation
- Establish testable foundation for parent-chunk enrichment logic

## Scope
### In scope
- `truncate_to_word_limit()` function that preserves sentences and headings
- Helper functions for sentence tokenization (spaCy-based with regex fallback)
- Helper function for markdown heading detection
- Helper function for accurate word counting
- Unit tests for all helper functions

### Out of scope
- Parent traversal logic (handled in T02)
- Database integration
- Consolidation logic
- Migration or UI changes

## Dependencies
- Depends on: none (pure functions)
- Unblocks: T02 (Parent Traversal Enrichment)

## Implementation plan
1. Create new module `src/vulcanlab/retrieval/content_utils.py` for helper functions
2. Implement `count_words(text: str) -> int` using whitespace splitting
3. Implement `is_heading(line: str) -> bool` using regex pattern `^#{1,6}\s+`
4. Implement `split_sentences(text: str) -> list[str]`:
   - Attempt to use spaCy sentence tokenizer if available
   - Fall back to regex `(?<=[.!?])\s+` if spaCy not available
5. Implement `truncate_to_word_limit(content: str, original_chunk_start: int, original_chunk_end: int, max_word_count: int) -> str`:
   - Split content into lines
   - Identify original chunk position within content
   - Build sliding window centered on original chunk
   - Expand window until max_word_count reached
   - Preserve all heading lines regardless of position
   - Preserve complete sentences at boundaries
   - Return truncated content
6. Add comprehensive unit tests

Patterns to apply:
- Core Module Independence - Pure functions with no external dependencies
- Session Management - N/A (no database access)

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - `count_words()` handles empty strings, single words, multiple spaces
  - `is_heading()` correctly identifies all markdown heading levels (h1-h6)
  - `is_heading()` rejects non-heading lines
  - `split_sentences()` correctly splits on periods, exclamation marks, question marks
  - `split_sentences()` preserves sentences with abbreviations (e.g., "Dr. Smith")
  - `truncate_to_word_limit()` returns content within max_word_count
  - `truncate_to_word_limit()` preserves all headings even if outside window
  - `truncate_to_word_limit()` does not break sentences mid-sentence
  - `truncate_to_word_limit()` centers window on original chunk position
  - `truncate_to_word_limit()` handles edge case where original chunk is at start/end
  - `truncate_to_word_limit()` handles content shorter than max_word_count (returns as-is)

- Suggested locations:
  - `tests/unit/test_content_utils.py`

- Mocking/fakes needed:
  - Mock spaCy import failure to test regex fallback path
  - None otherwise (pure functions)

## Acceptance criteria (checklist)
- [ ] `content_utils.py` module created in `src/vulcanlab/retrieval/`
- [ ] `count_words()` implemented and tested
- [ ] `is_heading()` implemented and tested
- [ ] `split_sentences()` implemented with spaCy primary and regex fallback
- [ ] `truncate_to_word_limit()` implemented with sliding window algorithm
- [ ] Sentence boundaries preserved in truncation
- [ ] All markdown headings preserved in truncation
- [ ] Word count stays within `max_word_count` unless necessary for sentence integrity
- [ ] All unit tests pass
- [ ] Code follows snake_case naming convention

## Manual verification
- Steps:
  1. Run unit tests: `python -m pytest tests/unit/test_content_utils.py -v`
  2. Import module in Python REPL and test with sample markdown content
  3. Verify truncation visually with a long markdown document

- Expected results:
  - All tests pass
  - Truncated content preserves readability (no broken sentences)
  - Headings remain intact

## Notes
- Use spaCy model `en_core_web_sm` if available in project dependencies
- Regex fallback pattern: `re.split(r'(?<=[.!?])\s+', text)`
- Heading detection pattern: `re.match(r'^#{1,6}\s+', line)`
- The sliding window should expand symmetrically from original chunk position
- If expansion would exceed max_word_count, truncate at sentence boundaries
- Edge case: If a single sentence exceeds max_word_count, include it anyway to avoid empty output
