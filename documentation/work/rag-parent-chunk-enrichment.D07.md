# Ticket: rag-parent-chunk-enrichment.T07 - End-to-End Integration and Backwards Compatibility

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Integrate all components (retrieval enrichment, consolidation, config updates, UI)
- Ensure backwards compatibility with presets containing deprecated keys
- Validate full RAG pipeline works with new parent-chunk approach
- Remove any remaining file I/O dependencies

## Scope
### In scope
- Integration of enrichment (T02) and consolidation (T03) into full RAG pipeline
- Backwards compatibility handling for deprecated config keys
- Config validation and warning system for deprecated keys
- Remove local markdown file reads from retrieval and consolidation
- End-to-end flow testing (unit tests, not integration tests)
- Error handling and fallback mechanisms

### Out of scope
- Integration tests with live database (per spec non-goals)
- Performance optimization (T11)
- Observability enhancements (T09)
- Documentation updates (T08)

## Dependencies
- Depends on: T02 (Parent Traversal), T03 (Consolidation), T04 (Migration), T05 (init_db), T06 (UI)
- Unblocks: T08 (Documentation), T09 (Observability), T10 (Edge Cases)

## Implementation plan
1. Read current RAG pipeline orchestration code (likely in `src/vulcanlab/retrieval/retrieve.py` and `src/vulcanlab/augmentation/`)
2. Integrate enrichment into retrieval flow:
   - After RRF fusion, before reranking
   - Check config for `min_word_count` and `max_word_count`
   - For backwards compatibility, fall back to defaults if missing
3. Integrate consolidation refactor:
   - Ensure consolidation uses parent chunks instead of files
   - Check config for `coverage_threshold`
   - Fall back to 0.5 if missing
4. Implement config key compatibility layer:
   - Create helper function `get_config_value(config, path, fallback)`
   - Check both top-level and `_deprecated` locations
   - Log warning if deprecated key is used
5. Remove all file I/O from retrieval and consolidation:
   - Search codebase for markdown file reads in these modules
   - Replace with parent chunk queries or remove
6. Add error handling:
   - If parent chunk missing, fall back to original chunk
   - If enrichment fails, continue with un-enriched chunk
   - Log errors but don't fail entire pipeline
7. Write comprehensive unit tests for integration scenarios

Patterns to apply:
- Core Module Independence - No FastAPI imports
- Session Management - Explicit session passing throughout pipeline
- Error Handling - Graceful degradation, not hard failures

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Full RAG pipeline with new enrichment and consolidation
  - Backwards compatibility with presets containing deprecated keys
  - Config value lookup from both current and `_deprecated` locations
  - Warning logged when deprecated keys used
  - Enrichment disabled when `min_word_count` not in config
  - Default values applied when new keys missing
  - Fallback to original chunk when parent missing
  - Pipeline continues when enrichment fails
  - No file I/O operations in retrieval or consolidation
  - Short chunks enriched with parent content
  - Adjacent chunks merged using parent content
  - Parent replacement triggered when coverage exceeds threshold

- Suggested locations:
  - `tests/unit/test_rag_pipeline_integration.py`
  - `tests/unit/test_config_compatibility.py`

- Mocking/fakes needed:
  - Mock SQLAlchemy Session
  - Mock Chunk model instances with parent relationships
  - Mock config dictionaries with various key combinations
  - Mock file system operations to verify no reads occur

## Acceptance criteria (checklist)
- [ ] Enrichment integrated into retrieval pipeline
- [ ] Consolidation integrated into augmentation pipeline
- [ ] Backwards compatibility with deprecated config keys implemented
- [ ] Config helper function handles both current and deprecated locations
- [ ] Warnings logged when deprecated keys used
- [ ] Default values applied when new keys missing
- [ ] All file I/O removed from retrieval and consolidation
- [ ] Error handling prevents pipeline failures
- [ ] Fallback mechanisms work correctly
- [ ] Full pipeline tested with new approach
- [ ] All unit tests pass
- [ ] Code follows snake_case naming convention

## Manual verification
- Steps:
  1. Run all unit tests: `python -m pytest tests/unit/ -v`
  2. Test with old config preset (containing deprecated keys)
  3. Verify warnings logged for deprecated keys
  4. Test with new config preset (clean schema)
  5. Verify no warnings logged
  6. Test retrieval with short chunks
  7. Verify parent content included in results
  8. Test consolidation with adjacent chunks
  9. Verify parent content used for merging
  10. Test with Simple Conversion document (no local files)
  11. Verify no file I/O errors

- Expected results:
  - All unit tests pass
  - Pipeline works with both old and new configs
  - Deprecated key warnings appear in logs
  - Enrichment improves context quality
  - Consolidation uses parent chunks
  - No file I/O dependency errors

## Notes
- Config compatibility layer example:
  ```python
  def get_config_value(config: dict, section: str, key: str, fallback: Any) -> Any:
      """Get config value from current or deprecated location."""
      section_config = config.get(section, {})

      # Check current location
      if key in section_config:
          return section_config[key]

      # Check deprecated location
      deprecated = section_config.get('_deprecated', {})
      if key in deprecated:
          logger.warning(f"Using deprecated config key: {section}.{key}")
          return deprecated[key]

      return fallback
  ```
- Search for file reads in retrieval/consolidation:
  - `grep -r "open(" src/vulcanlab/retrieval/ src/vulcanlab/augmentation/`
  - `grep -r "read_text" src/vulcanlab/retrieval/ src/vulcanlab/augmentation/`
  - `grep -r "Path(" src/vulcanlab/retrieval/ src/vulcanlab/augmentation/`
- Ensure all file I/O is removed or replaced with parent chunk queries
- Test with mix of document types: full conversion, simple conversion, various chunk sizes
- Verify no regressions in existing RAG quality
- This ticket completes the core refactor and enables manual end-to-end testing
