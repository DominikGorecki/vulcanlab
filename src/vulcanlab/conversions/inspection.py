"""Conversion inspection utilities.

This module provides functionality to inspect conversion artifacts
and determine what inspection/generation options are available for a given file.

Usage:
    from vulcanlab.conversions.inspection import get_conversion_inspection
    
    inspection_items = get_conversion_inspection(io_file_id=42)
    for item in inspection_items:
        print(f"{item.name}: {'Available' if item.available else 'Not available'}")

Functions:
    get_conversion_inspection(io_file_id) - Get inspection options for a converted file
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from vulcanlab.config import load_config
from vulcanlab.data.database import get_session
from vulcanlab.data.models.io_file import IOFile


@dataclass
class InspectionItem:
    """Represents an inspection option for a converted file.
    
    Attributes:
        name: Machine-readable name (e.g., 'inspect_style_hier')
        available: Whether the required files exist
        files_checked: List of filenames that were checked for this inspection
    """
    name: str
    available: bool
    files_checked: list[str]


def get_conversion_inspection(io_file_id: int) -> list[InspectionItem]:
    """Get inspection options available for a converted file.
    
    This function checks the filesystem for various conversion artifacts
    (style.md, hier.md, toc_titles.md, etc.) and returns a list of
    inspection options that are available or could be generated.
    
    Args:
        io_file_id: The ID of the file in the io_files table
        
    Returns:
        List of InspectionItem objects in priority order:
        1. inspect_style_hier (requires both style.md and hier.md)
        2. inspect_toc_titles (requires toc_titles.md)
        3. inspect_titles (requires titles.md)
        4. inspect_title_changes (requires title_changes.md)
        5. inspect_original_md (requires .md)
        
    Raises:
        ValueError: If io_file_id doesn't exist in database
        ValueError: If the file is not a PDF or doesn't have a valid base name
    """
    # Get the file from database
    with get_session() as session:
        io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
        
        if not io_file:
            raise ValueError(f"File with ID {io_file_id} not found in database")
        
        # Detach from session
        session.expunge(io_file)
    
    # Extract base name (everything before first dot)
    filename = io_file.filename
    first_dot = filename.find('.')
    if first_dot == -1:
        raise ValueError(f"Invalid filename format: {filename} (no extension found)")
    
    base_name = filename[:first_dot]
    
    # Get output directory from config
    config = load_config()
    output_dir = Path(config.paths.output_dir)
    
    # Define inspection checks in priority order
    inspection_checks = [
        {
            'name': 'inspect_style_hier',
            'files': [f'{base_name}.style.md', f'{base_name}.hier.md'],
            'require_all': True
        },
        {
            'name': 'inspect_toc_titles',
            'files': [f'{base_name}.toc_titles.md'],
            'require_all': True
        },
        {
            'name': 'inspect_titles',
            'files': [f'{base_name}.titles.md'],
            'require_all': True
        },
        {
            'name': 'inspect_title_changes',
            'files': [f'{base_name}.title_changes.md'],
            'require_all': True
        },
        {
            'name': 'inspect_original_md',
            'files': [f'{base_name}.md'],
            'require_all': True
        }
    ]
    
    # Check each inspection option
    results = []
    for check in inspection_checks:
        files_to_check = check['files']
        require_all = check['require_all']
        
        # Check if files exist
        existing_files = []
        for file_name in files_to_check:
            file_path = output_dir / file_name
            if file_path.exists() and file_path.is_file():
                existing_files.append(file_name)
        
        # Determine availability
        if require_all:
            available = len(existing_files) == len(files_to_check)
        else:
            available = len(existing_files) > 0
        
        results.append(InspectionItem(
            name=check['name'],
            available=available,
            files_checked=files_to_check
        ))
    
    return results

