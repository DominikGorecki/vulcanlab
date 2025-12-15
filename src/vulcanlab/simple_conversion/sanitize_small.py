"""
Small document sanitization module for simple conversion pipeline.

Processes documents classified as SMALL (<threshold tokens) by sending
the entire markdown content to an LLM for sanitization.
"""

import logging
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.heading_modifications import HeadingModification, ModificationAction
from vulcanlab.data.database import get_session
from vulcanlab.data.template_loader import load_template
from vulcanlab.ai.llm_factory import create_langchain_chat
from vulcanlab.ai.config import ModelTier
from vulcanlab.simple_conversion.parse_classify import count_tokens

logger = logging.getLogger(__name__)


def get_hardcoded_template_small() -> str:
    """
    Fallback hardcoded template for small document sanitization.

    Returns:
        Template string with {markdown} placeholder
    """
    return '''You are an expert document sanitizer preparing content for a RAG system.

Input markdown:
{markdown}

Your task: Return a cleaned version of this markdown with:
1. Correct heading hierarchy (no skipped levels, proper nesting)
2. Non-content headings removed (page numbers, ToC, references, copyright, etc.)
3. OCR errors and formatting issues fixed
4. All substantive content preserved

Return ONLY the sanitized markdown. No JSON, no explanations, no code fences. Just the literal markdown text.'''


def parse_llm_response(response_text: str) -> str:
    """
    Extract sanitized markdown from LLM response.

    The LLM should return literal markdown, but may wrap it in code fences or add preamble.
    This function extracts the markdown content.

    Args:
        response_text: Raw LLM response (should be literal markdown)

    Returns:
        Sanitized markdown string
    """
    # Strip common wrapper patterns
    content = response_text.strip()

    # Remove markdown code fences if present
    if content.startswith('```markdown'):
        content = content[len('```markdown'):].strip()
    elif content.startswith('```'):
        content = content[3:].strip()

    if content.endswith('```'):
        content = content[:-3].strip()

    return content


def sanitize_small_document(work_id: int, session: Session) -> SanitizedMarkdown:
    """
    Sanitize a small document using full LLM processing.

    This function:
    1. Retrieves ParsedMarkdown for the work
    2. Loads template from DB (with fallback)
    3. Formats prompt with full markdown content
    4. Calls LLM
    5. Parses response
    6. Creates SanitizedMarkdown record
    7. Creates HeadingModification records
    8. Updates Work.processing_status

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        Created SanitizedMarkdown record

    Raises:
        ValueError: If work not found, not parsed, or wrong classification
    """
    # Get work
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    # Get ParsedMarkdown
    parsed = session.query(ParsedMarkdown).filter(
        ParsedMarkdown.work_id == work_id
    ).first()

    if not parsed:
        raise ValueError(f"Work {work_id} has not been parsed yet")

    if parsed.classification.value != 'small':
        raise ValueError(
            f"Work {work_id} is classified as {parsed.classification.value}, "
            f"expected 'small'"
        )

    logger.info(f"Sanitizing small document for work {work_id}")

    # Load template
    template = load_template('simple_sanitize_small', get_hardcoded_template_small)

    # Format prompt
    prompt = template.format(markdown=parsed.content)

    # Call LLM using langchain
    logger.info(f"Calling LLM for small document sanitization (work {work_id})")
    llm_stack = create_langchain_chat(tier=ModelTier.LIGHT, temperature=0.2)
    response = llm_stack.chat.invoke(prompt)

    # Extract content from LangChain response
    response_text = response.content if hasattr(response, 'content') else str(response)

    # Parse response (now returns literal markdown)
    sanitized_content = parse_llm_response(response_text)

    # Count tokens in sanitized content
    sanitized_token_count = count_tokens(sanitized_content)

    # Create SanitizedMarkdown record
    sanitized = SanitizedMarkdown(
        work_id=work_id,
        content=sanitized_content,  # Auto-compressed if >1MB
        token_count=sanitized_token_count,
        created_at=datetime.now(UTC)
    )

    session.add(sanitized)
    session.flush()  # Get sanitized.id for later use

    # Update Work.processing_status
    # NOTE: Must reassign the dict to trigger SQLAlchemy change detection for JSON columns
    new_status = dict(work.processing_status) if work.processing_status else {}
    new_status['simple_conversion_step'] = 'sanitized'
    work.processing_status = new_status

    session.commit()
    session.refresh(sanitized)

    logger.info(f"Sanitization complete for work {work_id}")

    return sanitized


def sanitize_small_document_standalone(work_id: int) -> int:
    """
    Standalone version for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Number of heading modifications created

    Raises:
        ValueError: If validation fails
    """
    with get_session() as session:
        sanitized = sanitize_small_document(work_id, session)

        # Count modifications
        mod_count = session.query(HeadingModification).filter(
            HeadingModification.work_id == work_id
        ).count()

        return mod_count
