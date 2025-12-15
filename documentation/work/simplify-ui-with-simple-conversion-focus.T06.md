# Ticket: simplify-ui-with-simple-conversion-focus.T06 - Frontend: Conditional Navigation Visibility

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Conditionally render Conversion, Sanitization, and Chunking nav items based on Advanced Conversion toggle state
- Fetch toggle state on app initialization and share across navigation components
- Keep Simple Conversion, Corpus, Vectorization, RAG, Settings always visible
- Allow direct URL access to hidden pages (no route blocking)

## Scope
### In scope
- Fetch advanced_mode_enabled from /api/conversion/settings on app mount
- Store toggle state in React Context or global state (Zustand/similar)
- Update NavBar component to conditionally render advanced workflow nav items
- Hide Conversion, Sanitization, Chunking when toggle is OFF
- Show all nav items when toggle is ON
- Navigation state updates immediately when toggle changes in Settings
- No route blocking - direct URL access still works

### Out of scope
- Implementing new navigation structure or routes
- Changing navigation styling or layout
- Adding authentication or permissions
- Route guards or redirects
- Settings toggle implementation (T04)

## Dependencies
- Depends on: T02 (backend API), T04 (settings toggle that changes state)
- Unblocks: none (completes vertical slice for toggle feature)

## Implementation plan
1. Locate NavBar component (likely vulcanlab_ui/src/components/NavBar.tsx or Navigation.tsx)
2. Choose state management approach (React Context recommended for simplicity):
   - Create ConversionSettingsContext in vulcanlab_ui/src/contexts/conversion-settings.tsx
   - Or use existing global state solution if present (check for Zustand, Redux, etc.)
3. Create context provider with:
   - State: advanced_mode_enabled (boolean, default false)
   - Loading state for initial fetch
   - Fetch function that calls GET /api/conversion/settings
   - Update function to change local state (called from Settings page)
4. Wrap app root with ConversionSettingsProvider (in layout.tsx or _app.tsx)
5. Add useEffect in provider to fetch settings on mount
6. Update NavBar component to consume context
7. Identify nav items for Conversion, Sanitization, Chunking (by route or label)
8. Conditionally render these items: show only if advanced_mode_enabled === true
9. Keep all other nav items unconditionally rendered
10. Ensure Settings page toggle update triggers context state update (via update function)
11. Test that navigation updates immediately when toggle changes

- Patterns to apply:
  - **React Context API** - Global state for settings without prop drilling
  - **Client Components** - Context provider and NavBar need "use client"
  - **Fetch on Mount** - useEffect in provider to load initial state
  - **Conditional Rendering** - Simple boolean check for nav item visibility

- Deviations (if any):
  - None - follows React best practices for global state

## Unit tests (required)
- Add tests for:
  - Context provider fetches conversion settings on mount
  - Context provides advanced_mode_enabled value to consumers
  - NavBar hides Conversion, Sanitization, Chunking when advanced_mode_enabled is false
  - NavBar shows all nav items when advanced_mode_enabled is true
  - Simple Conversion, Corpus, Vectorization, RAG, Settings always visible regardless of toggle
  - Context state updates when update function called
  - NavBar re-renders when context state changes
  - Loading state handled gracefully (default to hidden during load)
  - Fetch failure defaults to hidden state (advanced_mode_enabled = false)
- Suggested locations:
  - vulcanlab_ui/src/contexts/__tests__/conversion-settings.test.tsx
  - vulcanlab_ui/src/components/__tests__/NavBar.test.tsx (extend existing or create)
- Mocking/fakes needed:
  - Mock fetch/API client for conversion settings endpoint
  - Mock context provider for NavBar tests
  - Mock router from next/navigation if needed

## Acceptance criteria (checklist)
- [ ] Conversion settings context provider created and wraps app
- [ ] Context fetches advanced_mode_enabled from API on app mount
- [ ] NavBar consumes context to get toggle state
- [ ] Conversion nav item hidden when toggle OFF, visible when ON
- [ ] Sanitization nav item hidden when toggle OFF, visible when ON
- [ ] Chunking nav item hidden when toggle OFF, visible when ON
- [ ] Simple Conversion, Corpus, Vectorization, RAG, Settings always visible
- [ ] Changing toggle in Settings immediately updates navigation (no refresh needed)
- [ ] Direct URL navigation to /conv works even when nav item hidden
- [ ] Default state is hidden (toggle OFF) during initial load
- [ ] Fetch failure defaults to hidden state without breaking app
- [ ] Unit tests cover visibility logic and state management

## Manual verification
- Steps:
  1. Start app with fresh database (default toggle OFF)
  2. Verify Conversion, Sanitization, Chunking not visible in nav
  3. Verify Simple Conversion, Corpus, Vectorization, RAG, Settings visible
  4. Navigate to Settings > Conversion and turn toggle ON
  5. Verify Conversion, Sanitization, Chunking appear in nav immediately
  6. Navigate to /conv directly via URL
  7. Verify page loads (not blocked)
  8. Return to Settings and turn toggle OFF
  9. Verify advanced nav items disappear from nav immediately
  10. Refresh page
  11. Verify nav state persists (items still hidden)
  12. Simulate network error on initial fetch (block request in devtools)
  13. Verify nav defaults to hidden state without crashing
- Expected results:
  - Navigation visibility matches toggle state instantly
  - Direct URL access works for hidden pages
  - No page refresh required when toggle changes
  - Default state is simplified (hidden) for new users
  - No console errors or visual glitches

## Notes
- React Context is recommended over prop drilling or local storage for consistency across tabs/windows
- If using Next.js App Router with Server Components, ensure context provider is in a Client Component
- Consider memoizing context value to prevent unnecessary re-renders
- NavBar should check for loading state and default to hidden during fetch (simplify by default)
- The update function in context allows Settings page (T04) to trigger nav update without full page refresh
- Consider adding error boundary around NavBar to catch context access errors
- Route list for advanced items: /conv (Conversion), /sanitize (Sanitization), /chunk (Chunking) - verify actual routes
- Next.js middleware or route guards are NOT used - we only control UI visibility, not access
- Consider adding data-testid attributes to nav items for easier testing
