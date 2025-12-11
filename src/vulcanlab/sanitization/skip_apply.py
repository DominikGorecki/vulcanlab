"""
Skip sanitization and copy original markdown to sanitized version.

This module provides functionality to skip the title change sanitization process
and simply copy the original markdown file to create a sanitized version. This is
useful when the document doesn't require heading corrections.

Usage:
    from vulcanlab.sanitization import skip_apply_from_work
    
    # Skip sanitization for a work
    output_path = skip_apply_from_work(work_id=1, source_key='original_markdown')

Functions:
    skip_apply_from_work(work_id, source_key, force, verbose) - Skip and copy to sanitized

Exceptions:
    ValueError - Raised when work not found, invalid params, or sanitized already exists
    HashMismatchError - Raised when file hash doesn't match database
    FileNotFoundError - Raised when source file doesn't exist
"""

import shutil
from pathlib import Path
from typing import Optional

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import compute_file_hash, set_file_readonly, get_path_resolver
from vulcanlab.sanitization.extract_titles import HashMismatchError

# Initialize path resolver
resolver = get_path_resolver()


def skip_apply_from_work(
    work_id: int,
    source_key: str = "original_markdown",
    force: bool = False,
    verbose: bool = False
) -> Path:
    """Skip sanitization and copy original markdown to create sanitized version.
    
    This function copies the source markdown file to a .sanitized.md version without
    applying any title changes. Updates the work's files metadata with the new file.
    
    Args:
        work_id: Database ID of the work.
        source_key: Key in the files JSON ("original_markdown" typically).
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.
    
    Returns:
        Path to the created sanitized file.
    
    Raises:
        ValueError: If work_id not found, source_key invalid, files not in database,
                   or sanitized file already exists.
        HashMismatchError: If file hash doesn't match stored hash (unless force=True).
        FileNotFoundError: If the file referenced in database doesn't exist on disk.
    """
    # Load work from database
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")
        
        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")
        
        # Validate source_key
        if source_key not in ["original_markdown", "sanitized"]:
            raise ValueError(
                f"Invalid source_key: {source_key}. "
                f"Must be 'original_markdown' or 'sanitized'"
            )
        
        # Check if sanitized already exists
        if "sanitized" in work.files and not force:
            raise ValueError(
                f"Work {work_id} already has a 'sanitized' file. "
                f"Use force=True to overwrite."
            )
        
        # Validate source file exists in metadata
        if source_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{source_key}' in files metadata"
            )
        
        # Get file info
        source_info = work.files[source_key]
        source_path = resolver.resolve_work_path(work, source_key)
        source_stored_hash = source_info["hash"]
        
        if verbose:
            print(f"Source file: {source_path}")
        
        # Validate file exists
        if not source_path.exists():
            raise FileNotFoundError(
                f"Source file not found on disk: {source_path}\n"
                f"Referenced in work {work_id}, key '{source_key}'"
            )
        
        # Compute current hash and validate
        source_current_hash = compute_file_hash(source_path)
        
        if source_current_hash != source_stored_hash and not force:
            raise HashMismatchError(
                stored_hash=source_stored_hash,
                current_hash=source_current_hash
            )
        
        if source_current_hash != source_stored_hash and verbose:
            print(f"Warning: Hash mismatch detected, proceeding with --force")
        
        # Determine output path
        if source_key == "original_markdown":
            # <file>.md -> <file>.sanitized.md
            output_path = source_path.parent / f"{source_path.stem}.sanitized.md"
        else:
            # If source is already sanitized, we're overwriting it
            output_path = source_path
        
        if verbose:
            print(f"Output file: {output_path}")
        
        # Check if output already exists and we're not forcing
        if output_path.exists() and "sanitized" in work.files and not force:
            raise ValueError(
                f"Sanitized file already exists: {output_path}\n"
                f"Use force=True to overwrite."
            )
        
        # Copy the file
        shutil.copy2(source_path, output_path)
        
        if verbose:
            print(f"Copied {source_path.name} to {output_path.name}")
        
        # Set file to read-only
        set_file_readonly(output_path)
        
        if verbose:
            print(f"File set to read-only")
        
        # Compute hash of sanitized file
        sanitized_hash = compute_file_hash(output_path)
        
        # Update work's files metadata
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files["sanitized"] = {
            "path": str(output_path.resolve()),
            "hash": sanitized_hash
        }
        work.files = updated_files
        
        session.commit()
        session.refresh(work)
        
        if verbose:
            print(f"Updated work {work_id} with 'sanitized' file metadata")
    
    return output_path

