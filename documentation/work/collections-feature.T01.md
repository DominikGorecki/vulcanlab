# Ticket: collections-feature.T01 - Database Schema and Core Models

## Source

* Spec: documentation/work/collections-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create database tables (collections, collection_items) with proper schema, indexes, and triggers
* Implement SQLAlchemy models for Collection and CollectionItem
* Add core CRUD functions with link validation logic
* Update init_db.py to create tables on database initialization

## Scope

### In scope

* Collections table with name, description, tags (JSONB), timestamps
* Collection_items table with item_type, link, note, order (NUMERIC), timestamps
* SQLAlchemy declarative models in src/vulcanlab/data/models/
* Core CRUD module in src/vulcanlab/collections/ with session-based functions
* Link validation patterns for three item types (excerpt, research_result, research_query)
* Auto-update triggers for updated_at and last_modified timestamps
* Indexes for search, sorting, and joins
* Unit tests with mocked database sessions

### Out of scope

* API endpoints (T02)
* UI components (T02-T05)
* Metadata enrichment for excerpts (T03)
* Migration script for existing databases (will be added later if needed)

## Dependencies

* Depends on: none
* Unblocks: T02, T03

## Implementation plan

* Create SQLAlchemy models:
  * Define Collection model in src/vulcanlab/data/models/collection.py
  * Define CollectionItem model in src/vulcanlab/data/models/collection_item.py
  * Add imports to src/vulcanlab/data/models/__init__.py
* Create core CRUD module:
  * Create src/vulcanlab/collections/__init__.py
  * Implement collection CRUD functions (create, get, list, update, delete) with session parameter
  * Implement collection_item CRUD functions (add, update, delete, bulk_delete) with session parameter
  * Add link validation function with regex patterns for each item_type as constants
* Update init_db.py:
  * Import Collection and CollectionItem models in import section
  * Add create_collections_table() function following existing pattern
  * Create collections table with schema, indexes, GIN index on tags
  * Create collection_items table with schema, indexes
  * Add auto-update triggers for both tables (updated_at, last_modified)
  * Transfer ownership to app_user
  * Call create_collections_table() in init_database() function
* Patterns to apply:
  * Session management: Pass session explicitly to all CRUD functions (Section 2)
  * Core module independence: No FastAPI imports (Section 2)
  * Naming conventions: snake_case for functions, PascalCase for classes (Section 7)
  * Database patterns: SQLAlchemy declarative models (Section 2)
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Collection model: create with name/description/tags, update fields, cascade delete
  * CollectionItem model: create with all fields, update note/order, proper foreign key relationship
  * Link validation: valid links for each item_type pass, malformed links fail
  * CRUD operations: create collection, list with filters/pagination, get by id, update, delete
  * CRUD operations: add item, update item, delete item, bulk delete items
  * Order field: sorting with decimals, negatives, null handling
  * Tag filtering: query collections by tag using JSONB operators
  * Timestamps: date_added and last_modified auto-update correctly
* Suggested locations:
  * tests/unit/test_collection_model.py
  * tests/unit/test_collection_item_model.py
  * tests/unit/test_collections_crud.py
  * tests/unit/test_link_validation.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session object
  * Mock database query results
  * No real database connections

## Acceptance criteria (checklist)

* [ ] Collections table created with proper schema (id, name, description, tags, created_at, updated_at)
* [ ] Collection_items table created with proper schema (id, collection_id, item_type, link, note, order, date_added, last_modified)
* [ ] Indexes created: idx_collections_name, idx_collections_tags (GIN), idx_collections_created_at
* [ ] Indexes created: idx_collection_items_collection_id, idx_collection_items_order, idx_collection_items_item_type
* [ ] Auto-update triggers created for updated_at on collections and last_modified on collection_items
* [ ] SQLAlchemy models defined with proper relationships and constraints
* [ ] CRUD functions implemented for collections (create, get, list, update, delete)
* [ ] CRUD functions implemented for collection_items (add, update, delete, bulk_delete)
* [ ] Link validation function validates patterns for excerpt, research_result, research_query
* [ ] Unit tests pass with 100% coverage of CRUD functions and validation logic
* [ ] init_db.py successfully creates tables when run with -v flag
* [ ] ON DELETE CASCADE properly configured for collection_items

## Manual verification

* Steps:
  * Run: python -m vulcanlab.data.init_db -v
  * Connect to database and verify tables exist: SELECT * FROM collections; SELECT * FROM collection_items;
  * Check indexes exist: \d collections, \d collection_items
  * Check triggers exist: \dft
  * Insert test data manually via SQL to verify constraints and defaults
  * Delete a collection and verify items cascade delete
* Expected results:
  * Both tables exist with correct schema
  * All indexes and triggers are present
  * Tags default to empty JSON array
  * Order defaults to 0
  * Timestamps auto-populate on insert
  * Cascade delete works correctly

## Notes

* Requirements covered: R1 (partial - schema), R5 (data storage), R9 (link validation), R10 (timestamps)
* Link validation patterns as constants:
  * EXCERPT_PATTERN = r'^/search/result/(\d+)/(\d+)/(\d+)$'
  * RESEARCH_RESULT_PATTERN = r'^/rag/(\d+)/results/(\d+)$'
  * RESEARCH_QUERY_PATTERN = r'^/rag/(\d+)$'
* Follow existing init_db.py patterns for trigger creation (see create_io_files_triggers, create_experiments_triggers)
* Use NUMERIC(10, 3) for order field to support decimals up to 3 places and large ranges
* Tags stored as JSONB array enables PostgreSQL operators like ? for tag existence queries
* CASCADE delete ensures no orphaned items when collection is deleted
