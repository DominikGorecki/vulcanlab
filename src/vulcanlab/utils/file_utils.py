"""Utility functions for file operations.

This module provides cross-platform file utilities including:
- Setting files to read-only
- Computing file hashes
- Path resolution for Work model files
"""

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Optional

from .exceptions import InvalidFilePathError


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal hash string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def set_file_readonly(file_path: Path) -> None:
    """
    Set a file to read-only on both Windows and Linux.

    Args:
        file_path: Path to the file to make read-only.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get current permissions
    current_mode = file_path.stat().st_mode

    # Remove write permissions for user, group, and others
    # This works on both Windows and Linux
    new_mode = current_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)

    file_path.chmod(new_mode)


def set_file_writable(file_path: Path) -> None:
    """
    Set a file to writable (removes read-only) on both Windows and Linux.

    Args:
        file_path: Path to the file to make writable.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get current permissions
    current_mode = file_path.stat().st_mode

    # Add write permission for user
    new_mode = current_mode | stat.S_IWUSR

    file_path.chmod(new_mode)


def is_file_readonly(file_path: Path) -> bool:
    """
    Check if a file is read-only.

    Args:
        file_path: Path to the file to check.

    Returns:
        True if the file is read-only (no write permissions), False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    current_mode = file_path.stat().st_mode

    # Check if any write permission is set
    return not (current_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


class PathResolver:
    """
    Resolves Work model filenames to absolute paths using config-based directories.

    Caches input_dir and output_dir from vulcanlab.config.json at initialization.
    Thread-safe singleton pattern via get_path_resolver().
    """

    def __init__(self, config_path: Path = None):
        """
        Initialize PathResolver from config file.

        Args:
            config_path: Path to config file (defaults to vulcanlab.config.json at project root)

        Raises:
            FileNotFoundError: If config file doesn't exist
            KeyError: If config missing required paths.input_dir or paths.output_dir
        """
        if config_path is None:
            # Assume config at project root (4 levels up from utils/)
            config_path = Path(__file__).parent.parent.parent.parent / "vulcanlab.config.json"

        with open(config_path, 'r') as f:
            config = json.load(f)

        self.input_dir = Path(config["paths"]["input_dir"])
        self.output_dir = Path(config["paths"]["output_dir"])

    def resolve_work_path(self, work, key: Optional[str] = None) -> Path:
        """
        Resolve a Work model path field to absolute Path.

        Args:
            work: Work model instance
            key: Key in work.files JSON (e.g., "sanitized", "original_file").
                 If None, resolves work.markdown_path instead.

        Returns:
            Absolute Path object

        Raises:
            InvalidFilePathError: If filename is NULL or empty

        Examples:
            resolver.resolve_work_path(work, "sanitized")
            resolver.resolve_work_path(work, "original_file")
            resolver.resolve_work_path(work)  # Resolves markdown_path
        """
        if key is None:
            # Resolve markdown_path
            filename = work.markdown_path
            if not filename:
                raise InvalidFilePathError(
                    f"Work {work.id}: markdown_path is NULL or empty",
                    work_id=work.id,
                    field_name="markdown_path"
                )
            base_dir = self.output_dir
        else:
            # Resolve files[key]["path"]
            if not work.files or key not in work.files:
                raise InvalidFilePathError(
                    f"Work {work.id}: files['{key}'] does not exist",
                    work_id=work.id,
                    field_name=f"files.{key}"
                )

            file_info = work.files[key]
            filename = file_info.get("path")

            if not filename:
                raise InvalidFilePathError(
                    f"Work {work.id}: files['{key}']['path'] is NULL or empty",
                    work_id=work.id,
                    field_name=f"files.{key}.path"
                )

            # Determine base directory
            base_dir = self.input_dir if key == "original_file" else self.output_dir

        return base_dir / filename


_path_resolver_instance = None


def get_path_resolver(config_path: Path = None) -> PathResolver:
    """
    Get or create the singleton PathResolver instance.

    Args:
        config_path: Optional config path (only used on first call)

    Returns:
        Cached PathResolver instance
    """
    global _path_resolver_instance
    if _path_resolver_instance is None:
        _path_resolver_instance = PathResolver(config_path)
    return _path_resolver_instance
