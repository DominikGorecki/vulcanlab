# Ticket: work-summarization.T07 - LLM Summarization Module

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement LLM integration for generating structured summaries from evidence packets
* Parse LLM responses into SummaryNode field structures
* Implement escalation loop for insufficient evidence scenarios
* Support configurable LLM model selection

## Phase

* Core Modules

## Scope

### In scope

* src/vulcanlab/summarize/llm_summarize.py module
* Prompt template for structured summary extraction
* Response parsing into gist, key_points, definitions, key_terms, examples
* Line anchor extraction from LLM response
* Insufficient evidence detection from LLM response
* Escalation logic: request more context and retry
* LLM model configuration via vulcanlab.config
* Retry logic with exponential backoff for API failures

### Out of scope

* Orchestration across multiple nodes (T08)
* Evidence packet extraction (T05)
* Derived output generation (T09)

## Dependencies

* Depends on: T05 (EvidencePacket), T10 (prompt templates must be seeded in database)
* Unblocks: T08

## Implementation plan

1. Create src/vulcanlab/summarize/llm_summarize.py
2. Define response dataclasses:
   - `KeyPoint(text: str, start_line: int, end_line: int)`
   - `Definition(term: str, definition: str, start_line: int, end_line: int)`
   - `KeyTerm(term: str, start_line: int, end_line: int)`
   - `Example(text: str, start_line: int, end_line: int)`
   - `SummaryResponse(gist: str, key_points: list[KeyPoint], definitions: list[Definition], key_terms: list[KeyTerm], examples: list[Example], insufficient_evidence: bool, missing_concepts: list[str])`
3. Implement `get_active_template(function_tag: str, session: Session) -> str`:
   - Query prompt_templates table for active template by function_tag
   - Return template_content string
   - Raise error if no active template found
4. Implement `build_summarization_prompt(evidence: EvidencePacket, session: Session) -> str`:
   - Load template from database using get_active_template("summarize_node", session)
   - Format template with evidence packet variables
   - Include heading path, line range, stats
   - Include all snippets with their line numbers
   - Include keyphrases as context
4. Implement `parse_llm_response(response_text: str, evidence: EvidencePacket) -> SummaryResponse`:
   - Parse JSON from LLM response
   - Validate line numbers are within evidence packet range
   - Handle malformed responses gracefully
5. Implement `get_llm_model() -> str`:
   - Read from vulcanlab.config or use default
6. Implement `call_llm(prompt: str, model: str) -> str`:
   - Use existing LLM integration pattern from project
   - Implement retry with exponential backoff (max 3 retries)
   - Log token usage
7. Implement `summarize_node(evidence: EvidencePacket, additional_context: str | None = None) -> SummaryResponse`:
   - Build prompt (include additional_context if provided)
   - Call LLM
   - Parse response
   - Return SummaryResponse
8. Implement `handle_escalation(evidence: EvidencePacket, missing_concepts: list[str], full_content: str) -> str`:
   - Extract additional sentences related to missing concepts
   - Return as additional_context string
* Patterns to apply:
  * Core Module independence (no FastAPI)
  * Use existing LLM/API patterns from project
  * Configuration via vulcanlab.config
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `build_summarization_prompt` includes all evidence packet components
  * `build_summarization_prompt` formats line numbers correctly
  * `parse_llm_response` extracts all fields from valid JSON
  * `parse_llm_response` handles missing optional fields
  * `parse_llm_response` validates line number ranges
  * `parse_llm_response` handles malformed JSON gracefully
  * `summarize_node` returns SummaryResponse with all fields
  * `summarize_node` detects insufficient_evidence flag
  * `handle_escalation` extracts relevant additional context
  * Retry logic triggers on API failure
  * Retry respects max retry limit
* Suggested locations:
  * tests/unit/summarize/test_llm_summarize.py
* Mocking/fakes needed:
  * Mock LLM API calls with predefined responses
  * Mock config for model selection
  * Mock API failures for retry testing

## Acceptance criteria (checklist)

* [ ] Prompt template requests structured JSON with line anchors
* [ ] LLM response parsed into all required fields
* [ ] Line numbers validated against evidence packet range
* [ ] Insufficient evidence flag detected from response
* [ ] Escalation adds relevant additional context
* [ ] Model selection reads from config
* [ ] Retry with exponential backoff implemented (max 3)
* [ ] Token usage logged
* [ ] Malformed responses handled without crash
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Create sample EvidencePacket
  2. Call `summarize_node(evidence)` with real LLM
  3. Inspect returned SummaryResponse
  4. Verify line numbers in response match evidence
* Expected results:
  * Structured summary returned with all fields
  * Line anchors point to valid locations
  * Response is coherent and relevant

## Notes

* Requirements covered: R7, R8, R15, R16
* Prompt should emphasize: "Return line numbers from the provided snippets"
* LLM output format should be explicit JSON schema in prompt
* insufficient_evidence flag allows LLM to signal when it can't summarize well
* Escalation is limited to one retry to avoid infinite loops
* Templates are loaded from database (prompt_templates table), NEVER from filesystem
* Use get_active_template() to query the active version for each function_tag
* Templates are editable via Settings > Templates UI (seeded by T10)
* Token usage tracking helps monitor costs per R16
