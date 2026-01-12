# Ticket: collection-deep-research.T07 - Section Synthesis and Quality Evaluation

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement section synthesis logic to generate research section content from assembled context
* Provide quality evaluation functions to assess citation coverage, coherence, and completeness
* Extract metadata (word count, citation count, source diversity) from generated sections

## Phase

* Core Modules

## Scope

### In scope

* Module src/vulcanlab/research/synthesizer.py
* Function generate_section(question_text, context, sources, llm_client) - calls LLM to synthesize section
* Function extract_metadata(section_content, sources) - calculates word count, citation count, source diversity
* Function evaluate_quality(section_content, sources, metadata) - calculates quality metrics
* Function check_citation_coverage(section_content, sources) - validates citations against sources
* Prompt templates for section generation and quality evaluation

### Out of scope

* Context assembly (covered in T06)
* Result matching (covered in T05)
* LangGraph node implementation (covered in T18)
* Manual wizard UI (covered in T22)

## Dependencies

* Depends on: T04 (planning), T06 (context assembly)
* Unblocks: T18 (SynthesizerNode and QualityEvaluatorNode), T22 (Manual wizard Step 4-5)

## Implementation plan

* Create src/vulcanlab/research/synthesizer.py
* Implement generate_section:
  * Accept question_text, context (from T06), sources list, llm_client
  * Load section generation prompt template (or inline)
  * Format prompt with question, context, sources
  * Specify output format: markdown with inline citations [Author Year, pp. X-Y]
  * Call LLM, parse response
  * Return section_content (markdown string)
* Implement extract_metadata:
  * Count words in section_content (split by whitespace)
  * Count citations using regex: r'\[([^\]]+)\]' or similar pattern
  * Count unique source works cited (parse citations, extract work IDs or titles)
  * Return dict: {word_count: int, citation_count: int, source_diversity: int}
* Implement evaluate_quality:
  * Calculate citation_coverage: citation_count / total_claims (heuristic: sentences ending with period)
  * Assess source_diversity: number of unique works cited
  * Calculate coherence_score: simple heuristic (length > 800 words, citation_coverage > 0.5)
  * Return dict: {citation_coverage: float, source_diversity: int, coherence_score: str (high/medium/low), completeness_score: str}
* Implement check_citation_coverage:
  * Parse all citations from section_content
  * For each citation, verify referenced work exists in sources list
  * Return list of broken citations (citations not in sources)
* Create prompt template for section generation:
  * Include question, context, sources
  * Specify requirements: synthesize insights, maintain citations, identify consensus vs divergent views
  * Output format: markdown with inline citations
* Create prompt template for quality evaluation (optional, for Step 6 manual wizard):
  * Evaluate citation accuracy, source diversity, coherence, completeness
  * Output format: JSON with metrics
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Configuration** - Use vulcanlab.config for LLM settings per patterns.md section 3.3
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * generate_section calls LLM with formatted prompt
  * generate_section returns markdown string
  * extract_metadata calculates word_count correctly
  * extract_metadata counts citations correctly using regex
  * extract_metadata calculates source_diversity (unique works cited)
  * evaluate_quality calculates citation_coverage ratio
  * evaluate_quality assigns coherence_score based on heuristics
  * check_citation_coverage identifies broken citations (not in sources)
  * check_citation_coverage returns empty list when all citations valid
* Suggested locations:
  * tests/unit/research/test_synthesizer.py
* Mocking/fakes needed:
  * Mock LLM client to return synthetic section content with citations
  * Sample section_content with known word count and citation count

## Acceptance criteria (checklist)

* [x] generate_section calls LLM and returns markdown section
* [x] extract_metadata calculates word_count, citation_count, source_diversity
* [x] evaluate_quality calculates citation_coverage and coherence_score
* [x] check_citation_coverage validates citations against sources
* [x] Section generation prompt template created (inline or seed_data)
* [x] Quality evaluation prompt template created (optional, for manual Step 6)
* [x] All functions work with existing VulcanLab LLM infrastructure
* [x] Unit tests pass for synthesis and quality evaluation logic

## Manual verification

* Steps:
  * Create test question and context (from T06)
  * Mock LLM to return sample section with 5 citations
  * Call generate_section, verify markdown returned
  * Call extract_metadata on returned section, verify word_count > 0, citation_count == 5
  * Call evaluate_quality, verify citation_coverage calculated correctly
  * Call check_citation_coverage with valid sources, verify returns empty list
  * Call check_citation_coverage with missing source, verify returns broken citation
* Expected results:
  * Section generated with correct format
  * Metadata extracted accurately
  * Quality metrics calculated correctly
  * Broken citations detected

## Notes

* Requirements covered: R13 (findings per sub-question, synthesis), quality evaluation for R14
* Citation format [Author Year, pp. X-Y] per spec "Implementation Notes"
* Citation coverage heuristic: citation_count / sentence_count (simple approximation for total_claims)
* Coherence scoring is heuristic for MVP - can be enhanced with semantic analysis later
* Quality evaluation prompt (Step 6 optional) can reuse same evaluate_quality logic with LLM assistance
