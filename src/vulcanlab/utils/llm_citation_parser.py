"""LLM-based citation parser module.

This module provides functions for parsing citation strings using LLM
to extract bibliographic metadata into structured Pydantic models.

Supported citation formats:
- APA (American Psychological Association)
- MLA (Modern Language Association)
- Chicago (Chicago Manual of Style)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from vulcanlab.ai.config import LLMSettings


class Citation(BaseModel):
    """Parsed citation data from LLM.

    All fields are optional to support partial extraction from
    incomplete or malformed citations. Maps to Work model fields
    plus additional citation-specific metadata.

    Attributes:
        title: Title of the work
        authors: List of author names as simple strings
        year: Year of publication (4-digit)
        publisher: Publisher name
        isbn: ISBN for books
        doi: Digital Object Identifier
        container_title: Journal name or book title (for articles/chapters)
        volume: Volume number
        issue: Issue number
        pages: Page range (e.g., '248-252')
        url: URL for online resources
        work_type: Type of work ('book', 'article', 'chapter', etc.)
    """

    title: str | None = Field(
        default=None,
        max_length=500,
        description="Title of the work"
    )
    authors: list[str] | None = Field(
        default=None,
        description="List of author names as simple strings"
    )
    year: int | None = Field(
        default=None,
        ge=1000,
        le=9999,
        description="Year of publication (4-digit)"
    )
    publisher: str | None = Field(
        default=None,
        max_length=255,
        description="Publisher name"
    )
    isbn: str | None = Field(
        default=None,
        max_length=20,
        description="ISBN for books"
    )
    doi: str | None = Field(
        default=None,
        max_length=255,
        description="Digital Object Identifier"
    )
    container_title: str | None = Field(
        default=None,
        max_length=500,
        description="Journal name or book title (for articles/chapters)"
    )
    volume: str | None = Field(
        default=None,
        max_length=50,
        description="Volume number"
    )
    issue: str | None = Field(
        default=None,
        max_length=50,
        description="Issue number"
    )
    pages: str | None = Field(
        default=None,
        max_length=50,
        description="Page range (e.g., '248-252')"
    )
    url: str | None = Field(
        default=None,
        max_length=1000,
        description="URL for online resources"
    )
    work_type: str | None = Field(
        default=None,
        max_length=50,
        description="Type of work: 'book', 'article', 'chapter', etc."
    )


def _build_citation_prompt(citation_text: str, citation_format: str) -> str:
    """Build the LLM prompt for citation parsing.

    Args:
        citation_text: The citation string to parse
        citation_format: Citation format (APA, MLA, or Chicago)

    Returns:
        Formatted prompt string for the LLM
    """
    return f"""You are an expert bibliographic data extractor. Parse the following {citation_format} citation and extract all available fields.

## Citation to Parse:
{citation_text}

## Citation Format: {citation_format}

## Extraction Rules:
1. Extract all available bibliographic information
2. For authors: return as a list of simple name strings (preserve format as-is)
3. For year: extract 4-digit year only
4. For work_type: infer from citation structure ('book', 'article', 'chapter', etc.)
5. Distinguish between publisher and container_title:
   - container_title: journal name or book title (for articles/chapters)
   - publisher: publishing company or organization
6. If a field cannot be determined, return null
7. For volume and issue, keep them separate if possible

## Output Format:
Return ONLY valid JSON matching this structure:
{{
    "title": "string or null",
    "authors": ["string1", "string2"] or null,
    "year": integer or null,
    "publisher": "string or null",
    "isbn": "string or null",
    "doi": "string or null",
    "container_title": "string or null",
    "volume": "string or null",
    "issue": "string or null",
    "pages": "string or null",
    "url": "string or null",
    "work_type": "string or null"
}}

Do not include any explanatory text, only the JSON object."""


def parse_citation_with_llm(
    citation_text: str,
    citation_format: str,
    settings: LLMSettings | None = None,
) -> Citation:
    """Parse a citation string using LLM.

    Uses the LIGHT tier LLM to extract bibliographic metadata from
    citation text in APA, MLA, or Chicago formats.

    Args:
        citation_text: The citation text to parse
        citation_format: Citation format - "APA", "MLA", or "Chicago"
        settings: LLM settings (loads from .env if None)

    Returns:
        Citation object with extracted fields (None for missing data)

    Raises:
        ValueError: If citation_text is empty, format is invalid,
                   or LLM parsing fails

    Examples:
        >>> citation = "Friston, K. (2012). Prediction, perception and agency. International Journal of Psychophysiology, 83(2), 248-252."
        >>> result = parse_citation_with_llm(citation, "APA")
        >>> print(result.title)
        'Prediction, perception and agency'
        >>> print(result.year)
        2012
    """
    # Validation
    if not citation_text or not citation_text.strip():
        raise ValueError("citation_text cannot be empty")

    if citation_format not in ["APA", "MLA", "Chicago"]:
        raise ValueError(f"Unsupported citation format: {citation_format}")

    # Load LLM settings
    if settings is None:
        from vulcanlab.ai.config import LLMSettings
        settings = LLMSettings()

    # Build prompt
    prompt = _build_citation_prompt(citation_text.strip(), citation_format)

    try:
        # Use llm_factory to create chat model with proper configuration
        from vulcanlab.ai.llm_factory import create_langchain_chat
        from vulcanlab.ai.config import ModelTier

        # Create chat stack using factory
        langchain_stack = create_langchain_chat(settings, tier=ModelTier.LIGHT)
        chat = langchain_stack.chat

        # Create structured output runnable
        structured_llm = chat.with_structured_output(Citation)

        # Invoke runnable
        citation = structured_llm.invoke(prompt)

        return citation

    except Exception as e:
        # Wrap errors with context
        raise ValueError(f"LLM citation parsing failed: {str(e)}") from e
