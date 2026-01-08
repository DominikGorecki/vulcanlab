# Ticket: collections-feature.T02 - Collections List Page and API Endpoints

## Source

* Spec: documentation/work/collections-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement API endpoints for collection management (list, create, get, update, delete)
* Create collections list page at /collections with DataTable, sorting, filtering
* Enable users to create, view, and delete collections end-to-end
* First vertical slice: manually testable collection lifecycle

## Scope

### In scope

* FastAPI router for collections at src/vulcanlab_api/routers/collections.py
* Endpoints: GET /api/v1/collections, POST /api/v1/collections, GET /api/v1/collections/{id}, PATCH /api/v1/collections/{id}, DELETE /api/v1/collections/{id}
* Collections list page at vulcanlab_ui/src/app/collections/page.tsx
* DataTable with columns: name, description, tags, created_at, updated_at, item_count
* New collection form/modal with name, description, tags input
* Delete collection confirmation dialog
* Navigation link under "Research (RAG)" section
* Unit tests for API endpoints

### Out of scope

* Collection items management (T03)
* Add to Collection modal (T04)
* Integration with search/RAG pages (T05)
* Metadata enrichment endpoints (T03)

## Dependencies

* Depends on: T01
* Unblocks: T03, T04

## Implementation plan

* Create API router:
  * Create src/vulcanlab_api/routers/collections.py
  * Implement GET /collections with query params for pagination, sorting, search, tag filtering
  * Implement POST /collections with request body validation (name required, description/tags optional)
  * Implement GET /collections/{id} returning collection with item_count computed
  * Implement PATCH /collections/{id} for updating name, description, tags
  * Implement DELETE /collections/{id} with cascade to items
  * Use dependency injection for database session
  * Call core CRUD functions from T01
  * Add router to main.py with prefix="/api/v1/collections"
* Create frontend page:
  * Create vulcanlab_ui/src/app/collections/page.tsx as client component
  * Use usePageData hook with memoized fetch function
  * Implement PageLoadingState, PageErrorState, EmptyState states
  * Create PageHeader with title "Collections" and description
  * Add "New Collection" button in header that opens creation modal
  * Define DataTable columns: name (sortable), description (truncated), tags (badge list), created_at (sortable), updated_at (sortable), item_count (computed), actions
  * Add click handler on rows to navigate to /collections/{id}
  * Add delete button in actions column with ConfirmDialog
  * Use useMemo for columns definition
* Create collection form modal:
  * Create NewCollectionModal component using Radix Dialog
  * Use react-hook-form for form state management
  * Fields: name (required text input), description (textarea), tags (comma-separated input or multi-select)
  * Submit handler calls POST /api/v1/collections
  * On success, close modal and refetch collections list
  * Show error toast on failure
* Update navigation:
  * Add "Collections" link to navigation under "Research (RAG)" section
  * Path: /collections
* Patterns to apply:
  * API versioning: All routes prefixed with /api/v1 in main.py (Section 3.1)
  * Error handling: Raise HTTPException for errors, use global handlers (Section 3.2)
  * Session management: Use dependency injection for database session (Section 2)
  * Page lifecycle: usePageData hook with loading/error/data states (Section 4.1)
  * Component composition: Reusable modal, DataTable, PageHeader (Section 4.2)
  * Naming: snake_case Python, camelCase/PascalCase TypeScript (Section 7)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * API endpoint GET /collections returns paginated list with correct structure
  * API endpoint POST /collections creates collection with valid data
  * API endpoint POST /collections rejects invalid data (missing name)
  * API endpoint GET /collections/{id} returns collection with item_count
  * API endpoint GET /collections/{id} returns 404 for non-existent collection
  * API endpoint PATCH /collections/{id} updates collection fields
  * API endpoint DELETE /collections/{id} deletes collection and returns success
  * API endpoint DELETE /collections/{id} returns 404 for non-existent collection
  * Query params: pagination (page, page_size), sorting (sort_by, sort_order), search (name/description), tag filtering
* Suggested locations:
  * tests/unit/test_collections_api.py
* Mocking/fakes needed:
  * Mock database session
  * Mock CRUD functions from src/vulcanlab/collections/

## Acceptance criteria (checklist)

* [ ] API router created and registered in main.py with /api/v1 prefix
* [ ] GET /api/v1/collections endpoint returns paginated collections with total count
* [ ] POST /api/v1/collections endpoint creates collection and returns created object
* [ ] GET /api/v1/collections/{id} endpoint returns collection with computed item_count
* [ ] PATCH /api/v1/collections/{id} endpoint updates collection metadata
* [ ] DELETE /api/v1/collections/{id} endpoint deletes collection and cascade deletes items
* [ ] Collections list page renders with PageHeader and DataTable
* [ ] DataTable shows all columns: name, description, tags, dates, item_count
* [ ] Table sorting works on name, created_at, updated_at columns
* [ ] New Collection button opens modal with form
* [ ] Form validation requires name field
* [ ] Form submission creates collection and refetches list
* [ ] Delete button shows confirmation dialog
* [ ] Delete action removes collection and refetches list
* [ ] Navigation link to /collections added under Research (RAG)
* [ ] Unit tests pass for all API endpoints
* [ ] Tags display as badges in table

## Manual verification

* Steps:
  * Navigate to /collections (click nav link)
  * Verify empty state shows when no collections exist
  * Click "New Collection" button
  * Fill in name "Test Collection", description "Test description", tags "test,sample"
  * Submit form
  * Verify new collection appears in table
  * Verify tags display as badges
  * Create 2 more collections with different data
  * Test sorting by clicking column headers
  * Click on a collection row (should navigate to /collections/{id} - will show error until T03)
  * Click delete button on a collection
  * Verify confirmation dialog appears
  * Confirm deletion
  * Verify collection is removed from list
* Expected results:
  * All CRUD operations work end-to-end
  * Table displays correctly with sorting
  * Modal form validation works
  * Navigation works
  * Empty state shows appropriately

## Notes

* Requirements covered: R1 (create collection), R2 (edit metadata), R8 (list page with table)
* Use existing DataTable component pattern from RAG page (see src/app/rag/page.tsx)
* Item_count should be computed via SQL COUNT in the list query for efficiency
* Tags can be displayed using existing StatusBadge component pattern or custom badge component
* Consider using react-select or similar for better tags input UX (multi-select dropdown)
* Description should be truncated in table with tooltip for full text
* Follow patterns.md Section 4.1 for useCallback on fetch function to avoid infinite loops
* API should return 404 for non-existent collection ID, 400 for validation errors
