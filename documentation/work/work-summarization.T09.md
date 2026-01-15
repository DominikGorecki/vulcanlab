# Ticket: work-summarization.T09 - Derived Output Compilation Module

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement compilation of derived outputs (abstract, outline, key_concepts, chapter_summaries) from summary_nodes
* Generate structured content with aggregated line references
* Store results in work_summaries table

## Phase

* Core Modules

## Scope

### In scope

* src/vulcanlab/summarize/compile.py module
* Abstract generation: synthesize work-level summary from all node gists
* Outline generation: build hierarchical structure from summary_nodes
* Key concepts generation: aggregate and deduplicate definitions/key_terms across nodes
* Chapter summaries generation: compile H1/H2 level summaries
* Line reference aggregation for each output type
* LLM calls for synthesis where needed (abstract, key concepts cleanup)
* Storage to work_summaries table

### Out of scope

* Initial summarization (T08)
* API endpoints (T11)
* UI display (T15)

## Dependencies

* Depends on: T03 (models), T07 (LLM for synthesis), T08 (summary_nodes must exist), T10 (templates for synthesize_abstract, organize_key_concepts)
* Unblocks: T11

## Implementation plan

1. Create src/vulcanlab/summarize/compile.py
2. Implement `load_summary_nodes(work_id: int, session: Session) -> list[SummaryNode]`:
   - Query all summary_nodes for work ordered by start_line
3. Implement `compile_abstract(nodes: list[SummaryNode], work_title: str, session: Session) -> WorkSummary`:
   - Collect all gists from nodes
   - Load template from database: get_active_template("synthesize_abstract", session)
   - Format template with work_title and gists
   - Call LLM to synthesize into cohesive abstract
   - Parse LLM response
   - Aggregate line references from all contributing nodes
   - Create and return WorkSummary with type='abstract'
4. Implement `compile_outline(nodes: list[SummaryNode], session: Session) -> WorkSummary`:
   - Build hierarchical structure from nodes using heading levels
   - For each node: heading (from breadcrumbs), gist, depth, start_line, end_line
   - Build nested children structure
   - No LLM needed - pure transformation
   - Create and return WorkSummary with type='outline'
5. Implement `compile_key_concepts(nodes: list[SummaryNode], work_title: str, session: Session) -> WorkSummary`:
   - Aggregate all definitions from all nodes
   - Aggregate all key_terms from all nodes
   - Deduplicate by term name (merge occurrences)
   - Load template from database: get_active_template("organize_key_concepts", session)
   - Format template with work_title and concepts
   - Call LLM to clean up and organize
   - Create and return WorkSummary with type='key_concepts'
6. Implement `compile_chapter_summaries(nodes: list[SummaryNode], session: Session) -> WorkSummary`:
   - Filter to H1 and H2 level nodes only
   - For each: heading, gist as summary, line references
   - Optionally call LLM to expand gists into fuller summaries
   - Create and return WorkSummary with type='chapter_summaries'
7. Implement `generate_derived_output(work_id: int, output_type: str, session: Session) -> WorkSummary`:
   - Load summary_nodes
   - Route to appropriate compile function
   - Check if output already exists (upsert or error)
   - Return created/updated WorkSummary
8. Implement `get_derived_outputs(work_id: int, session: Session) -> list[WorkSummary]`:
   - Query all work_summaries for work
* Patterns to apply:
  * Session passed explicitly
  * Core Module independence
  * Use WorkSummaryType enum for type values
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `load_summary_nodes` returns nodes in document order
  * `compile_abstract` synthesizes from multiple gists
  * `compile_abstract` aggregates line references correctly
  * `compile_outline` builds correct hierarchy from flat node list
  * `compile_outline` handles single-level documents (all H1)
  * `compile_outline` handles deeply nested documents (H1>H2>H3>H4)
  * `compile_key_concepts` deduplicates terms across nodes
  * `compile_key_concepts` merges occurrence line references
  * `compile_chapter_summaries` filters to H1/H2 only
  * `generate_derived_output` routes to correct compiler
  * `generate_derived_output` handles non-existent work gracefully
  * Upsert behavior: regenerating replaces existing output
* Suggested locations:
  * tests/unit/summarize/test_compile.py
* Mocking/fakes needed:
  * Mock session with fake summary_nodes
  * Mock LLM for abstract/key_concepts synthesis

## Acceptance criteria (checklist)

* [ ] Abstract compiles from all node gists with LLM synthesis
* [ ] Outline builds hierarchical structure without LLM
* [ ] Key concepts aggregates and deduplicates definitions/terms
* [ ] Chapter summaries extracts H1/H2 level content
* [ ] All outputs include aggregated line references
* [ ] WorkSummary records created with correct type
* [ ] Existing outputs can be regenerated (upsert)
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Ensure a work has summary_nodes (from T08)
  2. Call `generate_derived_output(work_id, 'outline', session)`
  3. Inspect returned WorkSummary content structure
  4. Generate other output types and verify
* Expected results:
  * Each output type has appropriate structure
  * Line references point to valid locations
  * Outline hierarchy matches document structure

## Notes

* Requirements covered: R9, R10, R11
* Abstract requires LLM to synthesize - can't just concatenate gists
* Outline is pure transformation - no LLM needed
* Key concepts uses LLM for cleanup/organization
* Chapter summaries: consider whether to expand gists or use as-is
* JSONB content structures must match spec definitions
* Deduplication for key_concepts: match by normalized term (lowercase, strip whitespace)
* Templates are loaded from database (prompt_templates table), NEVER from filesystem
* Use get_active_template() from T07 to query the active version for each function_tag
* Templates are editable via Settings > Templates UI (seeded by T10)
