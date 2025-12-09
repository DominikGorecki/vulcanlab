"""Sanitization utilities for markdown processing."""

from .extract_titles import extract_titles, extract_titles_to_file, extract_titles_from_work, HashMismatchError
from .suggest_heading_changes import (
    suggest_heading_changes,
    suggest_heading_changes_from_work,
    build_prompt_for_work,
    save_title_changes_from_response,
)
from .apply_title_changes import apply_title_changes_from_work
from .skip_apply import skip_apply_from_work
from .update_content_hash import update_content_hash, verify_title_changes_integrity

__all__ = [
    "extract_titles",
    "extract_titles_to_file",
    "extract_titles_from_work",
    "HashMismatchError",
    "suggest_heading_changes",
    "suggest_heading_changes_from_work",
    "build_prompt_for_work",
    "save_title_changes_from_response",
    "apply_title_changes_from_work",
    "skip_apply_from_work",
    "update_content_hash",
    "verify_title_changes_integrity",
]
