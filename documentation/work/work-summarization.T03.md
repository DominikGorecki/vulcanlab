# Ticket: work-summarization.T03 - Prompt Template for Section Summarization

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create the `summarize_sections` prompt template for LLM-based section summarization
* Register template in `templates.yaml` with appropriate metadata
* Document template variables in `variables.yaml`
* Ensure template is seeded on database initialization

## Phase

* Migrations

## Scope

### In scope

* Template file `src/vulcanlab/data/seed_data/templates/summarize_sections.txt`
* Entry in `src/vulcanlab/data/seed_data/templates.yaml`
* Variable documentation in `src/vulcanlab/data/seed_data/variables.yaml`
* Update `FUNCTION_LABELS` in UI template components

### Out of scope

* Core module prompt assembly logic (T08)
* API endpoints (T10+)
* Settings UI tab (T16)

## Dependencies

* Depends on: T02 (models must exist for seeding to work)
* Unblocks: T08 (prompt assembly uses this template)

## Implementation plan

1. Create `src/vulcanlab/data/seed_data/templates/summarize_sections.txt`:
   - System instructions for summarization task
   - Expected input format (headings with IDs and chunks)
   - JSON output format specification: `[{ "id": number, "summary": "markdown" }]`
   - Guidelines for summary length and style
   - Instructions to preserve heading structure in output
2. Add entry to `src/vulcanlab/data/seed_data/templates.yaml`:
   ```yaml
   - function_tag: summarize_sections
     version: 1
     title: "Section Summarization - Chunk-based Summary Generation"
     template_type: summarize
     is_active: true
     content_file: summarize_sections.txt
   ```
3. Add variable documentation to `src/vulcanlab/data/seed_data/variables.yaml`:
   ```yaml
   - function_tag: summarize_sections
     variables:
       - variable_name: sections_content
         variable_description: "Formatted sections with heading IDs and ranked chunks"
       - variable_name: context_headings
         variable_description: "Headings above and below current batch for context"
   ```
4. Update `vulcanlab_ui/src/components/settings/templates-tab.tsx`:
   - Add `summarize_sections` to `FUNCTION_LABELS` with human-readable label
5. Update `vulcanlab_ui/src/app/settings/templates/[function_tag]/page.tsx`:
   - Add `summarize_sections` to `FUNCTION_LABELS` (keep in sync)
6. Run `python -m vulcanlab.data.init_db -v` to verify seeding works
7. Verify template appears in Settings > Templates UI

* Patterns to apply:
  * **Prompt Templates in Database** - Template seeded via templates.yaml, loaded via `get_active_template()`
  * **Adding New Prompt Templates** - Follow checklist from patterns.md
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Template file exists and is non-empty
  * YAML entry is valid and references correct file
  * Template contains required placeholders (`{sections_content}`, `{context_headings}`)
  * JSON output format instructions are present in template
  * Variables.yaml entry documents all placeholders
* Suggested locations:
  * `tests/unit/test_summarize_template.py`
* Mocking/fakes needed:
  * None (file-based validation)

## Acceptance criteria (checklist)

* [ ] Template file created at correct path
* [ ] Entry added to templates.yaml with `template_type: summarize`
* [ ] Variables documented in variables.yaml
* [ ] FUNCTION_LABELS updated in both UI files
* [ ] Template seeds successfully on init_db
* [ ] Template appears in Settings > Templates UI with correct label
* [ ] Template instructs LLM to return JSON array format

## Manual verification

* Steps:
  * Run `python scripts/test_template_seeding.py` to validate configuration
  * Run `python -m vulcanlab.data.init_db -v` on fresh database
  * Navigate to Settings > Templates in UI
  * Find "Section Summarization" template and view content
  * Verify JSON output format instructions are clear
* Expected results:
  * Template appears with human-readable title
  * Content matches the .txt file
  * Template is marked as active

## Notes

* Requirements covered: R8 (use prompt template from database)
* Template should be clear about JSON output format to enable reliable parsing in T09
* Consider including example input/output in template for LLM clarity
* Template variables will be substituted by prompt_generator.py (T08)
