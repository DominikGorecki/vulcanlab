# Ticket: collection-deep-research.T24 - Integration, Documentation, and Rollout

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Complete end-to-end integration testing for manual and automated workflows
* Create user documentation and feature guide
* Deploy to staging and production environments with monitoring

## Phase

* Rollout

## Scope

### In scope

* End-to-end integration testing (manual workflow, automated workflow, resume)
* User documentation: feature overview, how-to guides for manual and automated research
* Sample collection creation for demo/testing
* Staging deployment and UAT
* Production deployment with monitoring
* Error log monitoring for first week

### Out of scope

* Individual unit tests (covered in all previous tickets)
* Performance optimization (can be addressed post-launch if issues arise)
* Advanced features (PDF export, citation validation, etc. - deferred per spec)

## Dependencies

* Depends on: All previous tickets (T01-T23)
* Unblocks: Production launch

## Implementation plan

* Integration testing:
  * Create test collection with 10+ items (3 research_results, 5 excerpts, 2 research_queries)
  * Test manual workflow end-to-end:
    * Start manual research from collection page
    * Complete all 6 steps of wizard (planning, result matching, context assembly, section generation, synthesis, quality evaluation)
    * Verify report saved to database
    * Verify report appears in collection page report list
    * View report and verify markdown rendering, citation links work
  * Test automated workflow end-to-end:
    * Start automated research from collection page
    * Monitor progress updates (polling)
    * Wait for completion
    * Verify report saved correctly
    * Compare manual vs automated report quality for same collection
  * Test session resume:
    * Start manual research, complete Step 2, close browser
    * Reopen collection page, verify in-progress session displayed
    * Click "Resume", verify wizard opens at Step 3
    * Verify all saved state loaded (research_plan, sections)
    * Complete workflow
  * Test result reuse:
    * Create collection with existing research_result
    * Start manual research
    * At Step 2 (result matching), verify matching result suggested
    * Select "Exact Reuse" strategy
    * Verify context assembly uses reused result
    * Complete workflow and verify section includes reused content
  * Test error cases:
    * Mock LLM failure in automated workflow
    * Verify session status updated to 'failed'
    * Verify error message displayed in UI
  * Test authorization:
    * Create collection as User A
    * Attempt to access research session as User B
    * Verify 403 forbidden
* Documentation:
  * Create documentation/features/collection-deep-research.md:
    * Feature overview: what is deep research, why use it
    * Manual research guide: step-by-step walkthrough with screenshots
    * Automated research guide: how to trigger, monitor progress, interpret results
    * Result reuse explanation: how it works, benefits
    * Session resume guide: how to pause and resume
    * Troubleshooting: common issues and solutions
  * Update main README.md with link to deep research feature
  * Create sample collection with demo data for user testing
* Staging deployment:
  * Deploy database migrations to staging: run T01 migration
  * Verify tables created correctly
  * Deploy backend changes: T02-T16 (models, CRUD, modules, APIs, LangGraph)
  * Verify all API endpoints working (curl or Postman tests)
  * Deploy frontend changes: T17-T23 (UI components, wizard, progress, reports)
  * Verify UI renders correctly, no console errors
  * Run integration tests on staging environment
  * Conduct UAT with 2-3 internal users
  * Collect feedback and fix critical issues
* Production deployment:
  * Schedule deployment during low-traffic window
  * Deploy migrations to production database (additive schema, no downtime)
  * Deploy backend changes
  * Deploy frontend changes
  * Smoke test: create test collection, start manual research, verify works
  * Monitor error logs for first 24 hours
  * Monitor session creation rate, completion rate
  * Check database query performance (indexes working correctly)
  * If critical issues: rollback frontend/backend (database schema additive, no rollback needed)
  * If successful: announce feature to users with documentation link
* Monitoring setup:
  * Add metrics:
    * research_sessions_created_total (counter by session_type)
    * research_sessions_completed_total (counter by session_type)
    * research_sessions_failed_total (counter)
    * research_session_duration_seconds (histogram)
  * Add alerts:
    * research_sessions_failed_total > 5 in 1 hour
    * research_session_duration > 30 minutes (potential stuck workflow)
  * Log all LangGraph node executions with timing
* Patterns to apply:
  * **Rollout plan** - Per spec "Rollout / Migration Plan" section
  * **Monitoring** - Per spec Non-functional requirements (Observability)
* Deviations (if any):
  * None

## Unit tests (required)

* This ticket is integration and rollout focused, no new unit tests
* Verify all unit tests from T01-T23 pass before deployment

## Acceptance criteria (checklist)

* [ ] End-to-end manual workflow test passes on test collection
* [ ] End-to-end automated workflow test passes on test collection
* [ ] Session resume test passes (pause and resume from different steps)
* [ ] Result reuse test passes (matching results suggested and used)
* [ ] Error handling test passes (failed sessions, unauthorized access)
* [ ] User documentation created in documentation/features/collection-deep-research.md
* [ ] Sample collection created for demo/testing
* [ ] Database migrations deployed to staging successfully
* [ ] Backend deployed to staging, all API endpoints working
* [ ] Frontend deployed to staging, UI renders correctly
* [ ] UAT conducted with 2-3 users, feedback collected
* [ ] Critical issues from UAT fixed
* [ ] Production deployment completed successfully
* [ ] Smoke test passes on production
* [ ] Monitoring metrics and alerts configured
* [ ] Error logs monitored for first 24 hours, no critical issues
* [ ] Feature announced to users with documentation link

## Manual verification

* Staging verification:
  * Create test collection with 10 items on staging
  * Run through manual workflow completely
  * Run through automated workflow completely
  * Test session resume
  * Test result reuse
  * Verify all features work on staging
* Production verification:
  * Smoke test: create collection, start research, verify works
  * Check metrics dashboard: sessions created, completed
  * Check error logs: no critical errors
  * Check database: research_sessions, research_sections, research_reports tables populated
  * Verify authorization: non-owner cannot access sessions
* User acceptance testing:
  * Provide UAT users with test collection
  * Guide through manual workflow
  * Guide through automated workflow
  * Collect feedback on usability, bugs, confusion points
  * Fix critical issues before production

## Notes

* Requirements covered: All requirements (end-to-end integration), rollout plan per spec
* Integration testing critical: ensures all pieces work together (T01-T23)
* UAT ensures feature is usable and understandable by real users
* Monitoring enables early detection of issues post-launch
* Documentation critical for user adoption - users need guidance for 6-step manual workflow
* Sample collection provides quick way for users to try feature without setup
* Rollout plan follows spec recommendations: staging → UAT → production → monitoring
* Additive database schema (T01) enables safe deployment with no downtime
