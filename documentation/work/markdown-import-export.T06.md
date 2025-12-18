# Ticket: markdown-import-export.T06 - Duplicate Detection Logic and API

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement duplicate work detection based on title/author
- Create API endpoint for checking duplicates before import
- Return duplicate work information for user decision

## Scope
### In scope
- Core function: check_duplicate_work(title: str, author: str, session: Session) -> Optional[Work]
- API endpoint: GET /api/v1/markdown/check-duplicate with query params
- Case-insensitive matching for title and author
- Return work ID and title if duplicate found

### Out of scope
- Frontend duplicate warning modal (covered in T08)
- Fuzzy matching or similarity detection
- Duplicate resolution strategies (user decides to proceed or cancel)
- Automatic de-duplication

## Dependencies
- Depends on: T01
- Unblocks: T08

## Implementation plan
1. Create src/vulcanlab/markdown_import/duplicate_check.py:
   - Implement check_duplicate_work(title: str, author: str, session: Session) -> Optional[Work]:
     - Query Work table for matching title (case-insensitive) and authors (case-insensitive)
     - Use SQLAlchemy func.lower() for case-insensitive comparison
     - Return first matching Work or None
     - Note: authors field may contain multiple names; match if any author matches
2. Extend src/vulcanlab_api/routers/markdown.py:
   - Add GET /check-duplicate endpoint:
     - Query params: title (required), author (required)
     - Validate params are non-empty strings
     - Get database session
     - Call check_duplicate_work(title, author, session)
     - If duplicate found: return {"exists": true, "work_id": work.id, "work_title": work.title}
     - If no duplicate: return {"exists": false}
     - Handle errors: 400 (missing params), 500 (database error)
3. Patterns to apply:
   - Core module: Business logic in duplicate_check.py
   - API layer: Thin router in markdown.py
   - Session management: Pass session explicitly
   - Error handling: HTTPException for API errors
   - Database query: Use SQLAlchemy ORM with case-insensitive filters
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - check_duplicate_work() finds exact title/author match
  - check_duplicate_work() matches case-insensitively
  - check_duplicate_work() returns None when no match found
  - check_duplicate_work() handles empty title/author
  - check_duplicate_work() matches partial author names in authors field
  - API endpoint returns exists=true for duplicate
  - API endpoint returns exists=false for non-duplicate
  - API endpoint returns work_id and work_title for duplicate
  - API endpoint validates required query params
  - API endpoint handles database errors
- Suggested locations:
  - tests/unit/test_markdown_duplicate_check.py
  - tests/unit/test_markdown_api.py (extend)
- Mocking/fakes needed:
  - Mock database session
  - Mock Work query and filter operations
  - Mock SQLAlchemy func.lower()

## Acceptance criteria (checklist)
- [ ] check_duplicate_work() queries database for matching title and author
- [ ] Matching is case-insensitive for both title and author
- [ ] Function returns matching Work or None
- [ ] API endpoint GET /api/v1/markdown/check-duplicate accepts title and author params
- [ ] Endpoint returns exists=true with work details if duplicate found
- [ ] Endpoint returns exists=false if no duplicate
- [ ] Endpoint validates required parameters
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Create work in database with title="Test Work" and author="John Doe"
  2. Call API: GET /api/v1/markdown/check-duplicate?title=test%20work&author=john%20doe
  3. Verify response: {"exists": true, "work_id": X, "work_title": "Test Work"}
  4. Call API with non-existent title/author
  5. Verify response: {"exists": false}
  6. Call API with missing params, verify 400 error
- Expected results:
  - Exact matches detected (case-insensitive)
  - Non-duplicates return exists=false
  - Work details returned for duplicates

## Notes
- Case-insensitive matching uses SQL LOWER() function via SQLAlchemy func.lower()
- Authors field is stored as comma-separated string; consider splitting and matching individual names
- Partial matches (e.g., "John" matching "John Doe") may need refinement based on user feedback
- This is a simple duplicate check; more sophisticated fuzzy matching is out of scope
- Consider adding index on title and authors columns for performance (future optimization)
- Multiple works with same title/author are possible; return first match only
