"""
Answer breakdown module for expanding RAG answers into multi-section reports.

This module handles the initial breakdown of a RAG answer into 3-7 logical sections
via LLM, with token validation to ensure the answer is within processing limits.

Usage:
    from vulcanlab.expansion.breakdown import breakdown_answer, validate_answer_length

    # Validate answer length before processing
    validate_answer_length(answer_text, max_tokens=30000)

    # Break down an answer into sections
    expansion_id = breakdown_answer(result_id, session, llm_client)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Protocol, Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from vulcanlab.data.models.result import Result
from vulcanlab.data.models.expansion import (
    AnswerExpansion,
    ExpansionSection,
    ExpansionMode,
    ExpansionStatus,
    SectionStatus,
)
from vulcanlab.data.template_loader import get_active_template


logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_TOKENS = 30000
TOKENS_PER_WORD_ESTIMATE = 1.3  # Rough estimate for English text


class LLMClient(Protocol):
    """Protocol for LLM client interface."""

    def invoke(self, prompt: str) -> Any:
        """Invoke the LLM with a prompt and return the response."""
        ...

    def with_structured_output(self, schema: type) -> "LLMClient":
        """Return a client configured for structured output."""
        ...


@dataclass
class SectionBreakdown:
    """Parsed section data from LLM breakdown response."""

    order: int
    heading: str
    summary: str
    expansion_prompt: str


class BreakdownResponseSchema(BaseModel):
    """Pydantic schema for LLM breakdown response.

    Used with with_structured_output() to ensure valid JSON from LLMs.
    """

    sections: list[dict] = Field(
        description="List of 3-7 sections, each with heading, summary, and expansion_prompt"
    )


def estimate_answer_tokens(answer_text: str) -> int:
    """Estimate the number of tokens in an answer text.

    Uses a simple word-based heuristic (approximately 1.3 tokens per word
    for English text). This is a rough estimate and may vary depending
    on the actual tokenizer used.

    Args:
        answer_text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    if not answer_text:
        return 0

    word_count = len(answer_text.split())
    return int(word_count * TOKENS_PER_WORD_ESTIMATE)


def validate_answer_length(answer_text: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
    """Validate that an answer is within the token limit.

    Args:
        answer_text: The answer text to validate.
        max_tokens: Maximum allowed tokens (default 30,000).

    Raises:
        ValueError: If the answer exceeds the token limit.
    """
    estimated_tokens = estimate_answer_tokens(answer_text)

    if estimated_tokens > max_tokens:
        raise ValueError(
            f"Answer exceeds token limit: estimated {estimated_tokens:,} tokens, "
            f"maximum allowed is {max_tokens:,} tokens. "
            f"Please use a shorter answer for expansion."
        )


def generate_breakdown_prompt(answer_text: str, session: Session) -> str:
    """Generate the LLM prompt for breaking down an answer into sections.

    Loads the prompt template from the database.

    Args:
        answer_text: The original RAG answer to break down.
        session: Database session for loading template.

    Returns:
        The complete prompt string to send to an LLM.

    Raises:
        ValueError: If no active template is found.
    """
    template_content = get_active_template("answer_breakdown", session)
    return template_content.format(answer_text=answer_text)


def parse_breakdown_response(response: Any) -> list[SectionBreakdown]:
    """Parse the LLM response into structured section data.

    Handles both structured output (Pydantic model) and raw text responses.

    Args:
        response: The LLM response (can be BreakdownResponseSchema or raw text).

    Returns:
        List of SectionBreakdown objects representing 3-7 sections.

    Raises:
        ValueError: If response cannot be parsed or section count is invalid.
    """
    # Handle structured output
    if isinstance(response, BreakdownResponseSchema):
        sections_data = response.sections
    elif hasattr(response, 'sections'):
        sections_data = response.sections
    else:
        # Try to parse as JSON text
        text = str(response)

        # Handle markdown code blocks
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            text = text[json_start:json_end].strip()
        elif "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
            text = text[json_start:json_end].strip()

        try:
            data = json.loads(text)
            sections_data = data.get("sections", [])
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    # Validate section count
    if not sections_data:
        raise ValueError("LLM response contained no sections")

    if len(sections_data) < 3:
        raise ValueError(f"LLM returned only {len(sections_data)} sections, minimum is 3")

    if len(sections_data) > 7:
        logger.warning(
            f"LLM returned {len(sections_data)} sections, truncating to 7"
        )
        sections_data = sections_data[:7]

    # Parse into dataclass objects
    sections = []
    for idx, section in enumerate(sections_data, start=1):
        # Handle both dict and object access
        if isinstance(section, dict):
            heading = section.get("heading", "")
            summary = section.get("summary", "")
            expansion_prompt = section.get("expansion_prompt", "")
        else:
            heading = getattr(section, "heading", "")
            summary = getattr(section, "summary", "")
            expansion_prompt = getattr(section, "expansion_prompt", "")

        if not heading or not expansion_prompt:
            raise ValueError(
                f"Section {idx} is missing required fields: "
                f"heading={bool(heading)}, expansion_prompt={bool(expansion_prompt)}"
            )

        sections.append(SectionBreakdown(
            order=idx,
            heading=heading.strip(),
            summary=summary.strip() if summary else "",
            expansion_prompt=expansion_prompt.strip()
        ))

    return sections


def breakdown_answer(
    result_id: int,
    session: Session,
    llm_client: LLMClient,
    mode: ExpansionMode = ExpansionMode.AUTOMATIC,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> int:
    """Break down a RAG answer into 3-7 sections for expansion.

    This function:
    1. Loads the result from the database
    2. Validates the answer is within the token limit
    3. Calls the LLM to generate section breakdown
    4. Creates AnswerExpansion and ExpansionSection records

    Args:
        result_id: ID of the Result to expand.
        session: Database session.
        llm_client: LLM client for breakdown generation.
        mode: Expansion mode (automatic or manual).
        max_tokens: Maximum tokens allowed for the answer (default 30,000).

    Returns:
        The ID of the created AnswerExpansion record.

    Raises:
        ValueError: If result not found, answer exceeds token limit,
                    or LLM response is invalid.
    """
    # Load result from database
    result = session.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise ValueError(f"Result with ID {result_id} not found")

    # Check if expansion already exists
    existing = session.query(AnswerExpansion).filter(
        AnswerExpansion.result_id == result_id
    ).first()
    if existing:
        raise ValueError(
            f"Expansion already exists for result {result_id} (expansion_id={existing.id})"
        )

    # Validate token limit
    answer_text = result.response_text
    validate_answer_length(answer_text, max_tokens)

    logger.info(
        f"Starting breakdown for result {result_id} "
        f"(~{estimate_answer_tokens(answer_text):,} tokens, mode={mode.value})"
    )

    # Generate breakdown prompt
    prompt = generate_breakdown_prompt(answer_text, session)

    # Call LLM with structured output
    try:
        structured_client = llm_client.with_structured_output(BreakdownResponseSchema)
        response = structured_client.invoke(prompt)
    except AttributeError:
        # Fallback to regular invocation if structured output not supported
        logger.warning("Structured output not supported, using raw invocation")
        response = llm_client.invoke(prompt)

    # Parse response
    sections = parse_breakdown_response(response)

    logger.info(f"LLM returned {len(sections)} sections for result {result_id}")

    # Create expansion record
    expansion = AnswerExpansion(
        result_id=result_id,
        query_id=result.query_id,
        mode=mode,
        status=ExpansionStatus.BREAKDOWN_COMPLETE,
        expansion_metadata={
            "source_token_estimate": estimate_answer_tokens(answer_text),
            "section_count": len(sections)
        }
    )
    session.add(expansion)
    session.flush()  # Get expansion ID

    # Create section records
    for section_data in sections:
        section = ExpansionSection(
            expansion_id=expansion.id,
            order=section_data.order,
            heading=section_data.heading,
            summary=section_data.summary,
            expansion_prompt=section_data.expansion_prompt,
            status=SectionStatus.PENDING
        )
        session.add(section)

    session.commit()

    logger.info(
        f"Created expansion {expansion.id} with {len(sections)} sections "
        f"for result {result_id}"
    )

    return expansion.id
