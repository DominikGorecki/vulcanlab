"""
Answer expansion module for breaking down RAG answers into multi-section reports.

This module provides functionality to:
- Break down a RAG answer into 3-7 logical sections via LLM
- Run full RAG pipeline for each section independently
- Generate section responses (automatic or manual)
- Combine sections into a final unified report

Usage:
    from vulcanlab.expansion import breakdown_answer, expand_section, generate_section, combine_sections

    # Break down an answer into sections
    expansion_id = breakdown_answer(result_id, session, llm_client)

    # Expand a section through RAG pipeline
    expand_section(section_id, session)

    # Generate section response via LLM
    generate_section(section_id, session, llm_client)

    # Or save a manual response
    save_manual_response(section_id, response_text, session)

    # Combine all sections into final report
    combine_sections(expansion_id, session)
"""

from vulcanlab.expansion.breakdown import (
    breakdown_answer,
    estimate_answer_tokens,
    validate_answer_length,
)
from vulcanlab.expansion.section_processing import (
    expand_section,
    generate_section,
    save_manual_response,
)
from vulcanlab.expansion.combine import combine_sections

__all__ = [
    "breakdown_answer",
    "estimate_answer_tokens",
    "validate_answer_length",
    "expand_section",
    "generate_section",
    "save_manual_response",
    "combine_sections",
]
