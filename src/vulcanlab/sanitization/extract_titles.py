"""Extract markdown titles from a document.

This module provides functionality to extract all titles (headings) from a markdown
file and save them to a separate file with line numbers for hierarchy analysis.

Usage:
    from vulcanlab.sanitization import extract_titles_to_file, extract_titles
    output_path = extract_titles_to_file("path/to/document.md")
    titles = extract_titles("path/to/document.md")

Examples:
    # Basic usage - creates document.titles.md
    from vulcanlab.sanitization import extract_titles_to_file
    result = extract_titles_to_file("book.md")

    # Get titles as list without writing to file
    from vulcanlab.sanitization import extract_titles
    titles = extract_titles("book.md")

    # Custom output path
    result = extract_titles_to_file("book.md", "output/titles.md")

Functions:
    extract_titles(input_path) - Extract titles and return as list
    extract_titles_to_file(input_path, output_path) - Extract titles to file
    extract_titles_from_work(work_id, source_key, force, verbose) - Extract from Work by ID

Exceptions:
    HashMismatchError - Raised when file hash doesn't match database
"""

import re
from pathlib import Path
from typing import Optional

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import compute_file_hash, set_file_writable, set_file_readonly


def _validate_input(input_path: Path) -> None:
    """Validate input file exists and is markdown.

    Args:
        input_path: Path to validate.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() not in ('.md', '.markdown'):
        raise ValueError(f"Input file must be a markdown file: {input_path}")


def _extract_titles_from_content(content: str) -> list[str]:
    """Extract titles from markdown content.

    Args:
        content: Markdown content as string.

    Returns:
        List of strings in format "line_num: heading_line".
    """
    lines = content.splitlines()
    title_pattern = re.compile(r'^#+\s+')
    titles = []

    for line_num, line in enumerate(lines, start=1):
        if title_pattern.match(line):
            titles.append(f"{line_num}: {line}")

    return titles


def extract_titles(input_path: str | Path) -> list[str]:
    """Extract all titles from a markdown file.

    Args:
        input_path: Path to the markdown file to analyze.

    Returns:
        List of strings in format "line_num: heading_line".

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    input_path = Path(input_path)
    _validate_input(input_path)

    content = input_path.read_text(encoding='utf-8')
    return _extract_titles_from_content(content)


def extract_titles_to_file(
    input_path: str | Path,
    output_path: str | Path | None = None
) -> Path:
    """Extract all titles from a markdown file and save to a titles file.

    Args:
        input_path: Path to the markdown file to analyze.
        output_path: Optional path for the output file. If not provided,
            will use the input filename with '.titles.md' suffix.

    Returns:
        Path to the created titles file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    input_path = Path(input_path)
    _validate_input(input_path)

    # Determine output path
    if output_path is None:
        # Default to output folder in current working directory
        output_dir = Path.cwd() / "output"
        output_path = output_dir / f"{input_path.stem}.titles.md"
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract titles
    content = input_path.read_text(encoding='utf-8')
    titles = _extract_titles_from_content(content)

    # Calculate relative path from output to input
    try:
        relative_uri = input_path.relative_to(output_path.parent)
        relative_uri_str = f"./{relative_uri.as_posix()}"
    except ValueError:
        # Files are on different drives or can't be made relative
        relative_uri_str = input_path.as_posix()

    # Build output content
    output_lines = [
        relative_uri_str,
        "",
        "# ALL TITLES IN DOC",
        "```",
        *titles,
        "```"
    ]

    output_content = "\n".join(output_lines)

    # Write output file
    output_path.write_text(output_content, encoding='utf-8')

    return output_path


class HashMismatchError(Exception):
    """Raised when file hash doesn't match the stored hash in the database.

    Attributes:
        stored_hash: The hash stored in the database.
        current_hash: The current hash of the file on disk.
    """
    def __init__(self, stored_hash: str, current_hash: str):
        self.stored_hash = stored_hash
        self.current_hash = current_hash
        super().__init__(
            f"File hash mismatch. Stored: {stored_hash}, Current: {current_hash}"
        )


def extract_titles_from_work(
    work_id: int,
    source_key: str,
    force: bool = False,
    verbose: bool = False
) -> Path:
    """Extract titles from a work's markdown file and update the database.

    Args:
        work_id: Database ID of the work.
        source_key: Key in the files JSON ("original_markdown" or "sanitized").
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.

    Returns:
        Path to the created titles file.

    Raises:
        ValueError: If work_id not found, source_key invalid, or file not in database.
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

        if source_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{source_key}' in files metadata"
            )

        # Get file info
        file_info = work.files[source_key]
        file_path = Path(file_info["path"])
        stored_hash = file_info["hash"]

        if verbose:
            print(f"Extracting titles from: {file_path}")

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found on disk: {file_path}\n"
                f"Referenced in work {work_id}, key '{source_key}'"
            )

        # Compute current hash and validate
        current_hash = compute_file_hash(file_path)

        if current_hash != stored_hash and not force:
            raise HashMismatchError(stored_hash, current_hash)

        if current_hash != stored_hash and verbose:
            print(f"Warning: Hash mismatch detected, proceeding with --force")

        # Extract titles
        content = file_path.read_text(encoding='utf-8')
        titles = _extract_titles_from_content(content)

        # Determine output path and key based on source
        if source_key == "original_markdown":
            # <file>.md -> <file>.titles.md
            output_path = file_path.parent / f"{file_path.stem}.titles.md"
            output_key = "titles"
        else:  # sanitized
            # <file>.sanitized.md -> <file>.sanitized.titles.md
            # Need to handle stem properly: test.sanitized.md -> stem is "test.sanitized"
            output_path = file_path.parent / f"{file_path.stem}.titles.md"
            output_key = "sanitized_titles"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate relative path from output to input
        try:
            relative_uri = file_path.relative_to(output_path.parent)
            relative_uri_str = f"./{relative_uri.as_posix()}"
        except ValueError:
            # Files are on different drives or can't be made relative
            relative_uri_str = file_path.as_posix()

        # Build output content
        output_lines = [
            relative_uri_str,
            "",
            "# ALL TITLES IN DOC",
            "```",
            *titles,
            "```"
        ]

        output_content = "\n".join(output_lines)

        # If file exists and is read-only, make it writable
        if output_path.exists():
            try:
                set_file_writable(output_path)
                if verbose:
                    print(f"Made existing file writable: {output_path}")
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not make file writable: {e}")

        # Write output file
        output_path.write_text(output_content, encoding='utf-8')

        if verbose:
            print(f"Titles saved to: {output_path}")

        # Set file to read-only
        set_file_readonly(output_path)

        # Compute hash of new titles file
        titles_hash = compute_file_hash(output_path)

        # Update work's files metadata
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files[output_key] = {
            "path": str(output_path.resolve()),
            "hash": titles_hash
        }
        work.files = updated_files

        session.commit()
        session.refresh(work)

        if verbose:
            print(f"Updated work {work_id} with '{output_key}' file metadata")

    return output_path
