"""
PDF Bookmarks to Table of Contents Extractor.

This module extracts PDF bookmarks and converts them to a hierarchical
markdown table of contents with H1, H2, H3, etc. based on bookmark depth.

Example (as library):
    from vulcanlab.conversions.pdf_bookmarks2toc import extract_bookmarks_to_toc

    # Extract bookmarks to markdown
    toc_content = extract_bookmarks_to_toc("input.pdf")

    # Save to file
    toc_content = extract_bookmarks_to_toc("input.pdf", output_path="toc.md")
"""

from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


def extract_bookmarks_to_toc(
    pdf_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False,
) -> str:
    """
    Extract PDF bookmarks and convert to hierarchical markdown TOC.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Optional path for the output markdown file.
                    If None, generates path as <pdf_stem>.toc_titles.md
        verbose: If True, print progress information.

    Returns:
        The table of contents as a markdown string.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the file is not a PDF file.
    """
    pdf_path = Path(pdf_path)

    # Validate input file
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File must be a PDF file, got: {pdf_path.suffix}")

    if verbose:
        print(f"Extracting bookmarks from: {pdf_path}")

    # Open PDF and extract bookmarks
    doc = fitz.open(str(pdf_path))
    toc = doc.get_toc()  # Returns list of [level, title, page]
    doc.close()

    if not toc:
        if verbose:
            print("No bookmarks found in PDF")
        return ""

    if verbose:
        print(f"Found {len(toc)} bookmarks")

    # Convert bookmarks to markdown headings
    lines = []
    for level, title, _ in toc:
        # Level 1 = H1, Level 2 = H2, etc.
        # Cap at H6 (maximum markdown heading level)
        heading_level = min(level, 6)
        prefix = "#" * heading_level
        lines.append(f"{prefix} {title}")

    toc_content = "\n\n".join(lines)

    # Determine output path
    if output_path is None:
        # Default to output folder in current working directory
        output_dir = Path.cwd() / "output"
        output_path = output_dir / f"{pdf_path.stem}.toc_titles.md"
    else:
        output_path = Path(output_path)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(toc_content, encoding="utf-8")

    if verbose:
        print(f"TOC written to: {output_path}")

    return toc_content
