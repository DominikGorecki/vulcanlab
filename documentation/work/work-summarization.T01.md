# Ticket: work-summarization.T01 - Add spaCy Dependency and NLP Utilities

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add spaCy as a project dependency with the small English model
* Create foundational NLP utility module for sentence segmentation with line mapping
* Verify spaCy integration works correctly in the project environment

## Phase

* Foundations

## Scope

### In scope

* Add spaCy and en_core_web_sm to pyproject.toml dependencies
* Create src/vulcanlab/summarize/__init__.py package structure
* Create src/vulcanlab/summarize/nlp_utils.py with sentence segmentation utilities
* Sentence-to-line-number mapping functionality
* Paragraph boundary detection with line ranges

### Out of scope

* Evidence packet extraction (T05)
* Keyphrase extraction (T04)
* Any LLM integration

## Dependencies

* Depends on: none
* Unblocks: T04, T05, T08

## Implementation plan

1. Add spaCy>=3.7 to pyproject.toml under dependencies
2. Add en_core_web_sm model download instruction to project setup (or as post-install hook)
3. Create src/vulcanlab/summarize/ directory with __init__.py
4. Create src/vulcanlab/summarize/nlp_utils.py with:
   - `load_spacy_model()` function with lazy loading and caching
   - `segment_sentences(text: str) -> list[SentenceSpan]` returning sentence text with char offsets
   - `map_char_offset_to_line(text: str, char_offset: int) -> int` utility
   - `segment_sentences_with_lines(text: str) -> list[SentenceWithLines]` combining both
   - `detect_paragraph_boundaries(text: str) -> list[ParagraphSpan]` for paragraph-level grouping
5. Define dataclasses: SentenceSpan, SentenceWithLines, ParagraphSpan in nlp_utils.py
6. Add error handling for missing spaCy model with helpful error message
* Patterns to apply:
  * Core Module independence - no FastAPI/HTTP imports in this module
  * Snake_case naming for functions and variables
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `segment_sentences` correctly splits multi-sentence text
  * `segment_sentences` handles edge cases: empty string, single sentence, no punctuation
  * `map_char_offset_to_line` returns correct line numbers for various offsets
  * `segment_sentences_with_lines` produces correct line ranges for sentences spanning multiple lines
  * `detect_paragraph_boundaries` identifies paragraph breaks correctly
  * Error handling when spaCy model is not installed
* Suggested locations:
  * tests/unit/summarize/test_nlp_utils.py
* Mocking/fakes needed:
  * Mock spaCy model loading for faster tests (optional - small model is fast)

## Acceptance criteria (checklist)

* [ ] spaCy added to pyproject.toml and installs correctly
* [ ] en_core_web_sm model can be loaded without errors
* [ ] segment_sentences returns accurate sentence boundaries
* [ ] Line number mapping is accurate for multi-line text
* [ ] All unit tests pass
* [ ] Module has no framework-specific imports (FastAPI, HTTP, etc.)

## Manual verification

* Steps:
  1. Run `pip install -e .` to install updated dependencies
  2. Run `python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print(nlp('Hello world. This is a test.')[:])"`
  3. Run `python -c "from vulcanlab.summarize.nlp_utils import segment_sentences_with_lines; print(segment_sentences_with_lines('Line one sentence.\\nLine two sentence.'))"`
* Expected results:
  * spaCy loads without errors
  * Sentences are correctly segmented with accurate line numbers

## Notes

* Requirements covered: R5, R6 (partial - sentence segmentation foundation)
* The en_core_web_sm model is ~12MB, acceptable for this use case
* Lazy loading of spaCy model avoids startup overhead when summarization is not used
* Line mapping assumes 1-indexed line numbers to match existing chunk.start_line/end_line convention
