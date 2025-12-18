# Ticket: simplify-ui-with-simple-conversion-focus.T04 - Frontend: Settings Advanced Conversion Toggle

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add "Advanced Conversion" toggle switch to Settings > Conversion tab
- Fetch toggle state from backend API on load
- Persist toggle changes via PUT request to backend
- Provide foundation for conditional navigation (used in T06)

## Scope
### In scope
- Add toggle UI component to Settings Conversion tab page
- Fetch advanced_mode_enabled from GET /api/conversion/settings on mount
- Update advanced_mode_enabled via PUT /api/conversion/settings on change
- Display loading state while fetching/saving
- Show success/error messages for save operations
- Toggle description: "Show advanced workflow pages (Conversion, Sanitization, Chunking) in navigation"
- Use existing UI components from vulcanlab_ui/src/components/ui/ (Switch, Label, Card)

### Out of scope
- Navigation visibility changes (handled in T06)
- Global state management setup (simple local state for now)
- Other settings fields modifications
- Validation beyond boolean type

## Dependencies
- Depends on: T02 (backend API for toggle state)
- Unblocks: T06 (navigation needs to read toggle state)

## Implementation plan
1. Locate Settings Conversion tab component (likely vulcanlab_ui/src/app/settings/conversion/page.tsx or similar)
2. Add "use client" directive if not already present (need interactivity)
3. Import Switch component from @/components/ui/switch (Shadcn/Radix)
4. Add state for advanced_mode_enabled (useState hook)
5. Add loading and error states (useState hooks)
6. Create useEffect hook to fetch conversion settings on mount
7. Parse response to extract advanced_mode_enabled field
8. Create handleToggleChange function that:
   - Sets loading state
   - Calls PUT /api/conversion/settings with updated value
   - Updates local state on success
   - Shows error message on failure
9. Render Switch component with Label and description text
10. Show loading spinner or skeleton while fetching initial state
11. Disable toggle during save operation
12. Add error message display using existing alert/toast component

- Patterns to apply:
  - **Client Components** - Use "use client" for interactive form elements
  - **TailwindCSS** - Use utility classes for spacing, layout, typography
  - **Shadcn/Radix Components** - Reuse existing UI components (Switch, Label, Card)
  - **Fetch Wrappers** - Use typed fetch or API client if available in codebase

- Deviations (if any):
  - None - follows established Next.js and Shadcn patterns

## Unit tests (required)
- Add tests for:
  - Component renders with toggle in OFF position by default (before API response)
  - Component fetches conversion settings on mount
  - Toggle displays ON position when API returns advanced_mode_enabled: true
  - Toggle displays OFF position when API returns advanced_mode_enabled: false
  - Clicking toggle calls PUT endpoint with updated value
  - Toggle disabled during save operation
  - Error message displayed when save fails
  - Success state shown after successful save
  - Loading state shown while fetching initial data
- Suggested locations:
  - vulcanlab_ui/src/app/settings/conversion/__tests__/page.test.tsx (or similar)
- Mocking/fakes needed:
  - Mock fetch/API client for GET and PUT requests
  - Mock responses: success, failure, validation error
  - Mock useState and useEffect if needed for testing hooks

## Acceptance criteria (checklist)
- [ ] Settings > Conversion tab includes "Advanced Conversion" toggle switch
- [ ] Toggle label and description text clearly explain purpose
- [ ] Toggle fetches initial state from GET /api/conversion/settings on page load
- [ ] Toggle state updates when user clicks switch
- [ ] PUT request sent to backend when toggle changes
- [ ] Loading spinner shown during save operation
- [ ] Toggle disabled during save to prevent race conditions
- [ ] Success message or visual feedback after successful save
- [ ] Error message displayed if save fails
- [ ] Toggle state persists across page refreshes (via backend persistence)
- [ ] Unit tests cover rendering, fetching, updating, and error states

## Manual verification
- Steps:
  1. Navigate to Settings > Conversion tab
  2. Verify "Advanced Conversion" toggle is visible with description
  3. Check initial state matches backend value (default OFF)
  4. Click toggle to turn ON
  5. Verify loading state shown briefly
  6. Verify success message or visual feedback
  7. Refresh page
  8. Verify toggle remains ON (persisted)
  9. Open browser network tab and toggle switch
  10. Verify PUT request sent to /api/conversion/settings with correct payload
  11. Simulate network error (offline mode) and toggle
  12. Verify error message displayed
- Expected results:
  - Toggle UI matches existing settings page style
  - State persists after refresh
  - Network requests visible in devtools
  - Error handling prevents silent failures
  - No console errors

## Notes
- Check if Settings page already has conversion settings (token threshold) - add toggle to same section
- Use consistent styling with other toggle switches in settings if they exist
- Consider adding confirmation dialog if user has unsaved changes (if applicable)
- The description text should clearly indicate this is a UI visibility preference, not a functional change
- Default state should be OFF (hidden) for new users to simplify initial experience
- This ticket focuses on the toggle itself; navigation changes happen in T06
- Consider using React Hook Form if other settings use it for consistency
