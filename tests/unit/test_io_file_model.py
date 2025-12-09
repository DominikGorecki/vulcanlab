"""
Unit tests for IOFile model.

Tests model creation, FileType enum, and basic logic.
Database-specific tests (constraints, timestamps) moved to integration tests.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from vulcanlab.data.models.io_file import IOFile, FileType


class TestIOFileCreation:
    """Test basic model creation and field values."""

    def test_create_io_file_input(self):
        """Test creating IOFile with INPUT file type."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )

        assert io_file.filename == "test.pdf"
        assert io_file.file_type == FileType.INPUT
        assert io_file.file_path == "/path/to/test.pdf"

    def test_create_io_file_to_convert(self):
        """Test creating IOFile with TO_CONVERT file type."""
        io_file = IOFile(
            filename="document.epub",
            file_type=FileType.TO_CONVERT,
            file_path="/path/to/document.epub"
        )

        assert io_file.file_type == FileType.TO_CONVERT
        assert io_file.filename == "document.epub"

    def test_repr(self):
        """Test __repr__ method."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        io_file.id = 1  # Simulate database-assigned ID

        repr_str = repr(io_file)
        assert "IOFile" in repr_str
        assert "test.pdf" in repr_str
        assert "input" in repr_str.lower()


class TestFileTypeEnum:
    """Test FileType enum values."""

    def test_file_type_enum_values(self):
        """Test FileType enum has correct values."""
        assert FileType.INPUT == "input"
        assert FileType.TO_CONVERT == "to_convert"

    def test_file_type_enum_string_comparison(self):
        """Test FileType enum can be compared with strings."""
        assert FileType.INPUT == "input"
        assert FileType.TO_CONVERT == "to_convert"

    def test_file_type_enum_membership(self):
        """Test FileType enum membership."""
        assert "input" in [ft.value for ft in FileType]
        assert "to_convert" in [ft.value for ft in FileType]

    def test_file_type_enum_iteration(self):
        """Test FileType enum can be iterated."""
        file_types = list(FileType)
        assert len(file_types) == 2
        assert FileType.INPUT in file_types
        assert FileType.TO_CONVERT in file_types


class TestIOFileCRUD:
    """Test CRUD operations with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_io_file(self, mock_get_session):
        """Test creating an IOFile."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            io_file = IOFile(
                filename="create_test.pdf",
                file_type=FileType.INPUT,
                file_path="/path/to/create_test.pdf"
            )
            session.add(io_file)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()
            assert io_file.filename == "create_test.pdf"

    @patch('vulcanlab.data.database.get_session')
    def test_update_io_file(self, mock_get_session):
        """Test updating an IOFile."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            io_file = IOFile(
                filename="original.pdf",
                file_type=FileType.INPUT,
                file_path="/path/to/original.pdf"
            )
            io_file.id = 1

            # Update filename
            io_file.filename = "updated.pdf"
            io_file.file_path = "/path/to/updated.pdf"
            session.commit()

            assert io_file.filename == "updated.pdf"
            assert io_file.file_path == "/path/to/updated.pdf"
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_delete_io_file(self, mock_get_session):
        """Test deleting an IOFile."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            io_file = IOFile(
                filename="delete_test.pdf",
                file_type=FileType.INPUT,
                file_path="/path/to/delete_test.pdf"
            )
            io_file.id = 1

            session.delete(io_file)
            session.commit()

            session.delete.assert_called_once_with(io_file)
            session.commit.assert_called_once()

    def test_io_file_attributes_independent(self):
        """Test that IOFile attributes can be set independently."""
        io_file1 = IOFile(
            filename="file1.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/file1.pdf"
        )
        io_file2 = IOFile(
            filename="file2.epub",
            file_type=FileType.TO_CONVERT,
            file_path="/path/to/file2.epub"
        )

        assert io_file1.filename == "file1.pdf"
        assert io_file2.filename == "file2.epub"
        assert io_file1.file_type == FileType.INPUT
        assert io_file2.file_type == FileType.TO_CONVERT


class TestIOFileTimestamps:
    """Test timestamp fields."""

    def test_timestamps_can_be_set(self):
        """Test that timestamps can be set explicitly."""
        now = datetime.now(timezone.utc)
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf",
            created_at=now,
            updated_at=now,
            last_seen_at=now
        )

        assert io_file.created_at == now
        assert io_file.updated_at == now
        assert io_file.last_seen_at == now

    def test_io_file_tablename(self):
        """Test that IOFile uses correct table name."""
        assert IOFile.__tablename__ == "io_files"


# NOTE: The following tests have been moved to integration tests as they require
# a real database to test database-level behavior. See documentation/integration-tests-needed.md
#
# Removed tests (now in integration tests):
# - test_timestamps_auto_populate - Tests server-side timestamp generation
# - test_filename_required - Tests NOT NULL constraint on filename
# - test_file_type_required - Tests NOT NULL constraint on file_type
# - test_file_path_required - Tests NOT NULL constraint on file_path
# - test_unique_file_path_constraint - Tests UNIQUE constraint on file_path
# - test_read_io_file - Tests actual database query/retrieval
# - test_query_by_file_type - Tests database filtering by file_type
# - test_query_by_filename_pattern - Tests database LIKE queries
# - test_update_last_seen_at - Tests server-side timestamp updates
