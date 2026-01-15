# Ticket: work-summarization.T04 - Salience Scoring Module

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement salience scoring module to evaluate heading-level chunks for summarization priority
* Support configurable weights for each scoring factor
* Enable filtering of chunks based on salience thresholds from settings

## Phase

* Core Modules

## Scope

### In scope

* src/vulcanlab/summarize/salience.py module
* Heading depth scoring (H1 > H2 > H3 > H4 > H5)
* Definition density detection using regex patterns
* List density calculation (bullets, numbered items)
* Keyphrase novelty scoring (new terms vs. previously seen)
* Location prior scoring (intro/conclusion boost)
* Composite score calculation with configurable weights
* Functions to load weights from SummarizeSettings

### Out of scope

* Evidence packet extraction (T05)
* Node selection logic integrating with chunks table (T06)
* LLM integration

## Dependencies

* Depends on: T01 (NLP utils), T03 (SummarizeSettings model)
* Unblocks: T06

## Implementation plan

1. Create src/vulcanlab/summarize/salience.py
2. Define SalienceWeights dataclass with all weight fields matching SummarizeSettings
3. Implement `load_salience_weights(session: Session) -> SalienceWeights` to fetch from DB
4. Implement `score_heading_depth(level: str) -> float`:
   - H1 -> 1.0, H2 -> 0.8, H3 -> 0.6, H4 -> 0.4, H5 -> 0.2
5. Implement `score_definition_density(content: str) -> float`:
   - Count matches for patterns: "X is...", "defined as...", "refers to...", "we call..."
   - Normalize by content length
6. Implement `score_list_density(content: str) -> float`:
   - Count bullet points (-, *, +) and numbered items (1., 2., (1), (a))
   - Normalize by content length
7. Implement `score_keyphrase_novelty(content: str, seen_keyphrases: set[str]) -> float`:
   - Extract noun phrases or capitalized terms
   - Score based on ratio of new vs. seen
8. Implement `score_location_prior(chunk_index: int, total_chunks: int) -> float`:
   - Boost first 10% and last 10% of document
9. Implement `compute_salience_score(chunk, weights: SalienceWeights, seen_keyphrases: set[str], chunk_index: int, total_chunks: int) -> float`:
   - Weighted combination of all factors
10. Implement `passes_threshold(score: float, level: str, weights: SalienceWeights) -> bool`:
    - Apply level-specific thresholds from settings
* Patterns to apply:
  * Core Module independence - no FastAPI imports
  * Session passed explicitly to functions
  * Pure functions where possible for testability
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `score_heading_depth` returns expected values for each level
  * `score_definition_density` detects various definition patterns
  * `score_definition_density` handles content with no definitions
  * `score_list_density` counts bullets and numbers correctly
  * `score_keyphrase_novelty` correctly identifies novel vs. seen terms
  * `score_location_prior` boosts intro and conclusion positions
  * `compute_salience_score` combines factors with correct weights
  * `passes_threshold` applies correct threshold per heading level
  * Edge cases: empty content, very short content, all-list content
* Suggested locations:
  * tests/unit/summarize/test_salience.py
* Mocking/fakes needed:
  * Mock session for load_salience_weights tests
  * Mock SummarizeSettings row

## Acceptance criteria (checklist)

* [ ] All scoring functions implemented and return values in 0-1 range
* [ ] Definition patterns detect common academic/technical definition styles
* [ ] List density correctly identifies markdown bullet and numbered formats
* [ ] Keyphrase novelty tracks seen terms across document
* [ ] Location prior boosts intro/conclusion sections
* [ ] Composite score uses weights from settings
* [ ] Threshold checking respects level-specific thresholds
* [ ] All unit tests pass
* [ ] No framework-specific imports

## Manual verification

* Steps:
  1. Create test content with definitions, lists, and varied heading levels
  2. Run scoring functions manually in Python REPL
  3. Verify scores are sensible (definition-heavy sections score higher on definition_density)
* Expected results:
  * Scores reflect content characteristics
  * Weighted composite produces reasonable ranking

## Notes

* Requirements covered: R1, R3, R4
* Definition patterns should be case-insensitive
* Keyphrase novelty requires tracking state across chunks - consider passing seen_keyphrases set
* Location prior assumes chunks are processed in document order
* Regex patterns for definitions: r"(\w+)\s+(is|are|refers?\s+to|means?|defined\s+as)"
* List patterns: r"^[\s]*[-*+]\s", r"^[\s]*\d+[.)]\s", r"^[\s]*\([a-z0-9]+\)\s"
