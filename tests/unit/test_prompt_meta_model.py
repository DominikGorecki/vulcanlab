"""
Unit tests for PromptMeta model.

Tests model creation, JSONB variables field, variable_dict property,
from_variables_list method, and queries using mocks.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from vulcanlab.data.models.prompt_meta import PromptMeta
from tests.unit.mock_helpers import create_mock_query_chain


class TestPromptMetaCreation:
    """Test basic model creation and field values."""

    def test_create_prompt_meta_basic(self):
        """Test creating a PromptMeta with basic fields."""
        meta = PromptMeta(
            function_tag="test_function",
            variables=[]
        )

        assert meta.function_tag == "test_function"
        assert meta.variables == []

    def test_create_prompt_meta_with_variables(self):
        """Test creating a PromptMeta with variables."""
        variables = [
            {"variable_name": "query", "variable_description": "User's search query"},
            {"variable_name": "context", "variable_description": "Retrieved documents"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )

        assert meta.variables == variables
        assert len(meta.variables) == 2

    def test_repr(self):
        """Test __repr__ method."""
        meta = PromptMeta(
            function_tag="test_function",
            variables=[
                {"variable_name": "var1", "variable_description": "Desc 1"},
                {"variable_name": "var2", "variable_description": "Desc 2"}
            ]
        )

        repr_str = repr(meta)
        assert "PromptMeta" in repr_str
        assert "test_function" in repr_str
        assert "2" in repr_str  # Number of variables


class TestPromptMetaVariableDict:
    """Test variable_dict property."""

    def test_variable_dict_empty(self):
        """Test variable_dict with empty variables."""
        meta = PromptMeta(
            function_tag="test_function",
            variables=[]
        )

        assert meta.variable_dict == {}

    def test_variable_dict_conversion(self):
        """Test variable_dict converts variables list to dictionary."""
        variables = [
            {"variable_name": "query", "variable_description": "User's search query"},
            {"variable_name": "context", "variable_description": "Retrieved documents"},
            {"variable_name": "n", "variable_description": "Number of queries"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )

        var_dict = meta.variable_dict
        assert isinstance(var_dict, dict)
        assert var_dict["query"] == "User's search query"
        assert var_dict["context"] == "Retrieved documents"
        assert var_dict["n"] == "Number of queries"

    def test_variable_dict_missing_fields(self):
        """Test variable_dict handles variables with missing fields."""
        variables = [
            {"variable_name": "query", "variable_description": "Description"},
            {"variable_name": "context"},  # Missing variable_description
            {"variable_description": "Description only"},  # Missing variable_name
            {"variable_name": "valid", "variable_description": "Valid var"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )

        var_dict = meta.variable_dict
        # Should only include variables with both fields
        assert "query" in var_dict
        assert "valid" in var_dict
        assert "context" not in var_dict  # Missing description
        assert len(var_dict) == 2

    def test_variable_dict_non_dict_items(self):
        """Test variable_dict handles non-dict items in variables list."""
        variables = [
            {"variable_name": "query", "variable_description": "Description"},
            "not a dict",  # Invalid item
            123,  # Invalid item
            {"variable_name": "valid", "variable_description": "Valid"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )

        var_dict = meta.variable_dict
        # Should only include valid dict items
        assert "query" in var_dict
        assert "valid" in var_dict
        assert len(var_dict) == 2


class TestPromptMetaFromVariablesList:
    """Test from_variables_list class method."""

    def test_from_variables_list_basic(self):
        """Test creating PromptMeta from variables list."""
        variables = [
            {"variable_name": "query", "variable_description": "User's search query"},
            {"variable_name": "context", "variable_description": "Retrieved documents"}
        ]
        meta = PromptMeta.from_variables_list("test_function", variables)

        assert meta.function_tag == "test_function"
        assert meta.variables == variables
        assert len(meta.variables) == 2

    def test_from_variables_list_empty(self):
        """Test from_variables_list with empty list."""
        meta = PromptMeta.from_variables_list("test_function", [])

        assert meta.function_tag == "test_function"
        assert meta.variables == []

    def test_from_variables_list_single_variable(self):
        """Test from_variables_list with single variable."""
        variables = [
            {"variable_name": "query", "variable_description": "User query"}
        ]
        meta = PromptMeta.from_variables_list("single_var", variables)

        assert meta.function_tag == "single_var"
        assert len(meta.variables) == 1
        assert meta.variables[0]["variable_name"] == "query"


class TestPromptMetaQueries:
    """Test querying PromptMeta using mocks."""

    def test_query_by_function_tag(self, mock_session):
        """Test querying PromptMeta by function_tag."""
        # Setup mock return
        meta = PromptMeta(
            function_tag="function1",
            variables=[]
        )
        mock_query = create_mock_query_chain(return_first=meta)
        mock_session.query.return_value = mock_query

        # Execute
        result = mock_session.query(PromptMeta).filter(
            PromptMeta.function_tag == "function1"
        ).first()

        # Verify
        assert result is not None
        assert result.function_tag == "function1"


class TestPromptMetaValidation:
    """Test model validation logic."""
    
    def test_variables_required(self):
        """Test that variables cannot be None."""
        # Test ORM-level validation - validator runs during object initialization
        # if @validates is used.
        with pytest.raises(ValueError, match="variables cannot be None"):
            PromptMeta(
                function_tag="test_function",
                variables=None
            )
