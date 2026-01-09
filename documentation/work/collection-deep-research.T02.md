# Ticket: collection-deep-research.T02 - SQLAlchemy Models and Enums

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SQLAlchemy declarative models for ResearchSession, ResearchSection, ResearchReport
* Define Python enums for session_type, status, current_phase, quality_status
* Establish ORM relationships to enable navigation between sessions, sections, reports, and collections

## Phase

* Core Modules

## Scope

### In scope

* ResearchSession model in src/vulcanlab/data/models/research_session.py
* ResearchSection model in src/vulcanlab/data/models/research_section.py
* ResearchReport model in src/vulcanlab/data/models/research_report.py
* Python enums: SessionType, SessionStatus, ResearchPhase, QualityStatus
* Relationships: ResearchSession.sections (one-to-many), ResearchSession.reports (one-to-many), ResearchSession.collection (many-to-one)
* Type hints for JSONB columns (research_plan, state_data, context_data, etc.)

### Out of scope

* CRUD functions (covered in T04)
* API endpoint schemas/DTOs (covered in T10-T14)
* Validation logic beyond SQLAlchemy column constraints
* Migration files (covered in T01)

## Dependencies

* Depends on: T01 (database tables must exist)
* Unblocks: T04 (CRUD operations), T10 (API endpoints)

## Implementation plan

* Create src/vulcanlab/data/models/research_session.py
* Define SessionType enum (manual, automated)
* Define SessionStatus enum (in_progress, completed, failed, paused)
* Define ResearchPhase enum (planning, research, synthesis, evaluation, completed)
* Define QualityStatus enum (pending, approved, needs_refinement)
* Create ResearchSession model:
  * __tablename__ = 'research_sessions'
  * Columns matching T01 schema: id, collection_id, session_type, thread_id, current_phase, research_plan (JSONB), state_data (JSONB), status, created_at, updated_at, completed_at
  * Use Enum type for session_type, status, current_phase
  * Relationship: collection = relationship("Collection", back_populates="research_sessions")
  * Relationship: sections = relationship("ResearchSection", back_populates="session", cascade="all, delete-orphan")
  * Relationship: reports = relationship("ResearchReport", back_populates="session", cascade="all, delete-orphan")
* Create ResearchSection model:
  * __tablename__ = 'research_sections'
  * Columns matching T01 schema with JSONB for context_data, matching_results, metadata, reuse_info
  * Relationship: session = relationship("ResearchSession", back_populates="sections")
* Create ResearchReport model:
  * __tablename__ = 'research_reports'
  * Columns matching T01 schema with JSONB for quality_evaluation, metadata
  * Relationship: session = relationship("ResearchSession", back_populates="reports")
* Update Collection model (if needed) to add back_populates="research_sessions"
* Add models to __init__.py for import convenience
* Patterns to apply:
  * **SQLAlchemy declarative models** - per patterns.md section 2
  * **Relationship cascade** - "all, delete-orphan" for parent-child relationships
* Deviations (if any):
  * None - standard SQLAlchemy ORM patterns

## Unit tests (required)

* Add tests for:
  * ResearchSession model instantiation with required fields
  * ResearchSession.sections relationship loads correctly
  * ResearchSession.reports relationship loads correctly
  * ResearchSession.collection relationship loads correctly
  * Enum fields accept valid values and reject invalid values
  * JSONB columns serialize and deserialize dictionaries correctly
  * Cascade delete: deleting session deletes sections and reports
  * Timestamps auto-populate (created_at, updated_at)
* Suggested locations:
  * tests/unit/data/models/test_research_session.py
  * tests/unit/data/models/test_research_section.py
  * tests/unit/data/models/test_research_report.py
* Mocking/fakes needed:
  * Mock database session using pytest-sqlalchemy fixtures
  * In-memory SQLite for model behavior testing

## Acceptance criteria (checklist)

* [ ] ResearchSession model defined with all columns and relationships
* [ ] ResearchSection model defined with all columns and relationships
* [ ] ResearchReport model defined with all columns and relationships
* [ ] SessionType, SessionStatus, ResearchPhase, QualityStatus enums defined
* [ ] Enum fields use Python Enum type in models
* [ ] All JSONB columns defined with appropriate type hints
* [ ] Relationships configured with cascade="all, delete-orphan"
* [ ] Collection model updated with back_populates if needed
* [ ] Unit tests pass for model instantiation, relationships, enums, JSONB serialization

## Manual verification

* Steps:
  * Import models in Python shell: from vulcanlab.data.models import ResearchSession, ResearchSection, ResearchReport
  * Create ResearchSession instance with test data
  * Verify session_type accepts SessionType.manual
  * Verify research_plan accepts dict and serializes to JSONB
  * Query session and access .sections relationship
  * Delete session and verify sections auto-deleted (cascade)
* Expected results:
  * Models import without errors
  * Enum fields work correctly
  * Relationships navigate correctly
  * JSONB columns accept dictionaries

## Notes

* Requirements covered: R6 (session state persistence with ORM)
* Use SQLAlchemy's JSON type for PostgreSQL JSONB columns
* Cascade deletes ensure referential integrity without manual cleanup
* Type hints for JSONB columns improve IDE support: research_plan: Mapped[Optional[dict]]
