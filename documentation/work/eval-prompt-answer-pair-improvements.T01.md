# Ticket: eval-prompt-answer-pair-improvements.T01 - Backend Answer Deletion and Detail Retrieval

## Source

* Spec: documentation/work/eval-prompt-answer-pair-improvements.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add backend capability to delete entire answer-pairs (cascade delete evaluations)
* Add backend endpoint to retrieve full answer details with optional evaluation data
* Enable manual testing of answer deletion and detail retrieval via API

## Scope

### In scope

* Core module: `delete_answer_pair()` function in `src/vulcanlab/eval/answers.py`
* Core module: Enhance `get_answer_by_id()` to optionally join evaluation data
* API endpoint: `DELETE /api/v1/eval/answers/{answer_id}` returns 204 on success
* API endpoint: `GET /api/v1/eval/answers/{answer_id}` returns AnswerDetailResponse
* Pydantic schema: `AnswerDetailResponse` with optional nested evaluation
* Unit tests for deletion cascade and detail retrieval with/without evaluation
* Logging for answer deletions with answer_id and prompt_id

### Out of scope

* Frontend changes (handled in later tickets)
* Evaluation overwrite functionality (T04)
* Integration tests
* UI components or pages

## Dependencies

* Depends on: none (uses existing database schema with CASCADE DELETE)
* Unblocks: T02, T03

## Implementation plan

1. Add `delete_answer_pair(session: Session, answer_id: int)` to `src/vulcanlab/eval/answers.py`:
   - Query answer by ID, raise ValueError if not found
   - Log deletion with answer_id and prompt_id
   - Delete answer (CASCADE handles evaluation and dimension_results)
   - Return None

2. Create `AnswerDetailResponse` schema in `src/vulcanlab_api/schemas/eval.py`:
   - Extends base answer fields (id, prompt_id, answer_x, answer_y, is_x_mapped_to_a, answer_a, answer_b, created_at, updated_at)
   - Add optional `evaluation` nested field with: id, overall_score, unblinded_score (computed), justification, dimension_results array, created_at
   - Use `from_attributes=True` config

3. Add helper function or modify `get_answer_by_id()` to support eager loading:
   - Use LEFT JOIN to load ExperimentEvaluation and ExperimentDimensionResults if they exist
   - Return answer with evaluation relationship populated

4. Add `DELETE /api/v1/eval/answers/{answer_id}` endpoint to `src/vulcanlab_api/routers/eval.py`:
   - Call `delete_answer_pair(session, answer_id)` in try/except
   - Return 204 No Content on success
   - Raise HTTPException 404 if ValueError (not found)
   - Raise HTTPException 500 for other exceptions
   - Commit session before returning

5. Add `GET /api/v1/eval/answers/{answer_id}` endpoint to `src/vulcanlab_api/routers/eval.py`:
   - Call enhanced `get_answer_by_id()` with evaluation join
   - Build AnswerDetailResponse with evaluation data if exists
   - Compute unblinded_score if evaluation exists: `overall_score * (1 if is_x_mapped_to_a else -1)`
   - Return AnswerDetailResponse
   - Raise HTTPException 404 if ValueError (not found)

6. Write unit tests (see Unit tests section below)

### Patterns to apply

* Three-tier Architecture: Core logic in `src/vulcanlab/eval/answers.py`, API in `src/vulcanlab_api/routers/eval.py`
* Session Management: Pass session explicitly to `delete_answer_pair()`
* API Versioning: Use `/api/v1` prefix
* Error Handling: Raise ValueError for not found, let global handler catch 500s
* ORM: Use SQLAlchemy models with CASCADE DELETE

### Deviations (if any)

* None

## Unit tests (required)

* Add tests for:
  * `test_delete_answer_pair_success()`: Create answer with evaluation, delete, verify answer and evaluation are gone
  * `test_delete_answer_pair_cascade_dimensions()`: Create answer with evaluation and dimension results, verify cascade delete
  * `test_delete_answer_pair_not_found()`: Call with non-existent answer_id, verify ValueError raised
  * `test_delete_answer_pair_without_evaluation()`: Delete answer that has no evaluation, verify success
  * `test_get_answer_detail_with_evaluation()`: Retrieve answer with evaluation, verify all fields populated including unblinded_score
  * `test_get_answer_detail_without_evaluation()`: Retrieve answer without evaluation, verify evaluation field is None
  * `test_delete_endpoint_returns_204()`: Mock core function, call DELETE endpoint, verify 204 status
  * `test_delete_endpoint_returns_404()`: Mock core function to raise ValueError, verify 404 response
  * `test_get_detail_endpoint_returns_answer()`: Mock core function, call GET endpoint, verify AnswerDetailResponse structure

* Suggested locations:
  * `tests/unit/test_eval_answers_delete.py` (core logic tests)
  * `tests/unit/test_eval_api_answer_endpoints.py` (API endpoint tests)

* Mocking/fakes needed:
  * Mock SQLAlchemy session for core logic tests
  * Mock `delete_answer_pair()` and `get_answer_by_id()` for API endpoint tests
  * Use in-memory SQLite or mock ORM objects for cascade delete verification

## Acceptance criteria (checklist)

- [ ] `delete_answer_pair()` function exists in `src/vulcanlab/eval/answers.py`
- [ ] Deleting answer cascades to evaluation and dimension_results (verified in unit test)
- [ ] `delete_answer_pair()` raises ValueError for non-existent answer_id
- [ ] Deletion logs answer_id and prompt_id
- [ ] `AnswerDetailResponse` schema exists with optional evaluation field
- [ ] `GET /api/v1/eval/answers/{answer_id}` endpoint returns full answer with evaluation if exists
- [ ] `GET /api/v1/eval/answers/{answer_id}` computes unblinded_score correctly
- [ ] `DELETE /api/v1/eval/answers/{answer_id}` endpoint returns 204 on success
- [ ] `DELETE /api/v1/eval/answers/{answer_id}` returns 404 for non-existent answer
- [ ] All unit tests pass with at least 9 test cases covering success/error paths
- [ ] No orphaned evaluation records after deletion (verified via cascade test)

## Manual verification

* Steps:
  1. Start API server locally
  2. Create experiment, prompt, and answer-pair with evaluation using existing endpoints
  3. Call `GET /api/v1/eval/answers/{answer_id}` and verify response includes evaluation data with unblinded_score
  4. Call `DELETE /api/v1/eval/answers/{answer_id}` and verify 204 response
  5. Query database directly to confirm answer, evaluation, and dimension_results are deleted
  6. Call `GET /api/v1/eval/answers/{answer_id}` on same ID and verify 404 response
  7. Create answer-pair without evaluation, call GET endpoint, verify evaluation field is null
  8. Call DELETE on non-existent answer_id, verify 404 response

* Expected results:
  * GET endpoint returns complete answer data with nested evaluation when it exists
  * Unblinded_score matches: `overall_score * (1 if is_x_mapped_to_a else -1)`
  * DELETE endpoint removes answer and cascades to evaluation/dimensions
  * 404 errors for non-existent resources
  * No database constraint violations or orphaned records

## Notes

* Requirements covered: R1, R2, R3 (backend portions)
* Database schema already has CASCADE DELETE on foreign keys, no migration needed
* The ExperimentAnswer model has `answer_a` and `answer_b` as computed properties based on `is_x_mapped_to_a`
* Unblinded score calculation: positive if X won, negative if Y won, based on blind mapping
* This ticket enables manual API testing of deletion and detail retrieval, unblocking frontend work
