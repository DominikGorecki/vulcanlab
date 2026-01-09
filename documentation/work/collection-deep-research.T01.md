# Ticket: collection-deep-research.T01 - Database Schema and Migration

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SQL migration for research_sessions, research_sections, and research_reports tables
* Establish JSONB-based state storage for manual and automated research workflows
* Enable session persistence with proper indexing and foreign key relationships

## Phase

* Migrations

## Scope

### In scope

* SQL migration file creating three new tables with all columns, constraints, and indexes
* Foreign key relationships to existing collections table
* JSONB columns for flexible state storage (research_plan, state_data, context_data, matching_results, metadata, quality_evaluation, reuse_info)
* Indexes on collection_id, thread_id, status, session_id, question_id, quality_status
* CHECK constraints for enums (session_type, status, current_phase, quality_status)

### Out of scope

* SQLAlchemy models (covered in T02)
* Data seeding or backfill (not needed for new tables)
* Altering existing tables
* Integration with checkpointer logic (covered in T15)

## Dependencies

* Depends on: none (foundational)
* Unblocks: T02 (SQLAlchemy models), T04 (CRUD operations)

## Implementation plan

* Create migration file: migrations/add_research_tables.sql (or Alembic revision if project uses Alembic)
* Define research_sessions table:
  * Primary key id (SERIAL)
  * Foreign key collection_id → collections(id) ON DELETE CASCADE
  * session_type VARCHAR(20) with CHECK (session_type IN ('manual', 'automated'))
  * thread_id VARCHAR(255) UNIQUE NOT NULL
  * current_phase VARCHAR(50)
  * research_plan JSONB
  * state_data JSONB
  * status VARCHAR(20) DEFAULT 'in_progress' with CHECK constraint
  * Timestamps: created_at, updated_at, completed_at
* Define research_sections table:
  * Primary key id (SERIAL)
  * Foreign key session_id → research_sessions(id) ON DELETE CASCADE
  * question_id VARCHAR(50), question_text TEXT
  * section_content TEXT
  * JSONB columns: context_data, matching_results, metadata, reuse_info
  * quality_status VARCHAR(20) with CHECK constraint
  * Timestamps: created_at, updated_at
* Define research_reports table:
  * Primary key id (SERIAL)
  * Foreign key session_id → research_sessions(id) ON DELETE CASCADE
  * report_content TEXT NOT NULL, executive_summary TEXT
  * JSONB columns: quality_evaluation, metadata
  * version INTEGER DEFAULT 1
  * Timestamp: created_at
* Create indexes:
  * idx_research_sessions_collection ON research_sessions(collection_id)
  * idx_research_sessions_thread ON research_sessions(thread_id)
  * idx_research_sessions_status ON research_sessions(status)
  * idx_research_sections_session ON research_sections(session_id)
  * idx_research_sections_question ON research_sections(question_id)
  * idx_research_sections_quality ON research_sections(quality_status)
  * idx_research_reports_session ON research_reports(session_id)
* Verify migration syntax and constraints
* Patterns to apply:
  * **Database migrations** - SQL-based migrations or Alembic per patterns.md section 5
  * **Foreign key cascades** - ON DELETE CASCADE for research sessions and child tables
* Deviations (if any):
  * None - standard PostgreSQL schema

## Unit tests (required)

* Add tests for:
  * Migration can be applied cleanly to empty database
  * All tables created with correct column types and constraints
  * Foreign key relationships enforced (insert without collection_id fails)
  * CHECK constraints enforced (invalid session_type rejected)
  * UNIQUE constraint on thread_id enforced
  * Indexes created and queryable
  * CASCADE delete works (deleting collection deletes sessions)
* Suggested locations:
  * tests/unit/data/test_migrations.py
* Mocking/fakes needed:
  * In-memory PostgreSQL instance or SQLite for migration testing (use pytest fixtures)

## Acceptance criteria (checklist)

* [ ] Migration file created in migrations/ directory
* [ ] research_sessions table has all 10 columns with correct types
* [ ] research_sections table has all 11 columns with correct types
* [ ] research_reports table has all 7 columns with correct types
* [ ] All foreign key constraints defined with ON DELETE CASCADE
* [ ] All CHECK constraints for enum fields defined
* [ ] thread_id has UNIQUE constraint
* [ ] All 7 indexes created
* [ ] Migration runs successfully on development database
* [ ] Unit tests pass for migration application and constraint enforcement

## Manual verification

* Steps:
  * Run migration on development database: python -m vulcanlab.data.init_db (or alembic upgrade head)
  * Verify tables created: psql -c "\dt research_*"
  * Verify indexes: psql -c "\di research_*"
  * Verify constraints: psql -c "\d research_sessions"
  * Test foreign key cascade: insert collection, insert session, delete collection, verify session deleted
  * Test CHECK constraint: attempt to insert session with session_type='invalid', verify rejection
  * Test UNIQUE constraint: insert two sessions with same thread_id, verify rejection
* Expected results:
  * All tables and indexes present
  * Constraints enforced correctly
  * No errors during migration

## Notes

* Requirements covered: R6 (persist session state to tables)
* JSONB columns enable flexible schema evolution without migrations for nested state changes
* thread_id UNIQUE constraint critical for LangGraph checkpointer compatibility
* CASCADE deletes ensure no orphaned research data when collections deleted
* If using Alembic, create revision with: alembic revision -m "Add research tables"
