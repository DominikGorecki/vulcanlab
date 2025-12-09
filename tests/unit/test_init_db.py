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
