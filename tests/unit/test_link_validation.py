"""
Unit tests for link validation logic.
"""

import pytest
from src.vulcanlab.collections import validate_item_link
from src.vulcanlab.data.models.enums import CollectionItemType


class TestLinkValidation:
    """Tests for link validation regex patterns."""

    @pytest.mark.parametrize("link, expected", [
        ("/search/result/1/2/3", True),
        ("/search/result/100/200/300", True),
        ("/search/result/1/2", False),
        ("/search/result/a/b/c", False),
        ("http://example.com", False),
        ("", False),
    ])
    def test_validate_excerpt_link(self, link, expected):
        assert validate_item_link(CollectionItemType.EXCERPT, link) == expected

    @pytest.mark.parametrize("link, expected", [
        ("/rag/1/results/2", True),
        ("/rag/100/results/200", True),
        ("/rag/1/results", False),
        ("/rag/1", False),
        ("/search/result/1/2/3", False),
    ])
    def test_validate_research_result_link(self, link, expected):
        assert validate_item_link(CollectionItemType.RESEARCH_RESULT, link) == expected

    @pytest.mark.parametrize("link, expected", [
        ("/rag/1", True),
        ("/rag/100", True),
        ("/rag/1/results/2", False),
        ("/rag", False),
    ])
    def test_validate_research_query_link(self, link, expected):
        assert validate_item_link(CollectionItemType.RESEARCH_QUERY, link) == expected

