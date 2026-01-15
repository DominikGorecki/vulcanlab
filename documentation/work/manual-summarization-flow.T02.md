# Ticket: manual-summarization-flow.T02 - Prompt Formatter Module

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Extract prompt construction logic from llm_summarize.py into reusable prompt_formatter module
* Ensure manual mode exposes identical prompts to automated flow
* Add function to format derived output prompts for manual mode

## Scope

### In scope

* Create `src/vulcanlab/summarize/prompt_formatter.py` module
* Extract `format_node_summarization_prompt()` from llm_summarize.py logic
* Add `format_derived_output_prompt()` for abstract/outline/key_concepts/chapter_summaries
* Refactor llm_summarize.py to use the new prompt_formatter (DRY)
* Load prompt templates from database using existing get_active_template pattern

### Out of scope

* API endpoints (T03)
* Response parsing (T03)
* Frontend display (T04)

## Dependencies

* Depends on: T01 (for enum imports, though not strictly blocking)
* Unblocks: T03, T06

## Implementation plan

1. Analyze existing prompt construction in `src/vulcanlab/summarize/llm_summarize.py`:
   - Identify template loading pattern
   - Extract variable substitution logic
   - Note any hardcoded prompt elements

2. Create `src/vulcanlab/summarize/prompt_formatter.py`:
   ```python
   def format_node_summarization_prompt(
       evidence: EvidencePacket,
       chunk_id: int,
       session: Session
   ) -> str:
       """Format the summarization prompt for a single node.

       Returns the exact same prompt used by automated flow.
       """
       template = get_active_template("summarize_node", session)
       # ... substitute variables
       return formatted_prompt

   def format_derived_output_prompt(
       output_type: str,
       summary_nodes: List[SummaryNode],
       session: Session
   ) -> str:
       """Format prompt for derived output generation.

       Args:
           output_type: One of 'abstract', 'outline', 'key_concepts', 'chapter_summaries'
       """
       template_tag = f"summarize_{output_type}"
       template = get_active_template(template_tag, session)
       # ... substitute variables
       return formatted_prompt
   ```

3. Refactor `llm_summarize.py` to import and use `format_node_summarization_prompt()`:
   - Replace inline prompt construction with function call
   - Ensure no behavior change in automated flow

4. Refactor `compile.py` to import and use `format_derived_output_prompt()`:
   - Replace inline prompt construction with function call
   - Ensure no behavior change in derived output generation

5. Verify prompt templates exist in database:
   - Check `summarize_node` template exists
   - Check derived output templates exist (or add to templates.yaml if missing)

* Patterns to apply:
  * **Prompt Templates**: Load from database via get_active_template, never from filesystem
  * **Three-tier architecture**: Core module logic, no HTTP concerns
  * **Session management**: Database session passed explicitly to functions

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `format_node_summarization_prompt` returns non-empty string with expected structure
  * `format_node_summarization_prompt` includes evidence packet content in output
  * `format_derived_output_prompt` accepts all four output types
  * `format_derived_output_prompt` raises ValueError for invalid output_type
  * Prompts contain expected variable substitutions (heading_path, content samples, etc.)

* Suggested locations:
  * `tests/unit/summarize/test_prompt_formatter.py`

* Mocking/fakes needed:
  * Mock database session
  * Mock get_active_template to return test template strings
  * Mock EvidencePacket with sample data

## Acceptance criteria (checklist)

* [ ] prompt_formatter.py module created with both functions
* [ ] llm_summarize.py refactored to use format_node_summarization_prompt
* [ ] compile.py refactored to use format_derived_output_prompt
* [ ] Automated summarization still works identically (no behavior change)
* [ ] All four derived output types supported
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Run existing automated summarization on a test work
  * Compare logged prompts before and after refactor
  * Call format_node_summarization_prompt directly and inspect output

* Expected results:
  * Prompts are identical before and after refactor
  * Manual prompt inspection shows proper variable substitution
  * No regressions in automated summarization

## Notes

* Requirements covered: R6 (identical prompts to automated flow)
* This is a refactor that extracts existing logic - prompts must remain identical
* If templates are missing from database, add them to templates.yaml and variables.yaml per patterns.md
* Evidence packet structure defined in evidence.py should be documented in prompt template
