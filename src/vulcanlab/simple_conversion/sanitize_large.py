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
        Condensed markdown string with line numbers and heading info
    """
    lines = []
    lines.append("# Condensed Document (Headings + Context)\n")

    for heading in headings:
        lines.append(f"\nLINE {heading['line_number']}: {'#' * heading['level']} {heading['text']}")

        if heading['context_before']:
            lines.append(f"  Context before: ...{heading['context_before']}")

        if heading['context_after']:
            lines.append(f"  Context after: {heading['context_after']}...")

    condensed = '\n'.join(lines)
    logger.debug(f"Created condensed markdown: {len(condensed)} chars")

    return condensed


def get_hardcoded_template_large() -> str:
    """
    Fallback hardcoded template for large document sanitization.

    Returns:
        Template string with {condensed_document} placeholder
    """
    return '''You are an expert document sanitizer analyzing a LARGE document. You will see headings with line numbers and surrounding context.

{condensed_document}

Your task: Analyze each heading and decide what to do with it.

Rules:
- REMOVE: Non-content headings (page numbers, ToC, references, copyright, etc.)
- CHANGE: Fix heading levels or text (OCR errors, wrong hierarchy, cleanup needed)
- KEEP: Heading is correct as-is

For CHANGE actions:
- Include the FULL markdown heading with correct # markers (e.g., "## Introduction")
- Fix hierarchy issues (no skipped levels, consistent sibling levels)
- Clean up text (whitespace, OCR artifacts, formatting issues)

Respond ONLY with valid JSON in this format:
{{
  "modifications": [
    {{"line": 5, "action": "remove", "vectorize": false}},
    {{"line": 12, "action": "change", "new": "## Methods", "vectorize": true}},
    {{"line": 25, "action": "keep", "vectorize": true}}
  ]
}}

Required fields:
- line: The line number from the condensed document
- action: "keep", "change", or "remove" (lowercase)
- vectorize: true if content should be indexed for RAG, false otherwise
- new: Required if action is "change" - the full corrected heading with # markers

Return ONLY the JSON object. No explanations or commentary.'''


def apply_modifications_to_markdown(
    original_markdown: str,
    modifications: List[Dict[str, Any]]
) -> str:
    """
    Apply heading modifications to original markdown using line numbers.

    Args:
        original_markdown: Full original markdown content
        modifications: List of modification dicts from LLM with 'line', 'action', 'new' fields

    Returns:
        Sanitized markdown with modifications applied
    """
    # Build modification lookup by line number
    mod_map = {mod['line']: mod for mod in modifications}

    lines = original_markdown.split('\n')
    result_lines = []

    for line_num, line in enumerate(lines, 1):
        # Check if this line is a heading
        match = HEADING_PATTERN.match(line)

        if match and line_num in mod_map:
            mod = mod_map[line_num]
            action = mod.get('action', '').lower()

            if action == 'remove':
                # Skip this line (don't add to result)
                continue
            elif action == 'change':
                # Replace with new heading (already includes # markers)
                new_heading = mod.get('new', line)
                result_lines.append(new_heading)
            else:  # keep or unknown
                result_lines.append(line)
        else:
            # Not a heading or no modification, keep as-is
            result_lines.append(line)

    result = '\n'.join(result_lines)

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
    modifications_list: List[Dict[str, Any]],
    work_id: int,
    headings_info: List[Dict[str, Any]],
    session: Session
) -> List[HeadingModification]:
    """
    Create HeadingModification records from LLM response.

    Args:
        modifications_list: List of modification dicts from LLM with 'line', 'action', 'new', 'vectorize'
        work_id: ID of the Work being processed
        headings_info: Original heading extraction data (for getting original heading text)
        session: Database session

    Returns:
        List of created HeadingModification records
    """
    records = []

    # Build lookup for heading info by line number
    line_lookup = {h['line_number']: h for h in headings_info}

    for mod in modifications_list:
        # Parse action - just use the lowercase string directly
        action_str = mod.get('action', '').lower()

        # Validate action
        valid_actions = {'remove', 'change', 'keep'}
        if action_str not in valid_actions:
            logger.warning(f"Unknown action '{action_str}', defaulting to 'keep'")
            action_str = 'keep'

        line_number = mod.get('line', 0)
        heading_info = line_lookup.get(line_number, {})
        original_heading = heading_info.get('text', '')

        # Get vectorize flag from LLM response
        vectorize_flag = mod.get('vectorize', False)

        # Create record - pass string directly, SQLAlchemy will convert to enum
        heading_mod = HeadingModification(
            work_id=work_id,
            line_number=line_number,
            original_heading=original_heading,
            modified_heading=mod.get('new'),  # Full heading with # markers if action=change
            action=action_str,  # Pass lowercase string directly
            vectorize_flag=vectorize_flag,
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
    prompt = template.format(condensed_document=condensed)

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
