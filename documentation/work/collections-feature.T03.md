# Ticket: collections-feature.T03 - Collection Detail Page and Item Management

## Source

* Spec: documentation/work/collections-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create collection detail page showing collection metadata and items table
* Implement API endpoints for collection items CRUD operations
* Enable inline editing of item notes and order values
* Support bulk delete for items
* Display excerpt metadata (biblio info, breadcrumbs, preview) for excerpt items

## Scope

### In scope

* API endpoints for collection items: POST /api/v1/collections/{id}/items, PATCH /api/v1/collections/{collection_id}/items/{item_id}, DELETE /api/v1/collections/{collection_id}/items/{item_id}, DELETE /api/v1/collections/{id}/items (bulk)
* API endpoint for metadata enrichment: GET /api/v1/collections/{id}/items/{item_id}/metadata
* Collection detail page at vulcanlab_ui/src/app/collections/[id]/page.tsx
* Editable collection description on detail page
* DataTable for items with columns: order, type, link, note (all sortable)
* Inline editing for note and order fields
* Bulk delete with checkbox selection
* Excerpt metadata display (title, author, year, breadcrumbs, truncated excerpt)
* Unit tests for all API endpoints

### Out of scope

* Add to Collection modal (T04)
* Integration on search/RAG pages (T05)
* Creating new items from detail page (items are added via modal in T04/T05)

## Dependencies

* Depends on: T01, T02
* Unblocks: T04

## Implementation plan

* Create collection items API endpoints:
  * Add POST /collections/{id}/items to collections router
  * Validate item_type against allowed values, validate link pattern based on item_type
  * Add PATCH /collections/{collection_id}/items/{item_id} for updating note/order
  * Add DELETE /collections/{collection_id}/items/{item_id} for single item deletion
  * Add DELETE /collections/{id}/items with body {item_ids: number[]} for bulk delete
  * Call core CRUD functions from T01
* Create metadata enrichment endpoint:
  * Add GET /collections/{id}/items/{item_id}/metadata
  * Parse link based on item_type to extract IDs
  * For excerpt type: query works table for title/author/year, query chunks for breadcrumbs and content
  * Truncate content to ~75 words for excerpt_preview
  * For research_result and research_query types: return basic metadata (query text, result content)
  * Return structured response varying by item_type
* Create collection detail page:
  * Create vulcanlab_ui/src/app/collections/[id]/page.tsx as client component
  * Use usePageData to fetch collection with items: GET /api/v1/collections/{id}
  * Display PageHeader with collection name as title
  * Add "Edit" button to toggle edit mode for description
  * Show collection description (editable with inline textarea when in edit mode)
  * Show tags as badges
  * Display DataTable for items with columns: order (editable), type (badge), link (clickable), note (editable)
  * Add bulk delete toolbar with checkboxes and delete button
  * Use StatusBadge for item_type display
* Implement inline editing:
  * Make order column editable: click to edit, input type number with step=0.001
  * Make note column editable: click to edit, show textarea
  * Auto-save on blur using debounced PATCH request
  * Show loading spinner during save
  * Show success/error toast after save
* Implement excerpt metadata display:
  * For excerpt items, fetch metadata via GET /api/v1/collections/{id}/items/{item_id}/metadata
  * Display biblio info below link: "Title by Author (Year)"
  * Display breadcrumbs as text: "Section > Subsection > ..."
  * Display truncated excerpt preview
  * Use Card component for better visual separation
* Implement bulk delete:
  * Add checkbox column to DataTable
  * Show bulk action toolbar when items selected
  * "Delete Selected" button triggers ConfirmDialog
  * On confirm, call DELETE /api/v1/collections/{id}/items with selected IDs
  * Refetch items after successful delete
* Patterns to apply:
  * API versioning: All routes prefixed with /api/v1 (Section 3.1)
  * Session management: Dependency injection for database session (Section 2)
  * Page lifecycle: usePageData with loading/error/data states (Section 4.1)
  * Component composition: DataTable, StatusBadge, Card, ConfirmDialog (Section 4.2)
  * Error handling: Raise HTTPException, use global handlers (Section 3.2)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * API endpoint POST /collections/{id}/items creates item with valid data
  * API endpoint POST /collections/{id}/items validates item_type and link pattern
  * API endpoint POST /collections/{id}/items rejects invalid links for each item_type
  * API endpoint PATCH /collections/{cid}/items/{iid} updates note and order
  * API endpoint DELETE /collections/{cid}/items/{iid} deletes single item
  * API endpoint DELETE /collections/{id}/items bulk deletes multiple items
  * API endpoint GET /collections/{id}/items/{iid}/metadata returns enriched data for excerpt
  * API endpoint GET /collections/{id}/items/{iid}/metadata handles missing source data gracefully
  * Metadata enrichment: truncates excerpt to ~75 words correctly
  * Metadata enrichment: extracts work_id, start_line, end_line from link correctly
* Suggested locations:
  * tests/unit/test_collection_items_api.py
  * tests/unit/test_collection_metadata_enrichment.py
* Mocking/fakes needed:
  * Mock database session
  * Mock CRUD functions from src/vulcanlab/collections/
  * Mock queries to works and chunks tables for metadata enrichment

## Acceptance criteria (checklist)

* [ ] POST /api/v1/collections/{id}/items endpoint creates item with validation
* [ ] PATCH /api/v1/collections/{cid}/items/{iid} endpoint updates note and order
* [ ] DELETE /api/v1/collections/{cid}/items/{iid} endpoint deletes single item
* [ ] DELETE /api/v1/collections/{id}/items endpoint bulk deletes items
* [ ] GET /api/v1/collections/{id}/items/{iid}/metadata endpoint returns enriched metadata
* [ ] Collection detail page displays collection name, description, tags
* [ ] Description is editable inline with save functionality
* [ ] Items table displays order, type, link (clickable), note columns
* [ ] Order field is editable inline and supports decimals
* [ ] Note field is editable inline with textarea
* [ ] Inline edits auto-save on blur with debouncing
* [ ] Item type displays as badge with appropriate styling
* [ ] Links are clickable and navigate to correct pages
* [ ] Bulk selection with checkboxes works correctly
* [ ] Bulk delete with confirmation dialog works
* [ ] Excerpt items show biblio metadata (title, author, year)
* [ ] Excerpt items show breadcrumbs
* [ ] Excerpt items show truncated preview (~75 words)
* [ ] Table sorting works on all columns
* [ ] Unit tests pass for all API endpoints and metadata enrichment

## Manual verification

* Steps:
  * Create a collection from T02 if not exists
  * Manually insert test items via SQL for all three types (excerpt, research_result, research_query)
  * Navigate to /collections/{id}
  * Verify collection name, description, and tags display
  * Click edit on description, change text, save
  * Verify items appear in table
  * Click on order field, change value to 2.5, blur
  * Verify order updates and table re-sorts
  * Click on note field, add text, blur
  * Verify note saves
  * Select multiple items with checkboxes
  * Click "Delete Selected" button
  * Confirm in dialog
  * Verify items are deleted
  * For excerpt item, verify biblio metadata displays below link
  * Verify breadcrumbs display
  * Verify truncated excerpt preview displays
  * Click on link, verify navigation to source page works
* Expected results:
  * All CRUD operations for items work correctly
  * Inline editing saves properly
  * Metadata enrichment displays for excerpts
  * Bulk delete works
  * Table sorting and filtering work

## Notes

* Requirements covered: R2 (edit description), R5 (store items), R6 (detail page table), R7 (inline edit), R11 (excerpt metadata)
* Debounce inline edits with 500ms delay to avoid excessive API calls
* Use react-hook-form or simple controlled inputs for inline editing
* Excerpt metadata may need to join works, chunks, and potentially heading_modifications tables
* Handle cases where source data (work, chunk) has been deleted - show "Source deleted" message
* Order field should accept decimals with up to 3 decimal places (matching NUMERIC(10,3))
* Consider using contenteditable or a custom inline edit component for better UX
* Link validation should prevent adding items with malformed links (already in T01 core logic)
* Bulk delete should show count of selected items in confirmation dialog
