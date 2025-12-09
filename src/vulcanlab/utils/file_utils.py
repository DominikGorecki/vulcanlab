"""Utility functions for file operations.

This module provides cross-platform file utilities including:
- Setting files to read-only
- Computing file hashes
"""

import hashlib
import os
import stat
from pathlib import Path


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
