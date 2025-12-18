# Title: Automate RAG Process

## Summary
- Add an "+ Auto" button to the `/rag` page that automates the complete RAG preparation pipeline
- The automation includes: LLM-based query expansion, vector embeddings, retrieval, and consolidation
- Upon completion, redirect the user to `/rag/[new-id]` where the query is ready for final prompt generation
- The process creates a query record first, then updates it through each step, matching the existing manual flow pattern
- Rename the existing "+ New" button to "+ Manual" for clarity

## Problem / Context
- Currently, users must manually navigate through multiple steps to prepare a RAG query: visit `/rag/new?q=`, run or copy/paste LLM expansion, then manually trigger embed, retrieve, and consolidate operations
- This multi-step process is tedious and error-prone for users who simply want to get a query ready for final RAG prompt generation
- Users must understand the pipeline stages to know which buttons to click in which order
- The manual flow is useful for advanced users who want control, but most users want a one-click solution
- Business impact: reduced friction means faster query processing and better user experience

## Goals
- Provide a one-click automation button that prepares a RAG query from raw text to "ready" status
- Maintain the same query lifecycle and data flow as the existing manual process
- Show real-time progress feedback during the automated pipeline
- Allow users to still use the manual flow when they need more control

## Non-goals (Strict)
- Running the final RAG prompt generation automatically (user must still click "Go" on `/rag/[id]`)
- Modifying the underlying core RAG logic (embed, retrieve, consolidate functions)
- Adding configuration or settings for the automation (use hardcoded defaults)
- Implementing retry logic or sophisticated error recovery
- Queue management or rate limiting for concurrent automation requests
- Supporting automation for existing queries (only new queries)

## Scope
### In scope
- Frontend: New "+ Auto" button on `/rag` page next to the renamed "+ Manual" button
- Frontend: New processing/progress page that shows pipeline step status
- Frontend: State management for passing query text to processing page (not URL query params)
- Backend: New API endpoint `/api/v1/rag/auto` that orchestrates the full pipeline
- Backend: Sequential execution of expand_query -> vectorize_query -> retrieve -> consolidate_context
- Error handling that leaves the query in its current state on failure
- Automatic redirect to `/rag/[new-id]` upon successful completion

### Out of scope
- Modifying the manual flow behavior (it should remain unchanged)
- Adding settings or configuration for model selection (use FULL tier)
- Retry logic or automatic recovery from failures
- Background job processing or queuing systems
- Notifications or alerts for completion
- Analytics or telemetry for automation usage

## Requirements (Functional)
- R1: The "+ Auto" button must be placed next to the "+ Manual" button (renamed from "+ New") in the New Query card on `/rag` page
- R2: Clicking "+ Auto" must validate that the query text is non-empty before proceeding
- R3: The query text must be passed to the processing page via React state or sessionStorage, NOT via URL query parameters
- R4: The processing page must be inaccessible via direct URL navigation (show error if no query text in state)
- R5: The backend endpoint must create a Query record BEFORE calling the LLM, following the exact pattern of the manual flow
- R6: The automation pipeline must execute in this exact order: expand_query (LLM call) -> vectorize_query -> retrieve -> consolidate_context
- R7: The processing page must show real-time progress for each step: "Expanding query...", "Generating embeddings...", "Retrieving chunks...", "Consolidating context..."
- R8: If any step fails, the query must remain in the database at its current state (not deleted) and the error displayed to the user
- R9: Upon successful completion, the user must be immediately redirected to `/rag/[new-id]` with no delay or confirmation
- R10: The expand_query function must use ModelTier.FULL, consistent with the manual "Run" flow
- R11: The manual flow must continue to work exactly as before, with the only change being the button label from "+ New" to "+ Manual"

## Requirements (Non-functional)
- Performance:
  - The full automation pipeline should complete in under 60 seconds for typical queries (dependent on LLM API speed)
  - Progress updates should appear within 100ms of each step starting
- Reliability:
  - Error messages must clearly indicate which step failed
  - Partial progress must be persisted (query record exists even if pipeline fails midway)
- Security / Privacy:
  - Query text passed via state must not be logged or persisted in browser history
  - No sensitive information should appear in URLs
- Observability:
  - Backend endpoint should log the start and completion of each pipeline step
  - Errors should be logged with sufficient context for debugging

## Proposed Solution (High-level)
- Frontend changes:
  - Rename "+ New" button to "+ Manual" in [vulcanlab_ui/src/app/rag/page.tsx](vulcanlab_ui/src/app/rag/page.tsx:522)
  - Add "+ Auto" button that navigates to `/rag/auto` with query text in React router state
  - Create new page `/rag/auto/page.tsx` that reads query text from router state
  - Display step-by-step progress using state variables (current_step, step_message)
  - Call new backend endpoint `/api/v1/rag/auto` with query text
  - Poll or use single endpoint that returns final query_id on completion
  - Redirect to `/rag/[query_id]` on success
- Backend changes:
  - Create new endpoint `POST /api/v1/rag/auto` in [src/vulcanlab_api/routers/rag.py](src/vulcanlab_api/routers/rag.py)
  - Endpoint accepts `{ "query": "user query text" }` request body
  - Orchestrate sequential calls: expand_query -> vectorize_query -> retrieve -> consolidate_context
  - Return `{ "query_id": int, "status": "ready" }` on success
  - Use existing core functions from vulcanlab.retrieval and vulcanlab.augmentation modules
- Data flow:
  1. User enters query text on `/rag` page
  2. Clicks "+ Auto", navigates to `/rag/auto` with state
  3. `/rag/auto` page calls `POST /api/v1/rag/auto`
  4. Backend creates Query record via expand_query (which calls save_expansion_to_db)
  5. Backend runs vectorize_query, retrieve, consolidate_context in sequence
  6. Frontend redirects to `/rag/[query_id]` when endpoint returns success

## Interfaces / APIs / Contracts
- New API endpoint:
  - `POST /api/v1/rag/auto`
  - Request body: `{ "query": string }`
  - Response: `{ "query_id": number, "status": string, "message": string }`
  - Error response: `{ "detail": string, "failed_step": string }` with appropriate HTTP status code
- New frontend route:
  - `/rag/auto` - processing page (not directly accessible via URL)
  - Expects router state with `{ queryText: string }`
- Frontend state contract:
  - sessionStorage or React router state key: `autoQueryText`
  - Clear the state after successful completion or user navigation away

## Data Model / Storage
- No new database tables or fields required
- Uses existing Query model with fields:
  - original_query (from expand_query)
  - expanded_queries (from expand_query)
  - hyde_answer (from expand_query)
  - intent (from expand_query)
  - entities (from expand_query)
  - vector_status (from vectorize_query)
  - retrieved_context (from retrieve)
  - clean_retrieval_context (from consolidate_context)
- Query status transitions: not yet created -> needs_embeddings -> needs_retrieval -> needs_consolidation -> ready

## UX / Workflows
- Happy path (automated flow):
  1. User enters query text in textarea on `/rag` page
  2. User clicks "+ Auto" button
  3. Browser navigates to `/rag/auto` with query text in state
  4. Processing page displays: "Expanding query..." with spinner
  5. Backend creates query record and expands query
  6. Processing page updates: "Generating embeddings..." with spinner
  7. Backend generates embeddings
  8. Processing page updates: "Retrieving chunks..." with spinner
  9. Backend retrieves relevant chunks
  10. Processing page updates: "Consolidating context..." with spinner
  11. Backend consolidates context
  12. Browser automatically redirects to `/rag/[query_id]`
  13. User sees the ready query with "Go" button to run final RAG prompt
- Error path:
  1. User enters query and clicks "+ Auto"
  2. Pipeline fails at step X (e.g., retrieval)
  3. Processing page shows error: "Failed at retrieval step: [error message]"
  4. User can click "Back to Queries" button to return to `/rag` page
  5. Query appears in table with status reflecting last successful step (e.g., "needs_retrieval")
  6. User can manually continue from that step or delete the query
- Manual flow (unchanged):
  1. User enters query text and clicks "+ Manual"
  2. Navigates to `/rag/new?q=...` as before
  3. Can copy/paste or run expansion as before

## Testing Plan
- Unit tests:
  - Test new `POST /api/v1/rag/auto` endpoint with valid query text (mock core functions)
  - Test endpoint error handling when expand_query fails
  - Test endpoint error handling when vectorize_query fails
  - Test endpoint error handling when retrieve fails
  - Test endpoint error handling when consolidate_context fails
  - Verify query record is created and persists even on mid-pipeline failure
  - Verify correct ModelTier.FULL is used in expand_query call
- Integration tests:
  - Not required for this ticket (defer to future manual testing)
- Manual test plan:
  - Verify "+ Manual" and "+ Auto" buttons both appear on `/rag` page
  - Click "+ Auto" with empty query text, verify validation error
  - Click "+ Auto" with valid query, verify navigation to `/rag/auto`
  - Verify processing page shows each step's progress message
  - Verify successful completion redirects to `/rag/[id]` with status "ready"
  - Verify query appears in the table on `/rag` page with "Go" button
  - Manually navigate to `/rag/auto` without state, verify error message
  - Simulate backend failure (e.g., stop API server mid-process), verify error handling
  - Verify manual flow still works (click "+ Manual", copy/paste flow)
  - Verify manual "Run" button on `/rag/new` still uses FULL model

## Acceptance Criteria (Checklist)
- [ ] "+ New" button is renamed to "+ Manual" on `/rag` page
- [ ] "+ Auto" button appears next to "+ Manual" button
- [ ] Clicking "+ Auto" with empty query shows validation error
- [ ] Clicking "+ Auto" with valid query navigates to `/rag/auto` with query text in state (not URL)
- [ ] `/rag/auto` page shows error if accessed without state
- [ ] Processing page displays step-by-step progress during pipeline execution
- [ ] Backend endpoint `POST /api/v1/rag/auto` successfully orchestrates all four steps
- [ ] Query record is created via expand_query before other steps run
- [ ] Pipeline uses ModelTier.FULL for LLM expansion
- [ ] On successful completion, user is redirected to `/rag/[query_id]`
- [ ] Query appears in queries table with status "ready" and "Go" button
- [ ] On failure, query remains in database at last successful state
- [ ] Error message clearly indicates which step failed
- [ ] Manual flow continues to work exactly as before
- [ ] Unit tests pass for new endpoint and error scenarios

## Rollout / Migration Plan
- No database migrations required
- No backwards compatibility concerns (only additive changes)
- Deploy backend endpoint first, then frontend changes (can be same deployment)
- No feature flags needed (new button is immediately visible)
- No user data migration required

## Risks and Alternatives
- Risks:
  - If LLM API is slow or fails, users are stuck waiting on the processing page (mitigated by showing error and allowing navigation back)
  - Users might not understand the difference between "+ Manual" and "+ Auto" buttons (mitigated by keeping names simple and consistent with behavior)
  - State-based navigation could be lost if user refreshes the processing page (acceptable - show error message)
  - Long-running automation could time out if API gateway has timeout limits (unlikely within 60s, can be addressed in future if needed)
- Alternatives considered:
  - **Alternative 1**: Use URL query parameter for query text
    - Rejected because it makes URLs long, bookmarkable, and potentially exposes query content in browser history
  - **Alternative 2**: Show progress on the main `/rag` page instead of dedicated processing page
    - Rejected because it clutters the main page and makes it harder to show detailed progress
  - **Alternative 3**: Use background jobs and polling
    - Rejected as over-engineering for initial version; synchronous API call is simpler and sufficient for 60s pipeline
  - **Alternative 4**: Combine "+ Manual" and "+ Auto" into a single button with mode selection
    - Rejected because it adds unnecessary complexity; two buttons are clearer

## Patterns and Standards Alignment (from documentation/patterns.md)
- Patterns applied:
  - **Three-tier architecture** - Frontend (Next.js) calls API layer (FastAPI) which calls Core module (vulcanlab)
  - **API versioning** - New endpoint uses `/api/v1` prefix as defined in main.py
  - **Core module independence** - No framework-specific code in core; use existing expand_query, vectorize_query, retrieve, consolidate_context functions
  - **Session management** - Database sessions passed explicitly via get_session() context manager
  - **Error handling** - Raise HTTPException for client errors, let global handler catch 500s, no generic try/except in endpoint
  - **App Router** - Use Next.js App Router for new `/rag/auto/page.tsx`
  - **Client Components** - Use "use client" for interactive processing page
  - **TailwindCSS** - Use utility classes for styling, consistent with existing `/rag` page
  - **Shadcn/Radix components** - Use existing Button, Card, Alert, Spinner components from `vulcanlab_ui/src/components/ui/`
- Deviations (if any):
  - None - this implementation fully aligns with documented patterns

## Implementation Notes (Non-binding)
- The processing page can use a simple polling approach or a single long-lived API call (recommend single call for simplicity)
- Consider using `useRouter()` from next/navigation to manage state and navigation
- The "+ Auto" button should use the same visual style as "+ Manual" but with a different icon (e.g., Zap or Sparkles vs Plus)
- The progress messages can be hardcoded strings; no need for i18n in initial version
- For sessionStorage approach, use key like `vulcanlab_auto_query_text` and clear it after use
- The backend endpoint can return immediately after consolidate_context completes (no need for streaming or websockets)
- Consider reusing the existing handleRunAll logic from [vulcanlab_ui/src/app/rag/page.tsx](vulcanlab_ui/src/app/rag/page.tsx:183) as a reference for sequential step execution
- The core function calls should match the pattern in expand_query: create query first via save_expansion_to_db, then update it through subsequent steps
- Import ModelTier.FULL from vulcanlab.ai.config in the endpoint, same as expand_query does internally

## Open Questions
- Q1: Should the processing page have a "Cancel" button to abort the pipeline?
  - Recommendation: No for initial version (adds complexity; user can navigate away)
- Q2: Should we show estimated time remaining for each step?
  - Recommendation: No for initial version (unpredictable due to LLM API variability)
- Q3: Should the automation support the `n` parameter for number of expanded queries?
  - Recommendation: No, hardcode to n=3 (same default as manual flow)
