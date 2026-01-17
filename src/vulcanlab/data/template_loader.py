"""
Template loader utility for prompt templates.

Provides functions to load LangChain PromptTemplates from the database
with fallback to hardcoded defaults.
"""

from typing import Callable, Optional, List
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

from vulcanlab.data.database import get_session
from vulcanlab.data.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


def get_active_template(function_tag: str, session: Session) -> str:
    """
    Load the active template content for a given function_tag from the database.

    Args:
        function_tag: The function tag to load (e.g., 'summarize_sections')
        session: Database session

    Returns:
        The template content string

    Raises:
        ValueError: If no active template is found for the function_tag
    """
    stmt = (
        select(PromptTemplate.template_content)
        .where(PromptTemplate.function_tag == function_tag)
        .where(PromptTemplate.is_active == True)
        .order_by(PromptTemplate.id.desc())
        .limit(1)
    )
    result = session.execute(stmt).scalar_one_or_none()

    if result is None:
        raise ValueError(f"No active template found for function_tag: {function_tag}")

    return result


def load_template(
    function_tag: str,
    fallback_builder: Optional[Callable[[], str]] = None
) -> LCPromptTemplate:
    """
    Load active template from database with optional fallback.

    This function attempts to load the active template for a given function_tag
    from the database. If no active template is found or if there's a database
    error:
    - If fallback_builder is provided, it falls back to calling fallback_builder()
      to get the hardcoded template string.
    - If fallback_builder is None, it raises a ValueError with clear instructions.

    Args:
        function_tag: The function tag to load (e.g., 'query_expansion', 'research_planning')
        fallback_builder: Optional callable that returns the hardcoded template string.
                         If None, raises ValueError when template not found.

    Returns:
        LangChain PromptTemplate ready for formatting

    Raises:
        ValueError: If template not found and no fallback provided

    Example with fallback:
        >>> def get_hardcoded_prompt():
        ...     return "You are an assistant. Query: {query}"
        >>> template = load_template("query_expansion", get_hardcoded_prompt)
        >>> result = template.format(query="test")

    Example without fallback (strict mode):
        >>> template = load_template("research_planning", fallback_builder=None)
        >>> # Raises ValueError if template not seeded in database
    """
    try:
        # Attempt to load from database
        with get_session() as session:
            db_template = session.query(PromptTemplate).filter(
                PromptTemplate.function_tag == function_tag,
                PromptTemplate.is_active == True
            ).order_by(PromptTemplate.id.desc()).first()

            if db_template:
                logger.info(
                    f"Loaded template from database: {function_tag} (ID: {db_template.id}, v{db_template.version})"
                )
                return LCPromptTemplate.from_template(db_template.template_content)

        # No active template found
        if fallback_builder is None:
            raise ValueError(
                f"Template '{function_tag}' not found in database and no fallback provided. "
                f"Ensure templates are seeded via init_database(). "
                f"Check /settings/templates for available templates."
            )

        # Use fallback
        logger.info(
            f"No active template in database for {function_tag}, using fallback"
        )
        fallback_str = fallback_builder()
        return LCPromptTemplate.from_template(fallback_str)

    except ValueError:
        # Re-raise ValueError (template not found in strict mode)
        raise
    except Exception as e:
        # Database error or other issue
        if fallback_builder is None:
            raise ValueError(
                f"Failed to load template '{function_tag}' from database: {e}. "
                f"No fallback provided. Ensure templates are seeded via init_database()."
            ) from e

        # Use fallback
        logger.warning(
            f"Failed to load template from database for {function_tag}: {e}. "
            f"Using fallback."
        )
        fallback_str = fallback_builder()
        return LCPromptTemplate.from_template(fallback_str)
