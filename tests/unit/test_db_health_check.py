"""
Unit tests for db_health_check module.

Tests database health check functions, connection testing, schema validation,
and error handling.
"""

from unittest.mock import MagicMock, patch, Mock
import pytest
from sqlalchemy.exc import SQLAlchemyError

from vulcanlab.data.db_health_check import (
    HealthCheckResult,
    TimeoutError,
    check_connection,
    check_table_exists,
    check_table_columns,
    check_extension,
    check_index,
    check_trigger,
    check_read_permission,
    check_write_permission,
    run_all_health_checks,
)


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test creating HealthCheckResult with all fields."""
        result = HealthCheckResult(
            name="Test Check",
            passed=True,
            message="Test passed",
            details="Additional details"
        )

        assert result.name == "Test Check"
        assert result.passed is True
        assert result.message == "Test passed"
        assert result.details == "Additional details"

    def test_health_check_result_no_details(self):
        """Test HealthCheckResult without details."""
        result = HealthCheckResult(
            name="Test",
            passed=False,
            message="Test failed"
        )

        assert result.name == "Test"
        assert result.passed is False
        assert result.details is None


class TestCheckConnection:
    """Tests for check_connection function."""

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_connection_success(self, mock_get_engine):
        """Test successful database connection."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_connection()

        assert result.passed is True
        assert result.name == "Connection"
        assert "can connect" in result.message.lower()
        mock_engine.dispose.assert_called_once()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_connection_timeout(self, mock_get_engine):
        """Test connection timeout handling."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_connection()

        assert result.passed is False
        assert result.name == "Connection"
        assert "timeout" in result.message.lower()
        assert result.details is not None

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_connection_sqlalchemy_error(self, mock_get_engine):
        """Test SQLAlchemy error handling."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
        mock_get_engine.return_value = mock_engine

        result = check_connection()

        assert result.passed is False
        assert result.name == "Connection"
        assert "failed to connect" in result.message.lower()
        assert "Connection failed" in result.details

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_connection_unexpected_error(self, mock_get_engine):
        """Test unexpected error handling."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = ValueError("Unexpected error")
        mock_get_engine.return_value = mock_engine

        result = check_connection()

        assert result.passed is False
        assert result.name == "Connection"
        assert "unexpected error" in result.message.lower()
        assert "Unexpected error" in result.details


class TestCheckTableExists:
    """Tests for check_table_exists function."""

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_exists_success(self, mock_get_engine, mock_inspect_func):
        """Test table existence check when table exists."""
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["works", "chunks", "queries"]
        mock_inspect_func.return_value = mock_inspector
        mock_get_engine.return_value = mock_engine

        result = check_table_exists("works")

        assert result.passed is True
        assert result.name == "Table: works"
        assert "exists" in result.message.lower()
        mock_engine.dispose.assert_called_once()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_exists_missing(self, mock_get_engine, mock_inspect_func):
        """Test table existence check when table doesn't exist."""
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["works", "chunks"]
        mock_inspect_func.return_value = mock_inspector
        mock_get_engine.return_value = mock_engine

        result = check_table_exists("nonexistent")

        assert result.passed is False
        assert result.name == "Table: nonexistent"
        assert "does not exist" in result.message.lower()
        assert "init_db" in result.details.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_exists_timeout(self, mock_get_engine, mock_inspect_func):
        """Test table existence check timeout."""
        mock_engine = MagicMock()
        mock_inspect_func.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_table_exists("works")

        assert result.passed is False
        assert "timeout" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_exists_error(self, mock_get_engine, mock_inspect_func):
        """Test table existence check with SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_inspect_func.side_effect = SQLAlchemyError("Database error")
        mock_get_engine.return_value = mock_engine

        result = check_table_exists("works")

        assert result.passed is False
        assert "error" in result.message.lower()
        assert "Database error" in result.details


class TestCheckTableColumns:
    """Tests for check_table_columns function."""

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_columns_success(self, mock_get_engine, mock_inspect_func):
        """Test column check when all required columns exist."""
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_columns.return_value = [
            {"name": "id"},
            {"name": "title"},
            {"name": "authors"},
            {"name": "year"},
        ]
        mock_inspect_func.return_value = mock_inspector
        mock_get_engine.return_value = mock_engine

        result = check_table_columns("works", ["id", "title", "authors"])

        assert result.passed is True
        assert result.name == "Columns: works"
        assert "all required columns exist" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_columns_missing(self, mock_get_engine, mock_inspect_func):
        """Test column check when some columns are missing."""
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_columns.return_value = [
            {"name": "id"},
            {"name": "title"},
        ]
        mock_inspect_func.return_value = mock_inspector
        mock_get_engine.return_value = mock_engine

        result = check_table_columns("works", ["id", "title", "authors", "year"])

        assert result.passed is False
        assert result.name == "Columns: works"
        assert "missing columns" in result.message.lower()
        assert "authors" in result.message or "year" in result.message
        assert "init_db" in result.details.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_columns_timeout(self, mock_get_engine, mock_inspect_func):
        """Test column check timeout."""
        mock_engine = MagicMock()
        mock_inspect_func.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_table_columns("works", ["id", "title"])

        assert result.passed is False
        assert "timeout" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_table_columns_error(self, mock_get_engine, mock_inspect_func):
        """Test column check with SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_inspect_func.side_effect = SQLAlchemyError("Error")
        mock_get_engine.return_value = mock_engine

        result = check_table_columns("works", ["id"])

        assert result.passed is False
        assert "error" in result.message.lower()


class TestCheckExtension:
    """Tests for check_extension function."""

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_extension_exists(self, mock_get_engine):
        """Test extension check when extension exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # Extension exists
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_extension("vector")

        assert result.passed is True
        assert result.name == "Extension: vector"
        assert "is installed" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_extension_missing(self, mock_get_engine):
        """Test extension check when extension doesn't exist."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # Extension doesn't exist
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_extension("nonexistent")

        assert result.passed is False
        assert result.name == "Extension: nonexistent"
        assert "is not installed" in result.message.lower()
        assert "init_db" in result.details.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_extension_timeout(self, mock_get_engine):
        """Test extension check timeout."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_extension("vector")

        assert result.passed is False
        assert "timeout" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_extension_error(self, mock_get_engine):
        """Test extension check with SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Error")
        mock_get_engine.return_value = mock_engine

        result = check_extension("vector")

        assert result.passed is False
        assert "error" in result.message.lower()


class TestCheckIndex:
    """Tests for check_index function."""

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_index_exists(self, mock_get_engine, mock_inspect_func):
        """Test index check when index exists."""
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_indexes.return_value = [
            {"name": "ix_chunks_embedding_hnsw"},
            {"name": "idx_prompt_meta_function_tag"},
        ]
        mock_inspect_func.return_value = mock_inspector
        mock_get_engine.return_value = mock_engine

        result = check_index("ix_chunks_embedding_hnsw", "chunks")

        assert result.passed is True
        assert result.name == "Index: ix_chunks_embedding_hnsw"
        assert "exists" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_index_missing(self, mock_get_engine, mock_inspect_func):
        """Test index check when index doesn't exist."""
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_indexes.return_value = [
            {"name": "other_index"},
        ]
        mock_inspect_func.return_value = mock_inspector
        mock_get_engine.return_value = mock_engine

        result = check_index("missing_index", "chunks")

        assert result.passed is False
        assert result.name == "Index: missing_index"
        assert "does not exist" in result.message.lower()
        assert "init_db" in result.details.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_index_timeout(self, mock_get_engine, mock_inspect_func):
        """Test index check timeout."""
        mock_engine = MagicMock()
        mock_inspect_func.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_index("test_index", "chunks")

        assert result.passed is False
        assert "timeout" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.inspect")
    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_index_error(self, mock_get_engine, mock_inspect_func):
        """Test index check with SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_inspect_func.side_effect = SQLAlchemyError("Error")
        mock_get_engine.return_value = mock_engine

        result = check_index("test_index", "chunks")

        assert result.passed is False
        assert "error" in result.message.lower()


class TestCheckTrigger:
    """Tests for check_trigger function."""

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_trigger_exists(self, mock_get_engine):
        """Test trigger check when trigger exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # Trigger exists
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_trigger("tsvector_update", "chunks")

        assert result.passed is True
        assert result.name == "Trigger: tsvector_update"
        assert "exists" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_trigger_missing(self, mock_get_engine):
        """Test trigger check when trigger doesn't exist."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # Trigger doesn't exist
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_trigger("missing_trigger", "chunks")

        assert result.passed is False
        assert result.name == "Trigger: missing_trigger"
        assert "does not exist" in result.message.lower()
        assert "init_db" in result.details.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_trigger_timeout(self, mock_get_engine):
        """Test trigger check timeout."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_trigger("test_trigger", "chunks")

        assert result.passed is False
        assert "timeout" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_trigger_error(self, mock_get_engine):
        """Test trigger check with SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Error")
        mock_get_engine.return_value = mock_engine

        result = check_trigger("test_trigger", "chunks")

        assert result.passed is False
        assert "error" in result.message.lower()


class TestCheckReadPermission:
    """Tests for check_read_permission function."""

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_read_permission_success(self, mock_get_engine):
        """Test read permission check when permission exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,)]
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_read_permission("works")

        assert result.passed is True
        assert result.name == "Read: works"
        assert "can read" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_read_permission_failure(self, mock_get_engine):
        """Test read permission check when permission is denied."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = SQLAlchemyError("Permission denied")
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_read_permission("works")

        assert result.passed is False
        assert result.name == "Read: works"
        assert "cannot read" in result.message.lower()
        assert "Permission denied" in result.details

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_read_permission_timeout(self, mock_get_engine):
        """Test read permission check timeout."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_read_permission("works")

        assert result.passed is False
        assert "timeout" in result.message.lower()


class TestCheckWritePermission:
    """Tests for check_write_permission function."""

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_write_permission_success(self, mock_get_engine):
        """Test write permission check when permission exists."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_trans = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (True,)  # Has INSERT permission
        mock_conn.execute.return_value = mock_result
        mock_conn.begin.return_value = mock_trans
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_write_permission("works")

        assert result.passed is True
        assert result.name == "Write: works"
        assert "can write" in result.message.lower()
        mock_trans.rollback.assert_called_once()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_write_permission_denied(self, mock_get_engine):
        """Test write permission check when permission is denied."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_trans = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (False,)  # No INSERT permission
        mock_conn.execute.return_value = mock_result
        mock_conn.begin.return_value = mock_trans
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get_engine.return_value = mock_engine

        result = check_write_permission("works")

        assert result.passed is False
        assert result.name == "Write: works"
        assert "cannot write" in result.message.lower()
        assert "INSERT privilege" in result.details

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_write_permission_timeout(self, mock_get_engine):
        """Test write permission check timeout."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = TimeoutError("Timeout")
        mock_get_engine.return_value = mock_engine

        result = check_write_permission("works")

        assert result.passed is False
        assert "timeout" in result.message.lower()

    @patch("vulcanlab.data.db_health_check.get_engine_with_timeout")
    def test_check_write_permission_error(self, mock_get_engine):
        """Test write permission check with SQLAlchemy error."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Error")
        mock_get_engine.return_value = mock_engine

        result = check_write_permission("works")

        assert result.passed is False
        assert "error" in result.message.lower()


class TestRunAllHealthChecks:
    """Tests for run_all_health_checks function."""

    @patch("vulcanlab.data.db_health_check.check_write_permission")
    @patch("vulcanlab.data.db_health_check.check_read_permission")
    @patch("vulcanlab.data.db_health_check.check_trigger")
    @patch("vulcanlab.data.db_health_check.check_index")
    @patch("vulcanlab.data.db_health_check.check_table_columns")
    @patch("vulcanlab.data.db_health_check.check_table_exists")
    @patch("vulcanlab.data.db_health_check.check_extension")
    @patch("vulcanlab.data.db_health_check.check_connection")
    def test_run_all_health_checks_executes_all(
        self,
        mock_check_connection,
        mock_check_extension,
        mock_check_table_exists,
        mock_check_table_columns,
        mock_check_index,
        mock_check_trigger,
        mock_check_read_permission,
        mock_check_write_permission,
    ):
        """Test that run_all_health_checks executes all check functions."""
        # Setup mocks to return successful results
        mock_check_connection.return_value = HealthCheckResult("Connection", True, "OK")
        mock_check_extension.return_value = HealthCheckResult("Extension", True, "OK")
        mock_check_table_exists.return_value = HealthCheckResult("Table", True, "OK")
        mock_check_table_columns.return_value = HealthCheckResult("Columns", True, "OK")
        mock_check_index.return_value = HealthCheckResult("Index", True, "OK")
        mock_check_trigger.return_value = HealthCheckResult("Trigger", True, "OK")
        mock_check_read_permission.return_value = HealthCheckResult("Read", True, "OK")
        mock_check_write_permission.return_value = HealthCheckResult("Write", True, "OK")

        results = run_all_health_checks()

        # Verify all checks were called
        assert mock_check_connection.called
        assert mock_check_extension.called
        assert len(results) > 0

        # Verify structure - should have connection, extension, multiple tables, etc.
        assert len(results) >= 8  # At least connection + extension + some tables

    @patch("vulcanlab.data.db_health_check.check_write_permission")
    @patch("vulcanlab.data.db_health_check.check_read_permission")
    @patch("vulcanlab.data.db_health_check.check_trigger")
    @patch("vulcanlab.data.db_health_check.check_index")
    @patch("vulcanlab.data.db_health_check.check_table_columns")
    @patch("vulcanlab.data.db_health_check.check_table_exists")
    @patch("vulcanlab.data.db_health_check.check_extension")
    @patch("vulcanlab.data.db_health_check.check_connection")
    def test_run_all_health_checks_returns_results(
        self,
        mock_check_connection,
        mock_check_extension,
        mock_check_table_exists,
        mock_check_table_columns,
        mock_check_index,
        mock_check_trigger,
        mock_check_read_permission,
        mock_check_write_permission,
    ):
        """Test that run_all_health_checks returns list of HealthCheckResult."""
        # Setup mocks
        mock_check_connection.return_value = HealthCheckResult("Connection", True, "OK")
        mock_check_extension.return_value = HealthCheckResult("Extension", True, "OK")
        mock_check_table_exists.return_value = HealthCheckResult("Table", True, "OK")
        mock_check_table_columns.return_value = HealthCheckResult("Columns", True, "OK")
        mock_check_index.return_value = HealthCheckResult("Index", True, "OK")
        mock_check_trigger.return_value = HealthCheckResult("Trigger", True, "OK")
        mock_check_read_permission.return_value = HealthCheckResult("Read", True, "OK")
        mock_check_write_permission.return_value = HealthCheckResult("Write", True, "OK")

        results = run_all_health_checks()

        # Verify all results are HealthCheckResult instances
        assert all(isinstance(r, HealthCheckResult) for r in results)
        assert len(results) > 0

