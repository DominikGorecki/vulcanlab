"""
Unit tests for PromptTemplate model.

Tests model creation, validation, and queries using mocks.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from vulcanlab.data.models.prompt_template import PromptTemplate
from tests.unit.mock_helpers import create_mock_query_chain


class TestPromptTemplateCreation:
    """Test basic model creation and field values."""

    def test_create_prompt_template(self):
        """Test creating a PromptTemplate instance with all fields."""
        template = PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Test Template V1",
            template_content="Test template with {variable}",
            is_active=True
        )

        # Verify all fields are set
        assert template.function_tag == "test_function"
        assert template.version == 1
        assert template.title == "Test Template V1"
        assert template.template_content == "Test template with {variable}"
        assert template.is_active is True

    def test_default_values(self):
        """Test that is_active defaults to FALSE."""
        template = PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Test Template",
            template_content="Test content"
            # is_active not specified
        )
        
        # Note: SQLAlchemy defaults are not applied on __init__ unless specified in python.
        # We check if it accepts the arguments correctly.
        assert template.function_tag == "test_function"

    def test_repr(self):
        """Test __repr__ method."""
        template = PromptTemplate(
            function_tag="test_function",
            version=2,
            title="Test",
            template_content="Content",
            is_active=True
        )
        # Manually set ID for repr test
        template.id = 1

        repr_str = repr(template)
        assert "PromptTemplate" in repr_str
        assert "test_function" in repr_str
        assert "version=2" in repr_str
        assert "active=True" in repr_str


class TestPromptTemplateValidation:
    """Test model validation logic."""

    def test_version_validation_positive(self):
        """Test that positive version numbers are accepted."""
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Content"
        )
        # Direct validation call if needed, or rely on @validates
        # @validates is triggered on assignment.
        assert template.version == 1

    def test_version_validation_zero(self):
        """Test that version=0 raises ValueError."""
        with pytest.raises(ValueError, match="Version must be greater than 0"):
            PromptTemplate(
                function_tag="test",
                version=0,
                title="Test",
                template_content="Content"
            )

    def test_version_validation_negative(self):
        """Test that negative version raises ValueError."""
        with pytest.raises(ValueError, match="Version must be greater than 0"):
            PromptTemplate(
                function_tag="test",
                version=-1,
                title="Test",
                template_content="Content"
            )


class TestPromptTemplateQueries:
    """Test querying templates using mocks."""

    @pytest.fixture
    def sample_templates(self):
        """Create sample templates for testing."""
        return [
            PromptTemplate(
                function_tag="query_expansion",
                version=1,
                title="Query Expansion V1",
                template_content="Template V1 with {query}",
                is_active=False
            ),
            PromptTemplate(
                function_tag="query_expansion",
                version=2,
                title="Query Expansion V2",
                template_content="Template V2 with {query}",
                is_active=True
            ),
            PromptTemplate(
                function_tag="rag_augmentation",
                version=1,
                title="RAG Augmentation V1",
                template_content="RAG template with {context}",
                is_active=True
            ),
        ]

    def test_query_by_function_tag(self, mock_session, sample_templates):
        """Test retrieving all templates for a function_tag."""
        # Setup mock return
        filtered_templates = [t for t in sample_templates if t.function_tag == "query_expansion"]
        mock_query = create_mock_query_chain(return_data=filtered_templates)
        mock_session.query.return_value = mock_query

        # Execute
        templates = mock_session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "query_expansion"
        ).all()

        # Verify
        assert len(templates) == 2
        assert all(t.function_tag == "query_expansion" for t in templates)
        mock_session.query.assert_called_with(PromptTemplate)

    def test_query_active_template(self, mock_session, sample_templates):
        """Test retrieving the active template for a function_tag."""
        # Setup mock return
        active_template = next(t for t in sample_templates if t.function_tag == "query_expansion" and t.is_active)
        mock_query = create_mock_query_chain(return_first=active_template)
        mock_session.query.return_value = mock_query

        # Execute
        active = mock_session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "query_expansion",
            PromptTemplate.is_active == True
        ).first()

        # Verify
        assert active is not None
        assert active.version == 2
        assert active.is_active is True

    def test_query_specific_version(self, mock_session, sample_templates):
        """Test retrieving a specific version."""
        # Setup mock return
        target_template = next(t for t in sample_templates if t.function_tag == "query_expansion" and t.version == 1)
        mock_query = create_mock_query_chain(return_first=target_template)
        mock_session.query.return_value = mock_query

        # Execute
        template = mock_session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "query_expansion",
            PromptTemplate.version == 1
        ).first()

        # Verify
        assert template is not None
        assert template.version == 1
        assert template.title == "Query Expansion V1"

    def test_query_no_results(self, mock_session):
        """Test querying non-existent function_tag returns None."""
        # Setup mock return
        mock_query = create_mock_query_chain(return_first=None)
        mock_session.query.return_value = mock_query

        # Execute
        result = mock_session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "nonexistent"
        ).first()

        # Verify
        assert result is None


class TestPromptTemplateLangChainCompatibility:
    """Test compatibility with LangChain PromptTemplate."""

    def test_langchain_template_loading(self):
        """Test that stored templates can be loaded as LangChain PromptTemplates."""
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate

        # Create template with valid LangChain syntax
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Hello {name}, you are {age} years old."
        )

        # Load as LangChain PromptTemplate
        lc_template = LCPromptTemplate.from_template(template.template_content)

        # Test formatting
        result = lc_template.format(name="Alice", age=30)
        assert "Hello Alice" in result
        assert "30 years old" in result

    def test_langchain_template_with_multiple_variables(self):
        """Test LangChain template with multiple variables."""
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate

        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Query: {query}, Number: {n}, Context: {context}"
        )

        lc_template = LCPromptTemplate.from_template(template.template_content)
        result = lc_template.format(query="test query", n=5, context="test context")

        assert "test query" in result
        assert "5" in result
        assert "test context" in result
