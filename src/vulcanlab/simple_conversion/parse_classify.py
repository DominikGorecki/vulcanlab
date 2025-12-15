"""
Parse and classify module for simple conversion pipeline.

Takes a Work with converted markdown, counts tokens, classifies the document
as SMALL or LARGE based on configurable threshold, and saves ParsedMarkdown
record to the database.
"""

import logging
from typing import Tuple
from datetime import datetime, UTC

import tiktoken
from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.enums import DocumentClassification, FileType
from vulcanlab.data.database import get_session
from vulcanlab.config.conversion_config import get_token_threshold

logger = logging.getLogger(__name__)

# Tiktoken encoding for token counting (matches OpenAI's cl100k_base)
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken cl100k_base encoding.

    Args:
        text: Markdown text to count tokens for

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0

    try:
        tokens = ENCODING.encode(text)
        return len(tokens)
    except Exception as e:
        logger.error(f"Failed to count tokens: {e}")
        # Fallback to rough word-based estimate (1 token ≈ 0.75 words)
        word_count = len(text.split())
        return int(word_count / 0.75)


def classify_document(token_count: int, threshold: int) -> DocumentClassification:
    """
    Classify document as SMALL or LARGE based on token count.

    Args:
        token_count: Number of tokens in the document
        threshold: Token threshold from configuration

    Returns:
        DocumentClassification.SMALL or DocumentClassification.LARGE
    """
    if token_count < threshold:
        return DocumentClassification.SMALL
    else:
        return DocumentClassification.LARGE


def get_markdown_from_citation(work: Work, session: Session) -> str:
    """
    Get markdown content from Citation API for the given Work.

    This uses the existing citation API pattern to retrieve the
    converted markdown content for the work.

    Args:
        work: Work record with conversion completed
        session: Database session

    Returns:
        Markdown content as string

    Raises:
        ValueError: If work has no citation or markdown not available
    """
    # TODO: This function needs to be implemented based on the actual Citation API
    # The ticket spec assumes this API exists, but it may need to be created
    # or the function signature may need to match an existing API

    if not work.citation_id:
        raise ValueError(f"Work {work.id} has no citation")

    # Placeholder: Read markdown from work's output file or citation storage
    # This should use the actual Citation API when available
    raise NotImplementedError(
        "Citation API integration not yet implemented. "
        "Need to implement get_markdown_for_work() function."
    )


def parse_and_classify(work_id: int, session: Session) -> ParsedMarkdown:
    """
    Parse markdown from Citation API and classify the document.

    This function:
    1. Retrieves Work by ID
    2. Gets markdown from Citation API
    3. Counts tokens using tiktoken
    4. Classifies as SMALL or LARGE
    5. Creates ParsedMarkdown record
    6. Updates Work.processing_status

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        Created ParsedMarkdown record

    Raises:
        ValueError: If work not found or invalid state
    """
    # Get work
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    # Get file path from processing status
    file_path = None
    if work.processing_status and 'file_path' in work.processing_status:
        file_path = work.processing_status['file_path']
    
    if not file_path:
        raise ValueError(f"No file path found for work {work_id}")

    try:
        from vulcanlab.conversions.conv_pdf2md import convert_pdf_to_markdown
        logger.info(f"Converting PDF: {file_path}")
        # Use hierarchical mode for single best output
        markdown_content = convert_pdf_to_markdown(
            pdf_path=file_path, 
            compare=False, 
            hierarchical=True,
            verbose=True
        )
    except Exception as e:
        logger.error(f"PDF conversion failed for {file_path}: {e}")
        # Propagate error so user sees it
        raise ValueError(f"PDF conversion failed: {str(e)}")
        
    if not markdown_content:
        raise ValueError("Conversion produced empty output")

    # Count tokens
    token_count = count_tokens(markdown_content)
    logger.info(f"Work {work_id} has {token_count} tokens")

    # Get threshold from config
    threshold = get_token_threshold()
    logger.info(f"Using token threshold: {threshold}")

    # Classify
    classification = classify_document(token_count, threshold)
    logger.info(f"Work {work_id} classified as: {classification.value}")

    # Determine file_type from work (assuming PDF for now, can be enhanced)
    # TODO: Get actual file type from work metadata
    file_type = FileType.PDF

    # Create ParsedMarkdown record
    parsed = ParsedMarkdown(
        work_id=work_id,
        content=markdown_content,  # Auto-compressed by model if >1MB
        file_type=file_type,
        classification=classification,
        token_count=token_count,
        created_at=datetime.now(UTC)
    )

    session.add(parsed)

    # Update Work.processing_status
    if not work.processing_status:
        work.processing_status = {}

    work.processing_status['simple_conversion_step'] = 'parsed'
    work.processing_status['simple_conversion_classification'] = classification.value
    work.processing_status['simple_conversion_token_count'] = token_count

    session.commit()
    session.refresh(parsed)

    logger.info(
        f"Created ParsedMarkdown {parsed.id} for work {work_id} "
        f"({classification.value}, {token_count} tokens)"
    )

    return parsed


def parse_and_classify_standalone(work_id: int) -> Tuple[int, str]:
    """
    Standalone version of parse_and_classify for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Tuple of (token_count, classification_string)

    Raises:
        ValueError: If work not found or invalid state
    """
    with get_session() as session:
        parsed = parse_and_classify(work_id, session)
        return (parsed.token_count, parsed.classification.value)
