# Ticket: collections-feature.T05 - Integration on Search and RAG Pages

## Source

* Spec: documentation/work/collections-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Add to Collection" buttons on search result page, RAG result page, and RAG query list page
* Wire up AddToCollectionModal component from T04 on all three pages
* Enable end-to-end workflow: discover content -> add to collection -> view in collection
* Complete the collections feature with full integration

## Scope

### In scope

* Add "Add to Collection" button on search result page (/search/result/[work_id]/[start_line]/[end_line])
* Add "Add to Collection" button on RAG result page (/rag/[id]/results/[resultId])
* Add "Add to Collection" button on RAG query list page (/rag) in table actions
* Wire up AddToCollectionModal with correct itemType and itemLink for each page
* Handle button placement and styling consistently across pages
* Verify end-to-end workflow works

### Out of scope

* Changes to modal component (completed in T04)
* Changes to collection pages (completed in T02, T03)
* Bulk add operations (add one item at a time)

## Dependencies

* Depends on: T01, T02, T03, T04
* Unblocks: none (final ticket)

## Implementation plan

* Integrate on search result page:
  * Open vulcanlab_ui/src/app/search/result/[work_id]/[start_line]/[end_line]/page.tsx
  * Import useAddToCollection hook from T04
  * Add "Add to Collection" button near page header or in action toolbar
  * On click, open modal with itemType="excerpt" and itemLink constructed from params
  * itemLink format: /search/result/{work_id}/{start_line}/{end_line}
  * Show success toast on successful add
  * No need to refresh page after add (user can navigate to collection to see item)
* Integrate on RAG result page:
  * Open vulcanlab_ui/src/app/rag/[id]/results/[resultId]/page.tsx
  * Import useAddToCollection hook
  * Add "Add to Collection" button near page header or in action toolbar
  * On click, open modal with itemType="research_result" and itemLink from params
  * itemLink format: /rag/{id}/results/{resultId}
  * Show success toast on successful add
* Integrate on RAG query list page:
  * Open vulcanlab_ui/src/app/rag/page.tsx
  * Import useAddToCollection hook
  * Add "Add to Collection" button in actions column of DataTable for each query
  * Use icon button or small button to fit in table cell
  * On click, open modal with itemType="research_query" and itemLink from query id
  * itemLink format: /rag/{id}
  * Show success toast on successful add
  * Consider placing button next to existing action buttons (Embed, Retrieve, etc.)
* Ensure consistent styling:
  * Use same button variant across all pages (e.g., outline variant)
  * Use consistent icon (e.g., Plus or FolderPlus from lucide-react)
  * Ensure button is accessible with proper aria-label
  * Ensure button works in both light and dark themes
* Patterns to apply:
  * Component composition: Reuse AddToCollectionModal via hook (Section 4.2)
  * Naming conventions: camelCase for variables, PascalCase for components (Section 7)
  * Theme awareness: Semantic Tailwind classes (Section 4.2)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Button renders on search result page with correct props
  * Button renders on RAG result page with correct props
  * Button renders on RAG query list page in table actions
  * Button click opens modal with correct itemType and itemLink
  * itemLink construction is correct for each page type
  * Success callback shows toast and does not break page state
* Suggested locations:
  * tests/unit/test_search_result_collections_integration.tsx
  * tests/unit/test_rag_result_collections_integration.tsx
  * tests/unit/test_rag_list_collections_integration.tsx
* Mocking/fakes needed:
  * Mock useAddToCollection hook
  * Mock router params
  * Mock toast notifications

## Acceptance criteria (checklist)

* [ ] "Add to Collection" button added to search result page
* [ ] "Add to Collection" button added to RAG result page
* [ ] "Add to Collection" button added to RAG query list page (in actions column)
* [ ] Button on search result page opens modal with itemType="excerpt"
* [ ] Button on RAG result page opens modal with itemType="research_result"
* [ ] Button on RAG query list page opens modal with itemType="research_query"
* [ ] itemLink constructed correctly for each page type
* [ ] Modal integration works on all three pages
* [ ] Success toast appears after adding item
* [ ] Buttons styled consistently across all pages
* [ ] Buttons accessible with proper aria-labels
* [ ] Buttons work in light and dark themes
* [ ] Unit tests pass for all three integrations
* [ ] End-to-end workflow verified manually

## Manual verification

* Steps:
  * Navigate to /search/result/1/100/200 (use existing work/chunk)
  * Click "Add to Collection" button
  * Verify modal opens with searchable collection list
  * Select a collection and add item
  * Verify success toast appears
  * Navigate to /collections/{id} and verify excerpt appears in items table
  * Navigate to /rag page
  * Click "Add to Collection" button on a query row
  * Verify modal opens
  * Create new collection inline and add item
  * Navigate to new collection detail page
  * Verify research query item appears
  * Navigate to /rag/{id}/results/{resultId} (use existing result)
  * Click "Add to Collection" button
  * Add to existing collection
  * Navigate to collection detail page
  * Verify research result item appears
  * For excerpt item, verify biblio metadata displays correctly
  * Click on each item link to verify navigation works
* Expected results:
  * All three pages have working "Add to Collection" buttons
  * Modal integration works seamlessly
  * Items appear in collection detail page with correct metadata
  * Links navigate correctly back to source pages
  * End-to-end workflow is smooth and intuitive

## Notes

* Requirements covered: R3 (add from three locations), R4 (modal integration)
* This completes the vertical slice of the entire collections feature
* Consider icon options: Plus, FolderPlus, Bookmark, Star (Plus or FolderPlus recommended for clarity)
* Button placement on search/RAG result pages: near header or in a sticky action bar for easy access
* Button placement on RAG query list: in actions column, possibly as icon-only button to save space
* Ensure button does not interfere with existing actions on RAG page (Embed, Retrieve, Consolidate, etc.)
* Consider adding tooltip on hover: "Add to Collection" for icon-only buttons
* Success toast message can be: "Added to collection successfully" or "Added to {collection_name}"
* If adding fails (e.g., duplicate item), show appropriate error message from API
