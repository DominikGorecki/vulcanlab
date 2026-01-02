# Ticket: rag-query-manual-result-model-tracking.T04 - Display Model Name in Results List Page

## Source

* Spec: documentation/work/rag-query-manual-result-model-tracking.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Model" column to results list table on `/rag/[id]/results` page
* Display model name for each result (show "Unspecified" for NULL model_id)
* Complete vertical slice: users can view model information for all results in list view

## Scope

### In scope

* Modify `vulcanlab_ui/src/app/rag/[id]/results/page.tsx`:
  * Add "Model" column to DataTable or results table
  * Display model_name from API response
  * Show "Unspecified" when model_name is NULL or undefined
  * Ensure table remains sortable and responsive

### Out of scope

* Backend API changes (covered in T02)
* Result detail page changes (covered in T05)
* Model filtering or search functionality
* Model editing or deletion

## Dependencies

* Depends on: T02 (API must return model_name in results list response)
* Unblocks: none (T05 is independent)

## Implementation plan

1. Read `vulcanlab_ui/src/app/rag/[id]/results/page.tsx` to understand current table structure:
   * Identify how results are fetched and displayed
   * Identify table component used (likely DataTable or custom table)
   * Check current columns defined

2. Update table columns definition:
   * Add new column definition for "Model":
     ```tsx
     {
       header: "Model",
       accessorKey: "model_name",
       cell: ({ row }) => {
         const modelName = row.original.model_name;
         return modelName || "Unspecified";
       }
     }
     ```
   * Position "Model" column logically (suggest: after "Response Preview", before "Created At")

3. Verify API response includes model_name:
   * Ensure fetch function requests results from API
   * Check response structure matches spec (results array with model_name field)
   * API already modified in T02 to return model_name (denormalized)

4. Style model name display:
   * Use consistent text styling (e.g., `text-sm text-muted-foreground`)
   * Consider using a badge or tag for model names for visual distinction (optional)
   * Ensure "Unspecified" is visually distinct (e.g., italic or muted)

5. Test responsiveness:
   * Ensure table remains responsive on mobile/tablet
   * Model column should not cause horizontal overflow
   * Consider truncating very long model names with ellipsis

6. Update TypeScript types:
   * Add `model_name?: string` to result interface/type if not already present
   * Ensure type safety for model_name field

* Patterns to apply:
  * **Frontend Component Patterns**: Use existing DataTable component or consistent table patterns
  * **Theme Awareness**: Use Tailwind semantic classes (e.g., text-foreground, text-muted-foreground)
  * **Component Composition**: Reuse existing table components, do not reinvent

* Deviations (if any):
  * None - follows established frontend patterns

## Unit tests (required)

* Add tests for:
  * Results table displays "Model" column header
  * Result with model_name shows model name in Model column
  * Result with NULL model_name shows "Unspecified"
  * Table remains sortable (if sorting is implemented)
  * Table is responsive and does not overflow

* Suggested locations:
  * `vulcanlab_ui/src/app/rag/[id]/results/__tests__/page.test.tsx`
  * Or rely on manual verification (per patterns.md, unit tests for frontend are optional)

* Mocking/fakes needed:
  * Mock fetch API to return results with model_name field
  * Mock results data with various model names and NULL values

## Acceptance criteria (checklist)

* [ ] Results list table includes "Model" column
* [ ] Model column displays model_name from API response
* [ ] NULL or undefined model_name displays as "Unspecified"
* [ ] Column is positioned logically in table (e.g., after Response, before Created At)
* [ ] Model names are styled consistently with theme
* [ ] "Unspecified" is visually distinct from actual model names
* [ ] Table remains responsive on mobile/tablet
* [ ] Long model names are truncated or wrapped appropriately
* [ ] TypeScript types include model_name field
* [ ] No runtime errors or type errors

## Manual verification

* Steps:
  1. Create multiple results for a query with different models:
     - One with automatic generation (model from config)
     - One with manual paste using existing model
     - One with manual paste using new model
     - One with manual paste with no model selected (NULL)
  2. Navigate to `/rag/{id}/results` page
  3. Verify "Model" column appears in table
  4. Verify each result displays correct model name
  5. Verify result with NULL model_id shows "Unspecified"
  6. Check table on mobile/tablet viewport
  7. Verify table is sortable (if sorting is implemented)
  8. Test in both light and dark mode

* Expected results:
  * Model column is visible and shows correct data
  * Model names match what was selected/created during result submission
  * NULL model_id shows "Unspecified" consistently
  * Table remains usable and responsive
  * UI works in both themes

## Notes

* Requirements covered: R9 (partial - list page only), R10 (partial - list page only)
* This is a simple vertical slice: adds model visibility to results list
* API already modified in T02 to include model_name in response (denormalized to avoid N+1 queries)
* Consider using a StatusBadge component if it exists for displaying model names
* "Unspecified" should be easily distinguishable from real model names (suggest italic or muted color)
* Long model names (e.g., "claude-3-opus-20240229") should be truncated with ellipsis to prevent layout issues
* Model column should not be the primary sort column (Created At is likely default)
* Optional enhancement: Add tooltip on hover to show full model name if truncated (out of scope for this ticket)
* If using DataTable component from Shadcn, follow existing column definition pattern
