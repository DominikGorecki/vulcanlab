# Ticket: work-summarization.T20 - End-to-End Manual Testing and Documentation

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Execute manual testing checklist from spec
* Document the summarization feature for users
* Verify all acceptance criteria are met
* Version bump and changelog update

## Phase

* Rollout

## Scope

### In scope

* Execute all manual test cases from spec
* Create user documentation for summarization feature
* Update CHANGELOG.md with feature description
* Version bump in relevant files
* Fix any issues discovered during testing

### Out of scope

* Automated integration tests
* Performance benchmarking
* User acceptance testing with external users

## Dependencies

* Depends on: T01-T19 (all previous tickets)
* Unblocks: none (final ticket)

## Implementation plan

1. Execute manual test checklist:
   - [ ] Trigger summarization on a work with mixed heading levels
   - [ ] Verify summary_nodes created with correct line references
   - [ ] Verify salience filtering respects configured thresholds
   - [ ] Generate each derived output type and verify content
   - [ ] Click line references and verify navigation to correct source location
   - [ ] Modify salience settings and verify they apply to new summarization
   - [ ] Test summarization on a work with sparse headings
   - [ ] Test summarization on a large work (>50K tokens)
   - [ ] Test error recovery: stop summarization mid-way, restart
   - [ ] Test escalation loop: work with sections that trigger insufficient evidence
2. Document issues found and create fix tasks if needed
3. Create user documentation:
   - Overview of summarization feature
   - How to trigger summarization from Corpus
   - Understanding summary nodes and their content
   - Generating derived outputs (abstract, outline, etc.)
   - Configuring salience settings
   - Troubleshooting common issues
4. Update CHANGELOG.md:
   - Add entry under appropriate version
   - Describe new Summarize feature
   - List key capabilities
5. Version bump:
   - Update version in vulcanlab_ui/src/components/nav-bar.tsx (or wherever version is displayed)
   - Update version in pyproject.toml if applicable
6. Final review:
   - Verify all acceptance criteria from spec
   - Confirm no regressions in existing functionality
* Patterns to apply:
  * Follow existing documentation format
  * Follow existing changelog format
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * This ticket is primarily manual testing; no new unit tests
  * Verify existing unit tests all pass
  * Document test coverage for summarization modules
* Suggested locations:
  * N/A - manual testing ticket
* Mocking/fakes needed:
  * N/A

## Acceptance criteria (checklist)

* [ ] All manual test cases executed and passing
* [ ] User documentation created
* [ ] CHANGELOG.md updated
* [ ] Version bumped appropriately
* [ ] All spec acceptance criteria verified:
  * [ ] User can trigger summarization from Corpus work detail page
  * [ ] summary_nodes table populated with gist, key_points, definitions, key_terms, examples
  * [ ] Each summary field includes start_line and end_line references
  * [ ] Salience scoring selects appropriate nodes based on configured thresholds
  * [ ] Evidence packets extracted using spaCy and regex before LLM calls
  * [ ] Escalation loop triggers when LLM reports insufficient evidence
  * [ ] User can view summarized works on dedicated Summarize page
  * [ ] User can generate derived outputs on demand
  * [ ] Derived outputs stored in work_summaries table with correct type
  * [ ] Line references in UI are clickable and navigate to source
  * [ ] Salience thresholds configurable via Settings > Summarize tab
  * [ ] All new API endpoints follow /api/v1 prefix convention
  * [ ] Unit tests pass for core summarization modules
  * [ ] No regressions in existing Corpus or Chunk functionality

## Manual verification

* Steps:
  1. Run through complete user workflow
  2. Verify documentation accuracy by following it
  3. Test edge cases and error scenarios
  4. Review logs for any warnings or errors
* Expected results:
  * Feature works as documented
  * No unexpected errors or behaviors
  * Documentation is accurate and helpful

## Notes

* Requirements covered: All requirements verification
* This ticket should be the last one executed
* Any issues found should be fixed before closing
* Consider creating a demo video or screenshots for documentation
* Keep notes on any usability issues for future improvements
* Documentation location TBD - could be README section or separate doc file
