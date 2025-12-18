"""Markdown export utilities.

This module provides utilities for exporting markdown files with metadata.
"""

import logging
from pathlib import Path

from vulcanlab.config import load_config

logger = logging.getLogger(__name__)


def get_exports_dir() -> Path:
    """Get the exports directory path from config, creating it if needed.

    Returns:
        Path object pointing to the exports subdirectory in the output folder

    Raises:
        ValueError: If output_dir is not configured or invalid
    """
    config = load_config()

    if not config.paths.output_dir:
        raise ValueError("output_dir not configured in vulcanlab.config.json")

    output_dir = Path(config.paths.output_dir)
    exports_dir = output_dir / "exports"

    # Create directory if it doesn't exist
    try:
        exports_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Exports directory ready at: {exports_dir}")
    except Exception as e:
        logger.error(f"Failed to create exports directory at {exports_dir}: {e}")
        raise

    return exports_dir


def is_safe_path(path: Path, base_dir: Path) -> bool:
    """Validate that a path is safely within a base directory.

    This prevents directory traversal attacks by ensuring the resolved
    path is a subdirectory of the base directory.

    Args:
        path: The path to validate
        base_dir: The base directory that path must be within

    Returns:
        True if path is safely within base_dir, False otherwise
    """
    try:
        # Resolve both paths to absolute, dereferencing symlinks
        resolved_path = path.resolve()
        resolved_base = base_dir.resolve()

        # Check if resolved_path is relative to resolved_base
        # This will raise ValueError if not relative
        resolved_path.relative_to(resolved_base)

        return True
    except (ValueError, RuntimeError, OSError):
        # ValueError: not relative to base
        # RuntimeError: symlink loop
        # OSError: filesystem errors
        return False


from .export import (
    export_work,
    generate_export_filename,
    create_frontmatter,
    get_markdown_source,
)

__all__ = [
    "get_exports_dir",
    "is_safe_path",
    "export_work",
    "generate_export_filename",
    "create_frontmatter",
    "get_markdown_source",
]
