# Ticket: work-summarization.T10 - API Router: Prepare and Generate Prompts Endpoints

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create summarization API router with prepare and generate-prompts endpoints
* Wire core modules to API layer
* Store ranking results in `summary_chunks` table during preparation

## Phase

* APIs

## Scope

### In scope

* New router `src/vulcanlab_api/routers/summarize.py`
* `POST /api/v1/summarize/works/{work_id}/prepare` endpoint
* `POST /api/v1/summarize/works/{work_id}/generate-prompts` endpoint
* Pydantic schemas for requests/responses
* Storage of ranking results to `summary_chunks` table

### Out of scope

* Submit-response endpoint (T11)
* Summary retrieval endpoints (T12)
* Settings endpoints (T12)
* Frontend integration (T13+)

## Dependencies

* Depends on: T04, T05, T06, T07, T08 (core modules)
* Unblocks: T11, T13

## Implementation plan

1. Create `src/vulcanlab_api/schemas/summarize.py` with Pydantic models:
   - `HeadingPreview`: chunk_id, level, title, start_line, content_word_count
   - `PrepareResponse`: headings (list[HeadingPreview]), total_prompts, estimated_tokens, has_existing_summaries
   - `GeneratePromptsRequest`: regenerate_all (bool)
   - `PromptResponse`: prompt_index, content, heading_ids
   - `GeneratePromptsResponse`: prompts (list[PromptResponse])
2. Create `src/vulcanlab_api/routers/summarize.py`
3. Implement `POST /api/v1/summarize/works/{work_id}/prepare`:
   - Load settings from `summarize_settings`
   - Call `select_headings_for_summarization()`
   - For each heading, call `rank_content_chunks()`
   - Store rankings in `summary_chunks` table (delete old first, insert new)
   - Check if `summary_results` has existing rows for work
   - Calculate estimated total tokens
   - Return PrepareResponse
4. Implement `POST /api/v1/summarize/works/{work_id}/generate-prompts`:
   - If regenerate_all, call `delete_existing_summaries()`
   - Load rankings from `summary_chunks` for work
   - Reconstruct HeadingWithChunks from stored data
   - Call `generate_prompts()` to assemble prompt batches
   - Return GeneratePromptsResponse
5. Register router in `main.py`:
   ```python
   app.include_router(summarize_router, prefix="/api/v1/summarize")
   ```
6. Add appropriate error handling:
   - 404 if work not found
   - 400 if work has no chunks
   - 400 if no heading-chunks qualify for summarization

* Patterns to apply:
  * **API Versioning** - Routes prefixed with `/api/v1`
  * **Thin API Layer** - Orchestrate core module calls, minimal business logic
  * **Error Handling** - Use HTTPException for API errors
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Prepare endpoint returns correct heading count
  * Prepare endpoint calculates estimated tokens
  * Prepare endpoint detects existing summaries
  * Prepare endpoint stores rankings in summary_chunks
  * Generate-prompts endpoint returns correct number of prompts
  * Generate-prompts with regenerate_all=true deletes existing
  * Generate-prompts with regenerate_all=false preserves existing
  * Error 404 when work not found
  * Error 400 when work has no heading-chunks
* Suggested locations:
  * `tests/unit/test_summarize_router.py`
* Mocking/fakes needed:
  * Mock database session
  * Mock core module functions (heading_selector, chunk_ranker, prompt_generator)
  * Mock Work model queries

## Acceptance criteria (checklist)

* [ ] Router registered at `/api/v1/summarize`
* [ ] Prepare endpoint returns heading list and estimates
* [ ] Prepare endpoint stores rankings in summary_chunks
* [ ] Generate-prompts endpoint returns assembled prompts
* [ ] Regenerate option deletes existing before generating
* [ ] Proper error responses for invalid work IDs
* [ ] Pydantic schemas validate request/response data
* [ ] Unit tests pass for all endpoints

## Manual verification

* Steps:
  * Start API server
  * POST to `/api/v1/summarize/works/{work_id}/prepare` with valid work
  * Verify response includes headings and estimates
  * Query `summary_chunks` table to verify rankings stored
  * POST to `/api/v1/summarize/works/{work_id}/generate-prompts`
  * Verify response includes prompt content
* Expected results:
  * Endpoints return expected data structures
  * Rankings persisted in database
  * Prompts are well-formed

## Notes

* Requirements covered: R1-R7 (via core modules), R5 (store in summary_chunks), R10 (regenerate option)
* Prepare endpoint is separate from generate to allow UI to show preview/confirmation
* summary_chunks stores rankings to avoid re-computing during generate-prompts
* Consider adding endpoint to check preparation status without re-running
