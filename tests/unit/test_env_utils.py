"""
Unit tests for environment variable utilities.
"""

import os
import pytest
from unittest.mock import patch

from vulcanlab.data.env_utils import (
    get_required_env_var,
    MissingEnvironmentVariableError,
    _build_error_message,
)


class TestGetRequiredEnvVar:
    """Tests for get_required_env_var function."""

    def test_get_existing_env_var(self):
        """Test that existing environment variable is returned."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_required_env_var("TEST_VAR")
            assert result == "test_value"

    def test_get_existing_env_var_with_description(self):
        """Test that description doesn't affect retrieval of existing variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_required_env_var("TEST_VAR", "Test variable description")
            assert result == "test_value"

    def test_missing_env_var_raises_error(self):
        """Test that missing environment variable raises MissingEnvironmentVariableError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingEnvironmentVariableError) as exc_info:
                get_required_env_var("MISSING_VAR")

            error_msg = str(exc_info.value)
            assert "MISSING_VAR" in error_msg
            assert "not set" in error_msg

    def test_missing_env_var_error_includes_description(self):
        """Test that error message includes description when provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingEnvironmentVariableError) as exc_info:
                get_required_env_var("MISSING_VAR", "Important test variable")

            error_msg = str(exc_info.value)
            assert "MISSING_VAR" in error_msg
            assert "Important test variable" in error_msg

    def test_missing_env_var_error_includes_help(self):
        """Test that error message includes helpful setup instructions."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingEnvironmentVariableError) as exc_info:
                get_required_env_var("MISSING_VAR")

            error_msg = str(exc_info.value)
            assert ".env" in error_msg
            assert ".env.example" in error_msg
            assert "README.md" in error_msg

    def test_empty_string_is_valid(self):
        """Test that empty string is considered a valid value."""
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            result = get_required_env_var("EMPTY_VAR")
            assert result == ""

    def test_whitespace_is_valid(self):
        """Test that whitespace-only value is considered valid."""
        with patch.dict(os.environ, {"SPACE_VAR": "   "}):
            result = get_required_env_var("SPACE_VAR")
            assert result == "   "


class TestBuildErrorMessage:
    """Tests for _build_error_message helper function."""

    def test_basic_error_message(self):
        """Test basic error message without description."""
        msg = _build_error_message("TEST_VAR", None)
        assert "TEST_VAR" in msg
        assert "not set" in msg
        assert ".env" in msg

    def test_error_message_with_description(self):
        """Test error message includes description."""
        msg = _build_error_message("TEST_VAR", "Test description")
        assert "TEST_VAR" in msg
        assert "Test description" in msg
        assert "Purpose:" in msg

    def test_error_message_structure(self):
        """Test that error message has proper structure."""
        msg = _build_error_message("TEST_VAR", None)
        lines = msg.split("\n")

        # Should have multiple lines
        assert len(lines) > 5

        # Should start with ERROR
        assert lines[0].startswith("ERROR:")

        # Should include setup instructions
        assert any("To fix this:" in line for line in lines)
        assert any(".env.example" in line for line in lines)


class TestIntegrationWithDatabase:
    """Integration tests for environment variable usage in database configuration."""

    def test_postgres_passwords_required(self):
        """Test that POSTGRES passwords are required for database connection."""
        # This test verifies the integration without actually connecting
        with patch.dict(os.environ, {}, clear=True):
            # Importing database module should fail if passwords are missing
            # We'll test this indirectly through get_required_env_var
            with pytest.raises(MissingEnvironmentVariableError):
                get_required_env_var("POSTGRES_APP_PASSWORD")

            with pytest.raises(MissingEnvironmentVariableError):
                get_required_env_var("POSTGRES_ADMIN_PASSWORD")

    def test_postgres_passwords_with_valid_env(self):
        """Test that valid passwords are retrieved correctly."""
        test_env = {
            "POSTGRES_APP_PASSWORD": "test_app_password",
            "POSTGRES_ADMIN_PASSWORD": "test_admin_password",
        }

        with patch.dict(os.environ, test_env):
            app_pwd = get_required_env_var("POSTGRES_APP_PASSWORD")
            admin_pwd = get_required_env_var("POSTGRES_ADMIN_PASSWORD")

            assert app_pwd == "test_app_password"
            assert admin_pwd == "test_admin_password"


class TestErrorMessageQuality:
    """Tests to ensure error messages are helpful to developers."""

    def test_error_mentions_env_example(self):
        """Test that error directs users to .env.example."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingEnvironmentVariableError) as exc_info:
                get_required_env_var("TEST_VAR")

            assert ".env.example" in str(exc_info.value)

    def test_error_mentions_readme(self):
        """Test that error directs users to README."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingEnvironmentVariableError) as exc_info:
                get_required_env_var("TEST_VAR")

            assert "README" in str(exc_info.value)

    def test_error_provides_example_syntax(self):
        """Test that error shows example of how to set the variable."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingEnvironmentVariableError) as exc_info:
                get_required_env_var("MY_VAR")

            error_msg = str(exc_info.value)
            # Should show the variable name with an equals sign
            assert "MY_VAR=" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
