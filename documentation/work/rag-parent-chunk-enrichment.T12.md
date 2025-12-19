# Ticket: rag-parent-chunk-enrichment.T12 - Manual Testing and Validation

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Execute comprehensive manual test plan from spec
- Validate all acceptance criteria met
- Confirm improved context quality for Simple Conversion documents
- Verify end-to-end RAG pipeline functionality
- Document test results and any issues found

## Scope
### In scope
- Execute all manual test steps from spec section "Manual Test Plan"
- Test migration on copy of production data
- Test fresh database initialization
- Test retrieval with various document types and chunk sizes
- Test consolidation with various coverage thresholds
- Test UI changes (coverage_threshold control)
- Verify acceptance criteria from spec
- Document results and create issue tickets for any bugs found

### Out of scope
- Automated integration tests (per spec non-goals)
- Performance load testing
- User acceptance testing (UAT)
- Production deployment

## Dependencies
- Depends on: T01-T11 (all previous tickets)
- Unblocks: Production deployment (out of scope)

## Implementation plan
1. Set up test environment:
   - Create copy of production database (or use staging database)
   - Ensure test documents of various types available (Simple Conversion, full conversion)
   - Ensure test chunks with various characteristics (short, long, deep hierarchies)
2. Execute migration testing:
   - Apply migration to test database
   - Verify all presets have `max_word_count: 750`
   - Verify deprecated keys moved to `_deprecated`
   - Run migration again to verify idempotency
   - Check for any errors or warnings
3. Execute fresh install testing:
   - Create fresh database
   - Run `init_db.py`
   - Verify default preset has clean schema (no deprecated keys)
   - Verify `max_word_count` and `coverage_threshold` present
4. Execute retrieval testing:
   - Test with Simple Conversion document
   - Test with short chunks (< min_word_count)
   - Test with very long parent chunks (> max_word_count)
   - Verify enrichment occurs correctly
   - Verify truncation preserves headings and sentences
   - Verify no file I/O errors
5. Execute consolidation testing:
   - Test with adjacent chunks
   - Test with various coverage_threshold values (0.3, 0.5, 0.7)
   - Verify parent replacement triggered appropriately
   - Verify heading chains preserved
6. Execute UI testing:
   - Open RAG Settings UI
   - Verify coverage_threshold slider visible
   - Change value and save
   - Reload page and verify persistence
   - Test edge values (0.0, 1.0)
7. Execute end-to-end testing:
   - Run complete RAG query with Simple Conversion document
   - Verify context quality maintained or improved
   - Check logs for enrichment metrics
   - Verify no errors or warnings (except expected deprecated key warnings)
8. Document results:
   - Create test report with pass/fail for each test case
   - Screenshot UI changes
   - Capture sample log output
   - Note any issues or unexpected behavior
   - Create issue tickets for bugs if found
9. Verify all acceptance criteria from spec checked off

Patterns to apply:
- Testing Strategy - Manual testing follows spec requirements
- Documentation - Clear test reporting

Deviations (if any):
- None

## Unit tests (required)
- Not applicable (manual testing ticket)

## Acceptance criteria (checklist)
- [ ] Test environment set up successfully
- [ ] Migration tested on copy of production data
- [ ] All presets have `max_word_count` after migration
- [ ] Migration is idempotent (no errors on second run)
- [ ] Fresh install creates clean config schema
- [ ] init_db.py default preset has no deprecated keys
- [ ] Retrieval works with Simple Conversion documents
- [ ] Short chunks enriched with parent content
- [ ] Long parent chunks truncated appropriately
- [ ] Truncation preserves headings and sentences
- [ ] No file I/O errors for database-only documents
- [ ] Adjacency merging uses parent chunk content
- [ ] Parent replacement triggered when coverage exceeds threshold
- [ ] coverage_threshold UI control visible and functional
- [ ] UI correctly saves and loads coverage_threshold value
- [ ] End-to-end RAG query produces quality results
- [ ] Context quality improved for Simple Conversion documents
- [ ] Logs show enrichment metrics
- [ ] No unexpected errors or warnings
- [ ] All spec acceptance criteria verified
- [ ] Test report documented

## Manual verification
This entire ticket is manual verification. Key steps:

1. Migration Testing:
   - [ ] Backup test database
   - [ ] Apply migration `migrations/021_add_max_word_count_to_rag_config.sql`
   - [ ] Query: `SELECT config->'retrieval'->'max_word_count' FROM rag_config;`
   - [ ] Verify all rows return `750`
   - [ ] Query: `SELECT config->'retrieval'->'_deprecated' FROM rag_config;`
   - [ ] Verify deprecated keys present
   - [ ] Run migration again, verify no errors

2. Fresh Install Testing:
   - [ ] Create new database
   - [ ] Run: `python src/vulcanlab/data/init_db.py` (or equivalent)
   - [ ] Query: `SELECT config FROM rag_config WHERE name = 'default';`
   - [ ] Verify `max_word_count: 750` in retrieval
   - [ ] Verify `coverage_threshold: 0.5` in consolidation
   - [ ] Verify no `_deprecated` keys

3. Retrieval Testing:
   - [ ] Find Simple Conversion document in database
   - [ ] Run retrieval query that returns short chunks
   - [ ] Check logs: verify enrichment summary appears
   - [ ] Inspect returned chunks: verify parent content included
   - [ ] Find chunk with long parent (>750 words)
   - [ ] Verify truncation applied
   - [ ] Verify headings preserved in truncated content
   - [ ] Verify sentences not broken mid-sentence

4. Consolidation Testing:
   - [ ] Set `coverage_threshold: 0.3` in config
   - [ ] Run retrieval with adjacent chunks
   - [ ] Verify parent replacement occurs (check logs)
   - [ ] Set `coverage_threshold: 0.9` in config
   - [ ] Run same query
   - [ ] Verify parent replacement does not occur
   - [ ] Verify heading chains present in output

5. UI Testing:
   - [ ] Start frontend: `cd vulcanlab_ui && npm run dev`
   - [ ] Navigate to RAG Settings
   - [ ] Locate "Parent Coverage Threshold" control
   - [ ] Verify default value is 0.5
   - [ ] Change to 0.7, save
   - [ ] Check network tab: verify API call
   - [ ] Reload page
   - [ ] Verify value is 0.7 (persisted)
   - [ ] Test edge values (0.0, 1.0)

6. End-to-End Testing:
   - [ ] Run complete RAG query: "What is [topic from Simple Conversion doc]?"
   - [ ] Inspect returned context
   - [ ] Verify context is coherent and relevant
   - [ ] Compare to old approach (if baseline available)
   - [ ] Verify quality maintained or improved
   - [ ] Check logs for enrichment metrics
   - [ ] Verify no errors in logs

- Expected results:
  - All checklist items pass
  - Context quality visibly improved for Simple Conversion documents
  - No regressions for other document types
  - UI functional and intuitive
  - Logs provide useful operational insights

## Notes
- This ticket is the final validation before considering the feature complete
- Use the manual test plan from spec as primary checklist (section "Manual Test Plan")
- Create a test report document with:
  - Date and tester name
  - Test environment details
  - Pass/fail for each test case
  - Screenshots of UI
  - Sample log output
  - Any issues or unexpected behavior
- If bugs found during testing:
  - Create issue tickets with clear repro steps
  - Prioritize: critical (breaks functionality), major (degrades quality), minor (cosmetic)
  - Fix critical bugs before marking feature complete
- Test with realistic data:
  - Simple Conversion documents (database-only content)
  - Regular documents (with local markdown files)
  - Various chunk sizes and hierarchies
  - Various query types
- Performance spot check:
  - Note retrieval latency before and after
  - Verify <10% increase (informal check, detailed benchmarking in T11)
- Coverage threshold testing values:
  - 0.0 (always replace)
  - 0.3 (low threshold)
  - 0.5 (default)
  - 0.7 (high threshold)
  - 1.0 (never replace unless 100% coverage)
- Document any workarounds or known limitations
- Spec acceptance criteria (section "Acceptance Criteria (Checklist)") should all be verified
