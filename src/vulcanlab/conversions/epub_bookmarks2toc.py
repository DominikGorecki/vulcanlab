"""
EPUB Table of Contents Extractor.

This module extracts the table of contents from EPUB files and converts it
to a hierarchical markdown list of headings.

Example (as library):
    from vulcanlab.conversions.epub_bookmarks2toc import extract_epub_toc

    # Extract TOC to markdown
    toc_content = extract_epub_toc("input.epub")

    # Save to file
    toc_content = extract_epub_toc("input.epub", output_path="toc.md")
"""

from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def _extract_hierarchy(book) -> list[dict]:
    """
    Extract hierarchical navigation structure from EPUB.

    Handles both EPUB 3 (HTML5 nav) and EPUB 2 (NCX) formats.
    Recursively processes nested sections to preserve heading levels.

    Args:
        book: The ebooklib epub object.

    Returns:
        List of dictionaries with structure:
        [
            {
                'level': int,           # 1-6 for h1-h6
                'title': str,           # Section title
            },
            ...
        ]
    """
    hierarchy = []

    # Try EPUB 3 navigation first (modern format)
    for item in book.get_items_of_type(ebooklib.ITEM_NAVIGATION):
        content = item.get_content().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")

        # Look for EPUB 3 navigation structure
        nav = soup.find("nav")
        if nav:
            ol = nav.find("ol")
            if ol:
                def parse_nested_ol(ol_elem, level=1):
                    """Recursively parse nested ordered lists."""
                    for li in ol_elem.find_all("li", recursive=False):
                        a = li.find("a", recursive=False)
                        if a:
                            title = a.get_text(strip=True)
                            
                            if title:
                                hierarchy.append({
                                    "level": min(level, 6),  # Cap at h6
                                    "title": title,
                                })

                        # Recurse into nested <ol>
                        nested_ol = li.find("ol", recursive=False)
                        if nested_ol:
                            parse_nested_ol(nested_ol, level + 1)

                parse_nested_ol(ol)
                return hierarchy  # Found EPUB 3 nav, return it

    # Fallback to EPUB 2 NCX format (legacy)
    for item in book.get_items_of_type(ebooklib.ITEM_NAVIGATION):
        content = item.get_content().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(content, "xml")

        def parse_nav_point(nav_point, level=1):
            """Recursively parse navPoint elements."""
            label = nav_point.find("navLabel", recursive=False)
            
            if label:
                title = label.get_text(strip=True)
                
                if title:
                    hierarchy.append({
                        "level": min(level, 6),  # Cap at h6
                        "title": title,
                    })

            # Recurse into nested navPoints
            for child_nav_point in nav_point.find_all("navPoint", recursive=False):
                parse_nav_point(child_nav_point, level + 1)

        # Find all top-level navPoints
        for nav_point in soup.find_all("navPoint", recursive=False):
            parse_nav_point(nav_point)

        if hierarchy:
            return hierarchy  # Found NCX navigation

    return hierarchy  # Return empty list if no navigation found


def extract_epub_toc(
    epub_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False,
) -> str:
    """
    Extract EPUB table of contents and convert to hierarchical markdown.

    Args:
        epub_path: Path to the input EPUB file.
        output_path: Optional path for the output markdown file.
                    If None, generates path as <epub_stem>.toc_titles.md
        verbose: If True, print progress information.

    Returns:
        The table of contents as a markdown string.

    Raises:
        FileNotFoundError: If the EPUB file does not exist.
        ValueError: If the file is not an EPUB file.
    """
    epub_path = Path(epub_path)

    # Validate input file
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    if epub_path.suffix.lower() != ".epub":
        raise ValueError(f"File must be an EPUB file, got: {epub_path.suffix}")

    if verbose:
        print(f"Extracting TOC from: {epub_path}")

    # Open EPUB
    try:
        book = epub.read_epub(str(epub_path))
    except Exception as e:
        if verbose:
            print(f"Error reading EPUB: {e}")
        return ""

    # Extract hierarchy
    hierarchy = _extract_hierarchy(book)

    if not hierarchy:
        if verbose:
            print("No navigation structure found in EPUB. Creating empty TOC file.")
        toc_content = "<!-- No navigation structure found in EPUB. Add headings here manually. -->"
    else:
        if verbose:
            print(f"Found {len(hierarchy)} navigation entries")

        # Convert hierarchy to markdown headings
        lines = []
        for entry in hierarchy:
            level = entry["level"]
            title = entry["title"]
            prefix = "#" * level
            lines.append(f"{prefix} {title}")

        toc_content = "\n\n".join(lines)

    # Determine output path
    if output_path is None:
        # Default to output folder in current working directory
        output_dir = Path.cwd() / "output"
        output_path = output_dir / f"{epub_path.stem}.toc_titles.md"
    else:
        output_path = Path(output_path)

    # Write output
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(toc_content, encoding="utf-8")
        if verbose:
            print(f"TOC written to: {output_path}")
    except Exception as e:
        if verbose:
            print(f"Error writing TOC file: {e}")

    return toc_content

