"""
Template loader utility for prompt templates.

Provides functions to load LangChain PromptTemplates from the database
with fallback to hardcoded defaults.
"""

from typing import Callable
import logging
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

from vulcanlab.data.database import get_session
from vulcanlab.data.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


def load_template(
    function_tag: str,
    fallback_builder: Callable[[], str]
) -> LCPromptTemplate:
    """
    Load active template from database with fallback.

    This function attempts to load the active template for a given function_tag
    from the database. If no active template is found or if there's a database
    error, it falls back to calling fallback_builder() to get the hardcoded
    template string.

    Args:
        function_tag: The function tag to load (e.g., 'query_expansion')
        fallback_builder: Callable that returns the hardcoded template string

    Returns:
        LangChain PromptTemplate ready for formatting

    Example:
        >>> def get_hardcoded_prompt():
        ...     return "You are an assistant. Query: {query}"
        >>> template = load_template("query_expansion", get_hardcoded_prompt)
        >>> result = template.format(query="test")
    """
    try:
        # Attempt to load from database
        with get_session() as session:
            db_template = session.query(PromptTemplate).filter(
                PromptTemplate.function_tag == function_tag,
                PromptTemplate.is_active == True
            ).first()

            if db_template:
                logger.info(
                    f"Loaded template from database: {function_tag} v{db_template.version}"
                )
                return LCPromptTemplate.from_template(db_template.template_content)

        # No active template found, use fallback
        logger.info(
            f"No active template in database for {function_tag}, using fallback"
        )
        fallback_str = fallback_builder()
        return LCPromptTemplate.from_template(fallback_str)

    except Exception as e:
        # Database error or other issue, use fallback
        logger.warning(
            f"Failed to load template from database for {function_tag}: {e}. "
            f"Using fallback."
        )
        fallback_str = fallback_builder()
        return LCPromptTemplate.from_template(fallback_str)
