# Ticket: work-summarization.T08 - Prompt Generator: Template Assembly and Batching

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Assemble LLM prompts from pruned content using database template
* Batch headings into multiple prompts within token budget
* Include context headings (above/below) for each batch
* Format content with heading IDs and line numbers

## Phase

* Core Modules

## Scope

### In scope

* Prompt assembly logic in `src/vulcanlab/summarization/prompt_generator.py`
* Template loading from database via `get_active_template()`
* Batching headings into multiple prompts
* Formatting sections with IDs, line numbers, and chunk content

### Out of scope

* Budget calculation and pruning (T07)
* JSON response parsing (T09)
* API endpoints (T10+)

## Dependencies

* Depends on: T03 (template exists), T07 (provides pruned content)
* Unblocks: T10 (API generates and returns prompts)

## Implementation plan

1. Extend `prompt_generator.py` with assembly functions
2. Implement `PromptBatch` dataclass:
   - prompt_index: int
   - content: str (the assembled prompt)
   - heading_ids: list[int] (chunk IDs of headings in this batch)
   - estimated_tokens: int
3. Implement `format_section(heading: HeadingInfo, chunks: list[RankedChunk]) -> str`:
   - Format as:
     ```
     # {heading_title}
     -- id: {heading.chunk_id}
     -- lines: {start_line}-{end_line}

     [Chunk 1 content]
     -- chunk_id: {chunk_id}, lines: {start}-{end}

     [Chunk 2 content]
     ...
     ```
4. Implement `format_context_headings(all_headings: list[HeadingInfo], batch_start: int, batch_end: int) -> str`:
   - List headings before batch_start (titles only, no content)
   - List headings after batch_end (titles only)
   - Provides document context for LLM
5. Implement `batch_headings(headings_with_chunks: list[HeadingWithChunks], max_tokens_per_call: int, tokens_per_word: float) -> list[list[HeadingWithChunks]]`:
   - Greedily pack headings into batches
   - Each batch stays under max_tokens_per_call
   - Return list of batches
6. Implement `assemble_prompts(headings_with_chunks: list[HeadingWithChunks], session: Session, settings: SummarizeSettings) -> list[PromptBatch]`:
   - Load template via `get_active_template("summarize_sections", session)`
   - Batch headings using `batch_headings()`
   - For each batch:
     - Format sections content
     - Format context headings
     - Substitute into template: `{sections_content}`, `{context_headings}`
     - Create PromptBatch with assembled content
   - Return list of PromptBatch
7. Implement main entry `generate_prompts(work_id: int, session: Session, settings: SummarizeSettings) -> list[PromptBatch]`:
   - Call heading_selector to get headings
   - Rank chunks for each heading
   - Prune to budget
   - Assemble prompts
   - Return batches

* Patterns to apply:
  * **Prompt Templates in Database** - Load via `get_active_template()`
  * **Session Passed Explicitly** - Session for template query
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `format_section` produces expected markdown format
  * `format_section` includes heading ID and line numbers
  * `format_section` includes chunk IDs and line numbers
  * `format_context_headings` lists headings before and after batch
  * `batch_headings` respects token limit
  * `batch_headings` creates multiple batches when needed
  * `batch_headings` handles single large heading (gets own batch)
  * `assemble_prompts` substitutes template variables correctly
  * `assemble_prompts` creates correct number of batches
  * Edge case: single heading fits in one batch
  * Edge case: max_llm_calls limit exceeded (error or warning)
* Suggested locations:
  * `tests/unit/test_prompt_generator_assembly.py`
* Mocking/fakes needed:
  * Mock `get_active_template()` to return test template
  * Mock session for template query
  * Mock HeadingWithChunks with controlled content

## Acceptance criteria (checklist)

* [ ] Template loaded from database using correct function_tag
* [ ] Sections formatted with IDs and line numbers
* [ ] Context headings included in each prompt
* [ ] Batching respects max_tokens_per_call
* [ ] Number of batches <= max_llm_calls
* [ ] PromptBatch includes heading_ids for response parsing
* [ ] Unit tests pass for formatting and batching

## Manual verification

* Steps:
  * Use a test work with multiple headings
  * Call `generate_prompts` and inspect returned batches
  * Copy a generated prompt to an LLM to verify it's coherent
  * Check that prompt includes document structure context
* Expected results:
  * Prompts are well-formatted and readable
  * Each prompt identifies which headings to summarize
  * Token estimates are reasonable

## Notes

* Requirements covered: R6 (max 5 calls, 15K tokens), R8 (use prompt template)
* Spec format for expected response:
  ```json
  [{ "id": heading_chunk_id, "summary": "markdown summary" }]
  ```
* Template should instruct LLM to return this exact format
* heading_ids in PromptBatch needed by T09 for response parsing
