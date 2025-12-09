# Integration Tests Needed

This document catalogs tests that were removed from the unit test suite because they require a real database. These tests should be implemented as integration tests in a future `tests/integration/` directory.

## Criteria for Integration Tests

A test requires integration testing (real database) if it:

- **Verifies database constraints** - Foreign keys, NOT NULL, UNIQUE, CHECK constraints
- **Tests CASCADE DELETE** - Database-level cascade behavior
- **Tests PostgreSQL-specific features** - pgvector, tsvector, JSONB, array types
- **Verifies transaction isolation** - Rollback behavior, concurrent access
- **Tests actual SQL query execution** - Complex joins, aggregations, window functions
- **Tests database initialization** - Schema creation, migrations, extensions

## Tests Removed from Unit Tests

### CASCADE Delete Tests

These tests verify that database-level CASCADE DELETE works correctly:

#### test_chunk_model.py
- `test_cascade_delete_from_work` - When a Work is deleted, all its Chunks should be deleted via CASCADE
- `test_cascade_delete_from_parent` - When a parent Chunk is deleted, all child Chunks should be deleted via CASCADE

**Why Integration Test:** Requires actual database FK CASCADE constraint, cannot be mocked meaningfully.

---

### Foreign Key Constraint Tests

These tests verify that FK constraints are enforced at the database level:

#### test_chunk_model.py
- `test_foreign_key_constraint_work` - Adding Chunk with invalid work_id should raise IntegrityError
- `test_foreign_key_constraint_parent` - Adding Chunk with invalid parent_id should raise IntegrityError

#### test_query_model.py
- Any FK constraint tests for Query model relationships

#### test_result_model.py
- `test_foreign_key_constraint_query` - Result with invalid query_id should raise IntegrityError
- `test_foreign_key_constraint_chunk` - Result with invalid chunk_id should raise IntegrityError

#### All Other Model Tests
- Similar FK validation tests across all models with foreign key relationships

**Why Integration Test:** Requires database to enforce FK constraints. Mocking IntegrityError doesn't verify the constraint exists.

---

### NOT NULL Constraint Tests

These tests verify that NOT NULL constraints are enforced:

#### test_chunk_model.py
- `test_work_id_required` - Chunk without work_id should raise IntegrityError
- `test_level_required` - Chunk without level should raise IntegrityError
- `test_content_required` - Chunk without content should raise IntegrityError
- `test_start_line_required` - Chunk without start_line should raise IntegrityError
- `test_end_line_required` - Chunk without end_line should raise IntegrityError
- `test_vector_status_required` - Chunk without vector_status should raise IntegrityError

#### test_work_model.py
- `test_title_required` - Work without title should raise IntegrityError
- `test_authors_required` - Work without authors should raise IntegrityError

#### test_query_model.py
- `test_original_query_required` - Query without original_query should raise IntegrityError
- `test_vector_status_required` - Query without vector_status should raise IntegrityError (with default)

#### test_prompt_template_model.py
- `test_name_required` - PromptTemplate without name should raise IntegrityError
- `test_template_text_required` - PromptTemplate without template_text should raise IntegrityError

#### All Other Model Tests
- Similar NOT NULL validation tests for required fields

**Why Integration Test:** Requires database to enforce NOT NULL constraints. Unit tests should validate at the application level (e.g., Pydantic validation), not database level.

---

### UNIQUE Constraint Tests

These tests verify that UNIQUE constraints are enforced:

#### test_prompt_template_model.py
- `test_unique_name_constraint` - Duplicate template names should raise IntegrityError

#### test_work_model.py
- `test_unique_file_path_constraint` - Duplicate file paths should raise IntegrityError (if constraint exists)

**Why Integration Test:** Requires database to enforce UNIQUE constraints.

---

### PostgreSQL-Specific Features

These tests require PostgreSQL extensions and types:

#### pgvector - Vector Similarity Search

**test_retrieve.py:**
- `_dense_search()` function tests - Requires pgvector extension
- Vector cosine similarity (`<=>` operator)
- Vector inner product (`<#>` operator)
- HNSW index usage

**test_chunk_model.py:**
- `test_vector_embedding_storage` - Store 768-dimension vector in Vector(768) column
- `test_vector_embedding_retrieval` - Retrieve vector and verify dimensions

**test_query_model.py:**
- `test_embedding_original_storage` - Store embedding in Vector column
- `test_embedding_hyde_storage` - Store HyDE embedding in Vector column

**Why Integration Test:** Requires PostgreSQL with pgvector extension installed. SQLite BLOB storage doesn't test pgvector functionality.

#### Full-Text Search - tsvector

**test_retrieve.py:**
- `_lexical_search()` function tests - Requires tsvector/tsquery
- Full-text search with ranking (`ts_rank`)
- GIN index usage on tsvector column

**test_chunk_model.py:**
- `test_fulltext_search_vector` - Test auto-updated tsvector column
- `test_fulltext_search_trigger` - Test trigger that updates tsvector on content change

**Why Integration Test:** Requires PostgreSQL full-text search. SQLite FTS5 is different and wouldn't validate the actual implementation.

#### JSONB Type

**test_query_model.py:**
- `test_expanded_queries_jsonb_storage` - Store list in JSONB column
- `test_embeddings_mqe_jsonb_storage` - Store list of vectors in JSONB
- `test_jsonb_query_operations` - Query using `->`, `->>`, `@>` operators

**test_prompt_meta_model.py:**
- `test_metadata_jsonb_storage` - Store dict in JSONB column
- `test_jsonb_containment` - Use `@>` containment operator

**Why Integration Test:** Requires PostgreSQL JSONB type. SQLite TEXT storage doesn't test JSONB-specific operations.

---

### Database Initialization and Health Checks

These tests verify actual database setup:

#### test_init_db.py

**Database Creation:**
- `test_create_database_and_user` - Create PostgreSQL database and user with psycopg
- `test_enable_pgvector_extension` - Enable pgvector extension
- `test_create_tables` - Create all tables using SQLAlchemy metadata
- `test_create_vector_indexes` - Create HNSW indexes for vector columns
- `test_create_fulltext_search` - Create tsvector column, GIN index, and trigger
- `test_create_prompt_meta_table` - Create table with JSONB column
- `test_seed_default_data` - Seed initial data (templates, config)

**Error Handling:**
- `test_database_already_exists` - Handle "database already exists" error
- `test_user_already_exists` - Handle "role already exists" error
- `test_extension_already_enabled` - Handle "extension already exists" error

**Why Integration Test:** These test actual database creation, extension installation, and schema setup. Cannot be meaningfully mocked.

#### test_db_health_check.py

**Connectivity Tests:**
- `test_check_connection_success` - Connect to PostgreSQL and execute `SELECT 1`
- `test_check_connection_timeout` - Handle connection timeout
- `test_check_connection_invalid_credentials` - Handle authentication failure
- `test_check_connection_database_not_found` - Handle database doesn't exist

**Version Checks:**
- `test_check_postgresql_version` - Verify PostgreSQL version >= 12
- `test_check_pgvector_extension` - Verify pgvector extension is installed

**Health Check Endpoints:**
- `test_health_check_all_passing` - All checks pass
- `test_health_check_database_down` - Database unreachable
- `test_health_check_extension_missing` - pgvector not installed

**Why Integration Test:** These test actual database connectivity and state. Mocking defeats the purpose of health checks.

---

### Transaction and Concurrency Tests

These tests verify transaction isolation and concurrent access:

#### test_database.py
- `test_transaction_rollback_on_error` - Verify changes are rolled back on exception
- `test_transaction_isolation` - Test read committed isolation level
- `test_concurrent_writes` - Multiple sessions writing simultaneously
- `test_deadlock_handling` - Detect and handle deadlocks

**Why Integration Test:** Requires real database to test ACID properties and isolation levels.

---

### Complex Query Tests

These tests verify complex SQL queries execute correctly:

#### test_retrieve.py
- `test_hybrid_search_with_joins` - Join Chunks, Works, Results with filters
- `test_aggregation_queries` - GROUP BY, HAVING, COUNT, AVG
- `test_subquery_performance` - Subqueries vs CTEs performance
- `test_window_functions` - ROW_NUMBER(), RANK() for pagination

**Why Integration Test:** While we mock queries in unit tests, integration tests verify the actual SQL is correct and performant.

---

## Implementation Guide

### Setup Integration Test Environment

Create `tests/integration/conftest.py`:

```python
"""Pytest fixtures for integration tests with real PostgreSQL database."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vulcanlab.data.database import get_database_url
from vulcanlab.data.models import Base


@pytest.fixture(scope="session")
def integration_engine():
    """
    Create engine for integration tests using test database.

    Uses environment variable or separate test database URL.
    """
    # Option 1: Use separate test database
    test_db_url = "postgresql+psycopg://test_user:test_pass@localhost:5432/vulcanLab_test_db"

    # Option 2: Use main database with test prefix
    # test_db_url = get_database_url().replace("/vulcanLab", "/vulcanLab_test")

    engine = create_engine(test_db_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup: Drop all tables
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def integration_session(integration_engine):
    """
    Provide a transactional session for each test.

    Each test runs in a transaction that is rolled back after the test,
    ensuring tests don't affect each other.
    """
    connection = integration_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def integration_session_commit(integration_engine):
    """
    Provide a session that allows commits (for testing commit behavior).

    Use this when you need to test actual commit/rollback behavior.
    Cleanup is done by truncating tables after test.
    """
    Session = sessionmaker(bind=integration_engine)
    session = Session()

    yield session

    # Cleanup: Truncate all tables
    session.execute("TRUNCATE TABLE chunk, work, query, result CASCADE")
    session.commit()
    session.close()
```

### Running Integration Tests

```bash
# Run only unit tests (fast, no database)
pytest tests/unit/ -v

# Run only integration tests (slow, requires PostgreSQL)
pytest tests/integration/ -v

# Run integration tests with specific marker
pytest -m integration -v

# Run all tests
pytest tests/ -v
```

### Marking Integration Tests

Add marker to `pytest.ini`:

```ini
[pytest]
markers =
    integration: marks tests as integration tests (deselect with '-m "not integration"')
    slow: marks tests as slow (deselect with '-m "not slow"')
```

Use in test files:

```python
import pytest

@pytest.mark.integration
def test_cascade_delete_from_work(integration_session):
    """Test that deleting a Work cascades to its Chunks."""
    # Test implementation
    pass
```

---

## Benefits of Separation

### Unit Tests (Fast)
- ✅ No database setup required
- ✅ Run in <10 seconds
- ✅ Test business logic in isolation
- ✅ Reliable in CI/CD (no external dependencies)
- ✅ Easy to debug (mocks are predictable)

### Integration Tests (Comprehensive)
- ✅ Test real database behavior
- ✅ Catch SQL errors and constraint violations
- ✅ Verify PostgreSQL-specific features
- ✅ Test performance with real queries
- ✅ Ensure schema matches models

### Together (Complete)
- ✅ Fast feedback from unit tests
- ✅ Confidence from integration tests
- ✅ Clear separation of concerns
- ✅ Easier maintenance and debugging

---

## Migration Checklist

- [x] Create `tests/unit/mock_helpers.py` with reusable mocks
- [x] Create this documentation file
- [ ] Convert all unit tests to use mocks
- [ ] Remove database fixtures from `tests/conftest.py`
- [ ] Create `tests/integration/` directory structure
- [ ] Implement integration test fixtures in `tests/integration/conftest.py`
- [ ] Implement integration tests for CASCADE deletes
- [ ] Implement integration tests for FK constraints
- [ ] Implement integration tests for pgvector operations
- [ ] Implement integration tests for full-text search
- [ ] Implement integration tests for database initialization
- [ ] Configure CI/CD to run unit tests always, integration tests optionally
- [ ] Document how to set up test PostgreSQL database locally

---

## Questions or Issues?

If you're unsure whether a test should be a unit test or integration test, ask:

1. **Does it test business logic?** → Unit test (with mocks)
2. **Does it test database behavior?** → Integration test (with real DB)
3. **Can it be meaningfully mocked?** → Unit test
4. **Does it require PostgreSQL features?** → Integration test

When in doubt, prefer unit tests for speed, but don't hesitate to add integration tests for confidence.
