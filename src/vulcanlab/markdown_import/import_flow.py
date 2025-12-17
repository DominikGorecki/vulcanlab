"""
Import flow for sanitized markdown files.

This module provides functions to import markdown files as Work records and
integrate with the chunking pipeline.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.enums import FileType
from vulcanlab.markdown_import.metadata import Metadata, strip_frontmatter
from vulcanlab.simple_conversion.chunk_simple import (
    create_heading_chunks_simple,
    create_content_chunks_simple,
)

logger = logging.getLogger(__name__)


def count_tokens_simple(text: str) -> int:
    """Simple token count estimation (words * 1.3).

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    words = len(text.split())
    return int(words * 1.3)


def import_sanitized_markdown(
    file_path: str,
    metadata: Metadata,
    session: Session
) -> Work:
    """Import a sanitized markdown file as a Work record.

    Creates a Work record with FileType.MARKDOWN_IMPORT, stores the markdown
    content in sanitized_markdown table, creates chunks, and sets them to
    TO_VEC status for vectorization.

    Args:
        file_path: Path to the markdown file
        metadata: Metadata object with title, author, year
        session: Database session

    Returns:
        Created Work object

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file cannot be read or processed
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Importing sanitized markdown: {path.name}")

    try:
        # Read file content
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise ValueError(f"Failed to read file: {e}")

    # Strip frontmatter to get clean markdown
    clean_content = strip_frontmatter(content)

    if not clean_content:
        raise ValueError("File contains no content after stripping frontmatter")

    # Calculate content hash for deduplication
    content_hash = hashlib.sha256(clean_content.encode('utf-8')).hexdigest()

    # Create Work record
    work = Work(
        title=metadata.title,
        authors=metadata.author,
        year=metadata.year,
        source_path=path.name,  # Store just filename
        work_type="markdown",
        files={
            "original_file": {
                "path": path.name,
                "type": "markdown"
            }
        },
        content_hash=content_hash,
        processing_status={
            "simple_conversion_step": "sanitizing",
            "simple_conversion_classification": "small",  # Default to small
            "simple_conversion_mode": "automatic"
        }
    )

    session.add(work)
    session.flush()  # Get work ID

    logger.debug(f"Created Work record with ID {work.id}")

    # Store sanitized markdown
    token_count = count_tokens_simple(clean_content)

    sanitized = SanitizedMarkdown(
        work_id=work.id,
        content=clean_content,
        token_count=token_count
    )

    session.add(sanitized)
    session.flush()

    logger.debug(f"Stored sanitized markdown ({token_count} tokens)")

    # Update processing status
    work.processing_status = {
        "simple_conversion_step": "chunking",
        "simple_conversion_classification": "small",
        "simple_conversion_mode": "automatic",
        "simple_conversion_token_count": token_count
    }
    session.flush()

    # Create heading chunks
    try:
        heading_chunks = create_heading_chunks_simple(work.id, session)
        logger.info(f"Created {len(heading_chunks)} heading chunks")
    except Exception as e:
        logger.error(f"Failed to create heading chunks for work {work.id}: {e}")
        # Update status to failed
        work.processing_status = {
            "simple_conversion_step": "failed",
            "simple_conversion_error": f"Heading chunking failed: {str(e)}"
        }
        session.commit()
        raise ValueError(f"Heading chunking failed: {e}")

    # Create content chunks
    try:
        content_chunks = create_content_chunks_simple(work.id, session)
        logger.info(f"Created {len(content_chunks)} content chunks")
    except Exception as e:
        logger.error(f"Failed to create content chunks for work {work.id}: {e}")
        # Update status to failed
        work.processing_status = {
            "simple_conversion_step": "failed",
            "simple_conversion_error": f"Content chunking failed: {str(e)}"
        }
        session.commit()
        raise ValueError(f"Content chunking failed: {e}")

    # Set all content chunks to TO_VEC status
    chunks_updated = 0
    for chunk in content_chunks:
        if chunk.vector_status != "no_vec":  # Skip heading chunks
            chunk.vector_status = "to_vec"
            chunks_updated += 1

    logger.info(f"Set {chunks_updated} chunks to TO_VEC status")

    # Update processing status to complete
    work.processing_status = {
        "simple_conversion_step": "complete",
        "simple_conversion_classification": "small",
        "simple_conversion_mode": "automatic",
        "simple_conversion_token_count": token_count,
        "heading_chunk_count": len(heading_chunks),
        "content_chunk_count": len(content_chunks)
    }

    session.commit()

    logger.info(f"Successfully imported work {work.id}: {metadata.title}")

    return work
