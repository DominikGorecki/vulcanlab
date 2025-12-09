"""Mock helpers for unit tests without database.

This module provides reusable mock fixtures and helper functions for creating
mock database sessions, query chains, and model instances without requiring
a real database connection.
"""

from unittest.mock import MagicMock
from typing import Any, Optional
import pytest


@pytest.fixture
def mock_session():
    """Mock database session for unit tests.

    Provides a fully mocked SQLAlchemy session with:
    - Basic operations: add, commit, rollback, close, delete, refresh, flush
    - Query operations: query() returning chainable mock query
    - Execute operations: execute() for raw SQL

    Returns:
        MagicMock: Mocked session object
    """
    session = MagicMock()

    # Basic session operations
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.delete = MagicMock()
    session.refresh = MagicMock()
    session.flush = MagicMock()
    session.expunge = MagicMock()
    session.expunge_all = MagicMock()

    # Query operations (chainable)
    mock_query = MagicMock()
    mock_query.filter = MagicMock(return_value=mock_query)
    mock_query.filter_by = MagicMock(return_value=mock_query)
    mock_query.order_by = MagicMock(return_value=mock_query)
    mock_query.limit = MagicMock(return_value=mock_query)
    mock_query.offset = MagicMock(return_value=mock_query)
    mock_query.all = MagicMock(return_value=[])
    mock_query.first = MagicMock(return_value=None)
    mock_query.count = MagicMock(return_value=0)
    mock_query.scalar = MagicMock(return_value=0)
    mock_query.one = MagicMock(return_value=None)
    mock_query.one_or_none = MagicMock(return_value=None)
    session.query = MagicMock(return_value=mock_query)

    # Execute operations
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(return_value=[])
    mock_result.fetchone = MagicMock(return_value=None)
    mock_result.scalar = MagicMock(return_value=None)
    session.execute = MagicMock(return_value=mock_result)

    return session


def create_mock_query_chain(
    return_data: Optional[list] = None,
    return_first: Optional[Any] = None,
    return_count: int = 0,
    return_scalar: Optional[Any] = None
):
    """Create a chainable mock query for testing.

    Args:
        return_data: List of objects to return from .all()
        return_first: Object to return from .first()
        return_count: Integer to return from .count()
        return_scalar: Value to return from .scalar()

    Returns:
        MagicMock: Chainable query mock
    """
    if return_data is None:
        return_data = []
    if return_first is None and return_data:
        return_first = return_data[0]

    mock_query = MagicMock()
    mock_query.filter = MagicMock(return_value=mock_query)
    mock_query.filter_by = MagicMock(return_value=mock_query)
    mock_query.order_by = MagicMock(return_value=mock_query)
    mock_query.limit = MagicMock(return_value=mock_query)
    mock_query.offset = MagicMock(return_value=mock_query)
    mock_query.join = MagicMock(return_value=mock_query)
    mock_query.outerjoin = MagicMock(return_value=mock_query)
    mock_query.group_by = MagicMock(return_value=mock_query)
    mock_query.having = MagicMock(return_value=mock_query)
    mock_query.distinct = MagicMock(return_value=mock_query)
    mock_query.all = MagicMock(return_value=return_data)
    mock_query.first = MagicMock(return_value=return_first)
    mock_query.count = MagicMock(return_value=return_count)
    mock_query.scalar = MagicMock(return_value=return_scalar)
    mock_query.one = MagicMock(return_value=return_first)
    mock_query.one_or_none = MagicMock(return_value=return_first)

    return mock_query


def configure_mock_session_query(
    mock_session,
    model_class: Any,
    return_data: Optional[list] = None,
    return_first: Optional[Any] = None,
    return_count: int = 0
):
    """Configure a mock session to return specific data for queries.

    Args:
        mock_session: The mock session to configure
        model_class: The model class being queried (for verification)
        return_data: List of objects to return from .all()
        return_first: Object to return from .first()
        return_count: Integer to return from .count()

    Returns:
        MagicMock: The configured query mock
    """
    mock_query = create_mock_query_chain(
        return_data=return_data,
        return_first=return_first,
        return_count=return_count
    )
    mock_session.query.return_value = mock_query
    return mock_query


def create_mock_work(id: int = 1, title: str = "Test Work", **kwargs):
    """Create a mock Work instance.

    Args:
        id: Work ID
        title: Work title
        **kwargs: Additional fields (authors, year, publisher, etc.)

    Returns:
        MagicMock: Mock Work object
    """
    work = MagicMock()
    work.id = id
    work.title = title
    work.authors = kwargs.get('authors', 'Test Author')
    work.year = kwargs.get('year')
    work.publisher = kwargs.get('publisher')
    work.isbn = kwargs.get('isbn')
    work.url = kwargs.get('url')
    work.file_path = kwargs.get('file_path')
    work.file_name = kwargs.get('file_name')
    work.file_type = kwargs.get('file_type')
    work.created_at = kwargs.get('created_at')
    work.updated_at = kwargs.get('updated_at')
    return work


def create_mock_chunk(
    id: int = 1,
    work_id: int = 1,
    level: str = "H1",
    content: str = "Test content",
    **kwargs
):
    """Create a mock Chunk instance.

    Args:
        id: Chunk ID
        work_id: Associated Work ID
        level: Heading level (H1, H2, etc.)
        content: Chunk content
        **kwargs: Additional fields (parent_id, embedding, etc.)

    Returns:
        MagicMock: Mock Chunk object
    """
    chunk = MagicMock()
    chunk.id = id
    chunk.work_id = work_id
    chunk.level = level
    chunk.content = content
    chunk.parent_id = kwargs.get('parent_id')
    chunk.start_line = kwargs.get('start_line', 1)
    chunk.end_line = kwargs.get('end_line', 10)
    chunk.vector_status = kwargs.get('vector_status', 'no_vec')
    chunk.embedding = kwargs.get('embedding')
    chunk.heading_breadcrumbs = kwargs.get('heading_breadcrumbs')
    chunk.heading_text = kwargs.get('heading_text')
    chunk.chunk_index = kwargs.get('chunk_index', 0)
    chunk.created_at = kwargs.get('created_at')
    chunk.updated_at = kwargs.get('updated_at')
    return chunk


def create_mock_query(
    id: int = 1,
    original_query: str = "Test query",
    **kwargs
):
    """Create a mock Query instance.

    Args:
        id: Query ID
        original_query: Original query text
        **kwargs: Additional fields (expanded_queries, embeddings, etc.)

    Returns:
        MagicMock: Mock Query object
    """
    query = MagicMock()
    query.id = id
    query.original_query = original_query
    query.expanded_queries = kwargs.get('expanded_queries')
    query.hyde_answer = kwargs.get('hyde_answer')
    query.intent = kwargs.get('intent')
    query.entities = kwargs.get('entities')
    query.embedding_original = kwargs.get('embedding_original')
    query.embeddings_mqe = kwargs.get('embeddings_mqe')
    query.embedding_hyde = kwargs.get('embedding_hyde')
    query.vector_status = kwargs.get('vector_status', 'no_vec')
    query.created_at = kwargs.get('created_at')
    query.updated_at = kwargs.get('updated_at')
    return query


def create_mock_prompt_template(
    id: int = 1,
    name: str = "test_template",
    template_text: str = "Test template: {input}",
    **kwargs
):
    """Create a mock PromptTemplate instance.

    Args:
        id: Template ID
        name: Template name
        template_text: Template text with placeholders
        **kwargs: Additional fields (description, category, etc.)

    Returns:
        MagicMock: Mock PromptTemplate object
    """
    template = MagicMock()
    template.id = id
    template.name = name
    template.template_text = template_text
    template.description = kwargs.get('description')
    template.category = kwargs.get('category')
    template.created_at = kwargs.get('created_at')
    template.updated_at = kwargs.get('updated_at')
    return template


def create_mock_prompt_meta(
    id: int = 1,
    key: str = "test_key",
    value: dict = None,
    **kwargs
):
    """Create a mock PromptMeta instance.

    Args:
        id: PromptMeta ID
        key: Metadata key
        value: Metadata value (dict/JSONB)
        **kwargs: Additional fields

    Returns:
        MagicMock: Mock PromptMeta object
    """
    if value is None:
        value = {"test": "data"}

    meta = MagicMock()
    meta.id = id
    meta.key = key
    meta.value = value
    meta.created_at = kwargs.get('created_at')
    meta.updated_at = kwargs.get('updated_at')
    return meta


def create_mock_result(
    id: int = 1,
    query_id: int = 1,
    chunk_id: int = 1,
    **kwargs
):
    """Create a mock Result instance.

    Args:
        id: Result ID
        query_id: Associated Query ID
        chunk_id: Associated Chunk ID
        **kwargs: Additional fields (score, rank, etc.)

    Returns:
        MagicMock: Mock Result object
    """
    result = MagicMock()
    result.id = id
    result.query_id = query_id
    result.chunk_id = chunk_id
    result.score = kwargs.get('score', 0.0)
    result.rank = kwargs.get('rank', 1)
    result.retrieval_method = kwargs.get('retrieval_method')
    result.created_at = kwargs.get('created_at')
    return result


def create_mock_io_file(
    id: int = 1,
    file_path: str = "test.txt",
    file_type: str = "txt",
    **kwargs
):
    """Create a mock IoFile instance.

    Args:
        id: IoFile ID
        file_path: File path
        file_type: File type
        **kwargs: Additional fields (status, etc.)

    Returns:
        MagicMock: Mock IoFile object
    """
    io_file = MagicMock()
    io_file.id = id
    io_file.file_path = file_path
    io_file.file_type = file_type
    io_file.filename = kwargs.get('filename')
    io_file.status = kwargs.get('status', 'pending')
    io_file.created_at = kwargs.get('created_at')
    io_file.updated_at = kwargs.get('updated_at')
    return io_file
