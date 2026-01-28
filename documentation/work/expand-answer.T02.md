# Ticket: expand-answer.T02 - Core Expansion Logic and Prompt Template

## Source

* Spec: documentation/work/expand-answer.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement the core expansion module with breakdown, section processing, and combination logic
* Create the `answer_breakdown` prompt template for LLM-driven section generation
* Enable full RAG pipeline execution for individual sections

## Scope

### In scope

* New module `src/vulcanlab/expansion/` with `__init__.py`
* `breakdown_answer(result_id, session, llm_client)` - validates token limit, calls LLM, creates sections
* `expand_section(section_id, session)` - runs RAG pipeline (query expansion, embed, retrieve, consolidate)
* `generate_section(section_id, session, llm_client)` - runs augmentation LLM for section response
* `save_manual_response(section_id, response_text, session)` - saves user-provided response
* `combine_sections(expansion_id, session)` - merges completed sections into final report
* Token estimation validation (30,000 token limit on source answer)
* Prompt template file `answer_breakdown.txt` and YAML entry
* FUNCTION_LABELS entry in UI template settings
* Unit tests with mocked DB and LLM

### Out of scope

* API endpoints (T03)
* UI components (T04, T05)
* Background job processing (not required per spec)

## Dependencies

* Depends on: T01 (models and schema)
* Unblocks: T03, T04, T05

## Implementation plan

1. Create `src/vulcanlab/expansion/__init__.py` with module exports
2. Create `src/vulcanlab/expansion/breakdown.py`:
   - `estimate_answer_tokens(answer_text)` using existing heuristic
   - `validate_answer_length(answer_text, max_tokens=30000)` raises ValueError if exceeded
   - `breakdown_answer(result_id, session, llm_client)`:
     - Load result from DB, validate token limit
     - Load `answer_breakdown` template from DB via `get_active_template()`
     - Call LLM with formatted prompt
     - Parse JSON response into 3-7 sections
     - Create `AnswerExpansion` record with status `breakdown_complete`
     - Create `ExpansionSection` records with status `pending`
     - Return expansion_id
3. Create `src/vulcanlab/expansion/section_processing.py`:
   - `expand_section(section_id, session)`:
     - Load section, update status to `expanding`
     - Run query expansion (MQE, HyDE, intent, entities) using existing RAG utilities
     - Generate embeddings for section query
     - Retrieve relevant chunks
     - Consolidate context
     - Store results in section record
     - Update status to `ready`
   - `generate_section(section_id, session, llm_client)`:
     - Load section, update status to `generating`
     - Build augmented prompt from retrieved context
     - Call LLM for response
     - Store response_text
     - Update status to `completed`
   - `save_manual_response(section_id, response_text, session)`:
     - Load section, store response_text
     - Update status to `completed`
4. Create `src/vulcanlab/expansion/combine.py`:
   - `combine_sections(expansion_id, session)`:
     - Load expansion and all sections
     - Verify all sections completed
     - Build markdown report with headings and section responses
     - Add link to original answer at top
     - Store in `combined_report`
     - Update expansion status to `completed`
5. Create prompt template:
   - `src/vulcanlab/data/seed_data/templates/answer_breakdown.txt`
   - Add entry to `templates.yaml` with function_tag, version, title, template_type
   - Add variable documentation to `variables.yaml`
6. Update FUNCTION_LABELS in:
   - `vulcanlab_ui/src/components/settings/templates-tab.tsx`
   - `vulcanlab_ui/src/app/settings/templates/[function_tag]/page.tsx`
7. Write unit tests for all core functions

* Patterns to apply:
  * Prompt Templates - Store in DB, load via `get_active_template()`, seed from YAML/txt
  * Session Management - All functions receive session as parameter
  * Three-tier architecture - Core module independent of API layer

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `test_validate_answer_length_under_limit` - accepts valid length
  * `test_validate_answer_length_over_limit` - raises ValueError when exceeded
  * `test_breakdown_answer_creates_sections` - verify 3-7 sections created with correct fields
  * `test_breakdown_answer_invalid_json` - handles malformed LLM response
  * `test_expand_section_updates_status` - verify status transitions
  * `test_expand_section_stores_rag_data` - verify expanded_queries, hyde_answer, etc. populated
  * `test_generate_section_stores_response` - verify response_text saved
  * `test_save_manual_response` - verify manual mode saves correctly
  * `test_combine_sections_builds_report` - verify markdown format with headings
  * `test_combine_sections_includes_original_link` - verify link to original answer

* Suggested locations:
  * `tests/unit/expansion/test_breakdown.py`
  * `tests/unit/expansion/test_section_processing.py`
  * `tests/unit/expansion/test_combine.py`

* Mocking/fakes needed:
  * Mock SQLAlchemy session
  * Mock LLM client (return predefined JSON for breakdown)
  * Mock existing RAG utilities (query expansion, retrieval, etc.)

## Acceptance criteria (checklist)

* [ ] `breakdown_answer()` validates 30,000 token limit and rejects oversized answers
* [ ] `breakdown_answer()` calls LLM and parses response into 3-7 sections
* [ ] Each section has heading, summary, and expansion_prompt populated
* [ ] `expand_section()` runs full RAG pipeline and stores results
* [ ] `generate_section()` calls LLM and stores response_text
* [ ] `save_manual_response()` stores user-provided text
* [ ] `combine_sections()` generates markdown with headings and original answer link
* [ ] `answer_breakdown` prompt template seeded via init_db
* [ ] FUNCTION_LABELS added to UI template settings
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Run `python -m vulcanlab.data.init_db -v` to seed template
  2. Navigate to Settings > Templates in UI
  3. Verify "Answer Breakdown" template appears and is editable
  4. Run unit tests: `pytest tests/unit/expansion/ -v`

* Expected results:
  * Template visible in Settings > Templates with proper label
  * All unit tests pass with mocked dependencies

## Notes

* Requirements covered: R2 (token validation), R3 (breakdown into 3-7 sections), R4 (RAG pipeline per section), R5 (automatic/manual modes), R9 (combine into report), R10 (link to original answer)
* The breakdown prompt should instruct LLM to output JSON matching expected schema
* Use `asyncio.Semaphore(2)` or similar for concurrent section processing in automatic mode (implemented in API layer)
* Section order must be preserved from breakdown through to combined report
* Import from `vulcanlab.retrieval` and `vulcanlab.augmentation` for RAG steps
