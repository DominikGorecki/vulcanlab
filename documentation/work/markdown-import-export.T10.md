# Ticket: markdown-import-export.T10 - Import Status Page Integration

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Integrate markdown import with existing status page infrastructure
- Redirect to status page after import initiation
- Display import progress (sanitization, chunking)
- Show completion status and link to corpus

## Scope
### In scope
- Redirect from import page to status page with work_id
- Status page displays import progress
- Reuse simple conversion status page patterns
- Show sanitization and chunking steps
- Link to corpus when complete

### Out of scope
- Real-time progress updates (use polling or page refresh)
- WebSocket-based live updates
- Detailed chunk-by-chunk progress
- Cancel/abort functionality

## Dependencies
- Depends on: T08
- Unblocks: none (completes import workflow)

## Implementation plan
1. Investigate existing status page implementation:
   - Check how simple conversion status page works
   - Identify route and component location
   - Understand status polling mechanism
2. Update import page (T08) redirect:
   - After successful import API call, redirect to status page
   - Pass work_id as query param or route param
   - Example: router.push(`/status/${workId}`) or `/simple-conversion/status/${workId}`
3. Update or create status page for markdown imports:
   - If reusing simple conversion status page, ensure it handles MARKDOWN_IMPORT type
   - Display steps:
     - Metadata validation ✓
     - Work creation ✓
     - Sanitization (if unsanitized) - in progress/completed
     - Heading chunking - in progress/completed
     - Content chunking - in progress/completed
     - Ready for vectorization ✓
   - Poll work status from API or use existing status endpoint
   - Show error state if any step fails
   - Display "View in Corpus" button when complete
4. Update Work status query endpoint if needed:
   - Ensure endpoint returns progress information for MARKDOWN_IMPORT works
   - Include sanitization status, chunking status, chunk counts
5. Patterns to apply:
   - Status page reuse: Leverage existing simple conversion status infrastructure
   - Polling: Use same mechanism as simple conversion
   - Client component: Use "use client" for status updates
   - Error handling: Display specific error messages for each step
- Deviations (if any):
  - If simple conversion status page cannot be reused, create dedicated markdown import status page

## Unit tests (required)
- Add tests for:
  - Import page redirects to status page after successful import
  - Status page receives work_id correctly
  - Status page polls for work status
  - Status page displays correct steps for sanitized import
  - Status page displays sanitization step for unsanitized import
  - Status page shows completion state
  - "View in Corpus" button navigates to corpus detail page
  - Status page handles errors during import process
  - Polling stops when work reaches final state
- Suggested locations:
  - vulcanlab_ui/src/app/markdown/import/__tests__/page.test.tsx (extend for redirect)
  - vulcanlab_ui/src/app/status/__tests__/[id].test.tsx (or similar)
- Mocking/fakes needed:
  - Mock fetch for status polling endpoint
  - Mock useRouter for redirect
  - Mock setTimeout/setInterval for polling tests

## Acceptance criteria (checklist)
- [ ] Import page redirects to status page after successful import
- [ ] Status page receives work_id parameter
- [ ] Status page displays import progress steps
- [ ] Sanitization step shown only for unsanitized imports
- [ ] Chunking steps display progress correctly
- [ ] Status page shows completion state
- [ ] "View in Corpus" button appears when complete
- [ ] Button navigates to /corpus/{work_id}
- [ ] Error state displayed if import fails
- [ ] Polling updates status automatically
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Import a sanitized markdown file
  2. Verify redirect to status page
  3. Watch progress through steps
  4. Verify sanitization step is skipped
  5. Verify chunking steps appear
  6. Verify completion state reached
  7. Click "View in Corpus" button
  8. Verify navigation to corpus detail page
  9. Import an unsanitized markdown file
  10. Verify sanitization step appears in progress
  11. Watch until completion
  12. Import file that will fail (invalid content)
  13. Verify error state displayed on status page
- Expected results:
  - Status page updates automatically
  - All steps display correctly based on import type
  - Completion leads to corpus view
  - Errors handled gracefully

## Notes
- Status page should reuse simple conversion status infrastructure where possible
- Polling interval should be reasonable (e.g., 2-3 seconds)
- Consider stopping polling after reasonable timeout (e.g., 5 minutes) with "stuck" message
- Status page should show estimated time remaining if possible (optional enhancement)
- If import fails during sanitization or chunking, display specific error from logs
- Work status should be queryable from same endpoint as simple conversion works
- Consider adding refresh button if polling fails or gets stuck
- Status should persist across page refreshes (query current status on mount)
