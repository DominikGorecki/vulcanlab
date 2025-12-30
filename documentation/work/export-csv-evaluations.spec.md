# Title: Export Evaluation Results to CSV

## Summary

* Create a new feature to export all evaluation data for a specific experiment into a CSV file.
* The CSV will contain prompts, grouping IDs, overall scores, individual dimension scores, and justifications.
* The export will be available via a button on the evaluation detail page (`/eval/[id]`).
* Only completed evaluations will be included in the export.
* The CSV format will be sanitized to handle commas and special characters in prompts and justifications.

## Problem / Context

* Currently, users can only view evaluation results within the web UI.
* There is no way to export the raw data for further analysis in external tools (like Excel or Google Sheets).
* Users need a structured format to analyze prompt performance across different evaluations and dimensions.

## Goals

* Provide a simple, one-click CSV export for any evaluation experiment.
* Ensure the CSV structure is easy to group by prompt.
* Include all scoring dimensions defined for the experiment.
* Sanitize all text fields for reliable CSV parsing.

## Non-goals (Strict)

* Exporting data from multiple experiments into a single CSV.
* Exporting prompts that have not been evaluated.
* Providing custom column selection in the UI.

## Scope

### In scope

* Backend: API endpoint to generate and stream the CSV file.
* Backend: Core logic to retrieve and format evaluation data, including grouping ID logic.
* Frontend: "Export CSV" button on the experiment details page.
* Formatting: CSV sanitization (escaping commas, newlines, etc.).
* File naming: `experiment_[id]_evaluations.csv`.

### Out of scope

* Exporting to other formats (JSON, Excel, Parquet).
* Multi-select export from the experiment list page.

## Requirements (Functional)

* R1: The CSV MUST have the following column order:
    1. `prompt`: The full text of the prompt.
    2. `grouping_id`: A numeric ID (1, 2, 3...) starting from 1 for the first prompt in the experiment and incrementing for each unique prompt.
    3. `overall_score`: The overall evaluation score.
    4. Dimension columns: One column for each unique dimension name found in the experiment's evaluations (e.g., `factual_correctness`, `coherence`).
    5. `justification`: The text justification for the evaluation.
* R2: Evaluations for the same prompt MUST share the same `grouping_id`.
* R3: Only completed evaluations MUST be included in the CSV.
* R4: All text data (especially prompts and justifications) MUST be correctly escaped for CSV compatibility.
* R5: The API endpoint MUST be `GET /api/v1/eval/experiments/{id}/export-csv`.
* R6: The downloaded file name MUST be `experiment_[id]_evaluations.csv`.

## Requirements (Non-functional)

* Performance:
    * The export should handle experiments with hundreds of evaluations without timing out.
* Reliability:
    * Use the standard Python `csv` module for robust formatting.
* Security / Privacy:
    * Standard API authentication and authorization (if applicable to the current system).
* Observability:
    * Log the export event, including the experiment ID and number of rows exported.

## Proposed Solution (High-level)

* Backend:
    * Add `export_experiment_evaluations_to_csv` in `src/vulcanlab/eval/evaluations.py`.
    * This function will query all `ExperimentEvaluation` objects joined with their `ExperimentAnswer` and `ExperimentPrompt`.
    * It will calculate the `grouping_id` by sorting unique prompts by their creation time or ID.
    * It will collect all unique dimension names for the experiment to define the CSV headers.
    * Use a `io.StringIO` buffer and the `csv.DictWriter` to generate the CSV content.
* API:
    * Add a route in `src/vulcanlab_api/routers/eval.py`.
    * Return a `StreamingResponse` (or `Response`) with `media_type="text/csv"`.
* Frontend:
    * Add an "Export CSV" button in the `StickyDetailHeader` or main action area of `vulcanlab_ui/src/app/eval/[id]/page.tsx`.

## Interfaces / APIs / Contracts

* `GET /api/v1/eval/experiments/{experiment_id}/export-csv`
    * Response: File download (text/csv).
    * Status Codes: 200 (Success), 404 (Experiment not found), 500 (Server error).

## Data Model / Storage

* Not applicable: No new tables or migrations required.

## UX / Workflows

* User navigates to an experiment detail page.
* User clicks the "Export CSV" button.
* Browser initiates a file download for `experiment_[id]_evaluations.csv`.

## Testing Plan

* Unit tests:
    * Test `grouping_id` logic for multiple prompts and evaluations.
    * Test CSV formatting with prompts containing commas and newlines.
    * Test dimension column alignment (handling cases where some evaluations might be missing a dimension if the config changed, although currently all evaluations for an experiment share the same dimension set).
* Integration tests:
    * End-to-end test of the export endpoint with seeded data.
* Manual test plan:
    * Create an experiment with 2 prompts, 3 evaluations each.
    * Export CSV and verify in Excel that `grouping_id` is correct and columns are aligned.

## Acceptance Criteria (Checklist)

* [ ] API endpoint `/api/v1/eval/experiments/{id}/export-csv` is functional.
* [ ] CSV contains `prompt`, `grouping_id`, `overall_score`, dimension columns, and `justification` in the correct order.
* [ ] `grouping_id` correctly groups evaluations by prompt.
* [ ] Prompts and justifications are correctly escaped in the CSV.
* [ ] Filename is correctly set to `experiment_[id]_evaluations.csv`.
* [ ] Export button is visible and working on the experiment details page.

## Rollout / Migration Plan

* Not applicable: No breaking changes or data migrations.

## Risks and Alternatives

* Risks:
    * Very large experiments might consume significant memory if the CSV is built entirely in memory before streaming. (Mitigation: Use `StreamingResponse`).
* Alternatives considered:
    * Using `pandas` for CSV generation. (Rejected to keep dependencies minimal as `csv` is sufficient).

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
    * Core Module Logic (`src/vulcanlab`) - Business logic for data formatting in the core module.
    * API Layer Routing (`src/vulcanlab_api`) - Thin router calling the core module.
    * Frontend Page Lifecycle - Using standard UI patterns for actions.
* Deviations (if any):
    * None.

## Implementation Notes (Non-binding)

* Use `csv.QUOTE_MINIMAL` or `csv.QUOTE_ALL` in `csv.DictWriter`.
* Ensure `overall_score` and dimension scores are formatted as numbers (no extra quotes unless needed).
* To get `grouping_id`, query prompts for the experiment ordered by ID and use their index + 1 as the ID.

## Open Questions

* None.

