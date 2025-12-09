"""
EPUB to Markdown Converter using Docling and ebooklib.

This module provides functionality to convert EPUB files to Markdown format.
It extracts HTML content from EPUB files using ebooklib and then converts
the HTML to Markdown using Docling.

Example (as script):
    venv\\Scripts\\python conv_epub2md.py input.epub -o output.md

Example (as library):
    from conv_epub2md import convert_epub_to_markdown
    markdown_content = convert_epub_to_markdown("input.epub")
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from vulcanlab.conversions.epub_bookmarks2toc import extract_epub_toc


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
                'document': str,        # Document filename
                'fragment': str or None # Anchor ID if present
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
                        if a and a.get("href"):
                            href = a["href"]
                            title = a.get_text(strip=True)

                            # Parse href into document and fragment
                            if "#" in href:
                                document, fragment = href.split("#", 1)
                            else:
                                document, fragment = href, None

                            # Extract filename from path if needed
                            if "/" in document:
                                document = document.split("/")[-1]

                            hierarchy.append({
                                "level": min(level, 6),  # Cap at h6
                                "title": title,
                                "document": document,
                                "fragment": fragment,
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
            content_elem = nav_point.find("content", recursive=False)

            if label and content_elem:
                title = label.get_text(strip=True)
                src = content_elem.get("src", "")

                # Parse src into document and fragment
                if "#" in src:
                    document, fragment = src.split("#", 1)
                else:
                    document, fragment = src, None

                # Extract filename from path if needed
                if "/" in document:
                    document = document.split("/")[-1]

                if document and title:
                    hierarchy.append({
                        "level": min(level, 6),  # Cap at h6
                        "title": title,
                        "document": document,
                        "fragment": fragment,
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


def _extract_epub_to_html(epub_path: Path) -> str:
    """
    Extract all text content from an EPUB file as a single well-formed HTML.

    Preserves hierarchical heading structure from navigation when available.

    Args:
        epub_path: Path to the EPUB file.

    Returns:
        Combined HTML content from all document items as a single HTML document.
    """
    book = epub.read_epub(str(epub_path))

    # Get hierarchical navigation structure
    hierarchy = _extract_hierarchy(book)

    # Build a mapping from documents to their heading entries
    # Structure: {document: [(fragment, level, title), ...]}
    doc_headings = {}
    for entry in hierarchy:
        doc = entry["document"]
        if doc not in doc_headings:
            doc_headings[doc] = []
        doc_headings[doc].append((entry["fragment"], entry["level"], entry["title"]))

    # Collect body content from all document items
    body_parts = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")

        # Get the filename for this item
        item_name = item.get_name()
        filename = item_name.split("/")[-1] if "/" in item_name else item_name

        # Inject headings from navigation hierarchy
        if filename in doc_headings:
            body = soup.find("body")
            if body:
                for fragment, level, title in doc_headings[filename]:
                    # Create heading tag with appropriate level (h1-h6)
                    heading_tag = soup.new_tag(f"h{level}")
                    heading_tag.string = title

                    if fragment:
                        # Find element with matching ID and insert heading before it
                        target = body.find(id=fragment)
                        if target:
                            target.insert_before(heading_tag)
                        else:
                            # Fragment not found, insert at beginning
                            body.insert(0, heading_tag)
                    else:
                        # No fragment specified, insert at beginning of body
                        body.insert(0, heading_tag)

        # If no TOC headings were found, preserve existing headings
        # (They're already in the content, so no action needed)

        # Remove all links but preserve their text content
        for a_tag in soup.find_all("a"):
            # Replace anchor with its text content
            a_tag.unwrap()

        # Remove all images
        for img_tag in soup.find_all("img"):
            img_tag.decompose()

        # Extract body content
        body = soup.find("body")
        if body:
            # Get inner HTML of body
            body_parts.append(str(body))

    # Create a single well-formed HTML document
    combined_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted EPUB</title>
</head>
<body>
{"".join(body_parts)}
</body>
</html>"""

    return combined_html


def convert_epub_to_markdown(
    epub_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False
) -> str:
    """
    Convert an EPUB file to Markdown format.

    Args:
        epub_path: Path to the input EPUB file.
        output_path: Optional path for the output Markdown file.
                    If provided, the markdown will be written to this file.
        verbose: If True, print progress information.

    Returns:
        The converted Markdown content as a string.

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
        print(f"Converting: {epub_path}")

    # Extract HTML from EPUB
    html_content = _extract_epub_to_html(epub_path)

    # Convert HTML to Markdown using markdownify
    # This preserves heading hierarchy (h1 -> #, h2 -> ##, etc.)
    markdown_content = md(
        html_content,
        heading_style="ATX",  # Use # style headings
        bullets="-",  # Use - for unordered lists
        strip=["script", "style"],  # Remove script and style tags
    )

    # Write to output file if specified
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy EPUB first (before writing any files)
        dest_epub = output_path.parent / epub_path.name
        if not (dest_epub.exists() and dest_epub.samefile(epub_path)):
             # Only copy if it's not the same file
             if dest_epub.exists():
                 dest_epub.unlink()
             shutil.copy2(epub_path, dest_epub)
             if verbose:
                print(f"Copied EPUB to: {dest_epub}")

        output_path.write_text(markdown_content, encoding="utf-8")
        if verbose:
            print(f"Output written to: {output_path}")

        # Extract TOC from EPUB bookmarks
        toc_path = output_path.parent / f"{output_path.stem}.toc_titles.md"
        try:
            extract_epub_toc(epub_path, output_path=toc_path, verbose=verbose)
        except Exception as e:
            if verbose:
                print(f"Warning: Could not extract TOC: {e}")

    return markdown_content


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Convert EPUB files to Markdown using Docling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s book.epub                    # Output to stdout
  %(prog)s book.epub -o book.md         # Output to file
  %(prog)s book.epub -o output/book.md  # Output to subdirectory
  %(prog)s book.epub -v                 # Verbose output
        """
    )

    parser.add_argument(
        "epub_path",
        type=str,
        help="Path to the input EPUB file"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path for the output Markdown file (default: print to stdout)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        markdown_content = convert_epub_to_markdown(
            epub_path=args.epub_path,
            output_path=args.output,
            verbose=args.verbose
        )

        # Print to stdout if no output file specified
        if not args.output:
            print(markdown_content)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
