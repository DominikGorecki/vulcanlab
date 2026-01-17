# Ticket: work-summarization.T05 - Chunk Ranker: Dense and Lexical Search with RRF

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement chunk ranking using dense search, lexical search, and RRF fusion
* Search child content-chunks of each heading using heading breadcrumbs + title as query
* Store intermediate scores and produce fused ranking per heading

## Phase

* Core Modules

## Scope

### In scope

* New module `src/vulcanlab/summarization/chunk_ranker.py`
* Dense search against content-chunk embeddings (pgvector cosine similarity)
* Lexical search against content-chunk tsvector (PostgreSQL full-text search)
* RRF fusion of dense and lexical results
* Dataclass for ranked chunk results with all scores

### Out of scope

* MMR re-ranking (T06)
* Storing results to database (handled in T10 API)
* Prompt generation (T07, T08)

## Dependencies

* Depends on: T02 (models), T04 (heading selector provides headings to rank)
* Unblocks: T06 (MMR uses RRF output), T10 (API stores results)

## Implementation plan

1. Create `src/vulcanlab/summarization/chunk_ranker.py`
2. Implement `RankedChunk` dataclass:
   - chunk_id, content, word_count
   - dense_score, dense_rank (nullable if not in dense results)
   - lexical_score, lexical_rank (nullable if not in lexical results)
   - rrf_score
3. Implement `build_search_query(heading_breadcrumbs: str, heading_title: str) -> str`:
   - Combine breadcrumbs and title for search query
   - Strip markdown formatting, normalize whitespace
4. Implement `search_dense(query: str, content_chunk_ids: list[int], session: Session, top_k: int) -> list[tuple[int, float]]`:
   - Generate embedding for query using `create_embeddings()` (lazy import)
   - Query chunks table with pgvector cosine similarity
   - Filter to only content_chunk_ids (children of heading)
   - Return list of (chunk_id, similarity_score) ordered by score desc
5. Implement `search_lexical(query: str, content_chunk_ids: list[int], session: Session, top_k: int) -> list[tuple[int, float]]`:
   - Use PostgreSQL ts_rank with plainto_tsquery
   - Filter to only content_chunk_ids
   - Return list of (chunk_id, rank_score) ordered by score desc
6. Implement `fuse_rrf(dense_results: list, lexical_results: list, k: int, top_k: int) -> list[RankedChunk]`:
   - Apply RRF formula: `score = 1/(k + rank_dense) + 1/(k + rank_lexical)`
   - Use penalty rank (999999) for missing results
   - Sort by rrf_score descending
   - Return top_k results
7. Implement main entry `rank_content_chunks(heading: HeadingInfo, session: Session, settings: SummarizeSettings) -> list[RankedChunk]`:
   - Get child content-chunks (where parent_id = heading.chunk_id)
   - Build search query from heading
   - Call dense search, lexical search
   - Fuse with RRF
   - Return ranked list with all scores populated

* Patterns to apply:
  * **Core Module Independence** - Lazy import for AI dependencies
  * **Session Passed Explicitly** - Session parameter for all DB operations
* Deviations (if any):
  * Independent RRF implementation (not reusing search_hybrid.py per spec requirement)

## Unit tests (required)

* Add tests for:
  * `build_search_query` combines breadcrumbs and title correctly
  * `build_search_query` handles empty breadcrumbs
  * `fuse_rrf` calculates scores correctly with known inputs
  * `fuse_rrf` handles chunks appearing in only one search
  * `fuse_rrf` handles chunks appearing in both searches
  * `fuse_rrf` applies penalty rank for missing results
  * `fuse_rrf` returns correct top_k count
  * Edge case: no dense results
  * Edge case: no lexical results
  * Edge case: single chunk
* Suggested locations:
  * `tests/unit/test_chunk_ranker.py`
* Mocking/fakes needed:
  * Mock SQLAlchemy session for search queries
  * Mock `create_embeddings()` to return fake embedding
  * Mock pgvector query results
  * Mock tsvector query results

## Acceptance criteria (checklist)

* [ ] `chunk_ranker.py` implements all specified functions
* [ ] Dense search uses pgvector cosine similarity
* [ ] Lexical search uses PostgreSQL full-text search
* [ ] RRF fusion produces correct scores per formula
* [ ] Results filtered to only child content-chunks of heading
* [ ] All scores (dense, lexical, RRF) populated in output
* [ ] Unit tests pass for all functions

## Manual verification

* Steps:
  * Create test work with known chunk structure
  * Call `rank_content_chunks` for a heading with multiple children
  * Verify dense scores correlate with semantic similarity
  * Verify lexical scores correlate with keyword overlap
  * Verify RRF combines rankings sensibly
* Expected results:
  * Chunks relevant to heading rank higher
  * Scores are populated and in expected ranges
  * Top-k limit respected

## Notes

* Requirements covered: R4 (dense top 7, lexical top 7, RRF K=60, top 7)
* This is a NEW RRF implementation, not reusing `search_hybrid.py` per spec requirement to keep summarization isolated
* Dense search requires chunks to have embeddings (vector_status='vec')
* Lexical search requires chunks to have content_vector populated
* Settings provide: dense_top_k, lexical_top_k, rrf_k, rrf_top_k
