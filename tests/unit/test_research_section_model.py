"""
Unit tests for ResearchSection model.
"""

from datetime import datetime
import pytest
from src.vulcanlab.data.models.research_section import ResearchSection
from src.vulcanlab.data.models.enums import QualityStatus


class TestResearchSectionModel:
    """Tests for the ResearchSection model."""

    def test_create_research_section(self):
        """Test creating a research section with all fields."""
        section = ResearchSection(
            session_id=1,
            question_id="Q001",
            question_text="What is the impact of AI on healthcare?",
            section_content="AI has shown significant improvements in diagnostic accuracy...",
            context_data={"sources": ["source1", "source2"]},
            matching_results={"total": 10, "relevant": 5},
            section_metadata={"author": "system", "confidence": 0.95},
            reuse_info={"reused": True, "original_id": "section_456"},
            quality_status=QualityStatus.PASS
        )

        assert section.session_id == 1
        assert section.question_id == "Q001"
        assert section.question_text == "What is the impact of AI on healthcare?"
        assert "diagnostic accuracy" in section.section_content
        assert section.context_data == {"sources": ["source1", "source2"]}
        assert section.matching_results == {"total": 10, "relevant": 5}
        assert section.section_metadata == {"author": "system", "confidence": 0.95}
        assert section.reuse_info == {"reused": True, "original_id": "section_456"}
        assert section.quality_status == QualityStatus.PASS

    def test_research_section_minimal_fields(self):
        """Test creating a section with only required field."""
        section = ResearchSection(session_id=1)

        assert section.session_id == 1
        assert section.question_id is None
        assert section.question_text is None
        assert section.section_content is None
        assert section.context_data is None
        assert section.matching_results is None
        assert section.section_metadata is None
        assert section.reuse_info is None
        assert section.quality_status is None

    def test_research_section_jsonb_fields(self):
        """Test that JSONB columns serialize and deserialize correctly."""
        context_data = {
            "search_query": "AI healthcare",
            "filters": {"date_range": "2020-2024"},
            "results_count": 100
        }
        matching_results = {
            "chunks": [{"id": 1, "score": 0.9}, {"id": 2, "score": 0.8}],
            "total_matches": 2
        }
        section_metadata = {
            "processing_time": 1.5,
            "model_version": "v2.1"
        }
        reuse_info = {
            "source_session": 123,
            "reused_at": "2024-01-09T10:00:00Z"
        }

        section = ResearchSection(
            session_id=1,
            context_data=context_data,
            matching_results=matching_results,
            section_metadata=section_metadata,
            reuse_info=reuse_info
        )

        assert section.context_data == context_data
        assert section.matching_results == matching_results
        assert section.section_metadata == section_metadata
        assert section.reuse_info == reuse_info
        assert section.matching_results["total_matches"] == 2
        assert section.section_metadata["model_version"] == "v2.1"

    def test_research_section_quality_status_enum(self):
        """Test that quality_status accepts valid enum values."""
        quality_statuses = [
            QualityStatus.PENDING,
            QualityStatus.PASS,
            QualityStatus.FAIL,
            QualityStatus.NEEDS_REVIEW
        ]

        for status in quality_statuses:
            section = ResearchSection(
                session_id=1,
                question_id=f"Q_{status.value}",
                quality_status=status
            )
            assert section.quality_status == status

    def test_research_section_repr(self):
        """Test the string representation of a ResearchSection."""
        section = ResearchSection(
            id=10,
            session_id=5,
            question_id="Q100"
        )
        assert repr(section) == "<ResearchSection(id=10, session_id=5, question_id='Q100')>"

    def test_research_section_tablename(self):
        """Test the table name."""
        assert ResearchSection.__tablename__ == "research_sections"

    def test_research_section_with_long_content(self):
        """Test creating a section with long text content."""
        long_content = "A" * 10000  # 10k characters
        long_question = "What is " + ("very " * 100) + "important?"

        section = ResearchSection(
            session_id=1,
            question_text=long_question,
            section_content=long_content
        )

        assert len(section.section_content) == 10000
        assert "very" in section.question_text

    def test_research_section_with_complex_jsonb(self):
        """Test JSONB columns with nested complex structures."""
        complex_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "values": [1, 2, 3],
                        "section_metadata": {"key": "value"}
                    }
                }
            },
            "arrays": [[1, 2], [3, 4]],
            "mixed": [{"a": 1}, {"b": 2}]
        }

        section = ResearchSection(
            session_id=1,
            context_data=complex_data
        )

        assert section.context_data["level1"]["level2"]["level3"]["values"] == [1, 2, 3]
        assert section.context_data["arrays"][0] == [1, 2]
