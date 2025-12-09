"""Apply title edits to markdown files.

This module provides functionality to apply title/heading edits to markdown files
based on line numbers. It's used to update markdown files after users edit titles
in the UI.

Usage:
    from vulcanlab.sanitization.apply_title_edits import apply_title_edits
    
    title_edits = '''
    10: # New Chapter Title
    15: ## Updated Section
    18: ***MISSING***
    25: -
    30: --
    '''
    
    apply_title_edits(Path("document.md"), title_edits)

Functions:
    apply_title_edits(markdown_file_path, title_edits) - Apply edits to a markdown file

Edit Formats:
    - `123: # New Title` - Replace entire line 123 with the new title
    - `123: ***MISSING***` - Skip (no change to line 123)
    - `123: -` - Remove heading markers from line 123 (keep text content)
    - `123: --` - Replace line 123 with a blank line
"""

import re
from pathlib import Path


def apply_title_edits(markdown_file_path: Path, title_edits: str) -> None:
    """Apply title edits to a markdown file based on line numbers.
    
    This function reads a markdown file, applies edits based on line numbers,
    and saves the modified content back to the file.
    
    Args:
        markdown_file_path: Path to the markdown file to edit
        title_edits: Multi-line string with format "line_num: title"
                    Each line should be in format: "123: # Title Text"
                    
    Special edit formats:
        - "123: ***MISSING***" - Skip this line (no change)
        - "123: -" - Remove heading markers (e.g., "## Title" becomes "Title")
        - "123: --" - Replace line with blank line
        
    Raises:
        FileNotFoundError: If the markdown file doesn't exist
        ValueError: If the markdown file is not a markdown file
    """
    if not markdown_file_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_file_path}")
    
    if markdown_file_path.suffix.lower() not in ('.md', '.markdown'):
        raise ValueError(f"File must be a markdown file: {markdown_file_path}")
    
    # Read the original markdown file
    content = markdown_file_path.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    
    # Parse title edits into a map: line_number -> new_title
    edits_map = _parse_title_edits(title_edits)
    
    # Apply edits to lines
    modified_lines = []
    for line_num, original_line in enumerate(lines, start=1):
        if line_num in edits_map:
            edit_value = edits_map[line_num]
            
            # Apply the appropriate edit
            if edit_value == "***MISSING***":
                # Skip - keep original line
                modified_lines.append(original_line)
            elif edit_value == "-":
                # Remove heading markers, keep text
                modified_line = _remove_heading_markers(original_line)
                modified_lines.append(modified_line)
            elif edit_value == "--":
                # Replace with blank line
                modified_lines.append("\n")
            else:
                # Replace entire line with new title
                # Preserve the line ending from original
                line_ending = "\n" if original_line.endswith("\n") else ""
                modified_lines.append(edit_value + line_ending)
        else:
            # No edit for this line, keep original
            modified_lines.append(original_line)
    
    # Write modified content back to file
    modified_content = "".join(modified_lines)
    markdown_file_path.write_text(modified_content, encoding='utf-8')


def _parse_title_edits(title_edits: str) -> dict[int, str]:
    """Parse title edits string into a dictionary.
    
    Args:
        title_edits: Multi-line string with format "line_num: title"
        
    Returns:
        Dictionary mapping line numbers to new titles
    """
    edits_map = {}
    lines = title_edits.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Match pattern: "123: some text"
        match = re.match(r'^(\d+):\s*(.*)$', line)
        if match:
            line_num = int(match.group(1))
            title = match.group(2)
            edits_map[line_num] = title
    
    return edits_map


def _remove_heading_markers(line: str) -> str:
    """Remove markdown heading markers from a line.
    
    Converts "## Some Title" to "Some Title"
    
    Args:
        line: The line to process
        
    Returns:
        Line with heading markers removed
    """
    # Match heading pattern: one or more # followed by space
    match = re.match(r'^(#{1,6})\s+(.*)$', line)
    if match:
        # Return just the title text, preserving original line ending
        title_text = match.group(2)
        line_ending = "\n" if line.endswith("\n") else ""
        return title_text + line_ending
    
    # Not a heading, return as-is
    return line



