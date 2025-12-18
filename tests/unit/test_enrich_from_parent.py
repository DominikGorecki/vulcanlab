"""
Unit tests for parent chunk enrichment functions.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from vulcanlab.retrieval.retrieve import extract_chunk_title, enrich_chunk_from_parent


class TestExtractChunkTitle:
    """Tests for extract_chunk_title() function."""

    def test_extract_from_heading_breadcrumbs(self):
        """Should extract title from heading_breadcrumbs JSON array."""
        chunk = Mock()
        chunk.heading_breadcrumbs = json.dumps(["Chapter 1", "Section 1.1", "Subsection A"])
        chunk.content = "Some content here"

        result = extract_chunk_title(chunk)
        assert result == "Subsection A"

    def test_extract_from_single_breadcrumb(self):
        """Should handle single breadcrumb."""
        chunk = Mock()
        chunk.heading_breadcrumbs = json.dumps(["Main Title"])
        chunk.content = "Content"

        result = extract_chunk_title(chunk)
        assert result == "Main Title"

    def test_invalid_json_falls_back_to_first_line(self):
        """Should fall back to first line if JSON is invalid."""
        chunk = Mock()
        chunk.heading_breadcrumbs = "invalid json"
        chunk.content = "# First Line\nSecond line"

        result = extract_chunk_title(chunk)
        assert result == "First Line"

    def test_extract_from_heading_line(self):
        """Should extract from heading line with markdown markers."""
        chunk = Mock()
        chunk.heading_breadcrumbs = None
        chunk.content = "## Introduction to Psychology\nThis is the content."

        result = extract_chunk_title(chunk)
        assert result == "Introduction to Psychology"

    def test_extract_from_non_heading_line(self):
        """Should use first line even if not a heading."""
        chunk = Mock()
        chunk.heading_breadcrumbs = None
        chunk.content = "This is a regular paragraph.\nSecond line."

        result = extract_chunk_title(chunk)
        assert result == "This is a regular paragraph."

    def test_empty_content_returns_untitled(self):
        """Should return 'Untitled' for empty content."""
        chunk = Mock()
        chunk.heading_breadcrumbs = None
        chunk.content = ""

        result = extract_chunk_title(chunk)
        assert result == "Untitled"

    def test_empty_breadcrumbs_array_falls_back(self):
        """Should fall back to first line if breadcrumbs array is empty."""
        chunk = Mock()
        chunk.heading_breadcrumbs = json.dumps([])
        chunk.content = "Fallback title"

        result = extract_chunk_title(chunk)
        assert result == "Fallback title"


class TestEnrichChunkFromParent:
    """Tests for enrich_chunk_from_parent() function."""

    def test_chunk_already_meets_minimum(self):
        """Should return original chunk if it already meets min_word_count."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = " ".join(["word"] * 200)  # 200 words
        chunk.heading_breadcrumbs = json.dumps(["Title"])
        chunk.parent_id = 2

        session = Mock()

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150)

        assert result['enriched'] is False
        assert result['content'] == chunk.content
        assert result['parent_id'] is None
        assert result['depth'] == 0

    def test_orphaned_chunk_no_parent(self):
        """Should return original chunk if parent_id is None."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.heading_breadcrumbs = json.dumps(["Title"])
        chunk.parent_id = None

        session = Mock()

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150)

        assert result['enriched'] is False
        assert result['content'] == chunk.content
        assert result['parent_id'] is None
        assert result['depth'] == 0

    def test_parent_traversal_stops_at_first_meeting_minimum(self):
        """Should stop at first parent meeting min_word_count."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.parent_id = 2

        parent = Mock()
        parent.id = 2
        parent.content = " ".join(["word"] * 200)  # 200 words
        parent.parent_id = 3
        parent.heading_breadcrumbs = json.dumps(["Parent Title"])

        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=1000)

        assert result['enriched'] is True
        assert result['content'] == parent.content
        assert result['parent_id'] == parent.id
        assert result['depth'] == 1
        assert result['title'] == "Parent Title"

    def test_parent_traversal_reaches_root(self):
        """Should reach root when no parent meets minimum."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.parent_id = 2
        chunk.heading_breadcrumbs = None

        parent1 = Mock()
        parent1.id = 2
        parent1.content = "Also short"  # 2 words
        parent1.parent_id = 3

        parent2 = Mock()
        parent2.id = 3
        parent2.content = "Still very short"  # 3 words
        parent2.parent_id = None
        parent2.heading_breadcrumbs = json.dumps(["Root Title"])

        session = Mock()
        query_mock = session.query.return_value.filter_by

        def filter_side_effect(id):
            mock = Mock()
            if id == 2:
                mock.first.return_value = parent1
            elif id == 3:
                mock.first.return_value = parent2
            return mock

        query_mock.side_effect = filter_side_effect

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=1000)

        assert result['enriched'] is True
        assert result['content'] == parent2.content
        assert result['parent_id'] == parent2.id
        assert result['depth'] == 2
        assert result['title'] == "Root Title"

    def test_full_parent_content_used_within_limit(self):
        """Should use full parent content when word_count <= max_word_count."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2

        parent = Mock()
        parent.id = 2
        parent.content = " ".join(["word"] * 200)  # 200 words
        parent.parent_id = None
        parent.heading_breadcrumbs = json.dumps(["Title"])

        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=300)

        assert result['enriched'] is True
        assert result['content'] == parent.content
        assert len(result['content'].split()) == 200

    def test_truncation_applied_when_exceeds_max(self):
        """Should apply truncation when parent exceeds max_word_count."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "This is the original chunk content in the middle"
        chunk.parent_id = 2

        # Parent with content that clearly exceeds max (simple sentences to ensure truncation works)
        sentences = []
        for i in range(100):
            sentences.append(f"Sentence number {i} with some content here.")

        # Insert chunk in middle
        parent_content = "\n".join(sentences[:40]) + "\n" + chunk.content + "\n" + "\n".join(sentences[40:])

        parent = Mock()
        parent.id = 2
        parent.content = parent_content
        parent.parent_id = None
        parent.heading_breadcrumbs = json.dumps(["Title"])

        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=100)

        assert result['enriched'] is True
        # Parent has ~600 words, should be truncated to around 100
        total_words = len(parent.content.split())
        truncated_words = len(result['content'].split())
        assert total_words > 500  # Verify parent is large
        assert truncated_words < 200  # Should be significantly truncated
        assert truncated_words >= 90  # But should be close to max

    def test_missing_parent_chunk_returns_original(self):
        """Should return original chunk if parent is missing from database."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.parent_id = 2
        chunk.heading_breadcrumbs = json.dumps(["Title"])

        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = None

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150)

        assert result['enriched'] is False
        assert result['content'] == chunk.content
        assert result['parent_id'] is None

    def test_circular_reference_protection(self):
        """Should detect and prevent circular parent references."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2
        chunk.heading_breadcrumbs = json.dumps(["Title"])

        parent1 = Mock()
        parent1.id = 2
        parent1.content = "Also short"
        parent1.parent_id = 3

        parent2 = Mock()
        parent2.id = 3
        parent2.content = "Still short"
        parent2.parent_id = 1  # Circular reference back to chunk

        session = Mock()
        query_mock = session.query.return_value.filter_by

        def filter_side_effect(id):
            mock = Mock()
            if id == 2:
                mock.first.return_value = parent1
            elif id == 3:
                mock.first.return_value = parent2
            return mock

        query_mock.side_effect = filter_side_effect

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=1000)

        # Should detect circular reference and stop
        assert result['enriched'] is True
        assert result['depth'] == 2  # Should have traversed 2 levels before detecting circle

    def test_max_depth_protection(self):
        """Should limit traversal to max depth of 10."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2

        # Create a chain of 15 parents
        parents = []
        for i in range(2, 17):
            parent = Mock()
            parent.id = i
            parent.content = "Short"
            parent.parent_id = i + 1 if i < 16 else None
            parent.heading_breadcrumbs = json.dumps([f"Parent {i}"])
            parents.append(parent)

        session = Mock()
        query_mock = session.query.return_value.filter_by

        def filter_side_effect(id):
            mock = Mock()
            for parent in parents:
                if parent.id == id:
                    mock.first.return_value = parent
                    return mock
            mock.first.return_value = None
            return mock

        query_mock.side_effect = filter_side_effect

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=1000)

        # Should stop at depth 10
        assert result['depth'] == 10

    def test_enriched_flag_set_correctly(self):
        """Should set enriched flag correctly based on whether enrichment occurred."""
        # Case 1: Enriched
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2

        parent = Mock()
        parent.id = 2
        parent.content = " ".join(["word"] * 200)
        parent.parent_id = None
        parent.heading_breadcrumbs = json.dumps(["Title"])

        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=300)
        assert result['enriched'] is True

        # Case 2: Not enriched (already meets minimum)
        chunk2 = Mock()
        chunk2.id = 3
        chunk2.content = " ".join(["word"] * 200)
        chunk2.parent_id = 4
        chunk2.heading_breadcrumbs = json.dumps(["Title2"])

        result2 = enrich_chunk_from_parent(chunk2, session, min_word_count=150)
        assert result2['enriched'] is False

    def test_traversal_depth_tracked_accurately(self):
        """Should track traversal depth accurately."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2

        parent1 = Mock()
        parent1.id = 2
        parent1.content = "Also short"
        parent1.parent_id = 3

        parent2 = Mock()
        parent2.id = 3
        parent2.content = "Still short"
        parent2.parent_id = 4

        parent3 = Mock()
        parent3.id = 4
        parent3.content = " ".join(["word"] * 200)  # Meets minimum
        parent3.parent_id = None
        parent3.heading_breadcrumbs = json.dumps(["Title"])

        session = Mock()
        query_mock = session.query.return_value.filter_by

        def filter_side_effect(id):
            mock = Mock()
            if id == 2:
                mock.first.return_value = parent1
            elif id == 3:
                mock.first.return_value = parent2
            elif id == 4:
                mock.first.return_value = parent3
            return mock

        query_mock.side_effect = filter_side_effect

        result = enrich_chunk_from_parent(chunk, session, min_word_count=150, max_word_count=1000)

        assert result['depth'] == 3
        assert result['parent_id'] == 4
