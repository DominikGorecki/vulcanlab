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
    return '''You are an expert document sanitizer. Your task is to clean up markdown content by:
1. Removing duplicate or redundant headings
2. Fixing heading hierarchy issues
3. Removing unnecessary metadata sections
4. Keeping all substantive content intact

Input markdown:
{markdown}

Respond in the following JSON format:
{{
  "sanitized_markdown": "... full sanitized markdown here ...",
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings in the modifications list
- Use action: "remove", "change", or "keep" for each heading
- Preserve all non-heading content exactly as-is'''


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM JSON response into structured data.

    Args:
        response_text: Raw LLM response (should be JSON)

    Returns:
        Dictionary with 'sanitized_markdown' and 'modifications' keys

    Raises:
        ValueError: If response is not valid JSON or missing required fields
    """
    try:
        # Try to extract JSON from response (handle cases where LLM adds extra text)
        # Look for first { and last }
        start = response_text.find('{')
        end = response_text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError("No JSON found in response")

        json_str = response_text[start:end+1]
        data = json.loads(json_str)

        # Validate required fields
        if 'sanitized_markdown' not in data:
            raise ValueError("Response missing 'sanitized_markdown' field")
        if 'modifications' not in data:
            raise ValueError("Response missing 'modifications' field")

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")


def create_heading_modifications(
    modifications_list: List[Dict[str, str]],
    work_id: int,
    session: Session
) -> List[HeadingModification]:
    """
    Create HeadingModification records from LLM response.

    Args:
        modifications_list: List of modification dicts from LLM
        work_id: ID of the Work being processed
        session: Database session

    Returns:
        List of created HeadingModification records
    """
    records = []

    for idx, mod in enumerate(modifications_list):
        # Parse action
        action_str = mod.get('action', '').lower()
        if action_str == 'remove':
            action = ModificationAction.REMOVE
        elif action_str == 'change':
            action = ModificationAction.CHANGE
        elif action_str == 'keep':
            action = ModificationAction.KEEP
        else:
            logger.warning(f"Unknown action '{action_str}', defaulting to KEEP")
            action = ModificationAction.KEEP

        # Create record (adapt to existing schema)
        heading_mod = HeadingModification(
            work_id=work_id,
            line_number=idx + 1,  # Use sequential line number
            original_heading=mod.get('original', ''),
            modified_heading=mod.get('new'),  # Maps to existing 'modified_heading' field
            action=action,
            vectorize_flag=False,  # Default for small documents
            created_at=datetime.now(UTC)
        )

        session.add(heading_mod)
        records.append(heading_mod)

    return records


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

    # Parse response
    parsed_response = parse_llm_response(response_text)
    sanitized_content = parsed_response['sanitized_markdown']
    modifications = parsed_response['modifications']

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

    # Create HeadingModification records
    heading_records = create_heading_modifications(
        modifications,
        work_id,
        session
    )

    logger.info(
        f"Created {len(heading_records)} heading modifications for work {work_id}"
    )

    # Update Work.processing_status
    if not work.processing_status:
        work.processing_status = {}

    work.processing_status['simple_conversion_step'] = 'sanitized'
    work.processing_status['sanitized_heading_count'] = len(heading_records)

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
