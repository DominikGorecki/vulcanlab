# Ticket: collection-deep-research.T05 - Result Matching and Reuse Logic

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement result matching logic to identify existing research_result items that match sub-questions
* Calculate embedding similarity, quality scores, and recommend reuse strategy (exact, partial, ensemble, new)
* Enable cost savings by reusing high-quality existing research results

## Phase

* Core Modules

## Scope

### In scope

* Module src/vulcanlab/research/result_matcher.py
* Function match_results_for_question(question_text, collection_id, session) - finds matching results
* Function calculate_similarity(question_embedding, result_embedding) - cosine similarity
* Function calculate_quality_score(result) - composite quality metric
* Function recommend_reuse_strategy(matched_results) - decision logic
* Quality scoring algorithm: citation_density (40%), freshness (20%), completeness (15%), source_diversity (15%), model_quality (10%)
* Reuse strategy decision tree per spec

### Out of scope

* Embedding generation (use existing VulcanLab embedding infrastructure)
* Actual reuse execution (covered in T06 context assembly)
* API endpoint (covered in T14)
* Manual wizard UI (covered in T21)

## Dependencies

* Depends on: T02 (models), T03 (CRUD)
* Unblocks: T14 (match-results endpoint), T17 (QueryExecutorNode), T21 (Manual wizard Step 2)

## Implementation plan

* Create src/vulcanlab/research/result_matcher.py
* Implement match_results_for_question:
  * Generate embedding for question_text using existing embedding infrastructure
  * Query all research_result items in collection
  * For each result, get original query text and generate embedding
  * Calculate cosine similarity between question_embedding and result_embedding
  * Filter results with similarity > 0.85 (per R7)
  * Calculate quality score for each matched result
  * Sort by quality_score DESC
  * Return list of dicts: [{result_id, similarity, quality_score, result_preview, created_at}]
* Implement calculate_similarity:
  * Accept two embedding vectors (numpy arrays or lists)
  * Compute cosine similarity: dot(a, b) / (norm(a) * norm(b))
  * Return float between -1 and 1
* Implement calculate_quality_score:
  * Parse result content to count citations (basic heuristic: count [Author Year] patterns)
  * citation_density = citation_count / word_count (weight 40%)
  * freshness = 1.0 - (days_old / 180) capped at 0 (weight 20%)
  * completeness = word_count / median_word_count (weight 15%)
  * source_diversity = unique_works_cited (weight 15%)
  * model_quality = 1.0 if high-quality model else 0.5 (weight 10%)
  * Return weighted sum (0.0 to 1.0)
* Implement recommend_reuse_strategy:
  * Count high-quality results (quality_score > 0.75)
  * If 0 high-quality → return "new_generation"
  * If 1 high-quality and similarity > 0.90 → return "exact_reuse"
  * If 1 high-quality and similarity 0.85-0.90 → return "partial_reuse"
  * If 2-3 high-quality → return "ensemble"
  * If 4+ high-quality → apply diversity sampling, return "ensemble"
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Pass session explicitly for database queries
  * **Configuration** - Use vulcanlab.config for embedding model settings
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * match_results_for_question returns results with similarity > 0.85
  * match_results_for_question filters out low-similarity results
  * match_results_for_question returns results sorted by quality_score DESC
  * calculate_similarity computes correct cosine similarity for test vectors
  * calculate_quality_score produces score in range 0.0-1.0
  * calculate_quality_score weights components correctly (citation_density 40%, etc.)
  * recommend_reuse_strategy returns "exact_reuse" for 1 high-quality result with similarity > 0.90
  * recommend_reuse_strategy returns "ensemble" for 2-3 high-quality results
  * recommend_reuse_strategy returns "new_generation" for 0 high-quality results
* Suggested locations:
  * tests/unit/research/test_result_matcher.py
* Mocking/fakes needed:
  * Mock database session and research_result queries
  * Mock embedding generation function to return test vectors
  * Mock result content with known citation patterns

## Acceptance criteria (checklist)

* [ ] match_results_for_question filters by similarity > 0.85 threshold (R7)
* [ ] calculate_similarity computes cosine similarity correctly
* [ ] calculate_quality_score uses weighted formula from spec (40%/20%/15%/15%/10%)
* [ ] recommend_reuse_strategy implements decision tree from spec
* [ ] All functions accept session parameter explicitly
* [ ] Module has no FastAPI imports
* [ ] Unit tests pass for matching, quality scoring, strategy recommendation

## Manual verification

* Steps:
  * Create collection with 5 research_result items
  * Generate embeddings for results (use existing infrastructure)
  * Create test question with known similarity to one result (cosine sim 0.92)
  * Call match_results_for_question, verify high-similarity result returned
  * Verify quality_score calculated correctly (check citation_density component)
  * Call recommend_reuse_strategy with 1 high-quality result, verify returns "exact_reuse"
  * Call recommend_reuse_strategy with 3 high-quality results, verify returns "ensemble"
* Expected results:
  * Matching results filtered by 0.85 threshold
  * Quality scores in 0.0-1.0 range
  * Reuse strategy recommendations match decision tree

## Notes

* Requirements covered: R7 (match results with similarity > 0.85), R8 (prompt user to approve reuse in manual mode)
* Similarity threshold 0.85 is configurable - could be adjusted based on empirical testing (per spec Open Question Q7)
* Quality scoring weights from spec Implementation Notes section
* Diversity sampling for 4+ results (mentioned in spec) can be simple: select top 3 by diversity metric (embedding distance)
* Citation parsing heuristic (regex for [Author Year]) is basic - can be improved with actual citation extraction if available
