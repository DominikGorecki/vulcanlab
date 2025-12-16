# Ticket: simplify-ui-with-simple-conversion-focus.T09 - Integration Testing: Full Workflow Verification

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Verify complete user workflows end-to-end across all implemented features
- Test settings toggle -> navigation visibility -> history viewing flows
- Validate data consistency between history list and detail pages
- Ensure performance meets requirements for history queries

## Scope
### In scope
- Manual testing of complete workflows per spec testing plan
- Performance testing: history list loads in under 2 seconds for 100 works
- Data consistency verification: counts match between API, list, and detail views
- Navigation flow testing: settings -> toggle -> nav visibility changes
- Cross-browser compatibility testing (Chrome, Firefox, Safari)
- Responsive design testing (mobile, tablet, desktop)
- Error handling verification: network failures, invalid IDs, failed conversions

### Out of scope
- Automated E2E test suite creation (Playwright/Cypress)
- Load testing beyond 100 works
- Security penetration testing
- Accessibility audit (WCAG compliance)
- Performance profiling and optimization (unless issues found)

## Dependencies
- Depends on: T01-T08 (all implementation tickets must be complete)
- Unblocks: none (final verification before release)

## Implementation plan
1. Set up test environment with clean database
2. Execute manual test plan from spec (lines 352-365):
   - Fresh install verification
   - Toggle ON/OFF testing
   - Navigation visibility checks
   - Direct URL access verification
   - History list functionality
   - Detail page navigation
   - Failed conversion handling
   - Empty state verification
3. Create test dataset:
   - Generate 100 simple conversion works in database
   - Mix of automatic/manual, success/failed, small/large
   - Variety of chunk counts and content types
4. Performance testing:
   - Measure history list load time with 100 works
   - Verify query uses indexes (check query plan)
   - Measure detail page load time
   - Check for N+1 query issues
5. Data consistency checks:
   - Compare chunk counts in history list vs detail page vs database
   - Verify heading/content chunk differentiation logic
   - Validate status determination logic (complete vs failed)
   - Check error message propagation
6. Cross-browser testing:
   - Test on Chrome, Firefox, Safari (macOS/iOS)
   - Verify badge styling consistent
   - Check layout on different viewport sizes
7. Error scenario testing:
   - Disconnect network, test error states
   - Navigate to invalid work_id, verify 404 handling
   - Simulate API timeout, test retry logic
   - Test with failed conversion (error_message present)
8. Responsive design verification:
   - Test on mobile (320px - 768px)
   - Test on tablet (768px - 1024px)
   - Test on desktop (1024px+)
   - Verify card layout adapts correctly
9. Document test results:
   - Create test report with findings
   - Screenshot any visual bugs
   - Log performance metrics
   - List any issues for follow-up tickets

- Patterns to apply:
  - **Manual Testing** - Systematic walkthrough of user workflows
  - **Performance Benchmarking** - Measure against requirements
  - **Cross-browser Compatibility** - Verify on major browsers
  - **Responsive Design Testing** - Check all viewport sizes

- Deviations (if any):
  - None - testing follows standard QA practices

## Unit tests (required)
- This ticket focuses on manual/integration testing, not unit tests
- Unit tests should already exist from T01-T08
- If gaps found during testing, add missing unit tests:
  - Edge cases discovered during manual testing
  - Browser-specific issues that can be unit tested
  - Performance regression tests for slow queries

- Suggested locations:
  - tests/integration/ (if creating any new automated tests)
- Mocking/fakes needed:
  - None for manual testing
  - For any new automated tests: mock external APIs only

## Acceptance criteria (checklist)
- [ ] All manual test cases from spec executed and passed
- [ ] Settings toggle changes navigation visibility correctly
- [ ] Advanced mode OFF hides Conversion, Sanitization, Chunking nav items
- [ ] Advanced mode ON shows all nav items
- [ ] Direct URL access works for hidden pages
- [ ] History list displays all simple conversions sorted by date DESC
- [ ] History list loads in under 2 seconds with 100 works
- [ ] Detail page shows correct data for all conversions
- [ ] Heading and content chunk counts accurate and consistent
- [ ] Failed conversions show error indicators and messages
- [ ] Empty state displays when no conversions exist
- [ ] Badge colors consistent between list and detail views
- [ ] Error states show retry options and friendly messages
- [ ] Layout responsive on mobile, tablet, desktop
- [ ] Functionality works on Chrome, Firefox, Safari
- [ ] No console errors during normal operation
- [ ] Test report document created with findings

## Manual verification
- Steps:
  1. Execute full manual test plan from spec section "Manual test plan" (lines 352-365)
  2. Create 100 test conversions using script or manual process
  3. Navigate to /simple-conversion and measure history load time
  4. Open browser DevTools Network tab and verify API response time
  5. Check browser DevTools Console for errors or warnings
  6. Test on Chrome: verify all features work
  7. Test on Firefox: verify all features work
  8. Test on Safari: verify all features work
  9. Resize browser to mobile width (375px) and test core flows
  10. Test error scenarios: disconnect WiFi, invalid URLs, etc.
  11. Compare chunk counts: database query vs API response vs UI display
  12. Take screenshots of key screens for documentation
  13. Document any bugs or issues found
  14. Create follow-up tickets for any issues requiring fixes
- Expected results:
  - All acceptance criteria met
  - Performance within requirements (< 2s for 100 works)
  - No critical bugs found
  - Minor issues documented for follow-up
  - UI consistent across browsers
  - Responsive design works on all viewport sizes
  - Data accuracy verified

## Notes
- This ticket is primarily manual testing - consider creating automated E2E tests in future for regression prevention
- Performance testing with 100 works is specified in non-functional requirements - use realistic data
- If performance is slower than 2 seconds, investigate:
  - Are indexes being used? (EXPLAIN ANALYZE the query)
  - Is JSON parsing slow? (consider caching computed values)
  - Are there N+1 queries? (use eager loading)
- Cross-browser testing can use BrowserStack or similar service if physical devices unavailable
- Document actual load times in test report for baseline metrics
- Test data generation: consider creating script to populate database with 100 varied works
- Check that database migration 017 indexes are actually used (pg_stat_user_indexes)
- Verify that navigation state persists across page refreshes and browser restarts
- Test accessibility basics even though full audit is out of scope: keyboard navigation, screen reader announcements
- If any critical issues found, block release and create fix tickets
- Minor issues can be tracked as technical debt for future sprints
