# Ticket: work-summarization.T05 - Evidence Packet Extraction Module

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement evidence packet extraction to build high-information-density inputs for LLM summarization
* Extract topic sentences, definitions, enumerations, emphasis cues, and keyphrases with line mappings
* Produce structured EvidencePacket objects ready for LLM consumption

## Phase

* Core Modules

## Scope

### In scope

* src/vulcanlab/summarize/evidence.py module
* EvidencePacket dataclass with all extracted components
* Topic sentence extraction (first sentence per paragraph)
* Definition-like sentence detection with regex patterns
* Enumeration/list extraction (preserve full list structure)
* Emphasis cue detection ("key", "important", "note that", "crucially")
* Keyphrase/entity extraction using spaCy noun chunks
* Line number mapping for all extracted snippets
* Configurable max snippets per packet (target 10-40)

### Out of scope

* LLM calls (T07)
* Salience scoring (T04)
* Node selection (T06)

## Dependencies

* Depends on: T01 (NLP utils for sentence segmentation)
* Unblocks: T07, T08

## Implementation plan

1. Create src/vulcanlab/summarize/evidence.py
2. Define dataclasses:
   - `Snippet(text: str, start_line: int, end_line: int, snippet_type: str)`
   - `EvidencePacket(heading_path: str, line_start: int, line_end: int, snippets: list[Snippet], keyphrases: list[str], stats: dict)`
3. Implement `extract_topic_sentences(text: str, sentences_with_lines: list) -> list[Snippet]`:
   - Identify paragraph boundaries
   - Return first sentence of each paragraph with line numbers
4. Implement `extract_definitions(text: str, sentences_with_lines: list) -> list[Snippet]`:
   - Regex patterns: "X is...", "X refers to...", "defined as...", "we call...", "known as..."
   - Return matching sentences with line numbers
   - Tag snippet_type as "definition"
5. Implement `extract_enumerations(text: str) -> list[Snippet]`:
   - Detect bullet lists (-, *, +) and numbered lists
   - Preserve complete list blocks with line ranges
   - Tag snippet_type as "enumeration"
6. Implement `extract_emphasis_cues(text: str, sentences_with_lines: list) -> list[Snippet]`:
   - Patterns: "key", "important", "in summary", "note that", "crucially", "essential"
   - Return sentences containing emphasis markers
   - Tag snippet_type as "emphasis"
7. Implement `extract_keyphrases(text: str) -> list[str]`:
   - Use spaCy noun chunks
   - Filter by frequency and capitalization
   - Return top-N keyphrases
8. Implement `build_evidence_packet(content: str, heading_path: str, start_line: int, end_line: int, max_snippets: int = 40) -> EvidencePacket`:
   - Call all extraction functions
   - Deduplicate overlapping snippets
   - Prioritize: definitions > enumerations > topic sentences > emphasis
   - Trim to max_snippets
   - Include stats (token_count, snippet_count by type)
* Patterns to apply:
  * Core Module independence
  * Pure functions for extraction logic
  * Dataclasses for structured returns
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `extract_topic_sentences` returns first sentence of each paragraph
  * `extract_topic_sentences` handles single-paragraph text
  * `extract_definitions` detects all specified patterns
  * `extract_definitions` returns correct line numbers
  * `extract_enumerations` captures complete bullet lists
  * `extract_enumerations` captures numbered lists
  * `extract_emphasis_cues` finds sentences with emphasis words
  * `extract_keyphrases` returns noun phrases
  * `build_evidence_packet` respects max_snippets limit
  * `build_evidence_packet` prioritizes correctly when over limit
  * Deduplication removes overlapping snippets
  * Edge cases: empty text, text with no special patterns, very short text
* Suggested locations:
  * tests/unit/summarize/test_evidence.py
* Mocking/fakes needed:
  * May mock spaCy for keyphrase tests (or use real small model)

## Acceptance criteria (checklist)

* [ ] All extraction functions implemented with line mapping
* [ ] EvidencePacket contains all required fields
* [ ] Topic sentences correctly identified from paragraph starts
* [ ] Definition patterns match common technical writing styles
* [ ] Enumerations preserve complete list structure
* [ ] Emphasis cues detected with configurable keywords
* [ ] Keyphrases extracted via spaCy noun chunks
* [ ] Snippets deduplicated when overlapping
* [ ] max_snippets limit enforced with correct prioritization
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Load a sample markdown document
  2. Run `build_evidence_packet` on a section
  3. Inspect returned snippets and their line numbers
  4. Verify line numbers match actual source
* Expected results:
  * Evidence packet contains representative snippets
  * Line numbers accurately point to source text

## Notes

* Requirements covered: R5, R6
* Definition regex should be case-insensitive
* Emphasis words list can be extended based on domain
* Enumeration detection should handle nested lists (flatten to top-level)
* Prioritization order based on strategy doc: definitions are highest ROI, then enumerations
* Stats dict useful for debugging and potential salience adjustments
