"""
Helper functions for content processing in parent-chunk enrichment.

This module provides pure functions for:
- Word counting
- Markdown heading detection
- Sentence boundary detection
- Content truncation with sliding window algorithm
"""

import re
from typing import List, Optional


def count_words(text: str) -> int:
    """
    Count words in text using whitespace splitting.

    Args:
        text: Input text to count words in

    Returns:
        Number of words in the text
    """
    if not text:
        return 0
    return len(text.split())


def is_heading(line: str) -> bool:
    """
    Check if a line is a markdown heading (h1-h6).

    Args:
        line: Single line of text to check

    Returns:
        True if line is a markdown heading, False otherwise
    """
    return bool(re.match(r'^#{1,6}\s+', line))


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using spaCy if available, regex fallback otherwise.

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences
    """
    if not text:
        return []

    # Try to use spaCy for better sentence tokenization
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        except OSError:
            # Model not available, fall back to regex
            pass
    except ImportError:
        # spaCy not installed, fall back to regex
        pass

    # Regex fallback: split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def truncate_to_word_limit(
    content: str,
    original_chunk_start: int,
    original_chunk_end: int,
    max_word_count: int
) -> str:
    """
    Truncate content using a sliding window centered on the original chunk.

    Preserves:
    - All markdown headings regardless of position
    - Complete sentences at boundaries
    - The original chunk content

    Args:
        content: Full content to truncate
        original_chunk_start: Character position where original chunk starts
        original_chunk_end: Character position where original chunk ends
        max_word_count: Maximum number of words to include

    Returns:
        Truncated content within word limit
    """
    if not content:
        return ""

    # If content is already within limit, return as-is
    if count_words(content) <= max_word_count:
        return content

    lines = content.split('\n')

    # Find which lines contain the original chunk
    char_pos = 0
    chunk_start_line = None
    chunk_end_line = None

    for i, line in enumerate(lines):
        line_start = char_pos
        line_end = char_pos + len(line)

        if chunk_start_line is None and line_end >= original_chunk_start:
            chunk_start_line = i

        if chunk_end_line is None and line_end >= original_chunk_end:
            chunk_end_line = i
            break

        # +1 for the newline character
        char_pos = line_end + 1

    # Default to full range if not found
    if chunk_start_line is None:
        chunk_start_line = 0
    if chunk_end_line is None:
        chunk_end_line = len(lines) - 1

    # Collect all headings (always included)
    heading_indices = set()
    for i, line in enumerate(lines):
        if is_heading(line):
            heading_indices.add(i)

    # Build sliding window centered on original chunk
    window_start = chunk_start_line
    window_end = chunk_end_line

    # Calculate initial word count
    def get_window_content(start: int, end: int) -> str:
        included_lines = []
        for i in range(len(lines)):
            if i in heading_indices or (start <= i <= end):
                included_lines.append((i, lines[i]))
        return '\n'.join(line for _, line in included_lines)

    current_content = get_window_content(window_start, window_end)
    current_word_count = count_words(current_content)

    # Expand window symmetrically until we reach max_word_count
    expand_up = True
    while current_word_count < max_word_count:
        # Try to expand in alternating directions
        if expand_up and window_start > 0:
            # Try expanding upward
            test_start = window_start - 1
            test_content = get_window_content(test_start, window_end)
            test_word_count = count_words(test_content)

            if test_word_count <= max_word_count:
                window_start = test_start
                current_content = test_content
                current_word_count = test_word_count
            else:
                # Can't expand upward without exceeding limit
                # Try to find sentence boundary
                window_start = _find_sentence_boundary_up(lines, window_start, test_start)
                current_content = get_window_content(window_start, window_end)
                current_word_count = count_words(current_content)
                break

            expand_up = False
        elif not expand_up and window_end < len(lines) - 1:
            # Try expanding downward
            test_end = window_end + 1
            test_content = get_window_content(window_start, test_end)
            test_word_count = count_words(test_content)

            if test_word_count <= max_word_count:
                window_end = test_end
                current_content = test_content
                current_word_count = test_word_count
            else:
                # Can't expand downward without exceeding limit
                # Try to find sentence boundary
                window_end = _find_sentence_boundary_down(lines, window_end, test_end)
                current_content = get_window_content(window_start, window_end)
                current_word_count = count_words(current_content)
                break

            expand_up = True
        else:
            # Can't expand in current direction, try the other
            if expand_up:
                expand_up = False
            else:
                # Can't expand in either direction
                break

    return current_content


def _find_sentence_boundary_up(lines: List[str], current_start: int, proposed_start: int) -> int:
    """
    Find a sentence boundary when expanding upward.

    Args:
        lines: All lines of content
        current_start: Current window start line
        proposed_start: Proposed new start line that would exceed limit

    Returns:
        Line index to use as new start (at sentence boundary)
    """
    # Look for sentence-ending punctuation in lines between proposed and current
    for i in range(current_start - 1, proposed_start - 1, -1):
        if i < 0:
            break
        line = lines[i].rstrip()
        if line and re.search(r'[.!?]$', line):
            return i + 1

    # No sentence boundary found, use current position
    return current_start


def _find_sentence_boundary_down(lines: List[str], current_end: int, proposed_end: int) -> int:
    """
    Find a sentence boundary when expanding downward.

    Args:
        lines: All lines of content
        current_end: Current window end line
        proposed_end: Proposed new end line that would exceed limit

    Returns:
        Line index to use as new end (at sentence boundary)
    """
    # Look for sentence-ending punctuation in lines between current and proposed
    for i in range(current_end + 1, proposed_end + 1):
        if i >= len(lines):
            break
        line = lines[i].rstrip()
        if line and re.search(r'[.!?]$', line):
            return i

    # No sentence boundary found, use current position
    return current_end
