"""
Scanner for markdown files in input directory.

This module provides functions to scan the input directory for markdown files
and extract their metadata.
"""

import logging
from pathlib import Path
from typing import List

from vulcanlab.config import load_config
from vulcanlab.markdown_import.metadata import MarkdownFile, extract_metadata

logger = logging.getLogger(__name__)


def list_markdown_files() -> List[MarkdownFile]:
    """Scan input directory for markdown files and extract metadata.

    Loads the input directory path from config, scans for all .md files,
    and attempts to extract metadata from each file.

    Returns:
        List of MarkdownFile objects with metadata information

    Raises:
        ValueError: If input_dir is not configured or invalid
    """
    config = load_config()

    if not config.paths.input_dir:
        raise ValueError("input_dir not configured in vulcanlab.config.json")

    input_dir = Path(config.paths.input_dir)

    if not input_dir.exists():
        logger.warning(f"Input directory does not exist: {input_dir}")
        return []

    if not input_dir.is_dir():
        raise ValueError(f"input_dir is not a directory: {input_dir}")

    logger.info(f"Scanning for markdown files in: {input_dir}")

    markdown_files = []

    # Find all .md files
    for md_file in sorted(input_dir.glob("*.md")):
        # Skip hidden files
        if md_file.name.startswith('.'):
            continue

        logger.debug(f"Found markdown file: {md_file.name}")

        # Extract metadata
        metadata = extract_metadata(str(md_file))

        markdown_file = MarkdownFile(
            filename=md_file.name,
            file_path=str(md_file),
            has_metadata=metadata is not None,
            metadata=metadata
        )

        markdown_files.append(markdown_file)

    logger.info(f"Found {len(markdown_files)} markdown files")

    return markdown_files
