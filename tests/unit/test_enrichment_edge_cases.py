"""
Unit tests for enrichment edge cases.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from vulcanlab.retrieval.retrieve import enrich_chunk_from_parent, extract_chunk_title

class TestEnrichmentEdgeCases:
    """Tests for edge cases in enrich_chunk_from_parent()."""

    def test_null_chunk_content(self):
        """Should handle chunk with null content gracefully."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = None
        chunk.start_line = 10
        chunk.end_line = 20
        
        session = Mock()
        
        result = enrich_chunk_from_parent(chunk, session)
        
        assert result['content'] == ""
        assert result['enriched'] is False
        assert result['fallback'] is True
        assert result['depth'] == 0

    def test_invalid_parent_id_type(self):
        """Should handle invalid parent_id type (e.g. string) gracefully."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.parent_id = "invalid_id"  # String instead of int
        chunk.start_line = 1
        chunk.end_line = 5
        
        session = Mock()
        
        # In our implementation, we try int(chunk.parent_id) which might raise ValueError 
        # but we added a check for isinstance(parent_id, (int, float))
        result = enrich_chunk_from_parent(chunk, session)
        
        assert result['enriched'] is False
        assert result['fallback'] is True
        assert result['content'] == "Short content"
        assert result['parent_id'] is None

    def test_parent_with_null_content(self):
        """Should handle parent chunk with null content."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.parent_id = 2
        chunk.start_line = 10
        chunk.end_line = 15
        
        parent = Mock()
        parent.id = 2
        parent.content = None
        parent.parent_id = None
        
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent
        
        result = enrich_chunk_from_parent(chunk, session, min_word_count=100)
        
        # When parent has null content, it should fall back to original chunk
        assert result['enriched'] is False
        assert result['fallback'] is True
        assert result['content'] == "Short content"
        assert result['parent_id'] is None

    def test_broken_hierarchy_missing_parent(self):
        """Should handle missing parent (None from query)."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short content"
        chunk.parent_id = 2
        
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = enrich_chunk_from_parent(chunk, session, min_word_count=100)
        
        assert result['enriched'] is False
        assert result['content'] == "Short content"

    def test_circular_reference_stops_traversal(self):
        """Should detect circular references and stop."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2
        
        parent1 = Mock()
        parent1.id = 2
        parent1.content = "Still short"
        parent1.parent_id = 3
        
        parent2 = Mock()
        parent2.id = 3
        parent2.content = "Medium length content here..."
        parent2.parent_id = 1 # Back to start
        
        session = Mock()
        query_mock = session.query.return_value.filter_by
        
        def filter_side_effect(id):
            mock = Mock()
            if id == 2:
                mock.first.return_value = parent1
            elif id == 3:
                mock.first.return_value = parent2
            elif id == 1:
                mock.first.return_value = chunk
            return mock
        
        query_mock.side_effect = filter_side_effect
        
        result = enrich_chunk_from_parent(chunk, session, min_word_count=100)
        
        # Should stop and return the best parent found so far or original
        # In our implementation it breaks and returns best_parent if it was found.
        assert result['depth'] <= 2

    def test_malformed_breadcrumbs_json(self):
        """Should handle malformed breadcrumbs JSON in extract_chunk_title."""
        chunk = Mock()
        chunk.heading_breadcrumbs = "['Not', 'valid', 'JSON']" # Python list style != JSON
        chunk.content = "# My Heading\nSome text"
        
        title = extract_chunk_title(chunk)
        assert title == "My Heading"

    def test_content_not_in_parent_safeguard(self):
        """Should handle case where original chunk content is not found in parent."""
        chunk = Mock()
        chunk.id = 1
        chunk.content = "This content is not in parent"
        chunk.parent_id = 2
        
        parent = Mock()
        parent.id = 2
        # Provide multi-line content so line-level truncation can work
        parent.content = "\n".join(["A completely different content line."] * 100)
        parent.parent_id = None
        parent.start_line = 100
        parent.end_line = 200
        
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent
        
        result = enrich_chunk_from_parent(chunk, session, min_word_count=50, max_word_count=60)
        
        # Should still work but log warning (sliding window centers on 0)
        assert result['enriched'] is True
        assert len(result['content'].split()) <= 60

class TestConsolidationEdgeCases:
    """Tests for edge cases in consolidation utility functions."""
    
    def test_extract_content_start_gt_end(self):
        """Should return empty string if start_line > end_line."""
        from vulcanlab.augmentation.consolidate_context import _extract_content_from_parent
        
        parent = Mock()
        parent.id = 1
        parent.content = "Line 1\nLine 2\nLine 3"
        parent.start_line = 1
        
        result = _extract_content_from_parent(parent, 5, 2)
        assert result == ""

    def test_extract_content_out_of_bounds(self):
        """Should clamp out of bounds line ranges."""
        from vulcanlab.augmentation.consolidate_context import _extract_content_from_parent
        
        parent = Mock()
        parent.id = 1
        parent.content = "Line 1\nLine 2\nLine 3"
        parent.start_line = 10
        
        # Start at 5 (before parent start 10) -> clamped to 0
        # End at 20 (after parent end 12) -> clamped to 3 (len)
        result = _extract_content_from_parent(parent, 5, 20)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_calculate_coverage_empty_parent(self):
        """Should handle empty parent content in coverage calculation."""
        from vulcanlab.augmentation.consolidate_context import _calculate_coverage
        
        parent = Mock()
        parent.id = 1
        parent.content = ""
        
        items = [{'content': 'some content'}]
        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0

    def test_calculate_coverage_null_parent_content(self):
        """Should handle null parent content in coverage calculation."""
        from vulcanlab.augmentation.consolidate_context import _calculate_coverage
        
        parent = Mock()
        parent.id = 1
        parent.content = None
        
        items = [{'content': 'some content'}]
        coverage = _calculate_coverage(items, parent)
        assert coverage == 0.0
