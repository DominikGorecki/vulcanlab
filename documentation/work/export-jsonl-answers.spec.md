# Title: Export Answer Pairs to JSONL

## Summary

* Create a new feature to export answer pairs for a specific experiment into a JSONL (newline-delimited JSON) file.
* The JSONL will contain one record per line with prompt text, answer_x, and answer_y fields.
* The export will be available via a button next to the CSV export button on the evaluation detail page (`/eval/[id]`).
* Only answer pairs with completed evaluations will be included in the export.
* The file format will be JSONL for efficient streaming and compatibility with data analysis tools.

## Problem / Context

* Currently, users can export evaluation scores to CSV, but cannot easily export the raw answer pairs themselves.
* Researchers and data scientists often need the original prompt and answer texts in a structured format for further analysis, fine-tuning datasets, or external processing.
* JSON/JSONL is preferred over CSV for text-heavy data because it handles multi-line text, special characters, and nested structures more naturally without escaping issues.
* JSONL format is streamable and works well with tools like jq, pandas, and various ML pipelines.

## Goals

* Provide a simple, one-click JSONL export for answer pairs in any evaluation experiment.
* Use JSONL format for efficient streaming and compatibility with data processing tools.
* Ensure consistent behavior with the CSV export (only completed evaluations).
* Keep the format simple and focused on the core answer pair data.

## Non-goals (Strict)

* Exporting evaluation scores, justifications, or dimension results (use CSV export for that).
* Exporting experiment metadata (name, models, judge config).
* Exporting answer pairs from multiple experiments into a single file.
* Providing format selection (JSON vs JSONL) in the UI.
* Exporting answer pairs without completed evaluations.

## Scope

### In scope

* Backend: API endpoint to generate and stream the JSONL file.
* Backend: Core logic to retrieve answer pairs with completed evaluations.
* Frontend: "Export JSONL" button next to the existing "Export CSV" button on the experiment details page.
* File naming: `experiment_[id]_answers.jsonl`.
* JSONL format with three fields per record: `prompt_text`, `answer_x`, `answer_y`.

### Out of scope

* Exporting to other formats (CSV, Parquet, standard JSON array).
* Multi-select export from the experiment list page.
* Including evaluation data in the export (that's what CSV is for).
* Custom field selection in the UI.

## Requirements (Functional)

* R1: The JSONL file MUST contain one JSON object per line (newline-delimited).
* R2: Each JSON object MUST have exactly three fields:
    1. `prompt_text`: The full text of the prompt (string).
    2. `answer_x`: The answer from model X (string).
    3. `answer_y`: The answer from model Y (string).
* R3: Only answer pairs with completed evaluations MUST be included in the export (consistent with CSV export behavior).
* R4: The API endpoint MUST be `GET /api/v1/eval/experiments/{id}/export-jsonl`.
* R5: The downloaded file name MUST be `experiment_[id]_answers.jsonl`.
* R6: The response Content-Type MUST be `application/x-ndjson` or `application/jsonl`.
* R7: Each line MUST be a valid JSON object with no trailing commas or formatting.
* R8: Newlines within field values MUST be properly escaped in the JSON encoding.

## Requirements (Non-functional)

* Performance:
    * The export should handle experiments with hundreds of answer pairs without timing out.
    * Use streaming response to avoid loading all data into memory at once.
* Reliability:
    * Use Python's `json` module for robust JSON encoding.
    * Ensure proper escaping of special characters, newlines, and Unicode.
* Security / Privacy:
    * Standard API authentication and authorization (consistent with existing eval endpoints).
* Observability:
    * Log the export event, including the experiment ID and number of records exported.

## Proposed Solution (High-level)

* Backend:
    * Add `export_experiment_answers_to_jsonl` function in `src/vulcanlab/eval/evaluations.py` (or a new dedicated module if preferred).
    * This function will query all `ExperimentAnswer` objects that have associated `ExperimentEvaluation` records (completed evaluations).
    * Join with `ExperimentPrompt` to get the prompt text.
    * For each answer pair, yield a line containing: `{"prompt_text": "...", "answer_x": "...", "answer_y": "..."}\n`.
    * Use a generator pattern to stream results rather than loading all into memory.
* API:
    * Add a route in `src/vulcanlab_api/routers/eval.py`.
    * Return a `StreamingResponse` with `media_type="application/x-ndjson"`.
    * Set the `Content-Disposition` header to trigger file download with the correct filename.
* Frontend:
    * Add an "Export JSONL" button next to the existing "Export CSV" button in the experiment details page header.
    * Use the same button styling and positioning pattern as the CSV export button.

## Interfaces / APIs / Contracts

* `GET /api/v1/eval/experiments/{experiment_id}/export-jsonl`
    * Response: File download (application/x-ndjson or application/jsonl).
    * Status Codes: 200 (Success), 404 (Experiment not found), 500 (Server error).
    * Content-Disposition: `attachment; filename="experiment_{id}_answers.jsonl"`.

* JSONL Format Example:
```jsonl
{"prompt_text":"What is photosynthesis?","answer_x":"Photosynthesis is the process by which plants...","answer_y":"It is a biological process where..."}
{"prompt_text":"Explain quantum entanglement","answer_x":"Quantum entanglement is a phenomenon...","answer_y":"This is a quantum mechanical effect..."}
```

## Data Model / Storage

* Not applicable: No new tables or migrations required.
* Uses existing tables: `ExperimentAnswer`, `ExperimentPrompt`, `ExperimentEvaluation`.

## UX / Workflows

* User navigates to an experiment detail page (`/eval/[id]`).
* User sees two export buttons: "Export CSV" and "Export JSONL".
* User clicks the "Export JSONL" button.
* Browser initiates a file download for `experiment_[id]_answers.jsonl`.
* File can be opened in text editors, processed with jq, loaded into pandas, etc.

## Testing Plan

* Unit tests:
    * Test JSONL formatting with prompts and answers containing special characters (quotes, newlines, Unicode).
    * Test that only answer pairs with completed evaluations are included.
    * Test correct ordering and completeness of records.
    * Mock the database session to avoid real DB dependencies.
* Integration tests:
    * End-to-end test of the export endpoint with seeded data (if integration tests are requested).
* Manual test plan:
    * Create an experiment with 3 prompts, each with 1-2 answer pairs.
    * Complete evaluations for some (but not all) answer pairs.
    * Export JSONL and verify:
        1. Only answer pairs with evaluations are included.
        2. Each line is valid JSON (use `jq` or `json.loads` to validate).
        3. Prompt text, answer_x, and answer_y are correctly populated.
        4. Filename is `experiment_[id]_answers.jsonl`.

## Acceptance Criteria (Checklist)

* [ ] API endpoint `/api/v1/eval/experiments/{id}/export-jsonl` is functional.
* [ ] JSONL file contains one valid JSON object per line.
* [ ] Each record has `prompt_text`, `answer_x`, and `answer_y` fields.
* [ ] Only answer pairs with completed evaluations are included.
* [ ] Newlines and special characters in text fields are properly escaped.
* [ ] Filename is correctly set to `experiment_[id]_answers.jsonl`.
* [ ] Content-Type header is `application/x-ndjson` or `application/jsonl`.
* [ ] Export button is visible and working on the experiment details page, next to CSV export.

## Rollout / Migration Plan

* Not applicable: No breaking changes or data migrations.
* This is a new feature that does not affect existing functionality.

## Risks and Alternatives

* Risks:
    * Very large experiments might consume significant memory if the JSONL is built entirely in memory before streaming. (Mitigation: Use generator pattern and `StreamingResponse`).
    * Some tools expect standard JSON arrays rather than JSONL. (Mitigation: JSONL is widely supported; users can convert if needed with tools like jq).
* Alternatives considered:
    * Standard JSON array format: Rejected because it requires loading all data into memory and is less suitable for large datasets.
    * Including evaluation data in the export: Rejected to keep the export focused on answer pairs; CSV already handles evaluation data well.
    * Using pandas for JSONL generation: Rejected to keep dependencies minimal; native Python `json` module is sufficient.

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
    * Core Module Logic (`src/vulcanlab`) - Business logic for data retrieval and formatting in the core module.
    * API Layer Routing (`src/vulcanlab_api`) - Thin router calling the core module function.
    * Frontend Page Lifecycle - Using standard UI patterns for action buttons.
    * Testing Strategy - Unit tests with mocked DB sessions, no real database connections.
* Deviations (if any):
    * None.

## Implementation Notes (Non-binding)

* Use `json.dumps(record, ensure_ascii=False)` to handle Unicode properly.
* Append `\n` after each JSON object to create valid JSONL.
* Query pattern: Join `ExperimentAnswer` with `ExperimentPrompt` and filter by existence of `ExperimentEvaluation`.
* Use `yield` in the core function to create a generator for streaming.
* In FastAPI, wrap the generator with `StreamingResponse(generator(), media_type="application/x-ndjson")`.
* Consider using the same authorization/authentication logic as the CSV export endpoint.
* Button placement: Use the same `StickyDetailHeader` or action area as the CSV export button, styled consistently.

## Open Questions

* None.
