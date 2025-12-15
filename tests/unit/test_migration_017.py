"""
Unit tests for migration 017: Add history query indexes.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy import text


class TestMigration017SQL:
    """Tests for migration 017 SQL file content."""

    def test_migration_file_exists(self):
        """Test that migration file exists."""
        import os
        assert os.path.exists("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql")

    def test_migration_uses_if_not_exists(self):
        """Test that both index creations use IF NOT EXISTS for idempotency."""
        with open("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql", "r") as f:
            content = f.read()

        assert content.count("IF NOT EXISTS") >= 2
        assert "CREATE INDEX IF NOT EXISTS ix_works_created_at" in content
        assert "CREATE INDEX IF NOT EXISTS ix_works_simple_conversion_created_at" in content

    def test_migration_uses_transaction_wrapper(self):
        """Test that migration uses BEGIN/COMMIT for atomicity."""
        with open("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql", "r") as f:
            content = f.read()

        assert "BEGIN;" in content
        assert "COMMIT;" in content

    def test_migration_creates_general_timestamp_index(self):
        """Test that migration SQL includes general timestamp index."""
        with open("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql", "r") as f:
            content = f.read()

        assert "ix_works_created_at" in content
        assert "ON works (created_at DESC)" in content

    def test_migration_creates_partial_index_for_simple_conversion(self):
        """Test that migration SQL includes partial index."""
        with open("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql", "r") as f:
            content = f.read()

        assert "ix_works_simple_conversion_created_at" in content
        assert "WHERE (processing_status ? 'simple_conversion_mode')" in content

    def test_partial_index_where_clause_syntax(self):
        """Test that partial index WHERE clause uses correct JSONB operator."""
        with open("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql", "r") as f:
            content = f.read()

        assert "processing_status ? 'simple_conversion_mode'" in content
        assert "WHERE" in content

    def test_migration_has_rollback_instructions(self):
        """Test that migration includes rollback instructions."""
        with open("/home/dardawk/python/vulcanlab/migrations/017_add_history_indexes.sql", "r") as f:
            content = f.read()

        assert "DROP INDEX IF EXISTS" in content
        assert "Rollback" in content or "rollback" in content


class TestInitDBHistoryIndexes:
    """Tests for init_db.py history index creation."""

    def test_create_history_indexes_function_exists(self):
        """Test that create_history_indexes function is defined in init_db.py."""
        from vulcanlab.data.init_db import create_history_indexes

        assert callable(create_history_indexes)

    def test_create_history_indexes_creates_both_indexes(self):
        """Test that create_history_indexes executes two SQL statements."""
        from vulcanlab.data.init_db import create_history_indexes

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            create_history_indexes(verbose=False)

        # Should execute 2 CREATE INDEX statements
        assert mock_conn.execute.call_count == 2
        # Should call commit once
        assert mock_conn.commit.call_count == 1

    def test_init_database_calls_create_history_indexes(self):
        """Test that init_database function calls create_history_indexes."""
        from vulcanlab.data.init_db import init_database

        with patch('vulcanlab.data.init_db.create_database_and_user'), \
             patch('vulcanlab.data.init_db.enable_pgvector_extension'), \
             patch('vulcanlab.data.init_db.create_tables'), \
             patch('vulcanlab.data.init_db.create_vector_indexes'), \
             patch('vulcanlab.data.init_db.create_fulltext_search'), \
             patch('vulcanlab.data.init_db.create_history_indexes') as mock_history_indexes, \
             patch('vulcanlab.data.init_db.create_prompt_meta_table'), \
             patch('vulcanlab.data.init_db.seed_prompt_templates'), \
             patch('vulcanlab.data.init_db.seed_simple_conversion_templates'), \
             patch('vulcanlab.data.init_db.create_default_rag_config'):

            init_database(verbose=False)

            mock_history_indexes.assert_called_once_with(verbose=False)

    def test_create_history_indexes_calls_commit(self):
        """Test that create_history_indexes commits the transaction."""
        from vulcanlab.data.init_db import create_history_indexes

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            create_history_indexes(verbose=False)

        # Verify commit was called
        mock_conn.commit.assert_called_once()

    def test_init_database_calls_in_correct_order(self):
        """Test that create_history_indexes is called after create_fulltext_search."""
        from vulcanlab.data.init_db import init_database

        call_order = []

        def track_fulltext(*args, **kwargs):
            call_order.append('fulltext')

        def track_history(*args, **kwargs):
            call_order.append('history')

        def track_prompt_meta(*args, **kwargs):
            call_order.append('prompt_meta')

        with patch('vulcanlab.data.init_db.create_database_and_user'), \
             patch('vulcanlab.data.init_db.enable_pgvector_extension'), \
             patch('vulcanlab.data.init_db.create_tables'), \
             patch('vulcanlab.data.init_db.create_vector_indexes'), \
             patch('vulcanlab.data.init_db.create_fulltext_search', side_effect=track_fulltext), \
             patch('vulcanlab.data.init_db.create_history_indexes', side_effect=track_history), \
             patch('vulcanlab.data.init_db.create_prompt_meta_table', side_effect=track_prompt_meta), \
             patch('vulcanlab.data.init_db.seed_prompt_templates'), \
             patch('vulcanlab.data.init_db.seed_simple_conversion_templates'), \
             patch('vulcanlab.data.init_db.create_default_rag_config'):

            init_database(verbose=False)

            # Verify order: fulltext -> history -> prompt_meta
            assert call_order == ['fulltext', 'history', 'prompt_meta']
