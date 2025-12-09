"""Update content hash after validating file integrity.

This module checks if the content hash matches and validates that:
1. Line numbers in vectorize_suggestions.md match headings in sanitized.md
2. All VECTORIZE entries have corresponding chunks in the database

Usage:
    from vulcanlab.sanitization.update_content_hash import update_content_hash
    result = update_content_hash(work_id=1, verbose=True)

Examples:
    # Validate and update hash for work ID 1
    from vulcanlab.sanitization.update_content_hash import update_content_hash
    success = update_content_hash(1)
    print(f"Update successful: {success}")
"""

import re
from pathlib import Path

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Chunk, Work
from vulcanlab.utils import compute_file_hash, set_file_readonly


def _parse_headings_from_file(file_path: Path) -> dict[int, str]:
    """Parse headings from a markdown file.

    Args:
        file_path: Path to the markdown file.

    Returns:
        Dictionary mapping line numbers to heading text.
    """
    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    headings = {}

    for i, line in enumerate(lines, start=1):
        match = re.match(r'^(#+)\s+(.*)$', line)
        if match:
            headings[i] = line

    return headings


def _parse_vectorize_suggestions(file_path: Path) -> dict[int, str]:
    """Parse vectorization suggestions file.

    Args:
        file_path: Path to the .vectorize_suggestions.md file.

    Returns:
        Dictionary mapping line numbers to SKIP/VECTORIZE decisions.
    """
    content = file_path.read_text(encoding='utf-8')
    decisions = {}

    # Extract from code block
    match = re.search(r'```\n(.*?)```', content, re.DOTALL)
    if not match:
        return decisions

    for line in match.group(1).strip().split('\n'):
        m = re.match(r'(\d+):\s*(SKIP|VECTORIZE)', line.strip(), re.IGNORECASE)
        if m:
            decisions[int(m.group(1))] = m.group(2).upper()

    return decisions


def verify_title_changes_integrity(work_id: int, source_key: str = "original_markdown", verbose: bool = False) -> dict:
    """Verify integrity of title changes file and update its hash if valid.
    
    This function validates that:
    1. The titles file hash is correct (must be already verified)
    2. Every line number in title_changes.md exists in titles.md
    3. Every line number in titles.md has a corresponding heading in the markdown file
    4. If all validations pass, updates the title_changes hash
    
    Args:
        work_id: ID of the work in the database.
        source_key: Source file key ("original_markdown" or "sanitized").
        verbose: Whether to print progress information.
    
    Returns:
        Dict with keys:
            - success: bool - Whether validation passed
            - message: str - Success or error message
            - errors: list[str] - List of validation errors if any
    
    Raises:
        ValueError: If work not found or required files missing.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")
        
        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")
        
        # Validate source_key
        if source_key not in ["original_markdown", "sanitized"]:
            raise ValueError(
                f"Invalid source_key: {source_key}. Must be 'original_markdown' or 'sanitized'"
            )
        
        # Determine file keys based on source
        if source_key == "original_markdown":
            titles_key = "titles"
            title_changes_key = "title_changes"
        else:
            titles_key = "sanitized_titles"
            title_changes_key = "sanitized_title_changes"
        
        # Validate all required files exist in metadata
        if source_key not in work.files:
            raise ValueError(f"Work {work_id} does not have '{source_key}' in files metadata")
        
        if titles_key not in work.files:
            raise ValueError(f"Work {work_id} does not have '{titles_key}' in files metadata")
        
        if title_changes_key not in work.files:
            raise ValueError(f"Work {work_id} does not have '{title_changes_key}' in files metadata")
        
        # Get file paths
        markdown_info = work.files[source_key]
        markdown_path = Path(markdown_info["path"])
        
        titles_info = work.files[titles_key]
        titles_path = Path(titles_info["path"])
        titles_stored_hash = titles_info["hash"]
        
        title_changes_info = work.files[title_changes_key]
        title_changes_path = Path(title_changes_info["path"])
        
        if verbose:
            print(f"Markdown: {markdown_path}")
            print(f"Titles: {titles_path}")
            print(f"Title Changes: {title_changes_path}")
        
        # Validate files exist on disk
        if not markdown_path.exists():
            raise ValueError(f"Markdown file not found: {markdown_path}")
        
        if not titles_path.exists():
            raise ValueError(f"Titles file not found: {titles_path}")
        
        if not title_changes_path.exists():
            raise ValueError(f"Title changes file not found: {title_changes_path}")
        
        validation_errors = []
        
        # Step 1: Verify titles file hash is correct
        titles_current_hash = compute_file_hash(titles_path)
        if titles_current_hash != titles_stored_hash:
            return {
                "success": False,
                "message": "Titles file hash mismatch. Please regenerate titles first.",
                "errors": [
                    f"Titles file hash mismatch: stored={titles_stored_hash[:16]}..., current={titles_current_hash[:16]}..."
                ]
            }
        
        if verbose:
            print("Titles file hash is valid")
        
        # Step 2: Parse headings from markdown file
        markdown_headings = _parse_headings_from_file(markdown_path)
        if verbose:
            print(f"Found {len(markdown_headings)} headings in markdown file")
        
        # Step 3: Parse line numbers from titles file
        titles_content = titles_path.read_text(encoding='utf-8')
        titles_line_numbers = set()
        
        # Extract from code block
        match = re.search(r'```\n(.*?)```', titles_content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split('\n'):
                m = re.match(r'^(\d+):\s*', line)
                if m:
                    titles_line_numbers.add(int(m.group(1)))
        
        if verbose:
            print(f"Found {len(titles_line_numbers)} line numbers in titles file")
        
        # Step 4: Validate every line in titles.md has a heading in markdown
        for line_num in titles_line_numbers:
            if line_num not in markdown_headings:
                validation_errors.append(
                    f"Line {line_num} in titles file has no heading in markdown file"
                )
        
        if validation_errors:
            return {
                "success": False,
                "message": "Validation failed: Line numbers in titles file don't match markdown headings",
                "errors": validation_errors
            }
        
        if verbose:
            print("Titles vs markdown validation passed")
        
        # Step 5: Parse line numbers from title_changes file
        title_changes_content = title_changes_path.read_text(encoding='utf-8')
        title_changes_line_numbers = set()
        
        # Extract from code block
        match = re.search(r'```\n(.*?)```', title_changes_content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split('\n'):
                m = re.match(r'^(\d+)\s*:\s*', line)
                if m:
                    title_changes_line_numbers.add(int(m.group(1)))
        
        if verbose:
            print(f"Found {len(title_changes_line_numbers)} line numbers in title_changes file")
        
        # Step 6: Validate every line in title_changes.md exists in titles.md
        for line_num in title_changes_line_numbers:
            if line_num not in titles_line_numbers:
                validation_errors.append(
                    f"Line {line_num} in title_changes file does not exist in titles file"
                )
        
        if validation_errors:
            return {
                "success": False,
                "message": "Validation failed: Line numbers in title_changes don't match titles file",
                "errors": validation_errors
            }
        
        if verbose:
            print("Title_changes vs titles validation passed")
        
        # Step 7: All validations passed - update title_changes hash
        new_hash = compute_file_hash(title_changes_path)
        
        # Update work.files with new hash
        updated_files = dict(work.files) if work.files else {}
        updated_files[title_changes_key] = {
            "path": str(title_changes_path.resolve()),
            "hash": new_hash
        }
        work.files = updated_files
        
        session.commit()
        session.refresh(work)
        
        if verbose:
            print(f"Updated {title_changes_key} hash to: {new_hash}")
        
        return {
            "success": True,
            "message": f"Validation passed. Title changes hash updated successfully.",
            "errors": []
        }


def update_content_hash(work_id: int, verbose: bool = False) -> bool:
    """Validate files and update content hash for a work.

    This function:
    1. Checks if the current content hash matches the file
    2. If not, validates that line numbers are consistent between files
    3. Validates that VECTORIZE entries have corresponding DB chunks
    4. If all validations pass, updates the hash and sets files as read-only

    Args:
        work_id: ID of the work in the database.
        verbose: Whether to print progress information.

    Returns:
        True if validation passed and hash was updated, False otherwise.

    Raises:
        ValueError: If work not found or required files missing.
    """
    with get_session() as session:
        # Step 1: Get work and validate it exists
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")

        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)
        if not markdown_path.exists():
            raise ValueError(f"Markdown file not found: {markdown_path}")

        if verbose:
            print(f"Processing work {work_id}: {work.title}")
            print(f"Markdown: {markdown_path}")

        # Step 2: Check if hash matches
        current_hash = compute_file_hash(markdown_path)
        stored_hash = work.content_hash

        if current_hash == stored_hash:
            if verbose:
                print("Content hash matches - no update needed")
            return True

        if verbose:
            print(f"Hash mismatch detected:")
            print(f"  Stored:  {stored_hash}")
            print(f"  Current: {current_hash}")
            print("Running validations...")

        # Step 3: Get file paths
        suggestions_path = markdown_path.with_suffix('.vectorize_suggestions.md')
        if not suggestions_path.exists():
            raise ValueError(f"Suggestions file not found: {suggestions_path}")

        if verbose:
            print(f"Suggestions: {suggestions_path}")

        # Step 4: Parse headings from sanitized file
        sanitized_headings = _parse_headings_from_file(markdown_path)
        if verbose:
            print(f"Found {len(sanitized_headings)} headings in sanitized file")

        # Step 5: Parse vectorize suggestions
        suggestions = _parse_vectorize_suggestions(suggestions_path)
        if verbose:
            print(f"Found {len(suggestions)} suggestions")

        # Step 6: Validate - every line in suggestions has a heading in sanitized
        validation_errors = []

        for line_num in suggestions.keys():
            if line_num not in sanitized_headings:
                validation_errors.append(
                    f"Line {line_num} in suggestions has no heading in sanitized file"
                )

        if validation_errors:
            if verbose:
                print("Validation FAILED - line number mismatches:")
                for error in validation_errors:
                    print(f"  - {error}")
            return False

        if verbose:
            print("Line number validation passed")

        # Step 7: Get VECTORIZE entries and check for DB chunks
        vectorize_lines = [
            line_num for line_num, decision in suggestions.items()
            if decision == 'VECTORIZE'
        ]

        if verbose:
            print(f"Found {len(vectorize_lines)} VECTORIZE entries")

        # Get all heading chunks for this work
        heading_chunks = session.query(Chunk).filter(
            Chunk.work_id == work_id,
            Chunk.level.in_(['H1', 'H2', 'H3', 'H4', 'H5'])
        ).all()

        chunk_start_lines = {chunk.start_line for chunk in heading_chunks}

        if verbose:
            print(f"Found {len(heading_chunks)} heading chunks in database")

        # Step 8: Validate - every VECTORIZE line has a chunk in DB
        missing_chunks = []
        for line_num in vectorize_lines:
            if line_num not in chunk_start_lines:
                missing_chunks.append(line_num)

        if missing_chunks:
            if verbose:
                print("Validation FAILED - missing chunks for VECTORIZE entries:")
                for line_num in missing_chunks:
                    print(f"  - Line {line_num}: no chunk with start_line={line_num}")
            return False

        if verbose:
            print("Chunk validation passed")

        # Step 9: All validations passed - update hash
        work.content_hash = current_hash
        session.commit()

        if verbose:
            print(f"Updated content_hash to: {current_hash}")

        # Step 10: Set files as read-only
        set_file_readonly(markdown_path)
        set_file_readonly(suggestions_path)

        if verbose:
            print(f"Set read-only: {markdown_path}")
            print(f"Set read-only: {suggestions_path}")

        print(f"Content hash updated successfully for work {work_id}")
        return True
