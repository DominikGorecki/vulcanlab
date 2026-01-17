# Ticket: work-summarization.T06 - Chunk Ranker: MMR Re-ranking

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement Maximal Marginal Relevance (MMR) re-ranking to diversify chunk selection
* Apply MMR after RRF fusion to reduce redundancy in selected chunks
* Balance relevance and diversity using configurable lambda parameter

## Phase

* Core Modules

## Scope

### In scope

* MMR algorithm implementation in `src/vulcanlab/summarization/chunk_ranker.py`
* Pairwise similarity computation between chunk embeddings
* Integration with existing RRF output from T05

### Out of scope

* Dense/lexical search (T05)
* Prompt generation (T07, T08)
* API endpoints (T10+)

## Dependencies

* Depends on: T05 (provides RRF-ranked chunks as input)
* Unblocks: T07, T10

## Implementation plan

1. Extend `RankedChunk` dataclass to include:
   - mmr_score (final score after MMR)
   - embedding (cached for pairwise comparison)
2. Implement `compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float`:
   - Calculate cosine similarity between two embeddings
   - Return value in range [-1, 1]
3. Implement `get_chunk_embeddings(chunk_ids: list[int], session: Session) -> dict[int, list[float]]`:
   - Batch fetch embeddings for given chunk IDs
   - Return mapping of chunk_id -> embedding
4. Implement `rerank_mmr(ranked_chunks: list[RankedChunk], embeddings: dict[int, list[float]], lambda_param: float, top_n: int) -> list[RankedChunk]`:
   - MMR formula: `MMR = lambda * relevance - (1 - lambda) * max_similarity_to_selected`
   - Start with empty selected set
   - Iteratively select chunk with highest MMR score
   - Add to selected, remove from candidates
   - Repeat until top_n selected or candidates exhausted
   - Assign mmr_score and rank_position to each selected chunk
5. Update `rank_content_chunks` to integrate MMR:
   - After RRF fusion, fetch embeddings for top candidates
   - Apply MMR re-ranking with settings.mmr_lambda and settings.mmr_top_n
   - Return final list with mmr_score and rank_position populated
6. Handle edge cases:
   - Chunks without embeddings (skip or use fallback)
   - Fewer candidates than top_n requested
   - Lambda = 1.0 (pure relevance, no diversity)
   - Lambda = 0.0 (pure diversity)

* Patterns to apply:
  * **Core Module Independence** - Pure Python algorithm, no framework dependencies
  * **Session Passed Explicitly** - Embedding fetch uses session
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `compute_similarity` returns 1.0 for identical embeddings
  * `compute_similarity` returns ~0 for orthogonal embeddings
  * `compute_similarity` handles normalized vectors correctly
  * `rerank_mmr` with lambda=1.0 preserves relevance order
  * `rerank_mmr` with lambda=0.0 maximizes diversity
  * `rerank_mmr` with lambda=0.7 balances both
  * `rerank_mmr` handles fewer candidates than top_n
  * `rerank_mmr` assigns correct rank_position (1, 2, 3...)
  * Edge case: single chunk (returns it as-is)
  * Edge case: empty input (returns empty list)
  * Edge case: chunks with missing embeddings are skipped
* Suggested locations:
  * `tests/unit/test_chunk_ranker_mmr.py`
* Mocking/fakes needed:
  * Mock embeddings (known vectors for deterministic tests)
  * Mock session for embedding fetch

## Acceptance criteria (checklist)

* [ ] MMR algorithm implemented correctly per formula
* [ ] Cosine similarity computed accurately
* [ ] Lambda parameter controls relevance vs diversity tradeoff
* [ ] Top-N limit respected in output
* [ ] mmr_score and rank_position populated for all selected chunks
* [ ] Integration with RRF pipeline works end-to-end
* [ ] Unit tests pass for all MMR functions

## Manual verification

* Steps:
  * Create test chunks with known embeddings (some similar, some diverse)
  * Run full ranking pipeline with various lambda values
  * Compare output order at lambda=1.0 vs lambda=0.5
  * Verify diverse chunks appear higher at lower lambda
* Expected results:
  * Lambda=1.0: Order matches RRF order
  * Lambda=0.7: Some reordering for diversity
  * Selected chunks have diminishing similarity to each other

## Notes

* Requirements covered: R4 (MMR 0.7, top N=5)
* MMR is applied AFTER RRF fusion, not during search
* Use existing chunk embeddings from `chunks.embedding` column
* Settings provide: mmr_lambda (default 0.7), mmr_top_n (default 5)
* Consider caching embeddings to avoid repeated fetches if processing many headings
