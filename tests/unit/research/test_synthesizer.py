"""
Unit tests for synthesizer module.

Tests generate_section, extract_metadata, evaluate_quality, and check_citation_coverage.
"""

import pytest
from unittest.mock import Mock
import re

from vulcanlab.research.synthesizer import (
    generate_section,
    extract_metadata,
    evaluate_quality,
    check_citation_coverage
)

@pytest.fixture
def sample_sources():
    """Create sample sources for testing."""
    return [
        {
            "item_id": 1,
            "type": "excerpt",
            "work_id": 101,
            "work_title": "AI in Medicine",
            "preview": "This study shows that AI improves diagnostic accuracy..."
        },
        {
            "item_id": 2,
            "type": "research_result",
            "work_id": 102,
            "work_title": "The Future of LLMs",
            "preview": "Large language models are transforming research workflows..."
        }
    ]

@pytest.fixture
def sample_section_content():
    """Create a sample section content for testing."""
    return (
        "Artificial intelligence is making significant strides in healthcare. "
        "Studies have shown that AI can improve diagnostic accuracy by 15% [AI in Medicine 2024]. "
        "Furthermore, large language models are being used to automate systematic reviews, "
        "significantly reducing the time required for data extraction [The Future of LLMs 2023]. "
        "However, ethical considerations remain paramount. "
        "Wait, this citation is invalid [Unknown Source 2022]."
    )

class TestGenerateSection:
    """Tests for generate_section function."""

    def test_generate_section_calls_llm_with_correct_format(self, sample_sources):
        """Test that generate_section calls LLM with formatted prompt."""
        question_text = "What is the impact of AI in medicine?"
        context = "Some context about AI in medicine."
        
        mock_llm = Mock()
        mock_llm.generate.return_value = "Generated section content."
        
        result = generate_section(question_text, context, sample_sources, mock_llm)
        
        assert mock_llm.generate.called
        call_args = mock_llm.generate.call_args[0][0]
        assert question_text in call_args
        assert context in call_args
        assert "AI in Medicine" in call_args
        assert result == "Generated section content."

    def test_generate_section_returns_markdown_string(self, sample_sources):
        """Test that generate_section returns a string."""
        mock_llm = Mock()
        mock_llm.generate.return_value = "### Impact\n\nAI is good."
        
        result = generate_section("Question?", "Context.", sample_sources, mock_llm)
        assert isinstance(result, str)
        assert "### Impact" in result

class TestExtractMetadata:
    """Tests for extract_metadata function."""

    def test_extract_metadata_calculates_word_count_correctly(self, sample_sources):
        """Test that extract_metadata calculates word_count correctly."""
        content = "One two three four five."
        metadata = extract_metadata(content, sample_sources)
        assert metadata["word_count"] == 5

    def test_extract_metadata_counts_citations_correctly(self, sample_sources):
        """Test that extract_metadata counts citations correctly."""
        content = "Claim one [Source 1]. Claim two [Source 2]. No citation."
        metadata = extract_metadata(content, sample_sources)
        assert metadata["citation_count"] == 2

    def test_extract_metadata_calculates_source_diversity(self, sample_sources):
        """Test that extract_metadata calculates source_diversity (unique works cited)."""
        content = (
            "Finding from source one [AI in Medicine 2024]. "
            "Another finding from same source [AI in Medicine 2024]. "
            "Finding from source two [The Future of LLMs 2023]."
        )
        metadata = extract_metadata(content, sample_sources)
        # AI in Medicine and The Future of LLMs should both match
        assert metadata["source_diversity"] == 2

    def test_extract_metadata_diversity_zero_on_mismatch(self, sample_sources):
        """Test that source_diversity is zero if no known sources are cited."""
        content = "Finding from unknown source [Unknown 2022]."
        metadata = extract_metadata(content, sample_sources)
        assert metadata["source_diversity"] == 0

class TestEvaluateQuality:
    """Tests for evaluate_quality function."""

    def test_evaluate_quality_calculates_citation_coverage(self, sample_sources):
        """Test that evaluate_quality calculates citation_coverage ratio."""
        content = "Sentence one. Sentence two. Sentence three. Sentence four."
        metadata = {"word_count": 100, "citation_count": 2, "source_diversity": 1}
        
        quality = evaluate_quality(content, sample_sources, metadata)
        # 2 citations / 4 sentences = 0.5 coverage
        assert quality["citation_coverage"] == 0.5

    def test_evaluate_quality_assigns_coherence_score(self, sample_sources):
        """Test that evaluate_quality assigns coherence_score based on heuristics."""
        # High quality
        metadata_high = {"word_count": 900, "citation_count": 12, "source_diversity": 3}
        content_high = "A. " * 20 # 20 sentences
        quality_high = evaluate_quality(content_high, sample_sources, metadata_high)
        # 12 / 20 = 0.6 coverage. Word count 900.
        assert quality_high["coherence_score"] == "High"

        # Low quality
        metadata_low = {"word_count": 100, "citation_count": 1, "source_diversity": 1}
        content_low = "A. B. C. D."
        quality_low = evaluate_quality(content_low, sample_sources, metadata_low)
        assert quality_low["coherence_score"] == "Low"

class TestCheckCitationCoverage:
    """Tests for check_citation_coverage function."""

    def test_check_citation_coverage_identifies_broken_citations(self, sample_sources):
        """Test that check_citation_coverage identifies citations not in sources."""
        content = (
            "Valid [AI in Medicine 2024]. "
            "Invalid [Fake Source 2024]."
        )
        broken = check_citation_coverage(content, sample_sources)
        assert len(broken) == 1
        assert "Fake Source 2024" in broken[0]

    def test_check_citation_coverage_returns_empty_list_when_all_valid(self, sample_sources):
        """Test that check_citation_coverage returns empty list when all citations valid."""
        content = (
            "Valid [AI in Medicine 2024]. "
            "Also valid [The Future of LLMs 2023]."
        )
        broken = check_citation_coverage(content, sample_sources)
        assert len(broken) == 0
