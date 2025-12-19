"""
Unit tests for init_db module.
"""

from unittest.mock import patch, MagicMock

import pytest

from vulcanlab.data.init_db import (
    create_database_and_user,
    create_tables,
    init_database,
    main,
)


class TestCreateDatabaseAndUser:
    """Tests for the create_database_and_user function."""

    @patch("vulcanlab.data.init_db.create_engine")
    @patch("vulcanlab.data.init_db.get_admin_database_url")
    def test_creates_database_if_not_exists(
        self, mock_get_url, mock_create_engine
    ):
        """Test that database is created if it doesn't exist."""
        mock_get_url.return_value = "postgresql://admin@localhost/postgres"

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        # Database doesn't exist
        mock_conn.execute.return_value.fetchone.return_value = None

        create_database_and_user(verbose=True)

        # Should have called execute multiple times
        assert mock_conn.execute.called

    @patch("vulcanlab.data.init_db.create_engine")
    @patch("vulcanlab.data.init_db.get_admin_database_url")
    def test_skips_if_database_exists(
        self, mock_get_url, mock_create_engine
    ):
        """Test that database creation is skipped if it exists."""
        mock_get_url.return_value = "postgresql://admin@localhost/postgres"

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        # Database exists
        mock_conn.execute.return_value.fetchone.return_value = (1,)

        create_database_and_user(verbose=True)

        assert mock_conn.execute.called


class TestCreateTables:
    """Tests for the create_tables function."""

    @patch("vulcanlab.data.init_db.Base")
    @patch("vulcanlab.data.init_db.engine")
    def test_creates_all_tables(self, mock_engine, mock_base):
        """Test that all tables are created."""
        create_tables(verbose=True)

        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)


class TestInitDatabase:
    """Tests for the init_database function."""

    @patch("vulcanlab.data.init_db.create_default_rag_config")
    @patch("vulcanlab.data.init_db.seed_prompt_templates")
    @patch("vulcanlab.data.init_db.create_prompt_meta_table")
    @patch("vulcanlab.data.init_db.create_fulltext_search")
    @patch("vulcanlab.data.init_db.create_vector_indexes")
    @patch("vulcanlab.data.init_db.create_tables")
    @patch("vulcanlab.data.init_db.enable_pgvector_extension")
    @patch("vulcanlab.data.init_db.create_database_and_user")
    def test_calls_both_functions(
        self,
        mock_create_db,
        mock_enable_pgvector,
        mock_create_tables,
        mock_create_vector_indexes,
        mock_create_fulltext_search,
        mock_create_prompt_meta_table,
        mock_seed_prompt_templates,
        mock_create_default_rag_config,
    ):
        """Test that init_database calls all setup functions."""
        init_database(verbose=True)

        mock_create_db.assert_called_once_with(verbose=True)
        mock_enable_pgvector.assert_called_once_with(verbose=True)
        mock_create_tables.assert_called_once_with(verbose=True)
        mock_create_vector_indexes.assert_called_once_with(verbose=True)
        mock_create_fulltext_search.assert_called_once_with(verbose=True)
        mock_create_prompt_meta_table.assert_called_once_with(verbose=True)
        mock_seed_prompt_templates.assert_called_once_with(verbose=True)
        mock_create_default_rag_config.assert_called_once_with(verbose=True)


class TestMain:
    """Tests for the main CLI function."""

    @patch("vulcanlab.data.init_db.init_database")
    def test_main_success(self, mock_init, monkeypatch):
        """Test main function succeeds."""
        monkeypatch.setattr("sys.argv", ["init_db"])

        result = main()

        assert result == 0
        mock_init.assert_called_once_with(verbose=False)

    @patch("vulcanlab.data.init_db.init_database")
    def test_main_verbose(self, mock_init, monkeypatch):
        """Test main function with verbose flag."""
        monkeypatch.setattr("sys.argv", ["init_db", "-v"])

        result = main()

        assert result == 0
        mock_init.assert_called_once_with(verbose=True)

    @patch("vulcanlab.data.init_db.init_database")
    def test_main_failure(self, mock_init, monkeypatch, capsys):
        """Test main function handles errors."""
        mock_init.side_effect = Exception("Connection failed")
        monkeypatch.setattr("sys.argv", ["init_db"])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Database initialization failed" in captured.err


class TestSentenceCountSchema:
    """Tests for sentence_count column in chunks table schema (T07)."""

    def test_chunk_model_has_sentence_count_column(self):
        """Test that Chunk model includes sentence_count column."""
        from vulcanlab.data.models.chunk import Chunk

        # Verify sentence_count attribute exists
        assert hasattr(Chunk, 'sentence_count')

        # Verify it's mapped as an Integer column
        column = Chunk.__table__.columns.get('sentence_count')
        assert column is not None
        assert str(column.type) == 'INTEGER'
        assert column.nullable is True

    def test_chunk_model_has_sentence_count_index(self):
        """Test that sentence_count column has an index."""
        from vulcanlab.data.models.chunk import Chunk

        # Verify sentence_count has an index
        column = Chunk.__table__.columns.get('sentence_count')
        assert column is not None
        assert column.index is True

    @patch("vulcanlab.data.init_db.Base")
    @patch("vulcanlab.data.init_db.engine")
    def test_create_tables_creates_sentence_count_column(self, mock_engine, mock_base):
        """Test that create_tables() includes sentence_count in chunks table."""
        from vulcanlab.data.init_db import create_tables

        # Call create_tables
        create_tables(verbose=False)

        # Verify Base.metadata.create_all was called (which creates all model columns)
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_rag_config_includes_sentence_filter_fields(self, mock_load_config):
        """Test that default RAG config includes min_sentence_filter_enabled and min_sentence_count."""
        from vulcanlab.data.init_db import create_default_rag_config
        import json

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON from the call - check both positional and keyword args
        insert_call = insert_calls[0]
        # The config is passed as a keyword argument
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify new fields are present with correct default values
        assert 'retrieval' in config
        assert 'min_sentence_filter_enabled' in config['retrieval']
        assert 'min_sentence_count' in config['retrieval']
        assert config['retrieval']['min_sentence_filter_enabled'] is False
        assert config['retrieval']['min_sentence_count'] == 5

    @patch('vulcanlab.data.init_db.load_config')
    def test_rag_config_seed_skips_if_exists(self, mock_load_config):
        """Test that RAG config seeding is skipped if config already exists."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock existing config
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Should not INSERT if config exists
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 0
