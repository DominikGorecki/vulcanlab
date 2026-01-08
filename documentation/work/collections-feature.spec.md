# Title: Collections Feature for Research Artifact Organization

## Summary

- Add a new Collections feature to organize and annotate research artifacts (document excerpts, RAG results, and RAG queries)
- Users can create named collections with descriptions and tags for categorization
- Each collection holds items (excerpts, research results, queries) with custom notes and user-defined ordering
- Collections are accessible from a new navigation link under "Research (RAG)" and items can be added from existing pages
- Use a generic, extensible data model to support future item types without migration complexity

## Problem / Context

- Users currently have no way to organize, annotate, or curate research artifacts across the RAG pipeline
- Valuable search results, RAG queries, and generated responses are scattered across different pages with no persistent organization
- Researchers need to collect and annotate relevant excerpts, queries, and results for literature review, citation management, or project organization
- Business impact: Enables researchers to build curated knowledge collections, improving research workflow efficiency and knowledge retention

## Goals

- Allow users to create and manage named collections with descriptions and tags
- Support adding three item types: excerpts (search results), research results, and research queries
- Provide a reusable "Add to Collection" modal component across all relevant pages
- Enable users to annotate collection items with custom markdown notes
- Support flexible user-defined ordering via numeric order field (decimals, negatives allowed)
- Display collection items with appropriate context (biblio info, breadcrumbs, truncated content)

## Non-goals (Strict)

- User-specific or private collections (all collections are shared/visible to all users)
- Access control, permissions, or sharing features
- Hard limits on collection size
- Auto-generated collections or smart collections based on queries
- Export/import functionality for collections
- Collaboration features (comments, assignments, etc.)
- Integration with external citation managers

## Scope

### In scope

- Database schema: collections table, collection_items table (generic design)
- Core module: SQLAlchemy models, CRUD operations for collections and items
- API layer: FastAPI endpoints for collection and item management
- UI: Collections list page, collection detail page, add-to-collection modal component
- UI integration: Add collection buttons on search result, RAG result, and RAG query pages
- Link validation for collection items based on item type
- Tags support (JSON array field) for collection organization
- Search and pagination for collection selection modal

### Out of scope

- Access control or permission system
- Collection templates or presets
- Bulk import of items into collections
- Analytics or reporting on collection usage
- Email notifications or activity feeds
- Mobile-specific UI optimizations

## Requirements (Functional)

- R1: Users can create a new collection with name (required), description (optional), and tags (optional)
- R2: Users can edit collection metadata (name, description, tags) from the collection detail page
- R3: Users can add items to collections from three locations: search result page, RAG result page, RAG query list page
- R4: The "Add to Collection" modal allows selecting an existing collection or creating a new collection inline
- R5: Collection items store a link (validated against expected patterns), item type, custom markdown note, and numeric order value
- R6: Collection detail page displays items in a sortable table with columns: order, type, link (clickable), note (editable)
- R7: Users can edit the note and order fields inline on the collection detail page
- R8: Collection list page displays all collections in a sortable table with columns: name, description, tags, date created, date modified, item count
- R9: Links in collection items are validated to match expected URL patterns for the item type
- R10: Collection items automatically track date_added and last_modified timestamps
- R11: Excerpt items display biblio metadata (title, author, year), heading breadcrumbs, and truncated excerpt (75 words)
- R12: The add-to-collection modal includes search/filter and pagination for large numbers of collections

## Requirements (Non-functional)

- Performance:
  - Collection list page loads in under 500ms for up to 1000 collections
  - Collection detail page loads in under 500ms for up to 500 items
  - Modal search/filter responds in under 200ms

- Reliability:
  - Link validation prevents broken links from being stored
  - All database operations use transactions to ensure consistency
  - Graceful handling of deleted source artifacts (queries, results, works)

- Security / Privacy:
  - No special security requirements (all collections are shared)
  - Markdown notes are sanitized on display to prevent XSS
  - SQL injection protection via parameterized queries (standard SQLAlchemy)

- Observability:
  - Standard API logging for all collection operations
  - No special metrics or tracing required

## Proposed Solution (High-level)

- Database: Two tables - `collections` and `collection_items` with generic schema
- Core Module: SQLAlchemy models in `src/vulcanlab/data/models/`, CRUD functions in new module `src/vulcanlab/collections/`
- API Layer: New router `src/vulcanlab_api/routers/collections.py` with endpoints for collection and item CRUD
- Frontend: New pages at `/collections` and `/collections/[id]`, reusable modal component at `vulcanlab_ui/src/components/collections/`
- Data Flow: UI -> API -> Core Module -> Database
- Link validation: Pattern matching in core module based on item_type
- Tags stored as JSONB array for flexibility and querying

## Interfaces / APIs / Contracts

### API Endpoints (all prefixed with `/api/v1`)

**Collections**
- `GET /collections` - List all collections (with pagination, sorting, filtering)
  - Query params: `page`, `page_size`, `sort_by`, `sort_order`, `search` (name/description), `tag`
  - Response: `{ collections: Collection[], total: number, page: number, page_size: number }`
- `POST /collections` - Create new collection
  - Body: `{ name: string, description?: string, tags?: string[] }`
  - Response: `Collection` object with generated ID
- `GET /collections/{id}` - Get collection details with items
  - Response: `{ collection: Collection, items: CollectionItem[] }`
- `PATCH /collections/{id}` - Update collection metadata
  - Body: `{ name?: string, description?: string, tags?: string[] }`
  - Response: Updated `Collection` object
- `DELETE /collections/{id}` - Delete collection and all items
  - Response: `{ message: string }`

**Collection Items**
- `POST /collections/{id}/items` - Add item to collection
  - Body: `{ item_type: string, link: string, note?: string, order?: number }`
  - Response: `CollectionItem` object
- `PATCH /collections/{collection_id}/items/{item_id}` - Update item note/order
  - Body: `{ note?: string, order?: number }`
  - Response: Updated `CollectionItem` object
- `DELETE /collections/{collection_id}/items/{item_id}` - Remove item from collection
  - Response: `{ message: string }`
- `DELETE /collections/{id}/items` - Bulk delete items
  - Body: `{ item_ids: number[] }`
  - Response: `{ deleted_count: number }`

**Item Metadata Enrichment**
- `GET /collections/{id}/items/{item_id}/metadata` - Get enriched metadata for display
  - Returns biblio info, breadcrumbs, excerpt preview based on item_type and parsed link
  - Response varies by item_type

### Data Types

```typescript
interface Collection {
  id: number;
  name: string;
  description: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
  item_count?: number;  // Computed field
}

interface CollectionItem {
  id: number;
  collection_id: number;
  item_type: "excerpt" | "research_result" | "research_query";
  link: string;
  note: string | null;
  order: number;
  date_added: string;
  last_modified: string;
}

interface ExcerptMetadata {
  title: string;
  author: string | null;
  year: string | null;
  breadcrumbs: string[];
  excerpt_preview: string;  // Truncated to ~75 words
}
```

## Data Model / Storage

### `collections` table
- `id`: SERIAL PRIMARY KEY
- `name`: VARCHAR(200) NOT NULL
- `description`: TEXT NULL
- `tags`: JSONB NOT NULL DEFAULT '[]'
- `created_at`: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
- `updated_at`: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()

Indexes:
- `idx_collections_name` on name (for search)
- `idx_collections_tags` GIN on tags (for tag filtering)
- `idx_collections_created_at` on created_at DESC (for sorting)

Triggers:
- Auto-update `updated_at` trigger (follow existing pattern from init_db.py)

### `collection_items` table
- `id`: SERIAL PRIMARY KEY
- `collection_id`: INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE
- `item_type`: VARCHAR(50) NOT NULL (values: "excerpt", "research_result", "research_query")
- `link`: VARCHAR(500) NOT NULL
- `note`: TEXT NULL
- `order`: NUMERIC(10, 3) NOT NULL DEFAULT 0  (supports decimals, negatives)
- `date_added`: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
- `last_modified`: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()

Indexes:
- `idx_collection_items_collection_id` on collection_id (for joins)
- `idx_collection_items_order` on (collection_id, order) (for sorting)
- `idx_collection_items_item_type` on item_type (for filtering)

Triggers:
- Auto-update `last_modified` trigger

### Link Validation Patterns
- `"excerpt"`: Must match `/search/result/{work_id}/{start_line}/{end_line}` where all are integers
- `"research_result"`: Must match `/rag/{id}/results/{resultId}` where both are integers
- `"research_query"`: Must match `/rag/{id}` where id is integer

## UX / Workflows

### Workflow 1: Create and populate a collection
1. User navigates to /collections
2. Clicks "New Collection" button
3. Fills in name, description, tags in modal/form
4. Collection created and redirected to /collections/{id}
5. User navigates to /search and finds relevant excerpt
6. Clicks "Add to Collection" button on search result page
7. Modal appears with searchable list of collections
8. User selects the newly created collection
9. Item added, modal shows success message
10. User returns to /collections/{id} to see the item
11. User edits the note field to add annotation
12. User sets order to 1.0

### Workflow 2: Browse collections and view items
1. User navigates to /collections
2. Sees table of all collections sorted by date modified
3. Filters by tag "literature-review"
4. Clicks into a collection
5. Sees collection description and table of items
6. Items sorted by order field (default)
7. Clicks on a link in the table
8. Navigated to /search/result/... page
9. Uses browser back to return to collection

### Workflow 3: Organize items within collection
1. User on /collections/{id} page
2. Sees 10 items with order values: 1, 2, 3, ... 10
3. Wants to insert new item between 2 and 3
4. Edits order field of new item to 2.5
5. Table re-sorts to show correct position
6. User edits notes inline for multiple items
7. Changes are auto-saved on blur

## Testing Plan

### Unit tests
- Test Collection model CRUD operations
- Test CollectionItem model CRUD operations
- Test link validation logic for all three item types
- Test order field sorting (including decimals, negatives)
- Test tag filtering and search
- Test cascading delete when collection is removed
- Mock database session (no real DB connection)

### Integration tests
- Not required for this ticket

### Manual test plan
- Create collection with name, description, and multiple tags
- Add items of all three types from their respective pages
- Verify link validation rejects malformed links
- Edit notes inline on collection detail page
- Edit order values (positive, negative, decimal) and verify sorting
- Sort collection items table by different columns
- Search and filter collections on list page
- Delete individual items from collection
- Bulk delete multiple items
- Delete entire collection and verify cascade
- Verify timestamps (date_added, last_modified) update correctly
- Test modal search/filter with 50+ collections
- Verify markdown notes render correctly with sanitization

## Acceptance Criteria (Checklist)

- [ ] Collections table created with proper schema, indexes, and triggers
- [ ] Collection_items table created with proper schema, indexes, and triggers
- [ ] SQLAlchemy models defined in src/vulcanlab/data/models/
- [ ] Core CRUD functions implemented and unit tested
- [ ] API endpoints implemented with proper error handling
- [ ] Collections list page displays all collections with sorting
- [ ] Collection detail page displays items in sortable table
- [ ] Add to Collection modal is reusable component
- [ ] Modal has search/filter and pagination
- [ ] Add to Collection button integrated on search result page
- [ ] Add to Collection button integrated on RAG result page
- [ ] Add to Collection button integrated on RAG query list page
- [ ] Link validation prevents invalid links from being stored
- [ ] Notes are editable inline on collection detail page
- [ ] Order field is editable and supports decimals/negatives
- [ ] Tags are displayed and filterable on collections list page
- [ ] Timestamps (date_added, last_modified) track correctly
- [ ] Bulk delete works for multiple items
- [ ] Collection description is editable on detail page
- [ ] Excerpt items show biblio metadata and truncated content
- [ ] init_db.py updated to create tables and triggers
- [ ] Navigation link added under "Research (RAG)" section

## Rollout / Migration Plan

- Add new tables via init_db.py (no migration script needed for fresh installs)
- For existing databases, create migration script to add collections and collection_items tables
- No data migration needed (starting fresh)
- Feature can be rolled out immediately, no flag required
- No backwards compatibility concerns (new feature)

## Risks and Alternatives

### Risks
- Link validation may break if URL patterns change in future (Mitigation: Use constants/config for patterns)
- Deleted source artifacts (works, queries, results) will leave broken links in collections (Mitigation: Document as known limitation, consider future cleanup job)
- Large collections (1000+ items) may have performance issues (Mitigation: Add pagination to detail page if needed)
- Tag management without dedicated UI could become unwieldy (Mitigation: Future enhancement for tag management page)

### Alternatives considered
- Alternative 1: Use enum for item_type
  - Rejected: User specifically mentioned trouble with enums and init_db.py mismatch
- Alternative 2: Store structured data (work_id, line numbers) instead of links
  - Rejected: More complex, harder to extend to new item types, links are simpler
- Alternative 3: Separate tables for each item type
  - Rejected: More complex schema, harder to extend, violates DRY principle
- Alternative 4: Use many-to-many relationship directly to source tables
  - Rejected: Tight coupling, no place for notes/order, breaks if source deleted

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied
- Three-tier architecture: Core module -> API layer -> Frontend (Section 1)
- Core module independence: No FastAPI imports in collection logic (Section 2)
- Session management: Pass session explicitly to CRUD functions (Section 2)
- API versioning: All routes prefixed with `/api/v1` (Section 3.1)
- Error handling: Use specific exceptions, global handlers (Section 3.2)
- Config separation: Core logic uses vulcanlab.config, API uses vulcanlab_api.config (Section 3.3)
- Frontend: Next.js App Router, TailwindCSS, Shadcn/Radix (Section 4.1)
- Page lifecycle: usePageData hook with loading/error/data states (Section 4.1)
- Component composition: Reusable modal component, props-in events-out (Section 4.2)
- DataTable component: For both collections list and items list (Section 4.3)
- Testing: Unit tests mock DB, integration tests optional (Section 6)
- Naming: snake_case Python, camelCase/PascalCase TypeScript (Section 7)

### Deviations (if any)
- None. This spec fully aligns with documented patterns.

## Implementation Notes (Non-binding)

- Follow existing patterns from RAG query list page for table UI
- Reuse StatusBadge component pattern for item type badges
- Consider using react-hook-form for collection create/edit forms
- Modal component should use Radix Dialog primitive
- Use existing PageHeader, DataTable, Card components from component library
- Link validation regex patterns should be defined as constants in core module
- Consider caching collection list in modal if performance becomes issue
- Excerpt metadata fetching may require joining works, chunks tables
- Order field sorting should handle NULL values (treat as 0 or max)
- Tag input could use a simple comma-separated input or react-select for better UX
- Markdown rendering for notes should use existing markdown renderer if available
- Consider debouncing inline edit saves to reduce API calls

## Open Questions

- Q1: Should we add a "duplicate collection" feature for common research patterns?
- Q2: Should excerpt metadata fetching be a separate API call or embedded in item list response?
- Q3: Do we need undo/redo for bulk delete operations?
- Q4: Should there be a "recently added" or "favorites" quick access for collections?
