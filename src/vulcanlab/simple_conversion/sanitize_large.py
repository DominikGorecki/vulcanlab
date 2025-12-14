"""
Large document sanitization module for simple conversion pipeline.

Processes documents classified as LARGE (>=threshold tokens) by extracting
headings with context, creating condensed representation, and using LLM
to analyze headings without processing the entire document.
"""

import logging
import json
import re
from typing import Dict, List, Tuple, Any
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

# Context window around each heading (chars before/after)
CONTEXT_WINDOW = 100

# Regex pattern for markdown headings (# through ######)
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)


def extract_headings_with_context(markdown: str) -> List[Dict[str, Any]]:
    """
    Extract all headings from markdown with surrounding context.

    Args:
        markdown: Full markdown content

    Returns:
        List of dicts with keys: level, text, context_before, context_after, position
    """
    headings = []

    for match in HEADING_PATTERN.finditer(markdown):
        level = len(match.group(1))  # Number of # symbols
        text = match.group(2).strip()
        start_pos = match.start()
        end_pos = match.end()

        # Extract context before (up to CONTEXT_WINDOW chars)
        context_before_start = max(0, start_pos - CONTEXT_WINDOW)
        context_before = markdown[context_before_start:start_pos].strip()

        # Extract context after (up to CONTEXT_WINDOW chars)
        context_after_end = min(len(markdown), end_pos + CONTEXT_WINDOW)
        context_after = markdown[end_pos:context_after_end].strip()

        headings.append({
            'level': level,
            'text': text,
            'context_before': context_before,
            'context_after': context_after,
            'position': start_pos,
            'line_number': markdown[:start_pos].count('\n') + 1
        })

    logger.info(f"Extracted {len(headings)} headings from markdown")
    return headings


def create_condensed_markdown(headings: List[Dict[str, Any]]) -> str:
    """
    Create condensed markdown with headings and context snippets.

    Args:
        headings: List of heading dicts from extract_headings_with_context

    Returns:
        Condensed markdown string
    """
    lines = []
    lines.append("# Condensed Document (Headings + Context)\n")

    for i, heading in enumerate(headings, 1):
        lines.append(f"\n## Heading {i}")
        lines.append(f"**Level:** {heading['level']}")
        lines.append(f"**Text:** {heading['text']}")

        if heading['context_before']:
            lines.append(f"**Before:** ...{heading['context_before']}")

        if heading['context_after']:
            lines.append(f"**After:** {heading['context_after']}...")

    condensed = '\n'.join(lines)
    logger.debug(f"Created condensed markdown: {len(condensed)} chars")

    return condensed


def get_hardcoded_template_large() -> str:
    """
    Fallback hardcoded template for large document sanitization.

    Returns:
        Template string with {condensed_markdown} placeholder
    """
    return '''You are an expert document sanitizer analyzing a LARGE document. Due to size, you're seeing only headings with surrounding context (100 chars before/after each heading).

Condensed markdown (headings + context):
{condensed_markdown}

Your task is to analyze the headings and decide which to keep, remove, or change:
- REMOVE: Duplicate, redundant, or unnecessary headings
- CHANGE: Headings that need rewording for clarity or consistency
- KEEP: Appropriate headings that should remain as-is

Respond in the following JSON format:
{{
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings from the condensed markdown in modifications list
- Use action: "remove", "change", or "keep"
- Base decisions on context snippets provided'''


def apply_modifications_to_markdown(
    original_markdown: str,
    modifications: List[Dict[str, Any]]
) -> str:
    """
    Apply heading modifications to original markdown.

    Args:
        original_markdown: Full original markdown content
        modifications: List of modification dicts from LLM

    Returns:
        Sanitized markdown with modifications applied
    """
    result = original_markdown

    # Build modification lookup by original heading text
    mod_map = {mod['original']: mod for mod in modifications}

    # Find and replace headings
    def replace_heading(match):
        level = match.group(1)  # The # symbols
        text = match.group(2).strip()

        if text in mod_map:
            mod = mod_map[text]
            action = mod.get('action', '').lower()

            if action == 'remove':
                # Remove entire heading line
                return ''
            elif action == 'change':
                # Replace with new heading
                new_text = mod.get('new', text)
                return f"{level} {new_text}"
            else:  # keep or unknown
                # Keep as-is
                return match.group(0)
        else:
            # No modification for this heading, keep as-is
            return match.group(0)

    result = HEADING_PATTERN.sub(replace_heading, result)

    # Clean up multiple consecutive blank lines left by removals
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result


def parse_llm_response_large(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse LLM JSON response for large document sanitization.

    Args:
        response_text: Raw LLM response (should contain JSON)

    Returns:
        List of modification dicts

    Raises:
        ValueError: If response is not valid JSON or missing modifications
    """
    try:
        # Extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError("No JSON found in response")

        json_str = response_text[start:end+1]
        data = json.loads(json_str)

        if 'modifications' not in data:
            raise ValueError("Response missing 'modifications' field")

        return data['modifications']

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")


def create_heading_modifications_large(
    modifications_list: List[Dict[str, str]],
    work_id: int,
    headings_info: List[Dict[str, Any]],
    session: Session
) -> List[HeadingModification]:
    """
    Create HeadingModification records from LLM response.

    Args:
        modifications_list: List of modification dicts from LLM
        work_id: ID of the Work being processed
        headings_info: Original heading extraction data for line numbers
        session: Database session

    Returns:
        List of created HeadingModification records
    """
    records = []

    # Build lookup for line numbers by heading text
    line_lookup = {h['text']: h['line_number'] for h in headings_info}

    for mod in modifications_list:
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

        original_heading = mod.get('original', '')
        line_number = line_lookup.get(original_heading, 0)

        # Create record (adapt to existing schema)
        heading_mod = HeadingModification(
            work_id=work_id,
            line_number=line_number,
            original_heading=original_heading,
            modified_heading=mod.get('new'),  # Maps to existing 'modified_heading' field
            action=action,
            vectorize_flag=False,  # Default for large documents
            created_at=datetime.now(UTC)
        )

        session.add(heading_mod)
        records.append(heading_mod)

    return records


def sanitize_large_document(work_id: int, session: Session) -> SanitizedMarkdown:
    """
    Sanitize a large document using condensed heading analysis.

    This function:
    1. Retrieves ParsedMarkdown for the work
    2. Extracts headings with context
    3. Creates condensed markdown
    4. Loads template from DB (with fallback)
    5. Calls LLM with condensed version
    6. Parses LLM response
    7. Applies modifications to full markdown
    8. Creates SanitizedMarkdown record
    9. Creates HeadingModification records
    10. Updates Work.processing_status

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

    if parsed.classification.value != 'large':
        raise ValueError(
            f"Work {work_id} is classified as {parsed.classification.value}, "
            f"expected 'large'"
        )

    logger.info(f"Sanitizing large document for work {work_id}")

    # Extract headings with context
    headings = extract_headings_with_context(parsed.content)

    # Create condensed markdown
    condensed = create_condensed_markdown(headings)
    logger.info(
        f"Condensed from {len(parsed.content)} to {len(condensed)} chars "
        f"({len(headings)} headings)"
    )

    # Load template
    template = load_template('simple_sanitize_large', get_hardcoded_template_large)

    # Format prompt
    prompt = template.format(condensed_markdown=condensed)

    # Call LLM using langchain
    logger.info(f"Calling LLM for large document sanitization (work {work_id})")
    llm_stack = create_langchain_chat(tier=ModelTier.LIGHT, temperature=0.2)
    response = llm_stack.chat.invoke(prompt)

    # Extract content from LangChain response
    response_text = response.content if hasattr(response, 'content') else str(response)

    # Parse response
    modifications = parse_llm_response_large(response_text)

    # Apply modifications to full markdown
    sanitized_content = apply_modifications_to_markdown(
        parsed.content,
        modifications
    )

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
    session.flush()  # Get sanitized.id

    # Create HeadingModification records
    heading_records = create_heading_modifications_large(
        modifications,
        work_id,
        headings,
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
    work.processing_status['condensed_char_count'] = len(condensed)

    session.commit()
    session.refresh(sanitized)

    logger.info(f"Sanitization complete for work {work_id}")

    return sanitized


def sanitize_large_document_standalone(work_id: int) -> Tuple[int, int]:
    """
    Standalone version for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Tuple of (heading_count, condensed_char_count)

    Raises:
        ValueError: If validation fails
    """
    with get_session() as session:
        sanitized = sanitize_large_document(work_id, session)

        # Get stats from processing_status
        work = session.query(Work).filter(Work.id == work_id).first()
        heading_count = work.processing_status.get('sanitized_heading_count', 0)
        condensed_chars = work.processing_status.get('condensed_char_count', 0)

        return (heading_count, condensed_chars)
