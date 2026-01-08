# Ticket: collections-feature.T04 - Add to Collection Modal Component

## Source

* Spec: documentation/work/collections-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create reusable "Add to Collection" modal component
* Support selecting existing collection or creating new collection inline
* Implement search/filter and pagination for large numbers of collections
* Prepare component for integration across multiple pages (T05)

## Scope

### In scope

* AddToCollectionModal component in vulcanlab_ui/src/components/collections/
* Search/filter input for collections by name
* Pagination for collections list within modal
* Inline "Create New Collection" form within modal
* Props-based API: onAdd callback, itemType, itemLink props
* Loading and error states
* Success/error toast notifications
* Unit tests for modal component logic (not React testing)

### Out of scope

* Integration on search/RAG pages (T05)
* Metadata enrichment (already in T03)
* Item note editing (notes added later on detail page, not in modal per user requirements)

## Dependencies

* Depends on: T01, T02, T03
* Unblocks: T05

## Implementation plan

* Create modal component:
  * Create vulcanlab_ui/src/components/collections/AddToCollectionModal.tsx
  * Use Radix Dialog primitive for modal
  * Accept props: isOpen, onClose, itemType (string), itemLink (string), onSuccess (callback)
  * Component manages its own state: searchQuery, currentPage, selectedCollectionId, showCreateForm
* Implement collections list in modal:
  * Fetch collections via GET /api/v1/collections with search query param
  * Display collections as selectable list (radio buttons or clickable cards)
  * Show collection name, description (truncated), item count, tags
  * Implement search input that filters collections by name
  * Implement pagination with page size of 10, show page controls
  * Use debounced search (300ms) to reduce API calls
  * Use useCallback for fetch function to avoid infinite loops
* Implement inline create form:
  * Add "Create New Collection" button at top of modal
  * Toggle to show create form inline
  * Form fields: name (required), description (optional), tags (optional)
  * Use react-hook-form for form state
  * Submit calls POST /api/v1/collections
  * On success, auto-select newly created collection and switch back to list view
* Implement add to collection action:
  * "Add" button at bottom of modal (disabled when no collection selected)
  * On click, call POST /api/v1/collections/{id}/items with itemType, itemLink
  * Note field left empty (user adds note later on detail page per requirements)
  * Order defaults to 0 (user sets order later on detail page)
  * Show loading spinner during API call
  * On success, show success toast and call onSuccess callback
  * On error, show error toast with message
  * Close modal on success
* Add helper hook:
  * Create useAddToCollection hook in vulcanlab_ui/src/hooks/
  * Hook returns: isOpen, openModal, closeModal, AddToCollectionModal component
  * Simplifies usage on pages: const {openModal, AddToCollectionModal} = useAddToCollection()
* Patterns to apply:
  * Component composition: Props-in events-out (Section 4.2)
  * Page lifecycle patterns: Loading/error states (Section 4.1)
  * Radix Dialog primitive for modal (Section 4.1)
  * useCallback for fetch functions (Section 4.1)
  * Theme awareness: Use semantic Tailwind classes (Section 4.2)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Modal opens and closes correctly
  * Collections list fetches and displays correctly
  * Search input filters collections with debouncing
  * Pagination controls navigate between pages
  * Create form validation requires name field
  * Create form submission creates collection and auto-selects it
  * Add action calls API with correct itemType and itemLink
  * Add action shows success toast and closes modal on success
  * Add action shows error toast on failure
  * Modal handles empty collections list (empty state)
  * Modal handles API errors gracefully
* Suggested locations:
  * tests/unit/test_add_to_collection_modal.tsx (if React testing is set up)
  * Otherwise, test logic functions separately in tests/unit/test_collection_modal_logic.ts
* Mocking/fakes needed:
  * Mock fetch calls to /api/v1/collections endpoints
  * Mock toast notification system

## Acceptance criteria (checklist)

* [ ] AddToCollectionModal component created as reusable component
* [ ] Modal accepts props: isOpen, onClose, itemType, itemLink, onSuccess
* [ ] Collections list displays with name, description, item count, tags
* [ ] Search input filters collections by name with 300ms debounce
* [ ] Pagination shows 10 collections per page with navigation controls
* [ ] "Create New Collection" button toggles inline form
* [ ] Create form has validation for required name field
* [ ] Create form submission creates collection and auto-selects it
* [ ] Radio buttons or clickable cards allow selecting a collection
* [ ] "Add" button is disabled when no collection selected
* [ ] Add action calls POST /api/v1/collections/{id}/items with correct data
* [ ] Success toast shows on successful add
* [ ] Error toast shows on failed add
* [ ] Modal closes on successful add
* [ ] onSuccess callback is called after successful add
* [ ] useAddToCollection hook simplifies modal usage
* [ ] Modal is theme-aware (works in light and dark mode)
* [ ] Empty state shows when no collections exist

## Manual verification

* Steps:
  * Create test page to render modal in isolation
  * Open modal with test props: itemType="excerpt", itemLink="/search/result/1/100/200"
  * Verify modal displays with collections list
  * Type in search input, verify filtering works
  * Create 20+ collections to test pagination
  * Navigate through pages, verify pagination works
  * Click "Create New Collection" button
  * Fill in form and submit
  * Verify new collection appears and is auto-selected
  * Select a collection
  * Click "Add" button
  * Verify success toast appears
  * Verify modal closes
  * Check database/API to confirm item was added to collection
  * Open modal again and trigger error (e.g., invalid link)
  * Verify error toast appears and modal stays open
  * Test search with no results, verify empty state
* Expected results:
  * All modal interactions work smoothly
  * Search and pagination perform well
  * Create and add actions work correctly
  * Error handling is graceful
  * Component is reusable and theme-aware

## Notes

* Requirements covered: R4 (modal allows selecting or creating collection), R12 (search/filter and pagination)
* Per user requirements (Q2: answer B), note field is NOT included in modal - users add notes later on detail page
* Order field also not in modal - defaults to 0, users set order later on detail page
* Modal should be small/medium size, not full screen
* Consider using virtual scrolling if pagination causes performance issues with 1000+ collections
* Search should be case-insensitive and match on name field only (description search is nice-to-have)
* useAddToCollection hook pattern similar to useModal pattern mentioned in patterns.md Section 4.2
* Consider adding keyboard shortcuts: Enter to add, Escape to close
* Auto-focus search input when modal opens for better UX
