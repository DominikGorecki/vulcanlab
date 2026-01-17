"""
Storage and parsing logic for generated summaries.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from vulcanlab.data.models.summary_chunk import SummaryChunk
from vulcanlab.data.models.summary_result import SummaryResult


@dataclass
class SummaryParseResult:
    """Result of parsing and saving summaries."""
    success: bool
    summaries_saved: int = 0
    errors: list[str] = field(default_factory=list)
    parsed_items: list[dict[str, Any]] = field(default_factory=list)


def parse_llm_response(response_json: str) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Parse JSON response from LLM containing per-heading summaries.

    Args:
        response_json: Raw JSON string from LLM.

    Returns:
        tuple containing:
            - List of valid parsed items (dict with 'id' and 'summary')
            - List of error messages for invalid items or parsing failures
    """
    errors = []
    valid_items = []

    try:
        data = json.loads(response_json)
    except json.JSONDecodeError as e:
        return [], [f"Invalid JSON syntax: {str(e)}"]

    if not isinstance(data, list):
        return [], ["LLM response must be a JSON array"]

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i} is not a JSON object")
            continue

        item_id = item.get("id")
        summary = item.get("summary")

        if item_id is None:
            errors.append(f"Item {i} missing 'id' field")
            continue
        
        if not isinstance(item_id, (int, str)):
             errors.append(f"Item {i} 'id' must be an integer or numeric string")
             continue
        
        try:
            int_id = int(item_id)
        except (ValueError, TypeError):
            errors.append(f"Item {i} 'id' must be a valid integer")
            continue

        if summary is None:
            errors.append(f"Item {i} (id={int_id}) missing 'summary' field")
            continue

        if not isinstance(summary, str):
            errors.append(f"Item {i} (id={int_id}) 'summary' must be a string")
            continue

        valid_items.append({"id": int_id, "summary": summary})

    return valid_items, errors


def validate_heading_ids(
    parsed_items: list[dict[str, Any]], expected_ids: list[int]
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Validate that parsed IDs match expected heading IDs.

    Args:
        parsed_items: List of dicts with 'id' and 'summary'.
        expected_ids: List of integer IDs expected for this prompt batch.

    Returns:
        tuple containing:
            - List of items that have matching expected IDs
            - List of warning messages
    """
    warnings = []
    expected_set = set(expected_ids)
    found_ids = set()
    filtered_items = []

    for item in parsed_items:
        item_id = item["id"]
        if item_id not in expected_set:
            warnings.append(f"Unexpected heading ID in response: {item_id}")
            continue
        
        if item_id in found_ids:
            warnings.append(f"Duplicate heading ID in response: {item_id}")
            continue

        found_ids.add(item_id)
        filtered_items.append(item)

    missing_ids = expected_set - found_ids
    if missing_ids:
        warnings.append(f"Missing summaries for expected heading IDs: {sorted(list(missing_ids))}")

    return filtered_items, warnings


def save_summaries(
    work_id: int, items: list[dict[str, Any]], prompt_index: int, session: Session
) -> int:
    """
    Upsert summaries into the database.

    Args:
        work_id: The ID of the work.
        items: List of dicts with 'id' (chunk_id) and 'summary'.
        prompt_index: Index of the prompt template used.
        session: SQLAlchemy session.

    Returns:
        Number of summaries saved.
    """
    count = 0
    for item in items:
        chunk_id = item["id"]
        summary_content = item["summary"]

        # Use merge for upsert behavior
        # First check if it exists to match the "update if exists, insert if not" logic
        existing = session.query(SummaryResult).filter_by(
            work_id=work_id, chunk_id=chunk_id
        ).first()

        if existing:
            existing.summary_content = summary_content
            existing.prompt_index = prompt_index
        else:
            new_summary = SummaryResult(
                work_id=work_id,
                chunk_id=chunk_id,
                summary_content=summary_content,
                prompt_index=prompt_index,
            )
            session.add(new_summary)
        
        count += 1
    
    session.flush() # Ensure we don't commit here, but flush to catch any DB errors
    return count


def delete_existing_summaries(work_id: int, session: Session) -> int:
    """
    Delete all existing summaries and summary chunks for a work.

    Args:
        work_id: The ID of the work.
        session: SQLAlchemy session.

    Returns:
        Total number of rows deleted from summary_results.
    """
    # Delete summary_chunks first
    session.execute(delete(SummaryChunk).where(SummaryChunk.work_id == work_id))
    
    # Delete summary_results
    result = session.execute(delete(SummaryResult).where(SummaryResult.work_id == work_id))
    
    return result.rowcount


def process_llm_response(
    work_id: int,
    prompt_index: int,
    response_json: str,
    expected_heading_ids: list[int],
    session: Session,
) -> SummaryParseResult:
    """
    Main entry point for processing LLM responses.

    Args:
        work_id: The ID of the work.
        prompt_index: Index of the prompt template used.
        response_json: Raw JSON string from LLM.
        expected_heading_ids: List of integer IDs expected.
        session: SQLAlchemy session.

    Returns:
        SummaryParseResult object.
    """
    parsed_items, parse_errors = parse_llm_response(response_json)
    
    if not parsed_items and parse_errors:
        return SummaryParseResult(success=False, errors=parse_errors)

    valid_items, validation_warnings = validate_heading_ids(parsed_items, expected_heading_ids)
    
    all_messages = parse_errors + validation_warnings
    
    if not valid_items:
        return SummaryParseResult(
            success=False, 
            errors=all_messages,
            parsed_items=parsed_items
        )

    try:
        saved_count = save_summaries(work_id, valid_items, prompt_index, session)
        session.commit()
        return SummaryParseResult(
            success=True,
            summaries_saved=saved_count,
            errors=all_messages,
            parsed_items=valid_items
        )
    except Exception as e:
        session.rollback()
        all_messages.append(f"Database error: {str(e)}")
        return SummaryParseResult(
            success=False,
            errors=all_messages,
            parsed_items=valid_items
        )
