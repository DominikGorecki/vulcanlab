# Ticket: automate-rag-process.T02 - Frontend Auto RAG UI and Processing Page

## Source
- Spec: documentation/work/automate-rag-process.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add "+ Auto" button to /rag page that triggers automated RAG pipeline
- Rename existing "+ New" button to "+ Manual"
- Create /rag/auto processing page with step-by-step progress indicators
- Redirect to /rag/[query_id] on successful completion

## Scope
### In scope
- Button changes on vulcanlab_ui/src/app/rag/page.tsx (rename "+ New" to "+ Manual", add "+ Auto")
- New processing page vulcanlab_ui/src/app/rag/auto/page.tsx
- State management for passing query text via router state (not URL params)
- API integration with POST /api/v1/rag/auto endpoint
- Real-time progress display during pipeline execution
- Error handling and display on processing page
- Automatic redirect to /rag/[query_id] on success
- Validation (non-empty query) before navigation

### Out of scope
- Backend endpoint implementation (covered in T01)
- Modifying manual flow behavior beyond button rename
- Adding configuration or settings UI
- Progress percentage or time estimates
- Cancel button or abort functionality
- Unit tests for frontend components (manual testing only)

## Dependencies
- Depends on: T01 (backend endpoint must exist)
- Unblocks: None (completes the feature)

## Implementation plan
1. Update vulcanlab_ui/src/app/rag/page.tsx:
   - Change button text from "+ New" to "+ Manual" (around line 522)
   - Add new "+ Auto" button next to "+ Manual" button
   - Add handleAutoQuery function:
     - Validate newQuery is non-empty (same validation as handleNewQuery)
     - Navigate to /rag/auto with router state: { queryText: newQuery.trim() }
     - Use useRouter from next/navigation
   - Update button styling to match (use Zap icon for "+ Auto" vs Plus icon for "+ Manual")

2. Create vulcanlab_ui/src/app/rag/auto/page.tsx:
   - Mark as "use client" (interactive component)
   - Use useRouter to read state from navigation
   - Check if queryText exists in router state on mount
     - If not, show error: "No query text provided. Please use the Auto button on the RAG page."
     - Display "Back to Queries" button to navigate to /rag
   - Define state variables:
     - currentStep: string ("expansion" | "embeddings" | "retrieval" | "consolidation")
     - loading: boolean
     - error: string | null
     - queryId: number | null
   - On mount with valid queryText:
     - Set loading=true, currentStep="expansion"
     - Call POST /api/v1/rag/auto with { query: queryText }
     - Update currentStep as backend progresses (use single API call, no polling needed)
     - On success: set queryId, immediately redirect to /rag/${queryId}
     - On error: set error message with failed_step details, show "Back to Queries" button

3. Processing page UI layout:
   - Header: "Automating RAG Query" with back navigation disabled during loading
   - Main content area: Current step message with spinner
     - "Expanding query..." (Loader2Icon spinner)
     - "Generating embeddings..." (Loader2Icon spinner)
     - "Retrieving chunks..." (Loader2Icon spinner)
     - "Consolidating context..." (Loader2Icon spinner)
   - Error state: Alert with error message and "Back to Queries" button
   - Use existing components from vulcanlab_ui/src/components/ui/:
     - Button, Card, Alert, AlertDescription, Loader2Icon (from lucide-react)

4. State management approach:
   - Use router.push('/rag/auto', { state: { queryText } }) for navigation
   - Read state in /rag/auto using useRouter and router state
   - Alternative: use sessionStorage with key "vulcanlab_auto_query_text"
     - Set in handleAutoQuery before navigation
     - Read in /rag/auto on mount
     - Clear after successful redirect or error
   - Recommendation: Use router state as primary, sessionStorage as fallback

5. Patterns to apply:
   - App Router: Use Next.js App Router for new page at src/app/rag/auto/page.tsx
   - Client Components: Mark page as "use client" for interactivity
   - TailwindCSS: Use utility classes for all styling
   - Shadcn/Radix components: Reuse existing Button, Card, Alert components
   - API integration: Use fetch with API_BASE_URL from environment variable

6. Deviations (if any):
   - None - implementation fully aligns with patterns.md

## Unit tests (required)
- Add tests for:
  - Not applicable - frontend component testing is out of scope per patterns.md
  - Manual testing only (see Manual verification section)

- Suggested locations:
  - N/A

- Mocking/fakes needed:
  - N/A

## Acceptance criteria (checklist)
- [ ] "+ New" button is renamed to "+ Manual" on /rag page
- [ ] "+ Auto" button appears next to "+ Manual" button with Zap icon
- [ ] Clicking "+ Auto" with empty query shows validation error (no navigation)
- [ ] Clicking "+ Auto" with valid query navigates to /rag/auto with queryText in state
- [ ] /rag/auto page shows error if accessed directly without state
- [ ] Processing page displays current step message with spinner
- [ ] Error state shows clear error message with failed step details
- [ ] "Back to Queries" button navigates to /rag page
- [ ] On successful completion, user is immediately redirected to /rag/[query_id]
- [ ] Manual flow (+ Manual button) continues to work exactly as before
- [ ] Query text is NOT visible in browser URL on /rag/auto page
- [ ] State is cleared after navigation away or successful completion

## Manual verification
- Steps:
  1. Navigate to http://localhost:3000/rag
  2. Verify "+ Manual" and "+ Auto" buttons both appear in the New Query card
  3. Click "+ Auto" with empty query textarea
  4. Verify validation error appears (no navigation)
  5. Enter query text: "What is working memory?"
  6. Click "+ Auto"
  7. Verify navigation to /rag/auto
  8. Verify URL does NOT contain query text as parameter
  9. Verify processing page shows "Expanding query..." with spinner
  10. Wait for pipeline to complete
  11. Verify automatic redirect to /rag/[id] page
  12. Verify query appears in queries table on /rag page with status "ready"
  13. Navigate directly to /rag/auto in a new tab
  14. Verify error message: "No query text provided..."
  15. Click "Back to Queries" button
  16. Verify navigation to /rag page
  17. Simulate backend failure (stop API server)
  18. Click "+ Auto" with query text
  19. Verify error message appears with failed step details
  20. Restart API server
  21. Click "+ Manual" with query text
  22. Verify navigation to /rag/new?q=... (manual flow unchanged)

- Expected results:
  - Both buttons appear with correct labels and icons
  - Validation prevents navigation with empty query
  - Processing page shows step-by-step progress
  - Successful automation redirects to query detail page
  - Direct access to /rag/auto shows error
  - Manual flow remains unchanged
  - No query text appears in URLs
  - Error states are clear and actionable

## Notes
- The processing page can use a simple approach: make single API call to /api/v1/rag/auto and show loading state
- Since the backend is synchronous (not streaming), we cannot show real-time progress for each step
- Instead, show generic "Processing..." message or cycle through step messages based on elapsed time estimates (optional)
- Simpler approach: Show "Automating query..." with spinner until API returns
- Consider adding step-by-step messages ONLY if backend supports streaming/polling (future enhancement)
- For initial version, use single loading state with one message: "Automating RAG query..."
- Alternative: Update UI to show all 4 steps at once with checkmarks as progress indicators (visual only, not real-time)
- Reference existing handleRunAll function in vulcanlab_ui/src/app/rag/page.tsx:183 for sequential step UI patterns
- The "+ Auto" button should be visually distinct from "+ Manual" but same size/style
- Use Zap icon from lucide-react for "+ Auto" button to suggest automation/speed
- sessionStorage approach is simpler than router state; recommend using sessionStorage.setItem("vulcanlab_auto_query_text", newQuery)
- Clear sessionStorage on successful redirect AND on component unmount to prevent stale state
- If using router state, note that Next.js router state may not persist on page refresh (acceptable behavior per spec)
