# Ticket: simplify-ui-with-simple-conversion-focus.T08 - Frontend: Refactor Simple Conversion to Use Dedicated Execution Pages

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Refactor Simple Conversion page to redirect to dedicated execution pages for both automatic and manual modes
- Remove inline automatic execution and results display from main Simple Conversion page
- Keep main Simple Conversion page focused on form input and history display only
- Ensure clean separation between form entry, execution, and history review
- Polish loading states, empty states, and error handling across history components
- Ensure consistent badge colors and styling between history list and execution result pages

## Scope
### In scope
- Modify form submission to redirect to `/simple-conversion/automatic/[work_id]` for automatic mode
- Modify form submission to redirect to `/simple-conversion/manual/[work_id]` for manual mode (already implemented)
- Remove inline automatic execution state, status tracking, and results display from main Simple Conversion page
- Simplify main Simple Conversion page to show only: form and history section
- Ensure history section is always visible (no conditional hiding during execution)
- Refresh history list when user returns to main page after completing a conversion
- Review and polish existing `/simple-conversion/automatic/[work_id]` page for execution and results display
- Standardize badge colors and styling: classification (small/large), mode (automatic/manual), status (success/error)
- Apply consistent badge styling across history list, detail page, and execution result pages
- Polish empty state message and styling for history section
- Improve loading skeletons to match final layout
- Add error boundary around history section to prevent crashes
- Smooth transitions between states (loading, empty, list, error)

### Out of scope
- Real-time updates via websockets
- Manual refresh button for history (auto-refresh on page navigation is sufficient)
- Advanced animations beyond simple transitions
- Pagination implementation
- History item actions (delete, edit, re-run)
- Modifications to manual mode workflow (already uses dedicated page)

## Dependencies
- Depends on: T05 (history list), T07 (detail page)
- Unblocks: none (completes polish for vertical slice)

## Implementation plan
1. Review current Simple Conversion page implementation:
   - Identify automatic execution state management (lines 103-107 in page.tsx)
   - Identify inline results display (lines 587-669 in page.tsx)
   - Identify automatic execution function (lines 222-256 in page.tsx)
2. Modify form submission handler (handleSubmit):
   - For automatic mode: Call `/api/simple-conversion/start` with mode='automatic'
   - Immediately redirect to `/simple-conversion/automatic/[work_id]` (no inline execution)
   - For manual mode: Keep existing redirect to `/simple-conversion/manual/[work_id]`
3. Remove automatic execution state management:
   - Remove autoExecuting, autoStatus, autoResults, autoError state variables
   - Remove executeAutomaticPipeline function
   - Remove conditional rendering based on autoExecuting/autoResults
4. Remove inline results display components:
   - Remove automatic execution status card (lines 552-562)
   - Remove automatic execution error alert (lines 565-584)
   - Remove automatic execution results display (lines 587-669)
   - Keep only form and history section on main page
5. Simplify main Simple Conversion page layout:
   - Always show form (unless submitting - brief loading state during redirect)
   - Always show history section below form (no conditional hiding)
   - Remove logic that hides history during execution (execution happens on separate page)
6. Review and polish `/simple-conversion/automatic/[work_id]` page:
   - Ensure it handles automatic pipeline execution on mount
   - Ensure it displays loading state during execution
   - Ensure it displays results summary and chunks after completion
   - Ensure it displays error state if execution fails
   - Add "Start New Conversion" button that navigates back to `/simple-conversion`
7. Update history refresh logic:
   - On component mount, fetch history list
   - Consider adding effect to refetch history when user navigates back to page (if feasible with Next.js router)
   - Or rely on page remount to trigger fresh fetch (simpler approach)
8. Standardize badge component styling:
   - Classification: small (blue bg-blue-600), large (purple bg-purple-600)
   - Mode: automatic (green outline or solid), manual (amber/orange outline or solid)
   - Status: success (green check icon), failed (red X icon)
9. Apply consistent badge styling across:
   - SimpleConversionHistoryCard (history list in main page)
   - SimpleConversionSummaryCard (detail page from T07)
   - Automatic execution results page (if displaying badges)
   - Manual workflow page (if displaying badges)
10. Improve empty state for history section:
    - Friendly message: "No past conversions yet"
    - Hint text: "Start a new conversion above to see it appear here"
11. Improve loading skeleton for history section:
    - Match final card/table layout structure
    - Use Shadcn Skeleton component if available
12. Add error boundary component wrapping history section:
    - Catch rendering errors in history components
    - Display fallback UI with error message
    - Prevent entire page crash if history fails
13. Add smooth transitions for history section:
    - Fade-in for list appearance
    - CSS transitions for state changes (optional)
14. Test all state transitions in history section:
    - Loading -> list, loading -> empty, loading -> error
15. Test full conversion flow:
    - Submit automatic conversion -> redirects to automatic page -> complete -> navigate back -> history refreshed
    - Submit manual conversion -> redirects to manual page -> complete -> navigate back -> history refreshed

- Patterns to apply:
  - **Page-Based Routing** - Use Next.js App Router for clean separation of concerns
  - **Single Responsibility** - Main page handles form + history, execution pages handle execution + results
  - **Error Boundaries** - React error boundary to isolate failures
  - **TailwindCSS Transitions** - Simple fade/slide effects
  - **Consistent Design Tokens** - Standardize colors via Tailwind theme

- Deviations (if any):
  - None - follows React and Next.js best practices for page-based architecture

## Unit tests (required)
- Modify existing tests for Simple Conversion page:
  - Remove tests for inline automatic execution state
  - Remove tests for inline results display
  - Update form submission tests to verify redirect behavior (automatic mode)
  - Add tests for history section always visible
  - Test history section renders regardless of form state
- Add/update tests for automatic execution page:
  - Test automatic pipeline executes on mount
  - Test loading state during execution
  - Test results display after completion
  - Test error state if execution fails
  - Test "Start New Conversion" navigation
- Add tests for badge consistency:
  - Classification badges render correct color (small = blue, large = purple)
  - Mode badges render correct color (automatic = green, manual = amber)
  - Status indicators render correct color/icon (success = green check, failed = red X)
  - Verify same badge styling across all components (history list, detail page, execution pages)
- Add tests for history section polish:
  - Empty state renders when no conversions exist
  - Error boundary catches rendering errors in history section
  - Error boundary displays fallback UI
  - Loading skeleton structure matches final card/table layout
- Suggested locations:
  - vulcanlab_ui/src/app/simple-conversion/__tests__/page.test.tsx (update)
  - vulcanlab_ui/src/app/simple-conversion/automatic/[work_id]/__tests__/page.test.tsx (update)
  - vulcanlab_ui/src/components/simple-conversion/__tests__/badge-consistency.test.tsx (new)
- Mocking/fakes needed:
  - Mock Next.js router.push for redirect verification
  - Mock fetch for form submission and history fetch
  - Simulate rendering error for error boundary test

## Acceptance criteria (checklist)
- [ ] Form submission for automatic mode redirects to `/simple-conversion/automatic/[work_id]`
- [ ] Form submission for manual mode redirects to `/simple-conversion/manual/[work_id]` (already working)
- [ ] Main Simple Conversion page shows only form and history section (no inline execution/results)
- [ ] History section always visible on main page (never hidden)
- [ ] Automatic execution page handles pipeline execution on mount
- [ ] Automatic execution page displays loading state during processing
- [ ] Automatic execution page displays results summary and chunks after completion
- [ ] Automatic execution page displays error state if execution fails
- [ ] Automatic execution page includes "Start New Conversion" button that navigates to `/simple-conversion`
- [ ] History list refreshes when user navigates back to main page after conversion
- [ ] New conversion appears at top of history list after completion and returning to main page
- [ ] Classification badges use consistent colors: blue (small), purple (large)
- [ ] Mode badges use consistent colors: green (automatic), amber (manual)
- [ ] Status indicators use consistent styling: green check (success), red X (failed)
- [ ] Badge styling identical across history list, detail page, and execution pages
- [ ] Empty state message clear and friendly
- [ ] Loading skeleton layout matches final card/table layout
- [ ] Error boundary prevents page crash if history rendering fails
- [ ] Error boundary shows user-friendly fallback message
- [ ] Smooth transitions between loading, empty, list, and error states in history section
- [ ] Unit tests cover redirect logic, badge consistency, and history section states

## Manual verification
- Steps:
  1. Navigate to `/simple-conversion` page
  2. Verify form and history section both visible
  3. Submit a new conversion in automatic mode
  4. Verify redirect to `/simple-conversion/automatic/[work_id]`
  5. Verify loading state shown during processing
  6. Wait for conversion to complete
  7. Verify results display with correct badges (classification, status)
  8. Click "Start New Conversion" button
  9. Verify navigation back to `/simple-conversion` main page
  10. Verify history section now shows new conversion at top
  11. Verify new conversion has correct badges (classification, mode, status)
  12. Submit another conversion in manual mode
  13. Verify redirect to `/simple-conversion/manual/[work_id]`
  14. Complete manual workflow and return to main page
  15. Verify history list includes both conversions
  16. Click first conversion in history, verify detail page badge colors
  17. Return to main page, verify badge colors match between list and detail
  18. Verify empty state shows when no conversions exist (test with fresh install or cleared data)
  19. Simulate error by modifying history component to throw during render
  20. Verify error boundary catches and shows fallback UI
- Expected results:
  - Both automatic and manual modes redirect to dedicated pages
  - Main page remains clean with only form and history
  - History section always visible (no hiding during execution)
  - Conversions execute and display results on dedicated pages
  - New conversions appear in history after completion and returning to main page
  - Badge colors are consistent and visually distinct across all pages
  - Transitions are smooth without jarring layout shifts
  - Error boundary prevents catastrophic failures
  - Empty and loading states are polished

## Notes
- This refactoring simplifies the main Simple Conversion page significantly by removing inline execution complexity
- Dedicated execution pages provide better UX: users see progress on a focused page, can bookmark results, and have clear navigation
- History section becomes a stable reference that's always accessible (no hiding during active conversions)
- Auto-refresh after conversion: Next.js App Router should naturally refetch history when user navigates back to main page (verify this behavior)
- Badge color standardization: define colors in Tailwind config or use existing theme colors for consistency
- Empty state illustration optional but improves UX - check if design system has standard illustrations
- Error boundary should log errors to console or monitoring service for debugging
- Loading skeleton: use Shadcn Skeleton component if available, or simple animated div with gradient
- Consider using Next.js useRouter to programmatically navigate after form submission
- Automatic execution page may need to trigger pipeline execution via API call on mount (check existing implementation)
- Test redirect behavior thoroughly - ensure work_id is correctly passed in URL
- Consider adding breadcrumb navigation on execution pages: "Simple Conversion > Automatic Execution" for better UX
- If automatic execution page doesn't exist yet or needs significant updates, coordinate with team about scope expansion
