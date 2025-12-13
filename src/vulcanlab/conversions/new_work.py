"""
Module for creating new work entries in the database.

This module provides functionality to insert bibliographic metadata
for psychology literature into the works table.

Example:
    from vulcanlab.sanitization.new_work import create_new_work
    from pathlib import Path

    work = create_new_work(
        title="Cognitive Psychology",
        markdown_path=Path("output/cognitive.md"),
        authors="John Smith",
        year=2025,
        publisher="Academic Press",
        isbn="978-0123456789",
        edition="3rd Edition"
    )
    print(f"Created work with ID: {work.id}")
"""

from pathlib import Path
from typing import Optional

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import compute_file_hash
from vulcanlab.sanitization.toc_titles2toc import parse_toc_titles


class DuplicateWorkError(Exception):
    """Raised when a work with the same content hash already exists."""
    pass


def create_new_work(
    title: str,
    markdown_path: Path,
    authors: Optional[str] = None,
    year: Optional[int] = None,
    publisher: Optional[str] = None,
    isbn: Optional[str] = None,
    edition: Optional[str] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    pages: Optional[str] = None,
    url: Optional[str] = None,
    city: Optional[str] = None,
    institution: Optional[str] = None,
    editor: Optional[str] = None,
    check_duplicates: bool = True,
    verbose: bool = False
) -> Work:
    """
    Create a new work entry in the database.

    Args:
        title: Title of the work (required).
        markdown_path: Path to the markdown file (required).
        authors: Author(s) of the work (optional).
        year: Year of publication (optional).
        publisher: Publisher name (optional).
        isbn: ISBN for books (optional).
        edition: Edition information (optional).
        volume: Volume number for journals/periodicals (optional).
        issue: Issue number for journals/periodicals (optional).
        pages: Page range (optional).
        url: URL for the work (optional).
        city: City of publication (optional).
        institution: Institution for theses/dissertations (optional).
        editor: Editor(s) of the work (optional).
        check_duplicates: If True, check for duplicate content_hash (default: True).
        verbose: If True, print warning messages for TOC issues (default: False).

    Returns:
        The created Work object with ID populated.

    Raises:
        FileNotFoundError: If the markdown file does not exist.
        DuplicateWorkError: If a work with the same content hash already exists.
        ValueError: If validation fails.
    """
    # Convert to absolute path
    markdown_path = markdown_path.resolve()

    # Validate markdown file exists
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    if not markdown_path.is_file():
        raise ValueError(f"Path is not a file: {markdown_path}")

    # Validate year if provided
    if year is not None:
        if not isinstance(year, int):
            raise ValueError(f"Year must be an integer, got: {type(year).__name__}")
        if year < 1000 or year > 9999:
            raise ValueError(f"Year must be a 4-digit year, got: {year}")

    # Compute content hash
    content_hash = compute_file_hash(markdown_path)

    # Discover and track all related files with their hashes
    files_metadata = {}
    stem = markdown_path.stem

    # Define file discovery rules
    file_specs = [
        ("original_file", [".pdf", ".epub", ".html"]),  # Check in order, use first found
        ("hier_markdown", [".hier.md"]),
        ("style_markdown", [".style.md"]),
        ("original_markdown", [".md"]),
        ("toc_titles", [".toc_titles.md"]),
        ("titles", [".titles.md"]),
        ("san_mapping", [".san_mapping.csv"]),
        ("sanitized", [".sanitized.md"]),
        ("sanitized_titles", [".sanitized.titles.md"]),
        ("vec_suggestions", [".sanitized.vec_sugg.md"]),
    ]

    # Discover files
    for field_name, extensions in file_specs:
        for ext in extensions:
            file_path = markdown_path.parent / f"{stem}{ext}"
            if file_path.exists() and file_path.is_file():
                # Compute hash using full path, but store only filename
                file_hash = compute_file_hash(file_path)
                files_metadata[field_name] = {
                    "path": file_path.name,
                    "hash": file_hash
                }
                break  # Use first match for this field

    # Check for TOC file and parse if present
    toc_path = markdown_path.parent / f"{markdown_path.stem}.toc_titles.md"
    toc_data = None

    if toc_path.exists():
        try:
            toc_result = parse_toc_titles(toc_path)
            # Convert to list of dicts for JSON storage
            toc_data = [{"level": entry.level, "title": entry.title} for entry in toc_result.entries]
        except Exception as e:
            if verbose:
                print(f"Warning: Could not parse TOC file {toc_path}: {e}")
    else:
        if verbose:
            print(f"Warning: TOC file not found: {toc_path}")

    # Check for duplicates if requested
    if check_duplicates:
        with get_session() as session:
            existing_work = session.query(Work).filter(
                Work.content_hash == content_hash
            ).first()

            if existing_work:
                raise DuplicateWorkError(
                    f"A work with the same content already exists (ID: {existing_work.id}, "
                    f"Title: '{existing_work.title}')"
                )

    # Create the work
    work = Work(
        title=title,
        markdown_path=markdown_path.name,
        authors=authors,
        year=year,
        publisher=publisher,
        isbn=isbn,
        edition=edition,
        volume=volume,
        issue=issue,
        pages=pages,
        url=url,
        city=city,
        institution=institution,
        editor=editor,
        content_hash=content_hash,
        toc=toc_data,
        files=files_metadata if files_metadata else None
    )

    # Insert into database
    with get_session() as session:
        session.add(work)
        session.commit()
        session.refresh(work)  # Refresh to get the generated ID

    return work
