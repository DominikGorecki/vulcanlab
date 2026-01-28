"""
Section combination module for merging expanded sections into final report.

This module handles combining all completed expansion sections into a unified
markdown report with proper headings, renumbered source references, and a
consolidated References section.

Usage:
    from vulcanlab.expansion.combine import combine_sections

    # Combine all sections into final report
    combine_sections(expansion_id, session)
"""

from __future__ import annotations

import logging
import re
from typing import Tuple

from sqlalchemy.orm import Session

from vulcanlab.data.models.expansion import (
    AnswerExpansion,
    ExpansionSection,
    ExpansionStatus,
    SectionStatus,
)


logger = logging.getLogger(__name__)


def _find_source_references(text: str) -> list[int]:
    """Find all [S#] source reference numbers in text.

    Args:
        text: The text to search for source references.

    Returns:
        List of unique reference numbers found (integers), sorted ascending.
    """
    pattern = r'\[S(\d+)\]'
    matches = re.findall(pattern, text)
    return sorted(set(int(m) for m in matches))


def _renumber_references(text: str, offset: int) -> str:
    """Renumber all [S#] references by adding offset.

    Args:
        text: The text containing source references.
        offset: The number to add to each reference.

    Returns:
        Text with renumbered references.
    """
    if offset == 0:
        return text

    def replace_ref(match):
        original_num = int(match.group(1))
        new_num = original_num + offset
        return f'[S{new_num}]'

    pattern = r'\[S(\d+)\]'
    return re.sub(pattern, replace_ref, text)


def _format_source_reference(
    index: int,
    source: dict
) -> str:
    """Format a single source reference for the References section.

    Args:
        index: The renumbered source index (1-based).
        source: The source metadata dict from clean_retrieval_context.

    Returns:
        Formatted reference string.
    """
    work_title = source.get('work_title', 'Unknown')
    heading_chain = source.get('heading_chain', [])
    work_id = source.get('work_id')
    start_line = source.get('start_line', 0)
    end_line = source.get('end_line', 0)

    if heading_chain:
        breadcrumb_path = " > ".join(heading_chain)
        source_path = f"{work_title} > {breadcrumb_path}"
    else:
        source_path = work_title

    return f"[S{index}] {source_path} | (work_id={work_id}, start-line={start_line}, end-line={end_line})"


def _build_references_section(sources: list[Tuple[int, dict]]) -> str:
    """Build the unified References section.

    Args:
        sources: List of (index, source_metadata) tuples.

    Returns:
        Formatted References section markdown with each reference
        separated by blank lines.
    """
    if not sources:
        return ""

    lines = ["## References", ""]
    for index, source in sorted(sources, key=lambda x: x[0]):
        lines.append(_format_source_reference(index, source))
        lines.append("")  # Empty line after each reference

    return "\n".join(lines)


def combine_sections(expansion_id: int, session: Session) -> str:
    """Combine all completed sections into a final unified report.

    This function:
    1. Loads the expansion and all its sections
    2. Verifies all sections are completed
    3. Renumbers source references to avoid collisions across sections
    4. Builds a markdown report with headings and section responses
    5. Adds a consolidated References section at the end
    6. Adds a link to the original answer at the top
    7. Stores the report in the expansion record

    Args:
        expansion_id: ID of the AnswerExpansion to combine.
        session: Database session.

    Returns:
        The combined report markdown text.

    Raises:
        ValueError: If expansion not found or sections not all completed.
    """
    # Load expansion
    expansion = session.query(AnswerExpansion).filter(
        AnswerExpansion.id == expansion_id
    ).first()
    if not expansion:
        raise ValueError(f"AnswerExpansion with ID {expansion_id} not found")

    logger.info(f"Starting combination for expansion {expansion_id}")

    # Update status
    expansion.status = ExpansionStatus.COMBINING
    session.commit()

    try:
        # Load all sections ordered by order
        sections = session.query(ExpansionSection).filter(
            ExpansionSection.expansion_id == expansion_id
        ).order_by(ExpansionSection.order).all()

        if not sections:
            raise ValueError(f"Expansion {expansion_id} has no sections")

        # Verify all sections are completed
        incomplete_sections = [
            s for s in sections if s.status != SectionStatus.COMPLETED
        ]
        if incomplete_sections:
            incomplete_info = ", ".join(
                f"#{s.order} ({s.status.value})" for s in incomplete_sections
            )
            raise ValueError(
                f"Cannot combine: {len(incomplete_sections)} sections not completed: "
                f"{incomplete_info}"
            )

        # Build the report with renumbered references
        report_parts = []

        # Add link to original answer
        original_answer_url = f"/rag/{expansion.query_id}/results/{expansion.result_id}"
        report_parts.append(
            f"[View Original Answer]({original_answer_url})\n"
        )

        report_parts.append("---\n")

        # Process sections with source renumbering
        offset = 0
        all_sources: list[Tuple[int, dict]] = []

        for section in sections:
            # Add section heading (H2)
            report_parts.append(f"## {section.heading}\n")

            # Add section summary as italicized intro if present
            if section.summary:
                report_parts.append(f"*{section.summary}*\n")

            # Process response text with renumbered references
            if section.response_text:
                renumbered_text = _renumber_references(section.response_text, offset)
                report_parts.append(f"\n{renumbered_text}\n")
            else:
                report_parts.append("\n*(No response available)*\n")

            # Collect source metadata with renumbered indices
            clean_context = section.clean_retrieval_context or {}
            chunks = clean_context.get("chunks", [])
            for idx, chunk in enumerate(chunks, start=1):
                renumbered_index = idx + offset
                all_sources.append((renumbered_index, chunk))

            # Update offset for next section
            offset += len(chunks)

            report_parts.append("")  # Empty line between sections

        # Add consolidated References section
        references_section = _build_references_section(all_sources)
        if references_section:
            report_parts.append("\n")
            report_parts.append(references_section)

        # Combine into final report
        combined_report = "\n".join(report_parts).strip()

        # Store in expansion record
        expansion.combined_report = combined_report
        expansion.status = ExpansionStatus.COMPLETED
        session.commit()

        logger.info(
            f"Combination complete for expansion {expansion_id}: "
            f"{len(sections)} sections, {len(all_sources)} total sources, "
            f"{len(combined_report):,} chars"
        )

        return combined_report

    except Exception as e:
        logger.error(f"Combination failed for expansion {expansion_id}: {e}")
        expansion.status = ExpansionStatus.FAILED
        expansion.expansion_metadata = expansion.expansion_metadata or {}
        expansion.expansion_metadata["error"] = str(e)
        session.commit()
        raise
