"""
Unit tests for database module.
"""

from unittest.mock import patch, MagicMock

import pytest

from vulcanlab.data.database import (
    get_session,
    get_admin_database_url,
    DATABASE_URL,
)


class TestGetSession:
    """Tests for the get_session context manager."""

    @patch("vulcanlab.data.database.SessionLocal")
    def test_session_yields_and_closes(self, mock_session_local):
        """Test that session is yielded and closed properly."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        with get_session() as session:
            assert session == mock_session

        mock_session.close.assert_called_once()

    @patch("vulcanlab.data.database.SessionLocal")
    def test_session_rollback_on_exception(self, mock_session_local):
        """Test that session is rolled back on exception."""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        with pytest.raises(ValueError):
            with get_session() as session:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestDatabaseUrl:
    """Tests for database URL construction."""

    def test_database_url_format(self):
        """Test that DATABASE_URL has correct format."""
        assert "postgresql+psycopg://" in DATABASE_URL
        assert "@" in DATABASE_URL

    @patch.dict("os.environ", {
        "POSTGRES_ADMIN_USER": "admin",
        "POSTGRES_ADMIN_PASSWORD": "secret",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
    })
    def test_admin_database_url(self):
        """Test admin database URL construction."""
        url = get_admin_database_url()
        assert "postgresql+psycopg://" in url
        assert "admin:secret" in url
        assert "5432" in url
        assert "/postgres" in url
