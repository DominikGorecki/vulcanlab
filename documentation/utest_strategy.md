# Unit Testing Strategy

## Core Philosophy
- **Zero Database Dependencies**: Unit tests must use mocks instead of actual database connections (SQLite/PostgreSQL).
- **Speed**: Tests should execute in sub-second time.
- **Isolation**: Test business logic and attribute assignment, not database behavior.

## Implementation Guidelines

### 1. Mocking Infrastructure
Use the centralized helpers in `tests/unit/mock_helpers.py`:
- `mock_session()`: For mocking SQLAlchemy sessions.
- Factories: `create_mock_work()`, `create_mock_chunk()`, etc. for creating model instances.

### 2. What to Unit Test directly
- Business logic and methods.
- Object attribute assignment.
- Verification that session methods (`add`, `delete`, `commit`) are called (using mocks).

### 3. What NOT to Unit Test (Defer to Integration Tests)
- Database constraints (Foreign Keys, NOT NULL, UNIQUE).
- CASCADE delete behavior.
- Database-specific features (Vector search, JSONB, Full-text search).
- Actual data persistence and retrieval.

## Example Pattern

**Do NOT setup a database:**
```python
def test_create_model(mock_session):
    # Use mock helpers
    chunk = create_mock_chunk(content="Test")
    mock_session.add(chunk)
    
    # Assert on the mock interaction, not the DB
    mock_session.add.assert_called_once()
```
