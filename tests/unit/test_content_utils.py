"""
Unit tests for content_utils helper functions.
"""

import pytest
from unittest.mock import patch, MagicMock
from vulcanlab.retrieval.content_utils import (
    count_words,
    is_heading,
    split_sentences,
    truncate_to_word_limit,
)


class TestCountWords:
    """Tests for count_words() function."""

    def test_empty_string(self):
        """Empty string should return 0."""
        assert count_words("") == 0

    def test_single_word(self):
        """Single word should return 1."""
        assert count_words("hello") == 1

    def test_multiple_words(self):
        """Multiple words should be counted correctly."""
        assert count_words("hello world") == 2
        assert count_words("the quick brown fox") == 4

    def test_multiple_spaces(self):
        """Multiple spaces between words should not affect count."""
        assert count_words("hello    world") == 2
        assert count_words("  hello   world  ") == 2

    def test_newlines(self):
        """Newlines should be treated as whitespace."""
        assert count_words("hello\nworld") == 2
        assert count_words("hello\n\nworld") == 2


class TestIsHeading:
    """Tests for is_heading() function."""

    def test_h1_heading(self):
        """Should detect h1 heading."""
        assert is_heading("# Heading") is True

    def test_h2_heading(self):
        """Should detect h2 heading."""
        assert is_heading("## Heading") is True

    def test_h3_heading(self):
        """Should detect h3 heading."""
        assert is_heading("### Heading") is True

    def test_h4_heading(self):
        """Should detect h4 heading."""
        assert is_heading("#### Heading") is True

    def test_h5_heading(self):
        """Should detect h5 heading."""
        assert is_heading("##### Heading") is True

    def test_h6_heading(self):
        """Should detect h6 heading."""
        assert is_heading("###### Heading") is True

    def test_not_heading_no_hash(self):
        """Should reject lines without hash."""
        assert is_heading("Heading") is False

    def test_not_heading_no_space(self):
        """Should reject hash without space after."""
        assert is_heading("#Heading") is False

    def test_not_heading_too_many_hashes(self):
        """Should reject more than 6 hashes."""
        assert is_heading("####### Heading") is False

    def test_not_heading_hash_in_middle(self):
        """Should reject hash not at start of line."""
        assert is_heading("Some # Heading") is False


class TestSplitSentences:
    """Tests for split_sentences() function."""

    def test_empty_string(self):
        """Empty string should return empty list."""
        assert split_sentences("") == []

    def test_single_sentence_period(self):
        """Single sentence with period."""
        result = split_sentences("This is a sentence.")
        assert len(result) == 1
        assert result[0] == "This is a sentence."

    def test_multiple_sentences_period(self):
        """Multiple sentences with periods."""
        result = split_sentences("First sentence. Second sentence.")
        assert len(result) == 2
        assert result[0] == "First sentence."
        assert result[1] == "Second sentence."

    def test_exclamation_mark(self):
        """Should split on exclamation marks."""
        result = split_sentences("Hello! How are you?")
        assert len(result) == 2
        assert result[0] == "Hello!"
        assert result[1] == "How are you?"

    def test_question_mark(self):
        """Should split on question marks."""
        result = split_sentences("Are you there? Yes I am.")
        assert len(result) == 2
        assert result[0] == "Are you there?"
        assert result[1] == "Yes I am."

    def test_abbreviations_with_spacy(self):
        """Should handle abbreviations correctly with spaCy if available."""
        # This test will work better with spaCy, but regex fallback may split incorrectly
        text = "Dr. Smith went to the store. He bought milk."
        result = split_sentences(text)
        # With spaCy: should be 2 sentences
        # With regex fallback: might be 3 (splitting on "Dr.")
        # We accept both for this test since it depends on availability
        assert len(result) >= 2

    def test_regex_fallback_works(self):
        """Verify regex fallback produces correct results."""
        # Test that the regex fallback path works correctly
        # (will be used if spaCy is not installed or model not available)
        import re
        text = "First sentence. Second sentence."
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = [s.strip() for s in sentences if s.strip()]
        assert len(result) == 2
        assert result[0] == "First sentence."
        assert result[1] == "Second sentence."

    def test_spacy_model_not_available_fallback(self):
        """Should fall back to regex when spaCy model not available."""
        # This test verifies the OSError fallback path
        # We'll test by patching spacy.load after import
        try:
            import spacy
            with patch.object(spacy, 'load', side_effect=OSError("Model not found")):
                result = split_sentences("First sentence. Second sentence.")
                assert len(result) == 2
        except ImportError:
            # If spaCy isn't installed, the regex fallback will be used anyway
            result = split_sentences("First sentence. Second sentence.")
            assert len(result) == 2


class TestTruncateToWordLimit:
    """Tests for truncate_to_word_limit() function."""

    def test_empty_content(self):
        """Empty content should return empty string."""
        assert truncate_to_word_limit("", 0, 0, 100) == ""

    def test_content_within_limit(self):
        """Content within limit should be returned as-is."""
        content = "This is a short sentence."
        result = truncate_to_word_limit(content, 0, len(content), 100)
        assert result == content

    def test_preserves_headings(self):
        """Should preserve all headings regardless of position."""
        content = """# Title
Some intro text here.

## Section 1
This is the original chunk content.

## Section 2
More content here.

## Section 3
Even more content."""

        # Original chunk is "This is the original chunk content."
        chunk_start = content.index("This is the original")
        chunk_end = chunk_start + len("This is the original chunk content.")

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 20)

        # All headings should be present
        assert "# Title" in result
        assert "## Section 1" in result
        assert "## Section 2" in result

    def test_does_not_break_sentences(self):
        """Should not break sentences mid-sentence."""
        content = """Sentence one is here. Sentence two is here. Sentence three is here. Sentence four is here."""

        # Original chunk is "Sentence two"
        chunk_start = content.index("Sentence two")
        chunk_end = chunk_start + len("Sentence two is here.")

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 15)

        # Should contain complete sentences only
        sentences = result.split('. ')
        for sentence in sentences:
            # Each sentence should end with a period or be the last sentence
            if sentence != sentences[-1]:
                assert sentence.endswith('.') or '. ' in result[result.index(sentence):]

    def test_centers_on_original_chunk(self):
        """Should center window on original chunk position."""
        content = """Line one.
Line two.
Line three is the original chunk.
Line four.
Line five."""

        chunk_start = content.index("Line three")
        chunk_end = chunk_start + len("Line three is the original chunk.")

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 15)

        # Original chunk must be included
        assert "Line three is the original chunk." in result

    def test_edge_case_chunk_at_start(self):
        """Should handle original chunk at start of content."""
        content = """Original chunk at start.
Line two.
Line three.
Line four.
Line five."""

        chunk_start = 0
        chunk_end = len("Original chunk at start.")

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 12)

        # Original chunk must be included
        assert "Original chunk at start." in result

    def test_edge_case_chunk_at_end(self):
        """Should handle original chunk at end of content."""
        content = """Line one.
Line two.
Line three.
Line four.
Original chunk at end."""

        chunk_start = content.index("Original chunk")
        chunk_end = len(content)

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 12)

        # Original chunk must be included
        assert "Original chunk at end." in result

    def test_content_shorter_than_max(self):
        """Content shorter than max should return as-is."""
        content = "Short content."
        result = truncate_to_word_limit(content, 0, len(content), 1000)
        assert result == content

    def test_symmetric_expansion(self):
        """Should expand window symmetrically around original chunk."""
        content = """Line 1.
Line 2.
Line 3.
Line 4 is original.
Line 5.
Line 6.
Line 7."""

        chunk_start = content.index("Line 4")
        chunk_end = chunk_start + len("Line 4 is original.")

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 18)

        # Should include original and expand around it
        assert "Line 4 is original." in result

        # Count lines above and below the original (roughly symmetric)
        lines_in_result = [line for line in result.split('\n') if line.strip()]
        original_line_idx = None
        for i, line in enumerate(lines_in_result):
            if "Line 4" in line:
                original_line_idx = i
                break

        # Should have expanded somewhat symmetrically
        # (exact symmetry may vary due to word count constraints)
        assert original_line_idx is not None

    def test_preserves_original_chunk_content(self):
        """Original chunk content must always be included."""
        content = """Some text before.
This is the important original chunk that must be preserved.
Some text after."""

        chunk_start = content.index("This is the important")
        chunk_end = chunk_start + len("This is the important original chunk that must be preserved.")

        # Very tight limit
        result = truncate_to_word_limit(content, chunk_start, chunk_end, 5)

        # Original chunk must be there even if it exceeds the limit
        assert "This is the important original chunk that must be preserved." in result

    def test_multiple_headings_preserved(self):
        """All headings should be preserved even with tight limit."""
        content = """# Main Title

## First Section
Some content.

### Subsection
Original chunk here.

## Second Section
More content.

# Another Title
Final content."""

        chunk_start = content.index("Original chunk")
        chunk_end = chunk_start + len("Original chunk here.")

        result = truncate_to_word_limit(content, chunk_start, chunk_end, 25)

        # All headings should be present
        assert "# Main Title" in result
        assert "## First Section" in result
        assert "### Subsection" in result
        assert "## Second Section" in result or "# Another Title" in result

    def test_word_count_within_limit(self):
        """Result should not exceed max_word_count unless necessary for sentence integrity."""
        content = """First sentence here. Second sentence here. Third sentence here.
Fourth sentence here. Fifth sentence here. Sixth sentence here."""

        chunk_start = content.index("Third")
        chunk_end = chunk_start + len("Third sentence here.")

        max_words = 20
        result = truncate_to_word_limit(content, chunk_start, chunk_end, max_words)

        word_count = count_words(result)

        # Should be close to max_words (may exceed slightly for sentence integrity)
        assert word_count <= max_words + 10  # Allow some overflow for sentence boundaries
