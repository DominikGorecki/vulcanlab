"""Delete conversion module - Remove converted files and database entries."""

from pathlib import Path
from typing import List

from vulcanlab.data.database import get_session
from vulcanlab.data.models.io_file import IOFile
from vulcanlab.config import load_config


def delete_conversion(io_file_id: int, verbose: bool = False) -> dict:
    """
    Delete all files associated with a conversion and remove the io_file database entry.

    This function:
    1. Finds the io_file entry by ID
    2. Determines the base name from the filename
    3. Deletes ALL files in the output directory with that base name
    4. Deletes the io_file database entry

    Args:
        io_file_id: ID of the file in the io_files table
        verbose: If True, print detailed information

    Returns:
        Dictionary with:
            - success: bool
            - message: str
            - deleted_files: List[str] (filenames that were deleted)
            - io_file_deleted: bool

    Raises:
        ValueError: If io_file_id is not found
    """
    deleted_files: List[str] = []

    # Get the io_file from database
    with get_session() as session:
        io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()

        if not io_file:
            raise ValueError(f"IOFile with ID {io_file_id} not found in database")

        # Extract filename and derive base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise ValueError(f"Invalid filename format: {filename} (no extension found)")

        base_name = filename[:first_dot]

        if verbose:
            print(f"Base name: {base_name}")
            print(f"IO File ID: {io_file_id}")

    # Get output directory from config
    config = load_config()
    output_dir = Path(config.paths.output_dir)

    if not output_dir.exists():
        raise ValueError(f"Output directory does not exist: {output_dir}")

    # Find and delete all files with the same base name
    # Pattern: base_name.* (e.g., bookname.pdf, bookname.md, bookname.style.md, etc.)
    matching_files = list(output_dir.glob(f"{base_name}.*"))

    if verbose:
        print(f"Found {len(matching_files)} files to delete:")
        for file_path in matching_files:
            print(f"  - {file_path.name}")

    # Delete each file
    for file_path in matching_files:
        try:
            file_path.unlink()
            deleted_files.append(file_path.name)
            if verbose:
                print(f"Deleted: {file_path.name}")
        except Exception as e:
            if verbose:
                print(f"Warning: Could not delete {file_path.name}: {e}")

    # Delete the io_file database entry
    io_file_deleted = False
    with get_session() as session:
        io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
        if io_file:
            session.delete(io_file)
            session.commit()
            io_file_deleted = True
            if verbose:
                print(f"Deleted io_file entry with ID {io_file_id}")

    return {
        "success": True,
        "message": f"Successfully deleted {len(deleted_files)} files and database entry for {base_name}",
        "deleted_files": deleted_files,
        "io_file_deleted": io_file_deleted,
    }
