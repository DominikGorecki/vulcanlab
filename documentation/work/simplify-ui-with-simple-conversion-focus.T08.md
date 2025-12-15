# Ticket: simplify-ui-with-simple-conversion-focus.T08 - Frontend: History Section Integration and Polish

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Integrate history section with existing Simple Conversion page flow
- Ensure history section shows/hides appropriately during conversion execution
- Polish loading states, empty states, and error handling across history components
- Ensure consistent badge colors and styling between history list and detail page

## Scope
### In scope
- Hide history section when conversion is actively being processed or results are shown inline
- Show history section when form is idle (no active conversion)
- Ensure history list refreshes after completing a new conversion (fetch updated list)
- Standardize badge colors and styling: classification (small/large), mode (automatic/manual), status (success/error)
- Polish empty state message and styling
- Improve loading skeletons to match final layout
- Add error boundary around history section to prevent crashes
- Smooth transitions between states (loading, empty, list, error)

### Out of scope
- Real-time updates via websockets
- Manual refresh button (auto-refresh on new conversion completion is sufficient)
- Advanced animations beyond simple transitions
- Pagination implementation
- History item actions (delete, edit, re-run)

## Dependencies
- Depends on: T05 (history list), T07 (detail page)
- Unblocks: none (completes polish for vertical slice)

## Implementation plan
1. Review Simple Conversion page flow for conversion execution states:
   - Form submission (automatic or manual mode)
   - Results display inline (for automatic mode)
   - Redirect to manual workflow page (for manual mode)
2. Add conditional logic to hide history section when:
   - Conversion is in progress (check processing state)
   - Results are displayed inline on same page
3. Add callback or effect to refresh history list after conversion completes:
   - Detect when conversion status changes to complete
   - Trigger history fetch to get updated list including new conversion
4. Standardize badge component styling:
   - Classification: small (blue), large (purple)
   - Mode: automatic (green), manual (amber/orange)
   - Status: success (green check), failed (red X)
5. Apply consistent badge styling in both SimpleConversionHistoryCard (T05) and SimpleConversionSummaryCard (T07)
6. Improve empty state:
   - Friendly message: "No past conversions yet"
   - Optional: illustration or icon
   - Optional: hint text about completing first conversion
7. Improve loading skeleton to match card layout
8. Add error boundary component wrapping history section:
   - Catch rendering errors in history components
   - Display fallback UI with error message
   - Prevent entire page crash if history fails
9. Add smooth transitions: fade-in for list, slide-in for cards (optional CSS transitions)
10. Test all state transitions: loading -> list, loading -> empty, loading -> error

- Patterns to apply:
  - **Error Boundaries** - React error boundary to isolate failures
  - **Conditional Rendering** - Show/hide based on conversion state
  - **TailwindCSS Transitions** - Simple fade/slide effects
  - **Consistent Design Tokens** - Standardize colors via Tailwind theme or CSS variables

- Deviations (if any):
  - None - follows React and styling best practices

## Unit tests (required)
- Add tests for:
  - History section hidden when conversion in progress
  - History section hidden when results displayed inline
  - History section shown when form is idle
  - History list refreshes after new conversion completes
  - Refresh fetch triggers after conversion status update
  - Badge colors consistent between history list and detail page
  - Classification badges render correct color (small = blue, large = purple)
  - Mode badges render correct color (automatic = green, manual = amber)
  - Status indicators render correct color/icon (success = green check, failed = red X)
  - Empty state renders when no conversions exist
  - Error boundary catches rendering errors in history section
  - Error boundary displays fallback UI
  - Loading skeleton structure matches final card layout
- Suggested locations:
  - vulcanlab_ui/src/app/simple-conversion/__tests__/page.test.tsx (extend)
  - vulcanlab_ui/src/components/simple-conversion/__tests__/badge-consistency.test.tsx (new)
- Mocking/fakes needed:
  - Mock conversion state transitions
  - Mock fetch for history refresh
  - Simulate rendering error for error boundary test

## Acceptance criteria (checklist)
- [ ] History section hidden during active conversion processing
- [ ] History section hidden when inline results displayed
- [ ] History section visible when form is idle (no active conversion)
- [ ] History list auto-refreshes after completing new conversion
- [ ] New conversion appears at top of history list after completion
- [ ] Classification badges use consistent colors: blue (small), purple (large)
- [ ] Mode badges use consistent colors: green (automatic), amber (manual)
- [ ] Status indicators use consistent styling: green check (success), red X (failed)
- [ ] Badge styling identical between history list and detail page
- [ ] Empty state message clear and friendly
- [ ] Loading skeleton layout matches final card layout
- [ ] Error boundary prevents page crash if history rendering fails
- [ ] Error boundary shows user-friendly fallback message
- [ ] Smooth transitions between loading, empty, list, and error states
- [ ] Unit tests cover state transitions, refresh logic, and badge consistency

## Manual verification
- Steps:
  1. Navigate to /simple-conversion page with no past conversions
  2. Verify empty state shows friendly message
  3. Submit a new conversion (automatic mode)
  4. Verify history section hides during processing
  5. Wait for conversion to complete
  6. Verify results display inline
  7. Scroll down - verify history section still hidden while results shown
  8. Click "Start New Conversion" or refresh page
  9. Verify history section now shows with new conversion at top
  10. Verify new conversion has correct badges (classification, mode, status)
  11. Submit another conversion (manual mode)
  12. Verify history section hides (redirect to manual workflow)
  13. Return to /simple-conversion
  14. Verify history list includes both conversions
  15. Click first conversion, check badge colors on detail page
  16. Return to list, verify badge colors match between list and detail
  17. Simulate error by modifying component to throw during render
  18. Verify error boundary catches and shows fallback UI
- Expected results:
  - History section visibility logic works correctly
  - New conversions appear in list after completion
  - Badge colors are consistent and visually distinct
  - Transitions are smooth without jarring layout shifts
  - Error boundary prevents catastrophic failures
  - Empty and loading states are polished

## Notes
- History section visibility depends on understanding Simple Conversion page state management - review existing code
- Auto-refresh after conversion: may need to pass callback from parent or use event/pub-sub pattern
- Consider using React transition libraries (framer-motion) for smooth animations, but CSS transitions sufficient for MVP
- Badge color standardization: define colors in Tailwind config or use existing theme colors for consistency
- Empty state illustration optional but improves UX - check if design system has standard illustrations
- Error boundary should log errors to console or monitoring service for debugging
- Loading skeleton: use Shadcn Skeleton component if available, or simple animated div with gradient
- If conversion results are displayed in a modal/overlay instead of inline, adjust visibility logic accordingly
- Consider adding a manual "Refresh" button in error state as escape hatch
- Test with various conversion counts: 0, 1, 5, 20+ to ensure layout scales well
