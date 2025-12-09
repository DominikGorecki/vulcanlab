"""
SQLAlchemy model for prompt template metadata.

The prompt_meta table stores metadata about prompt template variables,
with one record per function_tag (shared across all versions).
"""

from datetime import datetime, UTC
from typing import List, Dict, Any

from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

from vulcanlab.data.database import Base


class PromptMeta(Base):
    """
    Model for prompt template metadata.

    This table stores metadata about prompt templates, particularly
    information about the variables used in templates.

    Attributes:
        id: Primary key
        function_tag: Unique identifier linking to prompt_templates.function_tag
        variables: JSONB array of variable metadata objects
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "prompt_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    function_tag = Column(String(100), unique=True, nullable=False, index=True)
    variables = Column(JSONB, nullable=False, default=list)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    @validates('variables')
    def validate_variables(self, key, value):
        """Validate that variables is not None."""
        if value is None:
            raise ValueError("variables cannot be None")
        return value

    def __repr__(self) -> str:
        """String representation of PromptMeta."""
        return f"<PromptMeta(function_tag='{self.function_tag}', variables={len(self.variables or [])})>"

    @property
    def variable_dict(self) -> Dict[str, str]:
        """
        Convert variables JSONB array to a dictionary for easy lookup.

        Returns:
            Dictionary mapping variable_name to variable_description
        """
        if not self.variables:
            return {}
        return {
            var["variable_name"]: var["variable_description"]
            for var in self.variables
            if isinstance(var, dict) 
            and "variable_name" in var 
            and "variable_description" in var
        }

    @classmethod
    def from_variables_list(
        cls,
        function_tag: str,
        variables: List[Dict[str, str]]
    ) -> "PromptMeta":
        """
        Create a PromptMeta instance from a list of variable dictionaries.

        Args:
            function_tag: The function identifier
            variables: List of dicts with 'variable_name' and 'variable_description'

        Returns:
            New PromptMeta instance

        Example:
            >>> meta = PromptMeta.from_variables_list(
            ...     "query_expansion",
            ...     [
            ...         {"variable_name": "query", "variable_description": "User's search query"},
            ...         {"variable_name": "context", "variable_description": "Retrieved documents"}
            ...     ]
            ... )
        """
        return cls(
            function_tag=function_tag,
            variables=variables
        )
