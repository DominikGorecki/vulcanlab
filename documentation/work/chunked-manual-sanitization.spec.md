# Title: Batched Manual Sanitization for Large Markdown Files

## Summary

* Add a batched sanitization workflow to the `/simple-conversion/manual/[id]` page for very large markdown files (>5000 headings).
* Allow users to process heading sanitization in batches by generating LLM prompts for N headings at a time, pasting results incrementally, and progressing through the entire document.
* Store batch progress in a new database table to support session resumption and maintain backwards compatibility.
* Add a new prompt template `simple_sanitize_large_batched` with hierarchical context from previous batches.
* Add configuration settings to the Conversion tab: `batch_size_headings` (default 5000) and `batch_context_headings` (default 25).
* User can dynamically adjust batch size per-call, and prompt regenerates automatically.
* Maintain full backwards compatibility by creating new table, functions, and template without modifying existing single-step workflow.

## Problem / Context

* Currently, the manual conversion workflow on `/simple-conversion/manual/[id]` generates a single LLM prompt for the entire condensed document (all headings).
* For very large markdown files with thousands of headings (e.g., 15,000+ headings), the single prompt can exceed LLM context limits or be unwieldy for manual processing.
* Users need a way to break down large heading sanitization tasks into manageable **batches** (LLM calls) while maintaining heading hierarchy consistency across batches.
* **Critical distinction**: This feature is about batching the heading sanitization LLM calls, NOT about the content chunking that happens afterward. Content chunking (creating `Chunk` records in the database) already works correctly and happens AFTER sanitization is complete.
* The existing single-step workflow works perfectly for files under the threshold and must remain unchanged.
* Users may need to resume batched workflows across sessions if they close their browser mid-process.

## Goals

* Enable incremental, batched processing of heading sanitization for large markdown files in the manual workflow.
* Allow users to configure batch size (headings per LLM call) globally and adjust dynamically per-call.
* Automatically detect when a file requires batched processing based on heading count.
* Provide hierarchical context from previous batches to maintain consistency.
* Store batch progress in a dedicated database table to support resumption after browser close/refresh.
* Maintain 100% backwards compatibility with existing single-step workflow.

## Non-goals (Strict)

* Batched processing for automatic execution (manual workflow only).
* Reprocessing of existing completed works with the new batched workflow.
* Batched workflow for "small" classification files (only for "large" files).
* Changes to content chunking logic (creating `Chunk` records in DB after sanitization).
* UI changes to the results display or completion flow.
* Integration tests (only unit tests unless explicitly requested).

## Scope

### In scope

* New database table `batch_sanitization_progress` to track batched sanitization state.
* New configuration settings in `vulcanlab.config.json` under `conversion` section.
* New UI controls in Settings → Conversion tab for batch configuration.
* New prompt template `simple_sanitize_large_batched` with context parameters.
* Modified manual workflow page UI to support batched progression with dynamic batch size adjustment.
* New API endpoints for batched prompt generation and submission.
* New core logic functions for batch splitting and context extraction.
* Unit tests for new batching logic and prompt generation.

### Out of scope

* Changes to automatic execution workflow.
* Changes to single-step manual workflow behavior.
* Changes to "small" classification processing.
* Changes to content chunking logic (after sanitization).
* Integration tests.
* Reprocessing UI for existing works.

## Requirements (Functional)

* R1: System must automatically detect when a file has more headings than global `batch_size_headings` threshold and show batched workflow instead of single-step.
* R2: Batched workflow must generate prompts for exactly N headings at a time (where N is configurable per-call by the user).
* R3: Each batch prompt must include hierarchical context from previous batches (up to `batch_context_headings` from the next higher heading level).
* R4: System must store batch progress in a new `batch_sanitization_progress` table including work_id, current batch index, total batches, batch size used per batch, and sanitized results per batch.
* R5: Users must be able to resume batched workflows after browser close/refresh by loading progress from database.
* R6: System must validate each batch's LLM response (JSON schema, line numbers) before accepting it and block progression on invalid responses.
* R7: Batched workflow must only be available for "large" classification files (not "small").
* R8: Single-step workflow must remain completely unchanged and unaffected by this feature.
* R9: New prompt template `simple_sanitize_large_batched` must be seeded in database following the established template seeding pattern.
* R10: Settings page must expose `batch_size_headings` and `batch_context_headings` as configurable inputs.
* R11: User can adjust batch size dynamically on the manual page (e.g., change from 5000 to 10000 for next batch), and prompt must regenerate automatically.
* R12: LLM response includes both heading modifications (keep/change/remove) AND vectorization decisions (true/false per heading).
* R13: After all batches complete and results merge, existing content chunking logic proceeds unchanged.

## Requirements (Non-functional)

* Performance:
  * Batch splitting logic must execute in <500ms for files with 50,000 headings.
  * Database updates for batch progress must not block UI interaction.
* Reliability:
  * Progress state must be persisted in database after each successful batch submission.
  * Invalid batch responses must not corrupt the overall document state or previous batch results.
* Security / Privacy:
  * No new security concerns; uses existing authentication/authorization.
* Observability:
  * Log batch progression events (batch N of M started, completed, batch size used).
  * Include batch index and work_id in error logs for debugging.

## Proposed Solution (High-level)

* Add two new settings to `vulcanlab.config.json` under `conversion`: `batch_size_headings` (default 5000) and `batch_context_headings` (default 25).
* Create new database table `batch_sanitization_progress` with columns:
  * `id`: Primary key
  * `work_id`: Foreign key to `works` table
  * `total_batches`: Total number of batches
  * `current_batch_index`: Current batch (0-indexed)
  * `batch_sizes`: JSONB array of batch sizes used per batch (allows dynamic sizing)
  * `batch_results`: JSONB array of LLM responses (modifications JSON) per batch
  * `batch_context`: JSONB array of hierarchical context headings extracted from previous batches
  * `created_at`, `updated_at`: Timestamps
* Create new prompt template file `src/vulcanlab/data/seed_data/templates/simple_sanitize_large_batched.txt` based on `simple_sanitize_large.txt` with additional context section.
* Add template entry to `templates.yaml` for `simple_sanitize_large_batched`.
* Create new core module functions in `src/vulcanlab/simple_conversion/`:
  * `split_condensed_into_batches(condensed_doc, batch_size)`: Split condensed document into batches of N headings.
  * `extract_hierarchical_context(previous_batch_results, current_heading_level, max_headings)`: Extract up to 25 higher-level headings from previous batches.
  * `generate_batched_prompt(batch_data, context_headings, template)`: Generate prompt for one batch with context.
  * `merge_batch_results(batch_results)`: Combine all batch results into final sanitized modifications JSON.
* Add new API endpoints to `src/vulcanlab_api/routers/simple_conversion.py`:
  * `GET /api/simple-conversion/manual-prompt-batched/{work_id}?batch_size={N}`: Get prompt for next batch with optional batch size override.
  * `POST /api/simple-conversion/manual-submit-batched/{work_id}`: Submit LLM response for current batch.
  * `GET /api/simple-conversion/batched-status/{work_id}`: Get current batch progress state.
* Modify manual workflow page to:
  * Fetch heading count from work metadata (parsed markdown).
  * Compare against global `batch_size_headings` threshold.
  * If exceeds threshold, render batched workflow UI instead of single-step.
  * Display progress indicator showing "Batch N of M".
  * Include input field for user to adjust batch size for next batch.
  * After each batch submission, automatically fetch next batch prompt with updated batch size.
  * On final batch completion, merge all results and proceed to existing sanitization completion flow (then content chunking).
* Update Settings → Conversion tab to include two new input fields.

## Interfaces / APIs / Contracts

### New API Endpoints

**GET /api/simple-conversion/manual-prompt-batched/{work_id}?batch_size={N}**
* Request:
  * `work_id` (int, path parameter)
  * `batch_size` (int, optional query parameter, defaults to global config value)
* Response:
  ```json
  {
    "work_id": 123,
    "classification": "large",
    "batch_index": 0,
    "total_batches": 3,
    "batch_size_used": 5000,
    "prompt": "...",
    "instructions": "Paste JSON response for batch 1 of 3 (headings 1-5000)...",
    "heading_range": "1-5000",
    "context_headings_count": 0
  }
  ```

**POST /api/simple-conversion/manual-submit-batched/{work_id}**
* Request:
  ```json
  {
    "llm_response": "{ \"modifications\": [...] }"
  }
  ```
* Response:
  ```json
  {
    "success": true,
    "batch_index": 0,
    "total_batches": 3,
    "is_complete": false,
    "next_batch_index": 1
  }
  ```
  OR if complete:
  ```json
  {
    "success": true,
    "batch_index": 2,
    "total_batches": 3,
    "is_complete": true,
    "sanitized_work_id": 123
  }
  ```

**GET /api/simple-conversion/batched-status/{work_id}**
* Response:
  ```json
  {
    "work_id": 123,
    "batched_enabled": true,
    "current_batch": 2,
    "total_batches": 3,
    "completed_batches": [0, 1],
    "batch_sizes_used": [5000, 5000],
    "can_resume": true
  }
  ```

### Configuration Schema

```json
{
  "conversion": {
    "token_threshold": 30000,
    "advanced_mode_enabled": false,
    "use_full_model": false,
    "batch_size_headings": 5000,
    "batch_context_headings": 25
  }
}
```

## Data Model / Storage

### New Table: batch_sanitization_progress

```sql
CREATE TABLE batch_sanitization_progress (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    total_batches INTEGER NOT NULL,
    current_batch_index INTEGER NOT NULL DEFAULT 0,
    batch_sizes JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Array of batch sizes used per batch
    batch_results JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Array of LLM responses per batch
    batch_context JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Array of context headings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(work_id)
);

CREATE INDEX idx_batch_sanitization_progress_work_id ON batch_sanitization_progress(work_id);
```

**Example record:**
```json
{
  "id": 1,
  "work_id": 123,
  "total_batches": 3,
  "current_batch_index": 2,
  "batch_sizes": [5000, 5000, 2000],
  "batch_results": [
    { "modifications": [ {"line": 1, "action": "keep", "vectorize": true}, ... ] },
    { "modifications": [ {"line": 5001, "action": "change", "new": "## Fixed", "vectorize": true}, ... ] }
  ],
  "batch_context": [
    { "line": 10, "level": 2, "text": "## Chapter 1" },
    { "line": 450, "level": 2, "text": "## Chapter 2" }
  ]
}
```

### New Prompt Template Entry

Add to `templates.yaml`:

```yaml
- function_tag: simple_sanitize_large_batched
  version: 1
  title: "Simple Conversion - Large Document Batched Sanitization"
  template_type: null
  is_active: true
  content_file: simple_sanitize_large_batched.txt
```

## UX / Workflows

### Batched Manual Workflow (User Perspective)

1. User navigates to `/simple-conversion/manual/[id]` for a large file.
2. System detects file has 12,000 headings (exceeds 5,000 threshold).
3. UI displays: "This file has 12,000 headings and will be processed in batches. Default batch size: 5000 headings."
4. UI shows "Batch 1 of 3" with first prompt displayed and input field showing "5000" (adjustable).
5. User copies prompt, pastes into LLM, gets result (JSON with modifications and vectorize flags).
6. User pastes result into textarea and clicks "Submit Batch 1".
7. System validates result, saves batch 1 results to database, updates progress.
8. UI automatically shows "Batch 2 of 3" with next prompt (includes hierarchical context from batch 1).
9. User can adjust batch size (e.g., change to 7000 for batch 2), clicks "Regenerate Prompt".
10. User repeats for batches 2 and 3.
11. After batch 3 submission, system merges all batch results into final sanitized modifications.
12. System proceeds to existing sanitization completion flow, then content chunking (creating `Chunk` records).

### Resume Flow

1. User is on batch 2 of 3, closes browser.
2. User returns to `/simple-conversion/manual/[id]`.
3. System loads progress from `batch_sanitization_progress` table, shows "Resume from Batch 2 of 3".
4. User continues from batch 2.

### Dynamic Batch Sizing

1. User starts batch workflow with default 5000 headings.
2. On batch 2, user realizes remaining headings (2000) would leave a small final batch.
3. User changes batch size to 7000 for batch 2 to complete in 2 batches instead of 3.
4. System recalculates total batches, regenerates prompt with new size.

## Testing Plan

### Unit tests

* Test `split_condensed_into_batches` with various heading counts (5000, 10000, 15000) and batch sizes.
* Test `extract_hierarchical_context` with different heading level patterns.
* Test `generate_batched_prompt` template variable substitution with context.
* Test `merge_batch_results` combining multiple batch JSON responses (handling duplicate line numbers, ordering).
* Test batch progress state persistence and retrieval from `batch_sanitization_progress` table.
* Test validation of batched LLM responses (valid JSON, correct schema with vectorize flags).
* Test threshold detection logic (4999 vs 5000 vs 5001 headings).
* Test dynamic batch size adjustment (recalculate total batches, regenerate prompt).

### Integration tests

* Not required unless explicitly requested.

### Manual test plan

* Upload a markdown file with exactly 5001 headings, verify batched workflow appears.
* Upload a markdown file with exactly 4999 headings, verify single-step workflow appears.
* Complete a 3-batch workflow end-to-end, verify final results are correct and content chunks created.
* Complete batch 1, close browser, reopen, verify resume from batch 2.
* Submit invalid JSON for a batch, verify error shown and progress blocked.
* Adjust batch size from 5000 to 7000 on batch 2, verify prompt regenerates and total batches recalculated.
* Modify global `batch_size_headings` in settings from 5000 to 10000, verify new works use new threshold.
* Process a "small" classification file, verify batched workflow never appears.
* Verify LLM response includes both modifications and vectorize flags, and both are preserved through merge.

## Acceptance Criteria (Checklist)

* [ ] New configuration settings `batch_size_headings` and `batch_context_headings` added to `vulcanlab.config.json`.
* [ ] Settings → Conversion tab displays and saves both new settings.
* [ ] New database table `batch_sanitization_progress` created via migration.
* [ ] New prompt template `simple_sanitize_large_batched.txt` created and added to `templates.yaml`.
* [ ] Template seeds successfully via `init_db.py` seeding function.
* [ ] Core functions `split_condensed_into_batches`, `extract_hierarchical_context`, `generate_batched_prompt`, `merge_batch_results` implemented with unit tests.
* [ ] API endpoints for batched prompt and submission implemented and functional.
* [ ] Manual workflow page detects heading count and shows batched UI when threshold exceeded.
* [ ] Batched UI shows "Batch N of M" progress indicator and batch size input field.
* [ ] Each batch submission saves progress to `batch_sanitization_progress` table.
* [ ] Workflow supports resumption after browser close/refresh.
* [ ] Invalid batch responses display error and block progression.
* [ ] User can adjust batch size dynamically, and prompt regenerates automatically.
* [ ] Batched workflow only appears for "large" classification files.
* [ ] Single-step workflow remains unchanged for files below threshold and "small" files.
* [ ] Final merged result includes both modifications and vectorize flags.
* [ ] Content chunking proceeds unchanged after sanitization completes.
* [ ] All unit tests pass.

## Rollout / Migration Plan

* Database migration: Create `batch_sanitization_progress` table with migration script.
* Config file changes: Add new keys to `conversion` section with default values.
* Template seeding: Run `python -m vulcanlab.data.init_db -v` to seed new template.
* Backwards compatibility: Existing works and in-progress single-step workflows unaffected; new batched workflow only activates for new large files.

## Risks and Alternatives

* Risks:
  * Batch boundaries might split semantically related headings; mitigated by providing hierarchical context from previous batches.
  * Users might close browser mid-batch; mitigated by storing progress in dedicated database table.
  * LLM context from previous batches might grow too large; mitigated by `batch_context_headings` limit (default 25).
  * Dynamic batch sizing might confuse users; mitigated by clear UI labels and default values.
* Alternatives considered:
  * Store progress in `Work.processing_status` JSONB field: Rejected for backwards compatibility concerns; dedicated table is cleaner.
  * Batch all prompts upfront: Rejected because context depends on previous batch results.
  * In-memory progress only: Rejected because browser close would lose progress.
  * Support batching for automatic execution: Deferred as out-of-scope; manual workflow is the primary use case for very large files.

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
  * **Core Module Independence** - All batching logic in `src/vulcanlab/simple_conversion/`, no FastAPI dependencies.
  * **Database Session Management** - Session passed explicitly to core functions.
  * **Prompt Template Seeding** - New template follows YAML + .txt file pattern in `seed_data/templates/`.
  * **Frontend Page Lifecycle** - Manual page uses `usePageData` hook for fetching prompts and status.
  * **API Versioning** - New endpoints use `/api/simple-conversion` prefix (existing v1 implied).
  * **Error Handling** - Raise specific exceptions in core logic; API layer returns HTTPException.
  * **Testing Strategy** - Unit tests with mocked DB sessions; no integration tests unless requested.
* Deviations (if any):
  * None; spec follows all established patterns.

## Implementation Notes (Non-binding)

* Batching logic should preserve line numbers from original condensed document for correct mapping.
* Context extraction should walk backwards through previous batch results to find headings at level N-1 (e.g., if current batch has H3 headings, extract H2s from previous batches).
* UI should disable "Submit Batch" button until LLM response is pasted.
* Consider adding a "Reset Batches" button to restart from batch 1 if user wants to redo the workflow.
* Prompt template should clearly indicate batch range (e.g., "Processing headings 5001-10000 of 12000").
* For context headings, include line number, level, and text for LLM reference.
* Merge logic should concatenate all batch results' modification arrays in order and deduplicate by line number if needed.
* When user adjusts batch size, recalculate total batches: `total_batches = ceil((total_headings - processed_headings) / new_batch_size) + current_batch`.
* After all batches merge, proceed to existing `apply_sanitization` logic which creates the sanitized markdown, then content chunking creates `Chunk` records as normal.

## Open Questions

* None remaining (all questions answered by user).
