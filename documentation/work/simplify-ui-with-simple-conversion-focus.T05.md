# Ticket: simplify-ui-with-simple-conversion-focus.T05 - Frontend: Simple Conversion History List

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add past conversions history section to Simple Conversion page below the form
- Fetch and display list of simple conversion works from backend API
- Show summary cards with title, author, badges, status, and date
- Enable navigation to detail page on item click
- Provide empty state when no history exists

## Scope
### In scope
- History section on /simple-conversion page below conversion form
- Fetch data from GET /api/simple-conversion/history on page load
- Render list/grid of history item cards (SimpleConversionHistoryCard component)
- Each card displays: title, author, classification badge (small/large), mode badge (automatic/manual), status indicator (success/error), created date
- Clickable cards navigate to /simple-conversion/history/[work_id]
- Empty state message when no conversions exist
- Loading state while fetching data
- Error state with retry button if fetch fails
- Sort display by most recent first (backend handles sorting)

### Out of scope
- Detail page implementation (handled in T07)
- Pagination or infinite scroll
- Filtering or search UI
- Inline editing or deletion
- Real-time updates

## Dependencies
- Depends on: T03 (backend history endpoint)
- Unblocks: T07 (detail page needs history context to be useful)

## Implementation plan
1. Locate Simple Conversion page (likely vulcanlab_ui/src/app/simple-conversion/page.tsx)
2. Add "use client" directive if not already present
3. Create new component SimpleConversionHistoryCard in vulcanlab_ui/src/components/simple-conversion/
4. Import Card, Badge components from @/components/ui/
5. Add state for history data (useState: works array)
6. Add loading, error states (useState)
7. Create useEffect to fetch /api/simple-conversion/history on mount
8. Parse response and store in state
9. Implement SimpleConversionHistoryCard component:
   - Props: work_id, title, author, classification, mode, status, created_at, error_message
   - Render Card with hover effect
   - Display title and author as heading
   - Show classification badge (small/large with color)
   - Show mode badge (automatic/manual with icon or color)
   - Show status indicator (checkmark for success, X for error)
   - Format created_at as readable date (e.g., "Jan 15, 2025")
   - Make entire card clickable with onClick -> router.push
10. Render history section below conversion form
11. Conditional rendering: loading skeleton, error message with retry, empty state, or list
12. Map over works array to render SimpleConversionHistoryCard components
13. Use Next.js Link or router.push to navigate to /simple-conversion/history/[work_id]
14. Style with TailwindCSS: grid or flex layout, appropriate spacing

- Patterns to apply:
  - **Client Components** - Use "use client" for interactivity and data fetching
  - **TailwindCSS** - Utility classes for layout, spacing, hover effects
  - **Shadcn/Radix Components** - Reuse Card, Badge from existing UI kit
  - **Component Composition** - Extract SimpleConversionHistoryCard as reusable component

- Deviations (if any):
  - None - follows established Next.js App Router and component patterns

## Unit tests (required)
- Add tests for:
  - History section renders loading state on initial mount
  - Component fetches /api/simple-conversion/history on mount
  - History list renders cards when data available
  - Each card displays correct title, author, badges, status, date
  - Empty state shown when API returns empty array
  - Error state shown when fetch fails
  - Retry button refetches data after error
  - Clicking card navigates to /simple-conversion/history/[work_id]
  - Classification badge shows correct text and color (small vs large)
  - Mode badge shows correct text (automatic vs manual)
  - Status indicator shows success icon for completed conversions
  - Status indicator shows error icon for failed conversions
  - Date formatting displays human-readable format
- Suggested locations:
  - vulcanlab_ui/src/app/simple-conversion/__tests__/page.test.tsx
  - vulcanlab_ui/src/components/simple-conversion/__tests__/SimpleConversionHistoryCard.test.tsx
- Mocking/fakes needed:
  - Mock fetch/API client for history endpoint
  - Mock useRouter from next/navigation for navigation testing
  - Mock response data with various work states (success, failed, automatic, manual)

## Acceptance criteria (checklist)
- [ ] History section appears below conversion form on /simple-conversion page
- [ ] Section fetches data from /api/simple-conversion/history on mount
- [ ] Loading state shown while fetching (skeleton or spinner)
- [ ] Cards display in grid or list layout sorted by most recent first
- [ ] Each card shows title, author, classification badge, mode badge, status, date
- [ ] Classification badge differentiates small vs large with color/text
- [ ] Mode badge shows automatic or manual
- [ ] Status indicator shows success (green check) or error (red X)
- [ ] Date formatted as human-readable (e.g., "Jan 15, 2025")
- [ ] Clicking card navigates to /simple-conversion/history/[work_id]
- [ ] Empty state shows message "No past conversions yet" when list is empty
- [ ] Error state shows message with retry button on fetch failure
- [ ] Retry button refetches data
- [ ] Unit tests cover rendering, fetching, navigation, and all UI states

## Manual verification
- Steps:
  1. Navigate to /simple-conversion page
  2. Scroll below conversion form to history section
  3. Verify loading state appears briefly
  4. Verify list of past conversions appears (requires backend data)
  5. Check that most recent conversion is at top
  6. Verify each card shows correct badges and status icons
  7. Click on a history card
  8. Verify navigation to /simple-conversion/history/[work_id]
  9. Use backend to delete all simple conversions
  10. Refresh page and verify empty state message
  11. Simulate network error (offline mode) and refresh
  12. Verify error state with retry button
  13. Click retry and verify data loads
- Expected results:
  - History section visually integrated with page design
  - Cards have hover effects and clear clickable affordance
  - Empty and error states are user-friendly
  - No layout shift during loading
  - Navigation works correctly
  - No console errors

## Notes
- History section should be visually separated from the form (e.g., horizontal rule, heading "Past Conversions")
- Consider lazy loading history section (only fetch when scrolled into view) for performance
- Card hover effect should indicate interactivity (cursor pointer, subtle shadow/border change)
- Classification badge colors: consider using existing theme colors (e.g., blue for small, purple for large)
- Mode badge: optional icon like play button for automatic, hand/manual icon for manual
- Status indicator: use simple icon, not full error message in card (error details on detail page)
- Date formatting: use date-fns or built-in Intl.DateTimeFormat for consistent formatting
- Grid layout recommendation: responsive grid (1 column mobile, 2-3 columns desktop) using Tailwind grid classes
- Empty state could include encouraging message or link to documentation about simple conversion
