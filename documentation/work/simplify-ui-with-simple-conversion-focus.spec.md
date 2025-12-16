# Title: Simplify UI with Simple Conversion Focus and Past Conversions History

## Summary
- Hide advanced workflow pages (Conversion, Sanitization, Chunking) from navigation by default, showing only Simple Conversion as the primary user workflow
- Add an "Advanced Conversion" toggle in Settings > Conversion tab to control visibility of advanced nav items
- Enhance the Simple Conversion page with a past conversions history section showing all previously completed simple conversions
- Allow users to click into past conversions to view detailed results (on a separate detail page)
- Maintain current conversion initiation flow (form submission redirects to manual workflow page or stays on page for automatic execution)
- Create database migration for performance indexes supporting efficient history queries

## Problem / Context
- The current UI exposes multiple workflow pages (Conversion, Sanitization, Chunking, Simple Conversion) in the navigation, creating confusion about which workflow to use
- Users unfamiliar with the multi-step RAG pipeline may be overwhelmed by the granular workflow options
- Simple Conversion was designed as the primary, streamlined workflow but is presented as just another option in the navigation
- After completing a simple conversion, users cannot easily see their past conversions or re-examine results without navigating to the Corpus page
- The `/simple-conversion` page shows conversion results inline after automatic execution completes, but there is no persistent history or ability to review past work
- No clear distinction between "simple user" workflow and "advanced user" workflow in the UI

**User Impact:**
- New users are confused by multiple similar-sounding navigation options
- Users complete conversions but cannot easily review past work without going to the Corpus page (which shows all works, not just simple conversions)
- Power users who understand the granular pipeline steps have no easy way to access them without always seeing them in navigation

**Business Impact:**
- Lower user adoption due to complexity barrier
- Users may avoid the tool due to unclear workflows
- Support burden increases from users unsure which workflow to use

## Goals
- Simplify the default UI by hiding advanced workflow pages from navigation
- Make Simple Conversion the primary, prominent workflow for new users
- Provide an escape hatch (Advanced Conversion toggle) for power users who want granular control
- Add persistent history of past simple conversions directly on the Simple Conversion page
- Allow users to drill down into past conversion details without leaving the Simple Conversion workflow context
- Maintain current UX for conversion initiation (automatic stays on page, manual redirects to manual workflow page)
- Ensure performant queries for history lists via appropriate database indexes

## Non-goals (Strict)
- Changing the database schema (no new columns, tables, or field modifications)
- Modifying how simple conversion data is stored in the backend
- Changing the existing conversion pipeline logic or execution flow
- Implementing pagination, filtering, or advanced search for past conversions (load all at once)
- Adding edit, delete, or re-run actions for past conversions
- Creating a completely new UI design system or major visual overhaul
- Implementing authentication or user-specific filtering (system is single-user)
- Hiding the Simple Conversion page itself (it remains always visible)

## Scope
### In scope
- Adding "Advanced Conversion" boolean toggle to Settings > Conversion tab (stored in backend config)
- Conditionally rendering Conversion, Sanitization, and Chunking nav items based on toggle state
- Creating a past conversions history section on `/simple-conversion` page (below the form)
- Fetching list of simple conversion works from backend (filtering by `processing_status` JSON fields)
- Displaying summary cards/list items for past conversions (title, author, date, mode badge, status)
- Creating a detail page route (`/simple-conversion/history/[work_id]`) for viewing full conversion results
- Showing chunk details on history detail page (matching post-conversion results view)
- Differentiating heading vs content chunk counts in summary display
- Adding mode badge (automatic/manual) to past conversion list items
- Adding status indicator (success/error) to past conversion list items
- Creating SQL migration (017) for indexes supporting efficient history queries
- Updating `init_db.py` to include new indexes for fresh installs
- Frontend API client additions for fetching conversion settings toggle and past conversions list
- Backend API endpoint for fetching/updating the "Advanced Conversion" toggle setting
- Backend API endpoint for fetching list of simple conversion works with summary data

### Out of scope
- Pagination or infinite scroll for past conversions list
- Sorting, filtering, or search UI controls for past conversions
- Edit or delete actions for past conversions
- Re-running past conversions
- Showing in-progress conversions in the history list (only show completed/failed)
- User authentication or multi-user support
- Export functionality for conversion results
- Comparison view between multiple conversions
- Analytics or usage tracking

## Requirements (Functional)

### R1: Advanced Conversion Toggle in Settings
- Settings > Conversion tab MUST include a new "Advanced Conversion" toggle (switch/checkbox)
- Toggle MUST default to OFF (unchecked) for new installations
- Toggle state MUST be persisted in backend configuration (likely in conversion settings JSON/config)
- Toggle state MUST be fetched on app initialization and used to control nav visibility
- Toggling MUST take effect immediately after save (no page refresh required)

### R2: Conditional Navigation Visibility
- When Advanced Conversion toggle is OFF, Conversion, Sanitization, and Chunking nav items MUST be hidden
- When Advanced Conversion toggle is ON, all nav items MUST be visible
- Simple Conversion, Corpus, Vectorization, RAG, and Settings nav items MUST always be visible regardless of toggle state
- Navigation state MUST be consistent across all pages in the app
- Direct URL access to hidden pages (e.g., `/conv`) MUST still work (no route blocking)

### R3: Past Conversions History Section on Simple Conversion Page
- Simple Conversion page (`/simple-conversion`) MUST include a history section below the conversion form
- History section MUST display when no conversion is actively being processed or shown
- History section MUST show a list/grid of past simple conversion works sorted by most recent first (based on `created_at` timestamp)
- Each history item MUST display: title, author, classification (small/large badge), mode (automatic/manual badge), status (success/error indicator), date
- History items MUST be clickable, navigating to `/simple-conversion/history/[work_id]` detail page
- History list MUST load all simple conversion works at once (no pagination)
- Empty state MUST show friendly message when no past conversions exist

### R4: Past Conversion Detail Page
- Route `/simple-conversion/history/[work_id]` MUST display detailed results for a specific simple conversion work
- Detail page MUST show summary card with: title, author, classification badge, token count, total chunk count, heading chunk count, content chunk count, mode badge, status
- Detail page MUST show scrollable list of all chunks (matching the post-automatic-execution results view)
- Each chunk display MUST show: heading level badge, heading text, line range, content preview
- Detail page MUST include a back button/link to return to `/simple-conversion` page
- Detail page MUST include a "Start New Conversion" button that navigates to `/simple-conversion` and resets the form
- Detail page MUST handle cases where work_id does not exist or is not a simple conversion (show error state)

### R5: Differentiate Heading vs Content Chunks
- Summary displays (both in history list and detail page) MUST differentiate heading chunk count from content chunk count
- Backend API response for conversion history MUST include separate counts for heading chunks (level = "H1" | "H2" | etc.) and content chunks (level ends with "-chunk")
- UI MUST display these as separate metrics (e.g., "12 heading chunks, 45 content chunks")

### R6: Mode and Status Indicators
- Past conversion list items and detail pages MUST display a badge indicating execution mode (automatic/manual)
- Mode badge MUST only display if `simple_conversion_mode` exists in `processing_status`
- Past conversion list items MUST display status indicator (success icon for completed, error icon for failed)
- Status determination: failed if `simple_conversion_step = "failed"` or `simple_conversion_error` exists, otherwise success if `simple_conversion_step = "complete"` or `simple_conversion_step = "content_chunks_created"`
- Error message MUST be displayed on detail page if conversion failed (from `simple_conversion_error` in `processing_status`)

### R7: Backend API Endpoints
- API MUST provide GET endpoint for fetching Advanced Conversion toggle state (e.g., `/api/conversion/settings` already exists, extend to include `advanced_mode_enabled` boolean)
- API MUST provide PUT endpoint for updating Advanced Conversion toggle state (extend existing `/api/conversion/settings`)
- API MUST provide GET endpoint for fetching list of simple conversion works with summary data (e.g., `/api/simple-conversion/history`)
- History endpoint MUST filter works by presence of `simple_conversion_mode` in `processing_status` JSON
- History endpoint MUST return: work_id, title, author, year, created_at, classification, mode, status, token_count, chunk_count, heading_chunk_count, content_chunk_count, error_message (if failed)
- History endpoint MUST sort results by `created_at` DESC (most recent first)
- Detail endpoint already exists (`/api/simple-conversion/results/{work_id}`) and returns full chunk details

## Requirements (Non-functional)

### Performance:
- Past conversions history list MUST load in under 2 seconds for up to 100 works
- Database query for history list MUST use indexes to avoid full table scans
- Chunk count differentiation (heading vs content) MUST be computed efficiently (single query or optimized aggregation)
- Navigation visibility check MUST not introduce perceptible delay on page loads

### Reliability:
- Navigation visibility state MUST remain consistent even if backend config fetch fails (default to OFF/hidden)
- History list fetch failure MUST show error message with retry button, not break the page
- Invalid work_id on detail page MUST show user-friendly error message, not crash
- Backend config update failures MUST show clear error messages to user

### Security / Privacy:
- No authentication changes required (system remains single-user)
- Direct URL access to hidden pages MUST still function (no security-by-obscurity route blocking)
- API endpoints MUST validate work_id parameters to prevent SQL injection or invalid queries

### Observability:
- Backend API logging MUST include requests to new history endpoint
- Frontend console errors MUST clearly identify history fetch failures vs detail fetch failures
- Failed conversions in history MUST log error messages for debugging

## Proposed Solution (High-level)

### Architecture
- **Frontend:** Add React state management for Advanced Conversion toggle (fetch from API on mount, store in context/state)
- **Frontend:** Conditionally render nav items in `NavBar` component based on toggle state
- **Frontend:** Add history section to `/simple-conversion/page.tsx` below the form
- **Frontend:** Create new page component `/simple-conversion/history/[work_id]/page.tsx` for detail view
- **Backend:** Extend existing `/api/conversion/settings` endpoint to include `advanced_mode_enabled` field
- **Backend:** Create new `/api/simple-conversion/history` endpoint returning filtered works list
- **Backend:** Query works table with JSON filter on `processing_status ? 'simple_conversion_mode'`
- **Backend:** Aggregate chunk counts by level pattern (heading vs content) in single query
- **Database:** Add GIN index on `works.created_at` for efficient sorting (if not already indexed)
- **Database:** Consider composite index on `(processing_status, created_at)` for filtered sort queries

### Main Components
1. **SettingsConversionTab Component:** Add "Advanced Conversion" toggle switch, wire to API
2. **NavBar Component:** Read toggle state from context/API, conditionally render nav items
3. **SimpleConversionPage Component:** Add history section below form, fetch and display past conversions
4. **SimpleConversionHistoryListItem Component:** Display summary for single past conversion (reusable card)
5. **SimpleConversionDetailPage Component:** Full detail view for single conversion (new page)
6. **ConversionSettingsRouter (Backend):** Extend GET/PUT endpoints to handle `advanced_mode_enabled` field
7. **SimpleConversionRouter (Backend):** Add `/history` GET endpoint for fetching works list
8. **Database Migration 017:** Create indexes for efficient history queries

### Data Flow
1. User loads app → Frontend fetches conversion settings including `advanced_mode_enabled` → NavBar renders conditionally
2. User navigates to `/simple-conversion` → Page fetches conversion history list → Displays below form
3. User clicks history item → Navigate to `/simple-conversion/history/[work_id]` → Fetch full details → Display results
4. User toggles Advanced Conversion in Settings → PUT request updates backend config → NavBar re-renders on same page
5. User starts new conversion from detail page → Navigate back to `/simple-conversion` → Form resets

## Interfaces / APIs / Contracts

### Frontend → Backend API Calls

#### GET `/api/conversion/settings`
**Response (extended):**
```json
{
  "token_threshold": 15000,
  "advanced_mode_enabled": false
}
```

#### PUT `/api/conversion/settings`
**Request (extended):**
```json
{
  "token_threshold": 15000,
  "advanced_mode_enabled": true
}
```
**Response:** Same as GET

#### GET `/api/simple-conversion/history`
**Response:**
```json
{
  "works": [
    {
      "work_id": 123,
      "title": "Introduction to Machine Learning",
      "author": "John Doe",
      "year": 2023,
      "created_at": "2025-01-15T14:30:00Z",
      "classification": "small",
      "mode": "automatic",
      "status": "complete",
      "token_count": 12000,
      "chunk_count": 57,
      "heading_chunk_count": 12,
      "content_chunk_count": 45,
      "error_message": null
    },
    {
      "work_id": 122,
      "title": "Deep Learning Fundamentals",
      "author": "Jane Smith",
      "year": 2024,
      "created_at": "2025-01-14T10:15:00Z",
      "classification": "large",
      "mode": "manual",
      "status": "failed",
      "token_count": 45000,
      "chunk_count": 0,
      "heading_chunk_count": 0,
      "content_chunk_count": 0,
      "error_message": "LLM sanitization failed: timeout"
    }
  ]
}
```

#### GET `/api/simple-conversion/results/{work_id}` (existing endpoint)
**Response:** Already returns full results including chunks array (no changes needed)

### Backend Configuration Storage
- `advanced_mode_enabled` boolean should be stored in conversion settings (likely in `vulcanlab.config.json` or database config table)
- Default value: `false`

### Database Query Patterns

#### Filtering Simple Conversion Works:
```sql
SELECT * FROM works
WHERE processing_status ? 'simple_conversion_mode'
ORDER BY created_at DESC;
```

#### Counting Heading vs Content Chunks:
```sql
SELECT
  COUNT(*) FILTER (WHERE level IN ('H1', 'H2', 'H3', 'H4', 'H5')) AS heading_chunk_count,
  COUNT(*) FILTER (WHERE level LIKE '%-chunk' OR level = 'chunk') AS content_chunk_count
FROM chunks
WHERE work_id = ?;
```

## Data Model / Storage

### No Schema Changes Required
- Existing `works` table `processing_status` JSONB column already contains all necessary fields
- Existing `chunks` table `level` field already differentiates heading vs content chunks
- Existing indexes on `works.processing_status` (GIN) support JSON filtering

### New Indexes Required (Migration 017)

#### Index 1: Works Created Timestamp
```sql
CREATE INDEX IF NOT EXISTS ix_works_created_at
ON works(created_at DESC);
```
**Rationale:** Supports efficient sorting of history list by most recent first

#### Index 2: Partial Index for Simple Conversion Works with Created Timestamp
```sql
CREATE INDEX IF NOT EXISTS ix_works_simple_conversion_created_at
ON works(created_at DESC)
WHERE processing_status ? 'simple_conversion_mode';
```
**Rationale:** Partial index optimizes the specific query pattern for history list: filter by simple conversion works AND sort by created_at DESC. This is more efficient than using the full `ix_works_created_at` index when filtering. The WHERE clause limits index size to only simple conversion works.

**Note:** This complements the existing GIN index on `processing_status` from migration 008. The combination of GIN index (for JSON filtering) and this partial index (for filtered sorting) provides optimal performance for the history query.

### Configuration Storage
- Add `advanced_mode_enabled` boolean field to conversion settings config
- Likely stored in database `rag_config` table or `vulcanlab.config.json` (follow existing pattern for conversion settings)

## UX / Workflows

### Workflow 1: New User First-Time Experience
1. User navigates to app → sees Simple Conversion, Corpus, Vectorization, RAG, Settings in nav
2. User clicks Simple Conversion → sees form with file selection, metadata, and mode options
3. User completes conversion → sees results inline (existing automatic flow) or redirected to manual workflow
4. User scrolls down → sees empty history with message "No past conversions yet"
5. User completes another conversion → scrolls down → sees past conversion in history list

### Workflow 2: Power User Enabling Advanced Mode
1. User navigates to Settings > Conversion tab
2. User sees "Advanced Conversion" toggle (OFF by default) with description: "Show advanced workflow pages (Conversion, Sanitization, Chunking) in navigation"
3. User toggles ON → clicks Save Changes
4. Navigation immediately updates to show Conversion, Sanitization, Chunking items
5. User can now access granular workflow pages

### Workflow 3: Reviewing Past Conversions
1. User navigates to Simple Conversion page → scrolls past form to history section
2. User sees list of past conversions with title, author, badges (small/large, automatic/manual), date
3. User clicks on a past conversion → navigated to `/simple-conversion/history/[work_id]`
4. User sees full details: summary card + scrollable chunks list
5. User clicks "Back" or "Start New Conversion" → returns to `/simple-conversion` page

### Workflow 4: Handling Failed Conversions
1. User sees past conversion in history list with error indicator (red X icon)
2. User clicks on failed conversion → detail page shows error message at top
3. Error message displays: "Conversion failed: [error_message from processing_status]"
4. User can see partial results (if any) or empty state if no chunks created
5. User clicks "Start New Conversion" to retry with different settings

## Testing Plan

### Unit tests:
- Backend: Test filtering works by `simple_conversion_mode` JSON field
- Backend: Test chunk count aggregation (heading vs content) for various level patterns
- Backend: Test conversion settings GET/PUT with `advanced_mode_enabled` field
- Backend: Test history endpoint response format and data accuracy
- Frontend: Test NavBar conditional rendering based on toggle state
- Frontend: Test history list component rendering with mock data
- Frontend: Test detail page component with valid and invalid work_id

### Integration tests:
- Test full flow: toggle Advanced Conversion OFF → verify nav items hidden → verify direct URL access still works
- Test full flow: create simple conversion (automatic) → verify appears in history list → click detail → verify data matches
- Test full flow: create simple conversion (manual) → verify appears in history list with manual badge
- Test history list with mixed success/failed conversions → verify status indicators correct
- Test detail page with failed conversion → verify error message displayed

### Manual test plan:
- [ ] Fresh install: Verify Advanced Conversion defaults to OFF and nav items hidden
- [ ] Toggle Advanced Conversion ON → Save → Verify Conversion, Sanitization, Chunking appear in nav
- [ ] Toggle Advanced Conversion OFF → Save → Verify nav items disappear
- [ ] Navigate to `/simple-conversion` → Verify history section appears below form
- [ ] Complete automatic conversion → Verify appears in history list after page refresh or returning to page
- [ ] Complete manual conversion → Verify appears in history list with manual badge
- [ ] Click past conversion in list → Verify detail page loads with correct data
- [ ] Verify detail page shows heading chunk count and content chunk count separately
- [ ] Create failed conversion (simulate error) → Verify appears with error indicator
- [ ] Click failed conversion → Verify error message displayed on detail page
- [ ] Direct URL access to `/conv` with Advanced Conversion OFF → Verify page loads (not blocked)
- [ ] Verify history list sorts by most recent first (check timestamps)
- [ ] Verify empty history state shows friendly message

## Acceptance Criteria (Checklist)
- [ ] Settings > Conversion tab includes "Advanced Conversion" toggle switch
- [ ] Toggle state persists across page refreshes and app restarts
- [ ] When toggle is OFF, Conversion, Sanitization, and Chunking nav items are hidden
- [ ] When toggle is ON, all nav items are visible
- [ ] Simple Conversion page includes history section below the form
- [ ] History section displays list of past simple conversions sorted by most recent first
- [ ] Each history item shows title, author, classification badge, mode badge, status indicator, and date
- [ ] Clicking a history item navigates to `/simple-conversion/history/[work_id]` detail page
- [ ] Detail page shows summary card with all required metrics (including separate heading/content chunk counts)
- [ ] Detail page shows scrollable list of chunks matching post-conversion results view
- [ ] Detail page includes back button and "Start New Conversion" button
- [ ] Failed conversions show error indicator in list and error message on detail page
- [ ] Backend API endpoint `/api/conversion/settings` includes `advanced_mode_enabled` field
- [ ] Backend API endpoint `/api/simple-conversion/history` returns filtered works list with summary data
- [ ] Database migration 017 created with required indexes
- [ ] `init_db.py` updated to include new indexes for fresh installs
- [ ] Direct URL access to hidden pages still works (no route blocking)
- [ ] History list loads in under 2 seconds for up to 100 works

## Rollout / Migration Plan
1. **Database Migration (017):** Create and apply migration adding indexes for efficient history queries
2. **Backend API Changes:** Extend conversion settings endpoints and add history endpoint
3. **Frontend Component Updates:** Add toggle to settings, update NavBar, add history section to Simple Conversion page
4. **Frontend New Pages:** Create detail page component and route
5. **Testing:** Run full manual test plan in staging environment
6. **Documentation:** Update user documentation if any exists
7. **Deployment:** Deploy backend and frontend simultaneously (no breaking changes)
8. **Monitoring:** Monitor history endpoint performance and adjust indexes if needed

**Migration Strategy:**
- Existing works with simple conversion data require no updates (data already in correct format)
- New index creation on `works.created_at` is non-blocking (can run online)
- Default toggle state (OFF) maintains current UI behavior for existing users until they opt-in

## Risks and Alternatives

### Risks:
- **Performance Risk:** Loading all history works at once may be slow if user has hundreds of conversions (mitigated by starting with "load all" approach and adding pagination if needed later)
- **State Management Risk:** Navigation visibility state needs to be consistent across app (mitigated by using React Context or global state management)
- **Data Accuracy Risk:** Chunk count differentiation logic must correctly parse all level patterns (mitigated by comprehensive testing of level field variations)
- **Backwards Compatibility Risk:** Existing works created before `simple_conversion_mode` was added won't appear in history (acceptable - only show new simple conversions going forward)

### Alternatives considered:
1. **Alternative 1: Add explicit `is_simple_conversion` boolean column to works table**
   - Rejected: Violates non-goal of no schema changes; JSONB filtering is sufficient with proper indexes
2. **Alternative 2: Create separate navigation profile/mode stored in browser localStorage**
   - Rejected: Loses state across devices/browsers; backend config is more robust
3. **Alternative 3: Paginated history list with 20 items per page**
   - Rejected: User indicated preference for "load all at once" approach; can add pagination later if performance issue arises
4. **Alternative 4: History as separate top-level page (not embedded in Simple Conversion page)**
   - Rejected: Keeps user in Simple Conversion context; embedded history is more intuitive for reviewing past work in same workflow
5. **Alternative 5: Modal/overlay for detail view instead of separate page**
   - Rejected: User specified separate page for detail view; allows deep linking and better UX for detailed review

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied:
- **Three-tier Architecture** - Frontend (Next.js) communicates with API Layer (FastAPI) which queries Core Module/Database. No business logic in frontend.
- **API Versioning** - New history endpoint follows `/api/v1` prefix pattern (or existing `/api` pattern if using that convention)
- **React App Router** - New detail page uses Next.js App Router at `vulcanlab_ui/src/app/simple-conversion/history/[work_id]/page.tsx`
- **TailwindCSS** - All new UI components use Tailwind utility classes for styling
- **Shadcn/Radix Components** - Reuse existing UI components (Button, Card, Badge, etc.) from `vulcanlab_ui/src/components/ui/`
- **Client Components** - History section and detail page use `"use client"` for interactivity (fetch, navigation)
- **Database Session Management** - Backend API routes pass session explicitly to query functions (no session creation in logic)
- **Error Handling** - Let global exception handlers catch unhandled errors; use specific HTTPException for expected failures

### Deviations (if any):
- **None** - This spec fully aligns with established patterns. New API endpoints follow existing routing conventions, frontend follows App Router + Tailwind patterns, and database queries use existing SQLAlchemy patterns with explicit session passing.

## Implementation Notes (Non-binding)
- Consider using React Context API or Zustand for managing Advanced Conversion toggle state globally in frontend
- History list component could be lazy-loaded (code-split) to reduce initial bundle size if Simple Conversion page becomes large
- Chunk count aggregation could be cached in `processing_status` JSON at conversion completion time to avoid repeated database aggregation (optimization for future consideration)
- Consider adding a "Recent" vs "All" toggle if history list becomes very long (future enhancement)
- Error boundary around history section to prevent failures from breaking entire Simple Conversion page
- Loading skeletons for history list while fetching to improve perceived performance
- Breadcrumb navigation on detail page for better UX (Home > Simple Conversion > [Title])
- Consider debouncing/throttling history list refresh if implementing real-time updates (not in scope but good to plan for)

## Open Questions
- Q1: Should the Advanced Conversion toggle be in Settings > Conversion tab or in a new Settings > General tab?
  - **Answer:** Keep in Conversion tab (user confirmed "A. Keep it as 'Conversion'")
- Q2: Should failed conversions be shown in a separate section or mixed with successful ones?
  - **Answer:** Mixed, with status indicator (user confirmed "A. Yes, with an error state indicator")
- Q3: What is the exact format of `processing_status` JSON for identifying simple conversion works?
  - **Answer:** Filter by presence of `simple_conversion_mode` key in JSONB (confirmed via database investigation)
- Q4: Should history list be cached or always fetch fresh data?
  - **Answer:** Fetch fresh on page load (no caching complexity for MVP; can add later if needed)
- Q5: Should migration 017 include only `ix_works_created_at` index or also composite index for filtered sorting?
  - **Answer:** Include both indexes - `ix_works_created_at` for general timestamp sorting and `ix_works_simple_conversion_created_at` partial index for optimized simple conversion history queries (user confirmed "Both")
