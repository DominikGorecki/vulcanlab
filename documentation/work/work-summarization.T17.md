# Ticket: work-summarization.T17 - Corpus Page Line Highlight Support

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enhance Corpus work detail page to support line highlighting via URL parameter
* Enable clickable line references from summary pages to highlight source content
* Scroll to and visually highlight specified line ranges

## Phase

* Frontend

## Scope

### In scope

* Parse ?highlight=start-end URL parameter in Corpus work detail page
* Scroll MarkdownEditor to highlighted line on page load
* Visual highlight styling for specified line range
* Handle edge cases (invalid ranges, out-of-bounds)
* Clear highlight when navigating away or clicking elsewhere

### Out of scope

* Summary detail page (T15 - already links to this)
* Multi-range highlighting (single range only for now)

## Dependencies

* Depends on: T15 (generates the highlight links)
* Unblocks: none (enables full line reference flow)

## Implementation plan

1. Update vulcanlab_ui/src/app/corpus/[id]/page.tsx
2. Parse URL search params:
   - Use useSearchParams hook
   - Parse ?highlight=start-end format
   - Validate: start and end are positive integers, start <= end
3. Pass highlight range to MarkdownEditor:
   - Add highlightLines prop: { start: number, end: number } | null
4. Update MarkdownEditor component (or create wrapper):
   - Accept highlightLines prop
   - On mount/update: scroll to start line
   - Apply visual highlight to line range
5. Implement highlight styling:
   - Background color for highlighted lines (theme-aware)
   - Consider pulse animation on initial highlight
   - Use CSS class: .line-highlight
6. Implement scroll behavior:
   - On highlightLines change, scroll line into view
   - Position highlighted section in upper portion of viewport
   - Smooth scroll animation
7. Handle clear highlight:
   - Click outside highlighted area clears highlight
   - Or provide "Clear highlight" button
   - Update URL to remove ?highlight param
8. Handle invalid ranges:
   - Line numbers out of document bounds: highlight what's valid
   - Invalid format: ignore and show no highlight
   - Log warning for debugging
* Patterns to apply:
  * Theme-aware styling for highlight colors
  * Smooth scroll UX
  * URL parameter handling with useSearchParams
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Page parses ?highlight=10-20 parameter correctly
  * Invalid highlight param (non-numeric) is ignored
  * Invalid range (start > end) is ignored
  * highlightLines prop passed to MarkdownEditor
  * Highlight styling applied to correct lines
  * Scroll triggered on highlight
  * Clear highlight updates URL
  * Out-of-bounds range handled gracefully
* Suggested locations:
  * vulcanlab_ui/src/app/corpus/[id]/__tests__/page.test.tsx (update)
  * vulcanlab_ui/src/components/__tests__/markdown-editor-highlight.test.tsx
* Mocking/fakes needed:
  * Mock useSearchParams
  * Mock scrollIntoView

## Acceptance criteria (checklist)

* [ ] ?highlight=start-end parameter parsed from URL
* [ ] Specified lines visually highlighted
* [ ] Page scrolls to highlighted lines on load
* [ ] Highlight styling is theme-aware (dark/light)
* [ ] Invalid parameters handled gracefully
* [ ] Clear highlight functionality available
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to /corpus/[id]?highlight=10-15
  2. Verify lines 10-15 are highlighted
  3. Verify page scrolled to show highlighted section
  4. Clear highlight and verify styling removed
  5. Test with invalid param: ?highlight=abc
  6. Verify no error, no highlight
* Expected results:
  * Line highlighting works correctly
  * Navigation from summary page shows correct source

## Notes

* Requirements covered: R11 (line references clickable and navigate to source)
* Highlight color suggestions:
  * Light mode: bg-yellow-100 or bg-amber-100
  * Dark mode: bg-yellow-900/30 or bg-amber-900/30
* MarkdownEditor may need internal changes to support line-level styling
* If MarkdownEditor uses CodeMirror or similar, check for highlight APIs
* Consider storing highlight in URL for shareable links
