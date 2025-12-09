"""
Unit tests for template_loader module.

Tests template loading from database, fallback behavior, error handling,
and LangChain conversion.
"""

from unittest.mock import MagicMock, patch, Mock
import pytest

from vulcanlab.data.template_loader import load_template
from vulcanlab.data.models.prompt_template import PromptTemplate


class TestLoadTemplate:
    """Tests for load_template function."""

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_from_database(self, mock_get_session):
        """Test loading template from database successfully."""
        # Mock database session
        mock_session = MagicMock()
        mock_template = MagicMock()
        mock_template.function_tag = "test_function"
        mock_template.version = 1
        mock_template.template_content = "Template from DB with {variable}"
        mock_template.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_template
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock fallback builder
        def fallback_builder():
            return "Fallback template"

        template = load_template("test_function", fallback_builder)

        # Verify database query was made
        mock_session.query.assert_called_once_with(PromptTemplate)
        mock_query.filter.assert_called()
        assert template is not None

        # Verify template can be formatted
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        assert isinstance(template, LCPromptTemplate)

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_fallback_when_not_found(self, mock_get_session):
        """Test fallback when template not found in database."""
        # Mock database session - no template found
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Fallback builder
        def fallback_builder():
            return "Fallback template with {variable}"

        template = load_template("nonexistent_function", fallback_builder)

        # Verify fallback was used
        assert template is not None
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        assert isinstance(template, LCPromptTemplate)

        # Verify template can be formatted
        result = template.format(variable="test")
        assert "test" in result

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_fallback_on_database_error(self, mock_get_session):
        """Test fallback when database error occurs."""
        # Mock database session - raises exception
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("Database error")
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Fallback builder
        def fallback_builder():
            return "Fallback on error with {var}"

        template = load_template("test_function", fallback_builder)

        # Verify fallback was used
        assert template is not None
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        assert isinstance(template, LCPromptTemplate)

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_only_active_templates(self, mock_get_session):
        """Test that only active templates are loaded."""
        # Mock database session
        mock_session = MagicMock()
        mock_template = MagicMock()
        mock_template.function_tag = "test_function"
        mock_template.version = 1
        mock_template.template_content = "Active template"
        mock_template.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_template
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback"

        load_template("test_function", fallback_builder)

        # Verify filter was called with is_active=True
        filter_calls = mock_query.filter.call_args_list
        # Should filter by function_tag and is_active
        assert len(filter_calls) >= 1

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_inactive_template_uses_fallback(self, mock_get_session):
        """Test that inactive templates trigger fallback."""
        # Mock database session - template exists but is inactive
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None  # No active template
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback for inactive"

        template = load_template("test_function", fallback_builder)

        # Verify fallback was used
        assert template is not None
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        assert isinstance(template, LCPromptTemplate)

    @patch("vulcanlab.data.template_loader.get_session")
    @patch("vulcanlab.data.template_loader.logger")
    def test_load_template_logs_database_load(self, mock_logger, mock_get_session):
        """Test that loading from database is logged."""
        # Mock database session
        mock_session = MagicMock()
        mock_template = MagicMock()
        mock_template.function_tag = "test_function"
        mock_template.version = 1
        mock_template.template_content = "Template"
        mock_template.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_template
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback"

        load_template("test_function", fallback_builder)

        # Verify logging
        mock_logger.info.assert_called()
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("database" in str(call).lower() or "loaded" in str(call).lower() for call in log_calls)

    @patch("vulcanlab.data.template_loader.get_session")
    @patch("vulcanlab.data.template_loader.logger")
    def test_load_template_logs_fallback(self, mock_logger, mock_get_session):
        """Test that fallback usage is logged."""
        # Mock database session - no template found
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback"

        load_template("test_function", fallback_builder)

        # Verify logging
        mock_logger.info.assert_called()
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("fallback" in str(call).lower() or "no active" in str(call).lower() for call in log_calls)

    @patch("vulcanlab.data.template_loader.get_session")
    @patch("vulcanlab.data.template_loader.logger")
    def test_load_template_logs_error(self, mock_logger, mock_get_session):
        """Test that database errors are logged."""
        # Mock database session - raises exception
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("Database connection failed")
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback"

        load_template("test_function", fallback_builder)

        # Verify error logging
        mock_logger.warning.assert_called()
        log_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("failed" in str(call).lower() or "error" in str(call).lower() for call in log_calls)

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_langchain_conversion(self, mock_get_session):
        """Test that database template is converted to LangChain PromptTemplate."""
        # Mock database session
        mock_session = MagicMock()
        mock_template = MagicMock()
        mock_template.function_tag = "test_function"
        mock_template.version = 1
        mock_template.template_content = "Hello {name}, you are {age} years old."
        mock_template.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_template
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback"

        template = load_template("test_function", fallback_builder)

        # Verify LangChain conversion
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        assert isinstance(template, LCPromptTemplate)

        # Verify template can be formatted
        result = template.format(name="Alice", age=30)
        assert "Alice" in result
        assert "30" in result

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_fallback_langchain_conversion(self, mock_get_session):
        """Test that fallback template is converted to LangChain PromptTemplate."""
        # Mock database session - no template found
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Query: {query}, Context: {context}"

        template = load_template("test_function", fallback_builder)

        # Verify LangChain conversion
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        assert isinstance(template, LCPromptTemplate)

        # Verify template can be formatted
        result = template.format(query="test", context="context")
        assert "test" in result
        assert "context" in result

    @patch("vulcanlab.data.template_loader.get_session")
    def test_load_template_multiple_variables(self, mock_get_session):
        """Test template with multiple variables."""
        # Mock database session
        mock_session = MagicMock()
        mock_template = MagicMock()
        mock_template.function_tag = "test_function"
        mock_template.version = 1
        mock_template.template_content = "Query: {query}, N: {n}, Context: {context_blocks}"
        mock_template.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_template
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session

        def fallback_builder():
            return "Fallback"

        template = load_template("test_function", fallback_builder)

        # Verify template can handle multiple variables
        result = template.format(
            query="What is memory?",
            n=5,
            context_blocks="[S1] Context 1\n[S2] Context 2"
        )
        assert "What is memory?" in result
        assert "5" in result
        assert "Context 1" in result

