"""
Unit tests for Chunk model.

Tests model creation, relationships (parent, work, children), vector embedding field,
and basic logic. Database-specific tests (CASCADE, constraints) moved to integration tests.
"""

import pytest
from unittest.mock import MagicMock, patch

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.work import Work


class TestChunkCreation:
    """Test basic model creation and field values."""

    def test_create_chunk_basic(self):
        """Test creating a Chunk with basic fields."""
        chunk = Chunk(
            work_id=1,
            level="H1",
            content="Chapter 1 content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )

        assert chunk.work_id == 1
        assert chunk.level == "H1"
        assert chunk.content == "Chapter 1 content"
        assert chunk.start_line == 1
        assert chunk.end_line == 10
        assert chunk.vector_status == "no_vec"
        assert chunk.parent_id is None
        assert chunk.embedding is None
        assert chunk.heading_breadcrumbs is None

    def test_create_chunk_with_parent(self):
        """Test creating a Chunk with parent relationship."""
        parent_chunk = Chunk(
            work_id=1,
            level="H1",
            content="Parent content",
            start_line=1,
            end_line=20,
            vector_status="no_vec"
        )

        child_chunk = Chunk(
            work_id=1,
            parent_id=1,  # Assume parent has id=1
            level="H2",
            content="Child content",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )

        assert child_chunk.parent_id == 1
        assert child_chunk.level == "H2"

    def test_create_chunk_with_breadcrumbs(self):
        """Test creating a Chunk with heading breadcrumbs."""
        chunk = Chunk(
            work_id=1,
            level="H3",
            content="Subsection content",
            heading_breadcrumbs="H1 > H2 > H3",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )

        assert chunk.heading_breadcrumbs == "H1 > H2 > H3"

    def test_repr(self):
        """Test __repr__ method."""
        chunk = Chunk(
            work_id=1,
            level="H1",
            content="Test content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        # Simulate that chunk has been assigned an ID
        chunk.id = 1

        repr_str = repr(chunk)
        assert "Chunk" in repr_str
        assert "1" in repr_str
        assert "H1" in repr_str


class TestChunkRelationships:
    """Test relationships (parent, work, children)."""

    def test_chunk_has_work_id(self):
        """Test that Chunk has work_id attribute."""
        chunk = Chunk(
            work_id=5,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )

        assert chunk.work_id == 5

    def test_parent_child_ids(self):
        """Test parent-child ID relationships."""
        parent = Chunk(
            work_id=1,
            level="H1",
            content="Parent",
            start_line=1,
            end_line=20,
            vector_status="no_vec"
        )
        parent.id = 10  # Simulate database-assigned ID

        child1 = Chunk(
            work_id=1,
            parent_id=parent.id,
            level="H2",
            content="Child 1",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )
        child2 = Chunk(
            work_id=1,
            parent_id=parent.id,
            level="H2",
            content="Child 2",
            start_line=31,
            end_line=40,
            vector_status="no_vec"
        )

        # Test parent_id is set correctly
        assert child1.parent_id == parent.id
        assert child2.parent_id == parent.id
        assert child1.parent_id == 10
        assert child2.parent_id == 10


class TestChunkVectorField:
    """Test vector embedding field handling."""

    def test_chunk_embedding_nullable(self):
        """Test that embedding field can be None."""
        chunk = Chunk(
            work_id=1,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec",
            embedding=None
        )

        assert chunk.embedding is None

    def test_chunk_embedding_can_be_set(self):
        """Test that embedding can be set to a list."""
        embedding_vector = [0.1] * 768
        chunk = Chunk(
            work_id=1,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="vec",
            embedding=embedding_vector
        )

        assert chunk.embedding == embedding_vector
        assert len(chunk.embedding) == 768

    def test_chunk_vector_status_values(self):
        """Test different vector_status values."""
        statuses = ["no_vec", "to_vec", "vec", "vec_err"]
        chunks = []

        for status in statuses:
            chunk = Chunk(
                work_id=1,
                level="H1",
                content=f"Content {status}",
                start_line=1,
                end_line=10,
                vector_status=status
            )
            chunks.append(chunk)

        for i, status in enumerate(statuses):
            assert chunks[i].vector_status == status


class TestChunkCRUD:
    """Test CRUD operations with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_chunk(self, mock_get_session):
        """Test creating a Chunk."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            work = Work(title="Test Work", authors="Test Author")
            work.id = 1  # Simulate database-assigned ID

            chunk = Chunk(
                work_id=work.id,
                level="H1",
                content="Created chunk",
                start_line=1,
                end_line=10,
                vector_status="no_vec"
            )
            session.add(chunk)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()
            assert chunk.content == "Created chunk"

    @patch('vulcanlab.data.database.get_session')
    def test_update_chunk(self, mock_get_session):
        """Test updating a Chunk."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            chunk = Chunk(
                work_id=1,
                level="H1",
                content="Original content",
                start_line=1,
                end_line=10,
                vector_status="no_vec"
            )
            chunk.id = 1

            # Update content and vector_status
            chunk.content = "Updated content"
            chunk.vector_status = "vec"
            chunk.heading_breadcrumbs = "H1 > H2"
            session.commit()

            assert chunk.content == "Updated content"
            assert chunk.vector_status == "vec"
            assert chunk.heading_breadcrumbs == "H1 > H2"
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_delete_chunk(self, mock_get_session):
        """Test deleting a Chunk."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            chunk = Chunk(
                work_id=1,
                level="H1",
                content="Chunk to delete",
                start_line=1,
                end_line=10,
                vector_status="no_vec"
            )
            chunk.id = 1

            session.delete(chunk)
            session.commit()

            session.delete.assert_called_once_with(chunk)
            session.commit.assert_called_once()

    def test_chunk_attributes_independent(self):
        """Test that chunk attributes can be set and read independently."""
        chunk1 = Chunk(
            work_id=1,
            level="H1",
            content="Chunk 1",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        chunk2 = Chunk(
            work_id=1,
            level="H2",
            content="Chunk 2",
            start_line=11,
            end_line=20,
            vector_status="no_vec"
        )
        chunk3 = Chunk(
            work_id=2,
            level="H1",
            content="Chunk 3",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )

        # Verify attributes are independent
        assert chunk1.work_id == 1
        assert chunk2.work_id == 1
        assert chunk3.work_id == 2
        assert chunk1.level == "H1"
        assert chunk2.level == "H2"

    def test_chunks_with_different_levels(self):
        """Test creating chunks with different levels."""
        h1_chunk = Chunk(
            work_id=1,
            level="H1",
            content="H1 chunk",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        h2_chunk = Chunk(
            work_id=1,
            level="H2",
            content="H2 chunk",
            start_line=11,
            end_line=20,
            vector_status="no_vec"
        )
        another_h1 = Chunk(
            work_id=1,
            level="H1",
            content="Another H1 chunk",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )

        assert h1_chunk.level == "H1"
        assert h2_chunk.level == "H2"
        assert another_h1.level == "H1"

    def test_chunks_with_different_vector_statuses(self):
        """Test creating chunks with different vector_status values."""
        no_vec_chunk = Chunk(
            work_id=1,
            level="H1",
            content="No vec chunk",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        vec_chunk = Chunk(
            work_id=1,
            level="H2",
            content="Vec chunk",
            start_line=11,
            end_line=20,
            vector_status="vec"
        )

        assert no_vec_chunk.vector_status == "no_vec"
        assert vec_chunk.vector_status == "vec"

    def test_chunk_tablename(self):
        """Test that Chunk uses correct table name."""
        assert Chunk.__tablename__ == "chunks"


class TestChunkSentenceCount:
    """Test sentence_count field handling."""

    def test_chunk_has_sentence_count_attribute(self):
        """Test that Chunk model has sentence_count attribute."""
        chunk = Chunk(
            work_id=1,
            level="chunk",
            content="Test content with multiple sentences. This is sentence two.",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )

        # Verify attribute exists
        assert hasattr(chunk, 'sentence_count')

    def test_sentence_count_nullable(self):
        """Test that sentence_count field can be None."""
        chunk = Chunk(
            work_id=1,
            level="H1",
            content="Heading content",
            start_line=1,
            end_line=10,
            vector_status="no_vec",
            sentence_count=None
        )

        assert chunk.sentence_count is None

    def test_sentence_count_accepts_integer(self):
        """Test that sentence_count accepts integer values."""
        chunk = Chunk(
            work_id=1,
            level="chunk",
            content="Content chunk with sentences.",
            start_line=1,
            end_line=10,
            vector_status="no_vec",
            sentence_count=5
        )

        assert chunk.sentence_count == 5
        assert isinstance(chunk.sentence_count, int)

    def test_create_chunk_with_sentence_count_none(self):
        """Test model instantiation with sentence_count=None works."""
        chunk = Chunk(
            work_id=1,
            level="H1",
            content="Heading",
            start_line=1,
            end_line=5,
            vector_status="no_vec",
            sentence_count=None
        )

        assert chunk.sentence_count is None
        assert chunk.work_id == 1
        assert chunk.level == "H1"

    def test_create_chunk_with_sentence_count_value(self):
        """Test model instantiation with sentence_count=5 works."""
        chunk = Chunk(
            work_id=1,
            level="chunk",
            content="This is a content chunk. It has multiple sentences.",
            start_line=10,
            end_line=20,
            vector_status="no_vec",
            sentence_count=2
        )

        assert chunk.sentence_count == 2
        assert chunk.work_id == 1
        assert chunk.level == "chunk"

    def test_sentence_count_default_is_none(self):
        """Test that sentence_count defaults to None when not specified."""
        chunk = Chunk(
            work_id=1,
            level="H2",
            content="Heading content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )

        # When not specified, should be None
        assert chunk.sentence_count is None

    def test_sentence_count_various_values(self):
        """Test sentence_count with various integer values."""
        test_values = [1, 3, 10, 25, 100]

        for value in test_values:
            chunk = Chunk(
                work_id=1,
                level="chunk",
                content=f"Chunk with {value} sentences",
                start_line=1,
                end_line=10,
                vector_status="no_vec",
                sentence_count=value
            )
            assert chunk.sentence_count == value

    @patch('vulcanlab.data.database.get_session')
    def test_update_chunk_sentence_count(self, mock_get_session):
        """Test updating sentence_count on an existing chunk."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            chunk = Chunk(
                work_id=1,
                level="chunk",
                content="Original content",
                start_line=1,
                end_line=10,
                vector_status="no_vec",
                sentence_count=None
            )
            chunk.id = 1

            # Update sentence_count
            chunk.sentence_count = 7
            session.commit()

            assert chunk.sentence_count == 7
            session.commit.assert_called_once()


# NOTE: The following tests have been moved to integration tests as they require
# a real database to test database-level behavior. See documentation/integration-tests-needed.md
#
# Removed tests (now in integration tests):
# - test_cascade_delete_from_work - Tests CASCADE DELETE from Work to Chunks
# - test_cascade_delete_from_parent - Tests CASCADE DELETE from parent to child Chunks
# - test_work_id_required - Tests NOT NULL constraint on work_id
# - test_level_required - Tests NOT NULL constraint on level
# - test_content_required - Tests NOT NULL constraint on content
# - test_start_line_required - Tests NOT NULL constraint on start_line
# - test_end_line_required - Tests NOT NULL constraint on end_line
# - test_vector_status_required - Tests NOT NULL constraint on vector_status
# - test_foreign_key_constraint_work - Tests FK constraint to Work table
# - test_foreign_key_constraint_parent - Tests FK constraint to parent Chunk
# - test_read_chunk - Tests actual database query/retrieval
# - test_query_by_work_id - Tests database filtering by work_id
# - test_query_by_level - Tests database filtering by level
# - test_query_by_vector_status - Tests database filtering by vector_status
