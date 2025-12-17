"""Work deletion operations.

This module provides core business logic for deleting works and their associated data.
"""

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from .models.work import Work
from .models.parsed_markdown import ParsedMarkdown
from .models.sanitized_markdown import SanitizedMarkdown
from ..config.app_config import load_config

logger = logging.getLogger(__name__)


def delete_work(work_id: int, session: Session) -> None:
    """Delete a work and all associated data including files.

    Deletes the Work record along with all related ParsedMarkdown, SanitizedMarkdown,
    and physical files tracked in the Work.files JSON field. Chunks are automatically
    deleted via CASCADE foreign key constraints.

    Args:
        work_id: ID of the work to delete
        session: SQLAlchemy session (managed by caller)

    Raises:
        ValueError: If work_id is not found in database
        IOError: If file deletion fails (except for FileNotFoundError)

    Example:
        >>> from vulcanlab.data.database import get_session
        >>> with get_session() as session:
        ...     delete_work(work_id=123, session=session)
        ...     session.commit()
    """
    # Query work by ID
    work = session.query(Work).filter(Work.id == work_id).first()

    if work is None:
        raise ValueError(f"Work with ID {work_id} not found")

    logger.info(f"Deleting work_id={work_id}: {work.title}")

    # Load config to get output directory
    config = load_config()
    output_dir = Path(config.paths.output_dir)

    # Delete files tracked in Work.files JSON field
    files_deleted_count = 0
    if work.files is not None and work.files:
        logger.info(f"Processing {len(work.files)} file entries for work_id={work_id}")

        for file_key, file_info in work.files.items():
            if file_info and isinstance(file_info, dict) and "path" in file_info:
                file_path = output_dir / file_info["path"]

                try:
                    logger.debug(f"Attempting to delete file: {file_path}")
                    file_path.unlink(missing_ok=True)
                    files_deleted_count += 1
                    logger.debug(f"Deleted file: {file_path}")
                except FileNotFoundError:
                    # File already deleted, continue
                    logger.debug(f"File not found (already deleted): {file_path}")
                    pass
                except Exception as e:
                    # Other errors (permission, etc.) should raise IOError
                    logger.error(f"Failed to delete file {file_path}: {e}")
                    raise IOError(f"Failed to delete file {file_path}: {e}") from e

    logger.info(f"Deleted {files_deleted_count} files for work_id={work_id}")

    # Delete ParsedMarkdown records
    parsed_count = session.query(ParsedMarkdown).filter(
        ParsedMarkdown.work_id == work_id
    ).delete()
    logger.info(f"Deleted {parsed_count} ParsedMarkdown records for work_id={work_id}")

    # Delete SanitizedMarkdown records
    sanitized_count = session.query(SanitizedMarkdown).filter(
        SanitizedMarkdown.work_id == work_id
    ).delete()
    logger.info(f"Deleted {sanitized_count} SanitizedMarkdown records for work_id={work_id}")

    # Delete the Work record (chunks will cascade automatically)
    session.delete(work)
    logger.info(f"Deleted Work record for work_id={work_id} (chunks cascade automatically)")

    # Note: Caller is responsible for committing the transaction
