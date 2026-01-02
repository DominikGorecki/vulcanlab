# Ticket: rag-query-manual-result-model-tracking.T05 - Display Model Name in Result Detail Page

## Source

* Spec: documentation/work/rag-query-manual-result-model-tracking.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add model name display to result detail page
* Show model metadata in a consistent location (e.g., header or metadata section)
* Complete vertical slice: users can view model information on individual result detail page

## Scope

### In scope

* Modify `vulcanlab_ui/src/app/rag/[id]/results/[resultId]/page.tsx`:
  * Display model_name from API response
  * Add model info to metadata section or header
  * Show "Unspecified" when model_name is NULL or undefined
  * Style consistently with existing detail page layout

### Out of scope

* Backend API changes (covered in T02)
* Results list page changes (covered in T04)
* Model editing functionality
* Model history or versioning

## Dependencies

* Depends on: T02 (API must return model_name in result detail response)
* Unblocks: none

## Implementation plan

1. Read `vulcanlab_ui/src/app/rag/[id]/results/[resultId]/page.tsx` to understand current layout:
   * Identify where result metadata is displayed (likely in header or info card)
   * Check how other metadata fields are displayed (Created At, Query ID, etc.)
   * Identify data fetching pattern

2. Add model_name to result detail display:
   * If using a metadata card/section, add new field:
     ```tsx
     <div className="flex items-center gap-2">
       <span className="text-sm font-medium">Model:</span>
       <span className="text-sm text-muted-foreground">
         {result.model_name || "Unspecified"}
       </span>
     </div>
     ```
   * Position model info logically (suggest: near Created At or other metadata)

3. Style model name display:
   * Use consistent typography with other metadata fields
   * Consider using a badge or tag for visual distinction (optional)
   * Ensure "Unspecified" is visually distinct (e.g., italic or muted)

4. Update TypeScript types:
   * Add `model_name?: string` to result detail interface/type if not already present
   * Ensure type safety

5. Consider adding icon for visual clarity:
   * Optional: Add a small icon next to "Model:" label (e.g., `<Cpu className="h-4 w-4" />` from lucide-react)

* Patterns to apply:
  * **Frontend Component Patterns**: Use existing Card, metadata display patterns from detail pages
  * **Theme Awareness**: Use Tailwind semantic classes for dark/light mode
  * **Component Composition**: Follow existing detail page layout patterns

* Deviations (if any):
  * None - follows established frontend patterns

## Unit tests (required)

* Add tests for:
  * Result detail page displays model name when present
  * Result detail page displays "Unspecified" when model_name is NULL
  * Model info is positioned in metadata section
  * Styling is consistent with other metadata fields

* Suggested locations:
  * `vulcanlab_ui/src/app/rag/[id]/results/[resultId]/__tests__/page.test.tsx`
  * Or rely on manual verification (per patterns.md)

* Mocking/fakes needed:
  * Mock fetch API to return result detail with model_name field
  * Mock result data with model name and NULL model name

## Acceptance criteria (checklist)

* [ ] Result detail page displays "Model:" label
* [ ] Model name is shown from API response
* [ ] NULL or undefined model_name displays as "Unspecified"
* [ ] Model info is positioned in metadata section (consistent with other fields)
* [ ] Styling matches existing metadata fields
* [ ] "Unspecified" is visually distinct from actual model names
* [ ] TypeScript types include model_name field
* [ ] No runtime errors or type errors
* [ ] UI works in both light and dark mode

## Manual verification

* Steps:
  1. Create or select a result with a known model name
  2. Navigate to `/rag/{id}/results/{resultId}` detail page
  3. Verify "Model:" label appears in metadata section
  4. Verify model name is displayed correctly
  5. Navigate to a result with NULL model_id
  6. Verify "Unspecified" is shown
  7. Test in both light and dark mode
  8. Verify layout is consistent with other metadata fields
  9. Check on mobile/tablet viewport

* Expected results:
  * Model name is visible in metadata section
  * Correct model name is displayed for each result
  * NULL model_id shows "Unspecified"
  * Layout is consistent and responsive
  * UI works in both themes

## Notes

* Requirements covered: R10 (partial - detail page only)
* This is a simple vertical slice: completes model visibility in detail view
* API already modified in T02 to include model_name in response
* Metadata section is likely in a Card component or similar
* Consider grouping model info with other result metadata (Created At, Updated At, etc.)
* "Unspecified" should match the styling used in T04 (results list) for consistency
* Optional enhancement: Add tooltip explaining what "Unspecified" means (e.g., "No model information recorded") - out of scope
* If detail page has a header with badges/tags, consider adding model as a badge
* Model name should be easily scannable for users comparing results
