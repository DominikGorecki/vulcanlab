"""
Unit tests for schema/indexes.py module.

Tests the ensure_vector_dimensions() function that detects and alters
vector column dimensions in the database.
"""

from unittest.mock import patch, MagicMock, call

import pytest


class TestEnsureVectorDimensions:
    """Tests for the ensure_vector_dimensions function."""

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_detects_768_and_alters_to_1536(self, mock_engine):
        """Test that 768-dimension columns are detected and altered to 1536."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock pg_attribute query returning 768 dimensions (atttypmod = 772)
        # For vector type, atttypmod = dim + 4
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (772,)  # 768 + 4
        mock_conn.execute.return_value = mock_result

        ensure_vector_dimensions(target_dim=1536, verbose=True)

        # Verify execute was called
        assert mock_conn.execute.called

        # Get all SQL statements executed
        execute_calls = mock_conn.execute.call_args_list

        # Should have queries for all 3 columns, plus DROP INDEX and ALTER for each
        # 3 columns x (1 query + 1 drop + 1 alter) + 1 commit = 10 calls total
        # But we need to check the SQL contains expected statements
        sql_statements = [str(c[0][0]) for c in execute_calls]

        # Check DROP INDEX statements for all columns
        drop_statements = [s for s in sql_statements if "DROP INDEX" in s]
        assert len(drop_statements) == 3
        assert any("ix_chunks_embedding_hnsw" in s for s in drop_statements)
        assert any("ix_queries_embedding_original_hnsw" in s for s in drop_statements)
        assert any("ix_queries_embedding_hyde_hnsw" in s for s in drop_statements)

        # Check ALTER statements
        alter_statements = [s for s in sql_statements if "ALTER TABLE" in s]
        assert len(alter_statements) == 3
        assert any("chunks" in s and "vector(1536)" in s for s in alter_statements)
        assert any("queries" in s and "embedding_original" in s and "vector(1536)" in s for s in alter_statements)
        assert any("queries" in s and "embedding_hyde" in s and "vector(1536)" in s for s in alter_statements)

        # Verify commit was called
        mock_conn.commit.assert_called_once()

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_skips_when_already_1536(self, mock_engine):
        """Test that columns already at 1536 dimensions are skipped."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock pg_attribute query returning 1536 dimensions (atttypmod = 1540)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1540,)  # 1536 + 4
        mock_conn.execute.return_value = mock_result

        ensure_vector_dimensions(target_dim=1536, verbose=True)

        # Get all SQL statements executed
        sql_statements = [str(c[0][0]) for c in mock_conn.execute.call_args_list]

        # Should NOT have DROP INDEX statements
        drop_statements = [s for s in sql_statements if "DROP INDEX" in s]
        assert len(drop_statements) == 0

        # Should NOT have ALTER statements
        alter_statements = [s for s in sql_statements if "ALTER TABLE" in s]
        assert len(alter_statements) == 0

        # Verify commit was still called
        mock_conn.commit.assert_called_once()

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_drops_indexes_before_alter(self, mock_engine):
        """Test that HNSW indexes are dropped before ALTER COLUMN."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Track call order
        call_order = []

        def track_execute(query, *args, **kwargs):
            query_str = str(query)
            if "pg_attribute" in query_str:
                call_order.append("query")
                result = MagicMock()
                result.fetchone.return_value = (772,)  # 768 + 4
                return result
            elif "DROP INDEX" in query_str:
                call_order.append("drop")
                return MagicMock()
            elif "ALTER TABLE" in query_str:
                call_order.append("alter")
                return MagicMock()
            return MagicMock()

        mock_conn.execute.side_effect = track_execute

        ensure_vector_dimensions(target_dim=1536, verbose=False)

        # For each column: query -> drop -> alter
        # We have 3 columns, so the pattern repeats 3 times
        # Verify that for each column, drop comes before alter
        for i in range(3):
            # Find the index of this column's operations
            start_idx = i * 3
            assert call_order[start_idx] == "query"
            assert call_order[start_idx + 1] == "drop"
            assert call_order[start_idx + 2] == "alter"

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_handles_null_embedding_column(self, mock_engine):
        """Test graceful handling if column not found in pg_attribute."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock pg_attribute query returning None (column not found)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_conn.execute.return_value = mock_result

        # Should not raise an exception
        ensure_vector_dimensions(target_dim=1536, verbose=True)

        # Get all SQL statements executed
        sql_statements = [str(c[0][0]) for c in mock_conn.execute.call_args_list]

        # Should NOT have DROP INDEX or ALTER statements
        drop_statements = [s for s in sql_statements if "DROP INDEX" in s]
        assert len(drop_statements) == 0

        alter_statements = [s for s in sql_statements if "ALTER TABLE" in s]
        assert len(alter_statements) == 0

        # Verify commit was still called
        mock_conn.commit.assert_called_once()

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_handles_atttypmod_negative_one(self, mock_engine):
        """Test handling of atttypmod = -1 (no dimension specified)."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock pg_attribute query returning -1 (no dimension)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (-1,)
        mock_conn.execute.return_value = mock_result

        # Should not raise an exception
        ensure_vector_dimensions(target_dim=1536, verbose=True)

        # Get all SQL statements executed
        sql_statements = [str(c[0][0]) for c in mock_conn.execute.call_args_list]

        # Should NOT have DROP INDEX or ALTER statements
        drop_statements = [s for s in sql_statements if "DROP INDEX" in s]
        assert len(drop_statements) == 0

        alter_statements = [s for s in sql_statements if "ALTER TABLE" in s]
        assert len(alter_statements) == 0

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_custom_target_dimension(self, mock_engine):
        """Test that custom target dimension is used correctly."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock pg_attribute query returning 768 dimensions
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (772,)  # 768 + 4
        mock_conn.execute.return_value = mock_result

        # Use custom target dimension
        ensure_vector_dimensions(target_dim=3072, verbose=False)

        # Get all SQL statements executed
        sql_statements = [str(c[0][0]) for c in mock_conn.execute.call_args_list]

        # Check ALTER statements use custom dimension
        alter_statements = [s for s in sql_statements if "ALTER TABLE" in s]
        assert len(alter_statements) == 3
        assert all("vector(3072)" in s for s in alter_statements)

    @patch("vulcanlab.data.schema.indexes.engine")
    def test_idempotent_multiple_runs(self, mock_engine):
        """Test that function is idempotent - safe to run multiple times."""
        from vulcanlab.data.schema.indexes import ensure_vector_dimensions

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # First run: columns at 768
        mock_result_768 = MagicMock()
        mock_result_768.fetchone.return_value = (772,)

        # Second run: columns at 1536
        mock_result_1536 = MagicMock()
        mock_result_1536.fetchone.return_value = (1540,)

        # First run
        mock_conn.execute.return_value = mock_result_768
        ensure_vector_dimensions(target_dim=1536, verbose=False)

        first_run_calls = len(mock_conn.execute.call_args_list)

        # Reset mock
        mock_conn.reset_mock()

        # Second run - columns are now at 1536
        mock_conn.execute.return_value = mock_result_1536
        ensure_vector_dimensions(target_dim=1536, verbose=False)

        # Get all SQL statements from second run
        sql_statements = [str(c[0][0]) for c in mock_conn.execute.call_args_list]

        # Second run should NOT have DROP or ALTER statements
        drop_statements = [s for s in sql_statements if "DROP INDEX" in s]
        alter_statements = [s for s in sql_statements if "ALTER TABLE" in s]

        assert len(drop_statements) == 0
        assert len(alter_statements) == 0
