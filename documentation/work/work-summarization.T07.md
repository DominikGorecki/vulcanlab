# Ticket: work-summarization.T07 - Prompt Generator: Budget Calculation and Content Pruning

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement token budget calculation for LLM prompts
* Implement content pruning strategy to fit within budget
* Prioritize higher-level headings (H1/H2) when pruning

## Phase

* Core Modules

## Scope

### In scope

* New module `src/vulcanlab/summarization/prompt_generator.py`
* Token estimation using configurable tokens-per-word ratio
* Budget enforcement across multiple LLM calls
* Pruning algorithm that removes chunks from lower-level headings first

### Out of scope

* Prompt template assembly (T08)
* JSON response parsing (T09)
* API endpoints (T10+)

## Dependencies

* Depends on: T04 (heading selector), T06 (ranked chunks with MMR)
* Unblocks: T08 (uses pruned content for assembly)

## Implementation plan

1. Create `src/vulcanlab/summarization/prompt_generator.py`
2. Implement `PromptBudget` dataclass:
   - max_calls: int
   - max_tokens_per_call: int
   - tokens_per_word: float
   - current_token_count: int
3. Implement `estimate_tokens(text: str, tokens_per_word: float) -> int`:
   - Count words in text
   - Multiply by tokens_per_word ratio
   - Return estimated token count
4. Implement `HeadingWithChunks` dataclass:
   - heading: HeadingInfo
   - ranked_chunks: list[RankedChunk]
   - total_tokens: int (estimated)
5. Implement `calculate_total_budget(headings_with_chunks: list[HeadingWithChunks], settings: SummarizeSettings) -> tuple[int, int]`:
   - Sum tokens across all headings and their chunks
   - Return (total_tokens, max_budget = max_calls * max_tokens_per_call)
6. Implement `prune_to_budget(headings_with_chunks: list[HeadingWithChunks], max_budget: int, settings: SummarizeSettings) -> list[HeadingWithChunks]`:
   - While total > max_budget:
     - Find lowest level headings (H5 before H4 before H3, etc.)
     - Among those, find heading with most chunks > minimum
     - Remove lowest-ranked chunk from that heading
     - Recalculate total
   - Minimum chunks: H1/H2 = settings.h1_h2_min_chunks, H3+ = settings.h3_min_chunks
   - If still over budget after hitting minimums, remove entire lowest-level headings
   - Return pruned list
7. Implement `get_heading_level(level_str: str) -> int`:
   - Parse "H1" -> 1, "H2" -> 2, etc.
   - Used for pruning priority
8. Implement helper `total_tokens(headings_with_chunks: list[HeadingWithChunks]) -> int`:
   - Sum all heading and chunk tokens

* Patterns to apply:
  * **Core Module Independence** - Pure Python, no framework dependencies
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `estimate_tokens` with various texts and ratios
  * `estimate_tokens` handles empty string
  * `calculate_total_budget` sums correctly
  * `prune_to_budget` removes from lowest level first
  * `prune_to_budget` removes lowest-ranked chunk within level
  * `prune_to_budget` respects H1/H2 minimum of 2 chunks
  * `prune_to_budget` respects H3+ minimum of 1 chunk
  * `prune_to_budget` removes entire heading when at minimum and still over
  * `prune_to_budget` does nothing when already under budget
  * Edge case: single heading with single chunk
  * Edge case: all headings at minimum, still over budget
* Suggested locations:
  * `tests/unit/test_prompt_generator_budget.py`
* Mocking/fakes needed:
  * Mock HeadingInfo and RankedChunk with controlled token counts

## Acceptance criteria (checklist)

* [ ] Token estimation uses configurable ratio (default 0.75)
* [ ] Total budget calculated as max_calls * max_tokens_per_call
* [ ] Pruning removes chunks from lowest heading levels first
* [ ] Pruning removes lowest-ranked chunk when multiple options
* [ ] H1/H2 headings keep minimum 2 chunks
* [ ] H3+ headings keep minimum 1 chunk
* [ ] Result fits within budget after pruning
* [ ] Unit tests pass for all pruning scenarios

## Manual verification

* Steps:
  * Create test data with known word counts per heading/chunk
  * Set budget lower than total content
  * Call `prune_to_budget` and inspect which chunks were removed
  * Verify H1/H2 retain more chunks than H4/H5
* Expected results:
  * Lower-level headings pruned more aggressively
  * Higher-ranked chunks retained within each heading
  * Final token count under budget

## Notes

* Requirements covered: R6 (max 5 calls, 15K tokens each, 0.75 tokens/word), R7 (pruning priority)
* Token estimation is approximate; real LLM tokenization may differ
* Spec says: "if still over budget start removing the lowest level chunks without consideration for keeping at least 2 for H1 and H2" - implement as fallback
* This ticket handles the budget math; T08 handles prompt assembly
