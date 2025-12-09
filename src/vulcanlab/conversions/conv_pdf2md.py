"""
PDF to Markdown Converter using Docling.

This module provides functionality to convert PDF files to Markdown format
using the Docling library with hierarchical heading detection.

Example (as script):
    # Default: compare mode (generates .style.md and .hier.md)
    venv\\Scripts\\python -m vulcanlab.conversions.conv_pdf2md input.pdf -o output/doc.md

    # Force style-based single output
    venv\\Scripts\\python -m vulcanlab.conversions.conv_pdf2md input.pdf -o output/doc.md --style-ver

    # Force hierarchical single output
    venv\\Scripts\\python -m vulcanlab.conversions.conv_pdf2md input.pdf -o output/doc.md --hier-ver

    # CPU only
    venv\\Scripts\\python -m vulcanlab.conversions.conv_pdf2md input.pdf -o output/doc.md --no-gpu

Example (as library):
    from vulcanlab.conversions import convert_pdf_to_markdown

    # Default: compare mode (returns tuple of both versions)
    style_md, hier_md = convert_pdf_to_markdown("input.pdf", output_path="output/doc.md")

    # Single output: style-based
    markdown = convert_pdf_to_markdown("input.pdf", output_path="output/doc.md", compare=False, hierarchical=False)

    # Single output: hierarchical
    markdown = convert_pdf_to_markdown("input.pdf", output_path="output/doc.md", compare=False, hierarchical=True)

Options:
    -o, --output      Output file path (default: stdout)
    -v, --verbose     Print progress information
    --ocr             Enable OCR for scanned PDFs
    --style-ver       Force style-based single output
    --hier-ver        Force hierarchical single output
    --no-gpu          Disable GPU acceleration (CPU only)

Note: The source PDF is always copied to the output directory as <file>.pdf
"""

import argparse
import shutil
import sys
import threading
from pathlib import Path
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from hierarchical.postprocessor import ResultPostprocessor
from hierarchical.hierarchy_builder import create_toc
from hierarchical.hierarchy_builder_metadata import HierarchyBuilderMetadata

from .pdf_bookmarks2toc import extract_bookmarks_to_toc

# Default batch sizes for GPU processing
DEFAULT_LAYOUT_BATCH_SIZE = 16
DEFAULT_OCR_BATCH_SIZE = 4
DEFAULT_TABLE_BATCH_SIZE = 4


def _copy_pdf_to_output(
    pdf_path: Path,
    output_path: Path,
    verbose: bool = False
) -> Path:
    """
    Copy PDF to output directory with same stem as output file.

    Args:
        pdf_path: Source PDF path.
        output_path: Output markdown path (used to determine destination).
        verbose: If True, print copy information.

    Returns:
        Path to the copied PDF file.

    Raises:
        FileExistsError: If destination PDF already exists.
    """
    dest_pdf = output_path.parent / f"{output_path.stem}.pdf"

    # Check if PDF already exists at destination
    if dest_pdf.exists():
        raise FileExistsError(
            f"PDF already exists: {dest_pdf}\n"
            f"Remove the existing PDF before running conversion."
        )

    # Copy PDF to output directory
    shutil.copy2(pdf_path, dest_pdf)

    if verbose:
        print(f"Copied PDF to: {dest_pdf}")

    return dest_pdf


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False,
    ocr: bool = False,
    hierarchical: bool = True,
    compare: bool = True,
    use_gpu: bool = True
) -> str | tuple[str, str]:
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Optional path for the output Markdown file.
                    If provided, the markdown will be written to this file and the source PDF
                    will be copied to the same directory as <file>.pdf.
        verbose: If True, print progress information.
        ocr: If True, enable OCR for scanned PDFs. Default False for text PDFs.
        hierarchical: If True, apply hierarchical heading detection. Default True.
        compare: If True (default), generate both style-based and hierarchical outputs
                as <file>.style.md and <file>.hier.md.
        use_gpu: If True, use GPU acceleration when available (auto-detects). Default True.

    Returns:
        If compare=True: tuple of (style_md, hierarchical_md) strings.
        If compare=False: single markdown content string.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If the file is not a PDF file.
        FileExistsError: If destination PDF already exists (must be removed first).
    """
    pdf_path = Path(pdf_path)

    # Validate input file
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File must be a PDF file, got: {pdf_path.suffix}")

    if verbose:
        print(f"Converting: {pdf_path}")
        if ocr:
            print("OCR enabled for scanned content")
        if use_gpu:
            print("GPU acceleration enabled (auto-detect)")

    # Configure PDF pipeline options with GPU support and optimized batch sizes
    pipeline_options = ThreadedPdfPipelineOptions(do_ocr=ocr)

    if use_gpu:
        # Configure accelerator options for GPU support (auto-detect GPU, fallback to CPU)
        accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.AUTO  # Auto-detect GPU, fallback to CPU
        )
        pipeline_options.accelerator_options = accelerator_options

        # Set batch sizes for GPU processing
        pipeline_options.ocr_batch_size = DEFAULT_OCR_BATCH_SIZE
        pipeline_options.layout_batch_size = DEFAULT_LAYOUT_BATCH_SIZE
        pipeline_options.table_batch_size = DEFAULT_TABLE_BATCH_SIZE

    # Initialize converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Handle compare mode - generate both outputs
    if compare:
        if verbose:
            print("Compare mode: generating both style-based and hierarchical outputs...")

        # First pass: style-based
        result_style = converter.convert(str(pdf_path))
        if verbose:
            print("Generating style-based output...")

        postprocessor = ResultPostprocessor(result_style, pdf_path)
        headings = postprocessor.get_headers()
        if headings:
            from hierarchical.postprocessor import flatten_hierarchy_tree
            from docling_core.types.doc.document import SectionHeaderItem
            root = create_toc(headings)
            flat_hierarchy = flatten_hierarchy_tree(root, 0)
            by_ref = {el[0].doc_ref: el for el in flat_hierarchy}
            for item, _ in result_style.document.iterate_items():
                if item.self_ref in by_ref and isinstance(item, SectionHeaderItem):
                    _, level = by_ref[item.self_ref]
                    item.level = level

        style_md = result_style.document.export_to_markdown()

        # Second pass: hierarchical (TOC-based)
        result_hier = converter.convert(str(pdf_path))
        if verbose:
            print("Generating hierarchical (TOC-based) output...")

        # Run hierarchical processing with timeout (same as single-output mode)
        hier_error = [None]
        hier_timed_out = [False]

        def run_hier_processing():
            try:
                postprocessor_hier = ResultPostprocessor(result_hier, pdf_path)
                postprocessor_hier.process()
            except Exception as e:
                hier_error[0] = e

        hier_thread = threading.Thread(target=run_hier_processing, daemon=True)
        hier_thread.start()
        hier_thread.join(timeout=120)  # 120 second timeout for hierarchical in compare mode

        if hier_thread.is_alive():
            hier_timed_out[0] = True
            if verbose:
                print("Warning: Hierarchical processing timed out, using style-based as fallback for hier output")
            # Copy style_md to hier_md as fallback
            hier_md = style_md
        elif hier_error[0]:
            if verbose:
                print(f"Hierarchical processing failed: {hier_error[0]}, using style-based as fallback")
            hier_md = style_md
        else:
            # Hierarchical processing succeeded
            hier_md = result_hier.document.export_to_markdown()

        # Write to output files if specified
        if output_path:
            output_path = Path(output_path)
            stem = output_path.stem
            parent = output_path.parent
            parent.mkdir(parents=True, exist_ok=True)

            # Copy PDF first (before writing any files)
            _copy_pdf_to_output(pdf_path, output_path, verbose)

            style_path = parent / f"{stem}.style.md"
            hier_path = parent / f"{stem}.hier.md"
            toc_path = parent / f"{stem}.toc_titles.md"

            style_path.write_text(style_md, encoding="utf-8")
            hier_path.write_text(hier_md, encoding="utf-8")

            # Extract TOC from PDF bookmarks
            try:
                extract_bookmarks_to_toc(pdf_path, output_path=toc_path, verbose=verbose)
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not extract TOC: {e}")

            if verbose:
                print(f"Style-based output written to: {style_path}")
                print(f"Hierarchical output written to: {hier_path}")

        return (style_md, hier_md)

    result = converter.convert(str(pdf_path))

    # Apply hierarchical post-processing for better heading structure
    if hierarchical:
        if verbose:
            print("Applying hierarchical heading detection...")

        # First check if TOC-based approach will have too many missing titles
        use_style_based = False
        try:
            hbm = HierarchyBuilderMetadata(result, pdf_path)
            toc = hbm.toc
            if toc:
                # Count how many TOC entries are missing coordinates (not found)
                missing_count = sum(1 for _, _, _, info in toc if "coords" not in info)
                total_count = len(toc)
                if missing_count > 0 and verbose:
                    print(f"TOC has {missing_count}/{total_count} entries not found in document")
                # If more than 20% of entries are missing, use style-based approach
                if total_count > 0 and missing_count / total_count > 0.2:
                    if verbose:
                        print("Too many missing TOC entries, falling back to style-based approach")
                    use_style_based = True
            else:
                # No TOC found at all - use style-based approach
                if verbose:
                    print("No TOC found in document, using style-based approach")
                use_style_based = True
        except Exception as e:
            if verbose:
                print(f"TOC extraction failed: {e}, using style-based approach")
            use_style_based = True

        # Run hierarchical processing with timeout
        error_container = [None]
        timed_out = [False]

        def run_hierarchical():
            try:
                postprocessor = ResultPostprocessor(result, pdf_path)
                if use_style_based:
                    # Force style-based by clearing the TOC cache
                    postprocessor.result = result
                    headings = postprocessor.get_headers()
                    if headings:
                        from hierarchical.postprocessor import flatten_hierarchy_tree
                        from docling_core.types.doc.document import SectionHeaderItem
                        root = create_toc(headings)
                        flat_hierarchy = flatten_hierarchy_tree(root, 0)
                        by_ref = {el[0].doc_ref: el for el in flat_hierarchy}
                        for item, _ in result.document.iterate_items():
                            if item.self_ref in by_ref and isinstance(item, SectionHeaderItem):
                                _, level = by_ref[item.self_ref]
                                item.level = level
                else:
                    postprocessor.process()
            except Exception as e:
                error_container[0] = e

        thread = threading.Thread(target=run_hierarchical, daemon=True)
        thread.start()
        thread.join(timeout=60)  # 60 second timeout

        if thread.is_alive():
            timed_out[0] = True
            if verbose:
                print("Warning: Hierarchical processing timed out")
            # Try style-based as fallback
            if not use_style_based:
                if verbose:
                    print("Attempting style-based fallback...")
                try:
                    postprocessor = ResultPostprocessor(result, pdf_path)
                    headings = postprocessor.get_headers()
                    if headings:
                        from hierarchical.postprocessor import flatten_hierarchy_tree
                        from docling_core.types.doc.document import SectionHeaderItem
                        root = create_toc(headings)
                        flat_hierarchy = flatten_hierarchy_tree(root, 0)
                        by_ref = {el[0].doc_ref: el for el in flat_hierarchy}
                        for item, _ in result.document.iterate_items():
                            if item.self_ref in by_ref and isinstance(item, SectionHeaderItem):
                                _, level = by_ref[item.self_ref]
                                item.level = level
                        if verbose:
                            print("Style-based fallback successful")
                except Exception as e:
                    if verbose:
                        print(f"Style-based fallback failed: {e}")
        elif error_container[0]:
            if verbose:
                print(f"Warning: Hierarchical processing failed: {error_container[0]}")

    # Export to markdown
    markdown_content = result.document.export_to_markdown()

    # Write to output file if specified
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy PDF first (before writing any files)
        _copy_pdf_to_output(pdf_path, output_path, verbose)

        output_path.write_text(markdown_content, encoding="utf-8")

        # Extract TOC from PDF bookmarks
        toc_path = output_path.parent / f"{output_path.stem}.toc_titles.md"
        try:
            extract_bookmarks_to_toc(pdf_path, output_path=toc_path, verbose=verbose)
        except Exception as e:
            if verbose:
                print(f"Warning: Could not extract TOC: {e}")

        if verbose:
            print(f"Output written to: {output_path}")

    return markdown_content


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown using Docling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                    # Output to stdout
  %(prog)s document.pdf -o document.md     # Output to file
  %(prog)s document.pdf -o output/doc.md   # Output to subdirectory
  %(prog)s document.pdf -v                 # Verbose output
        """
    )

    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the input PDF file"
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

    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR for scanned PDFs (default: off for text PDFs)"
    )

    parser.add_argument(
        "--style-ver",
        action="store_true",
        help="Force style-based output only (single <file>.md)"
    )

    parser.add_argument(
        "--hier-ver",
        action="store_true",
        help="Force hierarchical output only (single <file>.md)"
    )

    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Disable GPU acceleration (use CPU only)"
    )

    args = parser.parse_args()

    try:
        # Validate conflicting flags
        if args.style_ver and args.hier_ver:
            print("Error: Cannot specify both --style-ver and --hier-ver", file=sys.stderr)
            return 1

        # Determine mode based on flags
        if args.style_ver:
            # Style-based single output
            compare = False
            hierarchical = False
        elif args.hier_ver:
            # Hierarchical single output
            compare = False
            hierarchical = True
        else:
            # Default: compare mode (both outputs)
            compare = True
            hierarchical = True

        result = convert_pdf_to_markdown(
            pdf_path=args.pdf_path,
            output_path=args.output,
            verbose=args.verbose,
            ocr=args.ocr,
            hierarchical=hierarchical,
            compare=compare,
            use_gpu=not args.no_gpu
        )

        # Print to stdout if no output file specified
        if not args.output:
            if compare:
                style_md, hier_md = result
                print("=== STYLE-BASED OUTPUT ===")
                print(style_md)
                print("\n=== HIERARCHICAL OUTPUT ===")
                print(hier_md)
            else:
                print(result)

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
