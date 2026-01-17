# Ticket: work-summarization.T04 - Heading Selector Module

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement `heading_selector.py` to identify, filter, and order heading-chunks for summarization
* Apply word count filtering and heading title budget constraints
* Return ordered list of heading-chunks eligible for summarization

## Phase

* Core Modules

## Scope

### In scope

* New module `src/vulcanlab/summarization/heading_selector.py`
* Package init `src/vulcanlab/summarization/__init__.py`
* Function to list heading-chunks ordered by `start_line`
* Function to filter by minimum word count in `chunks.content`
* Function to enforce maximum total heading words budget
* Dataclass for heading selection results

### Out of scope

* Chunk ranking/scoring (T05, T06)
* Prompt generation (T07, T08)
* API endpoints (T10+)

## Dependencies

* Depends on: T02 (models for querying chunks and settings)
* Unblocks: T05, T07, T10

## Implementation plan

1. Create `src/vulcanlab/summarization/__init__.py` with package exports
2. Create `src/vulcanlab/summarization/heading_selector.py`
3. Implement `HeadingInfo` dataclass:
   - chunk_id, level, start_line, end_line
   - content_word_count, heading_title (first line of content)
4. Implement `get_heading_chunks(work_id: int, session: Session) -> list[HeadingInfo]`:
   - Query chunks where level does NOT contain "-chunk"
   - Order by start_line ascending
   - Extract first line of content as heading_title
   - Count words in content field
5. Implement `filter_by_word_count(headings: list[HeadingInfo], min_words: int) -> list[HeadingInfo]`:
   - Remove headings where content_word_count < min_words
6. Implement `enforce_heading_budget(headings: list[HeadingInfo], max_total_words: int) -> list[HeadingInfo]`:
   - Calculate total words from all heading_titles
   - If over budget, iteratively remove lowest-level headings with shortest content
   - Continue until under budget
   - Preserve original order after removal
7. Implement main entry point `select_headings_for_summarization(work_id: int, session: Session, settings: SummarizeSettings) -> list[HeadingInfo]`:
   - Orchestrate: get_heading_chunks -> filter_by_word_count -> enforce_heading_budget
   - Return final ordered list

* Patterns to apply:
  * **Core Module Independence** - No FastAPI imports, pure Python logic
  * **Session Passed Explicitly** - All functions receive session as parameter
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `get_heading_chunks` returns only non-content-chunk levels
  * `get_heading_chunks` orders by start_line correctly
  * `filter_by_word_count` removes headings below threshold
  * `filter_by_word_count` keeps headings at or above threshold
  * `enforce_heading_budget` removes lowest-level shortest first
  * `enforce_heading_budget` preserves order after removal
  * `enforce_heading_budget` handles tie-breaking (same level, same length)
  * Edge case: empty heading list
  * Edge case: all headings filtered out
  * Edge case: single heading
* Suggested locations:
  * `tests/unit/test_heading_selector.py`
* Mocking/fakes needed:
  * Mock SQLAlchemy session with fake chunk data
  * Mock SummarizeSettings with test thresholds

## Acceptance criteria (checklist)

* [ ] Package `src/vulcanlab/summarization/` created with `__init__.py`
* [ ] `heading_selector.py` implements all four functions
* [ ] Heading-chunks correctly identified (level without "-chunk")
* [ ] Word count filtering works with configurable threshold
* [ ] Heading budget enforcement removes correct headings
* [ ] Original document order preserved in output
* [ ] All unit tests pass

## Manual verification

* Steps:
  * Import module in Python REPL
  * Create mock chunks with various levels and word counts
  * Call `select_headings_for_summarization` with test settings
  * Verify returned list matches expected filtering
* Expected results:
  * Only heading-chunks (H1, H2, H3, etc.) returned
  * Short content headings filtered out
  * Budget enforcement removes expected headings

## Notes

* Requirements covered: R1, R2, R3
* "Level without -chunk" means H1, H2, H3, H4, H5 are heading-chunks; H1-chunk, H2-chunk are content-chunks
* Word count should use simple `len(content.split())` for consistency
* First line extraction: `content.split('\n')[0].lstrip('#').strip()`
