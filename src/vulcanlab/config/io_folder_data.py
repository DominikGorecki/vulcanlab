"""IO folder data management.

This module scans input and output directories, syncs with the io_files database table,
and provides file tracking without repeated hash computations.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from vulcanlab.config import load_config


# Supported input formats (expandable list)
INPUT_FORMATS = [".pdf", ".epub"]

# Supported output formats
OUTPUT_FORMATS = [".md", ".pdf", ".epub", ".csv"]


@dataclass
class ProcessedFile:
    """Represents a processed file with its variants."""

    base_name: str  # Filename without extension
    io_file_id: Optional[int]  # ID from io_files table (if has PDF variant)
    variants: list[str]  # List of file extensions found (e.g., ['.pdf', '.md', '.style.md'])


@dataclass
class IOFolderData:
    """Container for input/output folder scan results."""

    input_files: list[str]  # Unprocessed input filenames
    processed_files: list[ProcessedFile]  # Processed files with their variants


@dataclass
class IOFileObject:
    """Object representation of an IO file for API usage."""

    id: int
    filename: str
    file_type: str
    file_path: str
    base_name: Optional[str] = None  # For to_convert files, the base name without extension
    variants: Optional[list[str]] = None  # For to_convert files, list of variants


def sync_files_with_database() -> None:
    """Sync filesystem files with io_files database table.

    This function:
    1. Scans input and output directories
    2. Adds new files to the database
    3. Updates last_seen_at for existing files
    4. Removes files from database that no longer exist
    """
    from vulcanlab.data.database import get_session
    from vulcanlab.data.models.io_file import IOFile, FileType

    config = load_config()
    input_dir = Path(config.paths.input_dir)
    output_dir = Path(config.paths.output_dir)

    # Collect all files from filesystem
    filesystem_files = {}  # file_path -> (filename, file_type)

    # Scan input directory
    if input_dir.exists():
        for format_ext in INPUT_FORMATS:
            for file_path in input_dir.glob(f"*{format_ext}"):
                if file_path.is_file():
                    abs_path = str(file_path.absolute())
                    filesystem_files[abs_path] = (file_path.name, FileType.INPUT)

    # Scan output directory
    if output_dir.exists():
        for format_ext in OUTPUT_FORMATS:
            for file_path in output_dir.glob(f"*{format_ext}"):
                if file_path.is_file():
                    abs_path = str(file_path.absolute())
                    filesystem_files[abs_path] = (file_path.name, FileType.TO_CONVERT)

    # Sync with database
    with get_session() as session:
        now = datetime.now(timezone.utc)

        # Get all existing files from database
        db_files = session.query(IOFile).all()
        db_file_paths = {f.file_path: f for f in db_files}

        # Add new files and update existing ones
        for file_path, (filename, file_type) in filesystem_files.items():
            if file_path in db_file_paths:
                # Update last_seen_at for existing file
                db_file = db_file_paths[file_path]
                db_file.last_seen_at = now
            else:
                # Add new file
                new_file = IOFile(
                    filename=filename,
                    file_type=file_type,
                    file_path=file_path,
                    last_seen_at=now
                )
                session.add(new_file)

        # Remove files that no longer exist
        for file_path, db_file in db_file_paths.items():
            if file_path not in filesystem_files:
                session.delete(db_file)

        session.commit()


def get_io_files_by_type(file_type):
    """Get all IO files of a specific type from database.

    Args:
        file_type: Type of files to retrieve

    Returns:
        List of IOFile objects
    """
    from vulcanlab.data.database import get_session
    from vulcanlab.data.models.io_file import IOFile

    with get_session() as session:
        files = session.query(IOFile).filter(IOFile.file_type == file_type).all()
        # Detach from session
        session.expunge_all()
        return files


def get_processed_files_from_works() -> set[str]:
    """Query works table to get filenames of processed files.

    Returns:
        Set of filenames (without path) that have been processed
    """
    from vulcanlab.data.database import get_session
    from vulcanlab.data.models.work import Work

    processed_files = set()

    with get_session() as session:
        works = session.query(Work).all()

        for work in works:
            if work.files and isinstance(work.files, dict):
                # Check for original_file in the files JSON
                original_file = work.files.get('original_file')
                if original_file and isinstance(original_file, dict):
                    file_path = original_file.get('path')
                    if file_path:
                        # Extract just the filename from the absolute path
                        filename = Path(file_path).name
                        processed_files.add(filename)

    return processed_files


def get_io_folder_data() -> IOFolderData:
    """Get comprehensive IO folder data for CLI display.

    Syncs with database and returns filtered lists.

    Returns:
        IOFolderData object with input files and processed files
    """
    from vulcanlab.data.models.io_file import FileType

    # Sync filesystem with database
    sync_files_with_database()

    # Get all input files from database
    input_io_files = get_io_files_by_type(FileType.INPUT)

    # Get all to_convert files from database
    to_convert_io_files = get_io_files_by_type(FileType.TO_CONVERT)

    # Get processed files from works table
    processed_filenames = get_processed_files_from_works()

    # Filter input files (remove already processed)
    input_files = [
        f.filename for f in input_io_files
        if f.filename not in processed_filenames
    ]

    # Group to_convert files by base name
    file_groups: dict[str, tuple[Optional[int], list[str]]] = {}
    for io_file in to_convert_io_files:
        # Extract base name (everything before first dot)
        first_dot = io_file.filename.find('.')
        if first_dot != -1:
            base_name = io_file.filename[:first_dot]
            variant = io_file.filename[first_dot:]  # Include all extensions

            if base_name not in file_groups:
                file_groups[base_name] = (None, [])

            io_file_id, variants = file_groups[base_name]

            # Store the ID of the PDF variant (if this is one)
            if variant == '.pdf' or variant == '.epub':
                io_file_id = io_file.id

            # Add variant
            if variant not in variants:
                variants.append(variant)

            file_groups[base_name] = (io_file_id, variants)

    # Filter out already processed file groups
    filtered_groups = {
        base: (io_id, variants)
        for base, (io_id, variants) in file_groups.items()
        if not any(f"{base}{variant}" in processed_filenames for variant in variants)
        and not any("sanitized" in variant for variant in variants)
    }

    # Convert to ProcessedFile objects
    processed_files = [
        ProcessedFile(
            base_name=base,
            io_file_id=io_file_id,
            variants=sorted(variants)
        )
        for base, (io_file_id, variants) in sorted(filtered_groups.items())
    ]

    return IOFolderData(
        input_files=sorted(input_files),
        processed_files=processed_files
    )


def get_io_folder_objects() -> list[IOFileObject]:
    """Get IO folder data as objects for API usage.

    Syncs with database and returns all files (unfiltered) as objects.

    Returns:
        List of IOFileObject instances
    """
    from vulcanlab.data.models.io_file import FileType

    # Sync filesystem with database
    sync_files_with_database()

    # Get all input files
    input_files = get_io_files_by_type(FileType.INPUT)

    # Get all to_convert files
    to_convert_files = get_io_files_by_type(FileType.TO_CONVERT)

    result = []

    # Add input files
    for io_file in input_files:
        result.append(IOFileObject(
            id=io_file.id,
            filename=io_file.filename,
            file_type=io_file.file_type.value,
            file_path=io_file.file_path
        ))

    # Group to_convert files by base name
    file_groups: dict[str, tuple[int, list[str]]] = {}
    for io_file in to_convert_files:
        # Extract base name
        first_dot = io_file.filename.find('.')
        if first_dot != -1:
            base_name = io_file.filename[:first_dot]
            variant = io_file.filename[first_dot:]

            if base_name not in file_groups:
                file_groups[base_name] = (io_file.id, [])

            io_file_id, variants = file_groups[base_name]

            # Use PDF's ID if this is a PDF
            if variant == '.pdf' or variant == '.epub':
                io_file_id = io_file.id

            if variant not in variants:
                variants.append(variant)

            file_groups[base_name] = (io_file_id, variants)

    # Add to_convert file groups
    for base_name, (io_file_id, variants) in file_groups.items():
        # Find the file path (use PDF/EPUB if exists, otherwise first variant)
        file_path = None
        for io_file in to_convert_files:
            if io_file.filename == f"{base_name}.pdf" or io_file.filename == f"{base_name}.epub":
                file_path = io_file.file_path
                break

        if not file_path:
            # Use first variant's path
            for io_file in to_convert_files:
                if io_file.filename.startswith(f"{base_name}."):
                    file_path = io_file.file_path
                    break

        result.append(IOFileObject(
            id=io_file_id,
            filename=f"{base_name}.pdf" if '.pdf' in variants else (
                f"{base_name}.epub" if '.epub' in variants else f"{base_name}{variants[0]}"
            ),
            file_type=FileType.TO_CONVERT.value,
            file_path=file_path or "",
            base_name=base_name,
            variants=sorted(variants)
        ))

    return result
