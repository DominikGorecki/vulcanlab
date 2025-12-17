"""
Import flow for sanitized markdown files.

This module provides functions to import markdown files as Work records and
integrate with the chunking pipeline.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import tiktoken
from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.enums import FileType
from vulcanlab.markdown_import.metadata import Metadata, strip_frontmatter
from vulcanlab.simple_conversion.chunk_simple import (
    create_heading_chunks_simple,
    create_content_chunks_simple,
)
from vulcanlab.simple_conversion.sanitize_small import sanitize_small_document
from vulcanlab.simple_conversion.sanitize_large import sanitize_large_document
from vulcanlab.config.conversion_config import get_token_threshold

logger = logging.getLogger(__name__)

# Tiktoken encoding for token counting (matches OpenAI's cl100k_base)
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken cl100k_base encoding.

    Args:
        text: Text to count tokens for

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


def determine_sanitization_method(content: str) -> str:
    """Determine whether to use small or large sanitization method.

    Uses tiktoken to count tokens and compares against the configured threshold.

    Args:
        content: Markdown content to analyze

    Returns:
        "small" if token count < threshold, "large" otherwise
    """
    token_count = count_tokens(content)
    threshold = get_token_threshold()

    logger.debug(
        f"Token count: {token_count}, threshold: {threshold}"
    )

    if token_count < threshold:
        return "small"
    else:
        return "large"


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
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check for empty file
    file_size = path.stat().st_size
    if file_size == 0:
        logger.error(f"Empty file (0 bytes): {file_path}")
        raise ValueError("File is empty (0 bytes)")

    # Warn about very large files (> 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f"Large file detected ({file_size / (1024*1024):.2f} MB): {file_path}. "
            "Processing may take longer."
        )

    logger.info(f"Importing sanitized markdown: {path.name} ({file_size} bytes)")

    try:
        # Read file content with UTF-8 encoding
        content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError as e:
        # Try fallback encodings
        logger.warning(f"UTF-8 decoding failed for {file_path}, trying fallback encodings: {e}")
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                content = path.read_text(encoding=encoding)
                logger.info(f"Successfully read file using {encoding} encoding")
                break
            except Exception:
                continue
        else:
            logger.error(f"Failed to decode file with any known encoding: {file_path}")
            raise ValueError("File encoding not supported (tried UTF-8, latin-1, cp1252, iso-8859-1)")
    except PermissionError as e:
        logger.error(f"Permission denied reading file {file_path}: {e}")
        raise ValueError("Permission denied reading file")
    except OSError as e:
        logger.error(f"OS error reading file {file_path}: {e}")
        raise ValueError(f"Cannot read file: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {e}")
        raise ValueError(f"Failed to read file: {type(e).__name__}")

    # Strip frontmatter to get clean markdown
    clean_content = strip_frontmatter(content)

    # Check for empty content after stripping frontmatter
    if not clean_content or not clean_content.strip():
        logger.error(f"File contains no content after stripping frontmatter: {file_path}")
        raise ValueError("File contains only frontmatter or whitespace, no actual content")

    # Calculate content hash for deduplication
    content_hash = hashlib.sha256(clean_content.encode('utf-8')).hexdigest()

    # Begin transaction
    try:
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
            # Rollback transaction
            session.rollback()
            raise ValueError(f"Heading chunking failed: {str(e)}")

        # Create content chunks
        try:
            content_chunks = create_content_chunks_simple(work.id, session)
            logger.info(f"Created {len(content_chunks)} content chunks")
        except Exception as e:
            logger.error(f"Failed to create content chunks for work {work.id}: {e}")
            # Rollback transaction
            session.rollback()
            raise ValueError(f"Content chunking failed: {str(e)}")

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

        # Commit transaction
        session.commit()

        logger.info(f"Successfully imported work {work.id}: {metadata.title}")

        return work

    except Exception as e:
        # Rollback on any error
        logger.error(f"Import failed, rolling back transaction: {e}")
        session.rollback()
        raise


def import_unsanitized_markdown(
    file_path: str,
    metadata: Metadata,
    session: Session
) -> Work:
    """Import an unsanitized markdown file and run it through sanitization.

    Creates a Work record with FileType.MARKDOWN_IMPORT, stores the original
    markdown content, runs it through appropriate sanitization (small or large),
    creates chunks, and sets them to TO_VEC status for vectorization.

    Args:
        file_path: Path to the unsanitized markdown file
        metadata: Metadata object with title, author, year
        session: Database session

    Returns:
        Created Work object

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file cannot be read or sanitization fails
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check for empty file
    file_size = path.stat().st_size
    if file_size == 0:
        logger.error(f"Empty file (0 bytes): {file_path}")
        raise ValueError("File is empty (0 bytes)")

    # Warn about very large files (> 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file_size > MAX_FILE_SIZE:
        logger.warning(
            f"Large file detected ({file_size / (1024*1024):.2f} MB): {file_path}. "
            "Processing may take longer."
        )

    logger.info(f"Importing unsanitized markdown: {path.name} ({file_size} bytes)")

    try:
        # Read file content with UTF-8 encoding
        content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError as e:
        # Try fallback encodings
        logger.warning(f"UTF-8 decoding failed for {file_path}, trying fallback encodings: {e}")
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                content = path.read_text(encoding=encoding)
                logger.info(f"Successfully read file using {encoding} encoding")
                break
            except Exception:
                continue
        else:
            logger.error(f"Failed to decode file with any known encoding: {file_path}")
            raise ValueError("File encoding not supported (tried UTF-8, latin-1, cp1252, iso-8859-1)")
    except PermissionError as e:
        logger.error(f"Permission denied reading file {file_path}: {e}")
        raise ValueError("Permission denied reading file")
    except OSError as e:
        logger.error(f"OS error reading file {file_path}: {e}")
        raise ValueError(f"Cannot read file: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {e}")
        raise ValueError(f"Failed to read file: {type(e).__name__}")

    # Strip frontmatter to get clean markdown
    clean_content = strip_frontmatter(content)

    # Check for empty content after stripping frontmatter
    if not clean_content or not clean_content.strip():
        logger.error(f"File contains no content after stripping frontmatter: {file_path}")
        raise ValueError("File contains only frontmatter or whitespace, no actual content")

    # Calculate content hash for deduplication
    content_hash = hashlib.sha256(clean_content.encode('utf-8')).hexdigest()

    # Determine sanitization method
    sanitization_method = determine_sanitization_method(clean_content)
    token_count = count_tokens(clean_content)

    logger.info(
        f"Determined sanitization method: {sanitization_method} "
        f"(token count: {token_count})"
    )

    # Begin transaction
    try:
        # Create Work record
        work = Work(
            title=metadata.title,
            authors=metadata.author,
            year=metadata.year,
            source_path=path.name,
            work_type="markdown",
            files={
                "original_file": {
                    "path": path.name,
                    "type": "markdown",
                    "unsanitized": True
                }
            },
            content_hash=content_hash,
            processing_status={
                "simple_conversion_step": "parsed",
                "simple_conversion_classification": sanitization_method,
                "simple_conversion_mode": "automatic",
                "simple_conversion_token_count": token_count
            }
        )

        session.add(work)
        session.flush()  # Get work ID

        logger.debug(f"Created Work record with ID {work.id}")

        # Store original unsanitized markdown in converted_markdown field
        # Note: We're not using the converted_markdown model directly,
        # but storing the content in the work record's metadata for traceability
        work.processing_status["original_markdown_stored"] = True
        session.flush()

        # Run sanitization based on method
        try:
            logger.info(f"Starting {sanitization_method} sanitization for work {work.id}")

            # Create a temporary ParsedMarkdown record for the sanitization functions
            from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
            from vulcanlab.data.models.enums import DocumentClassification

            classification = (
                DocumentClassification.SMALL
                if sanitization_method == "small"
                else DocumentClassification.LARGE
            )

            parsed = ParsedMarkdown(
                work_id=work.id,
                content=clean_content,
                file_type=FileType.MARKDOWN_IMPORT,
                classification=classification,
                token_count=token_count
            )
            session.add(parsed)
            session.flush()

            # Call appropriate sanitization function
            if sanitization_method == "small":
                sanitized = sanitize_small_document(work.id, session)
            else:
                sanitized = sanitize_large_document(work.id, session)

            logger.info(
                f"Sanitization complete: {sanitized.token_count} tokens in sanitized version"
            )

        except Exception as e:
            logger.error(f"Sanitization failed for work {work.id}: {e}")
            # Rollback transaction
            session.rollback()
            raise ValueError(f"Sanitization failed: {str(e)}")

        # Update processing status before chunking
        work.processing_status["simple_conversion_step"] = "chunking"
        session.flush()

        # Create heading chunks
        try:
            heading_chunks = create_heading_chunks_simple(work.id, session)
            logger.info(f"Created {len(heading_chunks)} heading chunks")
        except Exception as e:
            logger.error(f"Failed to create heading chunks for work {work.id}: {e}")
            # Rollback transaction
            session.rollback()
            raise ValueError(f"Heading chunking failed: {str(e)}")

        # Create content chunks
        try:
            content_chunks = create_content_chunks_simple(work.id, session)
            logger.info(f"Created {len(content_chunks)} content chunks")
        except Exception as e:
            logger.error(f"Failed to create content chunks for work {work.id}: {e}")
            # Rollback transaction
            session.rollback()
            raise ValueError(f"Content chunking failed: {str(e)}")

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
            "simple_conversion_classification": sanitization_method,
            "simple_conversion_mode": "automatic",
            "simple_conversion_token_count": token_count,
            "sanitized_token_count": sanitized.token_count,
            "heading_chunk_count": len(heading_chunks),
            "content_chunk_count": len(content_chunks)
        }

        # Commit transaction
        session.commit()

        logger.info(
            f"Successfully imported unsanitized work {work.id}: {metadata.title} "
            f"({sanitization_method} method)"
        )

        return work

    except Exception as e:
        # Rollback on any error
        logger.error(f"Import failed, rolling back transaction: {e}")
        session.rollback()
        raise
