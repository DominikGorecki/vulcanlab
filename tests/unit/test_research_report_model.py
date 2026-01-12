"""
Unit tests for ResearchReport model.
"""

from datetime import datetime
import pytest
from src.vulcanlab.data.models.research_report import ResearchReport


class TestResearchReportModel:
    """Tests for the ResearchReport model."""

    def test_create_research_report(self):
        """Test creating a research report with all fields."""
        report = ResearchReport(
            session_id=1,
            report_content="# Research Report\n\nThis is a comprehensive report on AI...",
            executive_summary="AI technologies show promising results in multiple domains.",
            quality_evaluation={"score": 0.92, "reviewer": "expert_001"},
            report_metadata={"word_count": 5000, "citations": 50},
            version=2
        )

        assert report.session_id == 1
        assert "comprehensive report" in report.report_content
        assert "promising results" in report.executive_summary
        assert report.quality_evaluation == {"score": 0.92, "reviewer": "expert_001"}
        assert report.report_metadata == {"word_count": 5000, "citations": 50}
        assert report.version == 2

    def test_research_report_minimal_fields(self):
        """Test creating a report with only required fields."""
        report = ResearchReport(
            session_id=1,
            report_content="Minimal report content."
        )

        assert report.session_id == 1
        assert report.report_content == "Minimal report content."
        assert report.executive_summary is None
        assert report.quality_evaluation is None
        assert report.report_metadata is None
        # Note: version default is set at DB level, not Python level

    def test_research_report_default_version(self):
        """Test that version can be set explicitly."""
        report = ResearchReport(
            session_id=1,
            report_content="Version test",
            version=1
        )

        assert report.version == 1

    def test_research_report_jsonb_fields(self):
        """Test that JSONB columns serialize and deserialize correctly."""
        quality_evaluation = {
            "overall_score": 0.88,
            "criteria": {
                "clarity": 0.9,
                "completeness": 0.85,
                "accuracy": 0.9
            },
            "feedback": "Well-structured report with minor gaps",
            "approved": True
        }
        report_metadata = {
            "generated_at": "2024-01-09T10:00:00Z",
            "model": "gpt-4",
            "sections_count": 5,
            "references": ["ref1", "ref2", "ref3"]
        }

        report = ResearchReport(
            session_id=1,
            report_content="Test content",
            quality_evaluation=quality_evaluation,
            report_metadata=report_metadata
        )

        assert report.quality_evaluation == quality_evaluation
        assert report.report_metadata == report_metadata
        assert report.quality_evaluation["criteria"]["clarity"] == 0.9
        assert report.report_metadata["sections_count"] == 5
        assert report.quality_evaluation["approved"] is True

    def test_research_report_with_long_content(self):
        """Test creating a report with long content."""
        long_content = "# " + ("Chapter\n\n" + "A" * 1000 + "\n\n") * 10
        long_summary = "Summary: " + "B" * 5000

        report = ResearchReport(
            session_id=1,
            report_content=long_content,
            executive_summary=long_summary
        )

        assert "Chapter" in report.report_content
        assert len(report.report_content) > 10000
        assert len(report.executive_summary) > 5000

    def test_research_report_repr(self):
        """Test the string representation of a ResearchReport."""
        report = ResearchReport(
            id=5,
            session_id=10,
            report_content="Content",
            version=3
        )
        assert repr(report) == "<ResearchReport(id=5, session_id=10, version=3)>"

    def test_research_report_tablename(self):
        """Test the table name."""
        assert ResearchReport.__tablename__ == "research_reports"

    def test_research_report_multiple_versions(self):
        """Test creating multiple versions of reports."""
        versions = [1, 2, 3, 4, 5]

        for v in versions:
            report = ResearchReport(
                session_id=1,
                report_content=f"Version {v} content",
                version=v
            )
            assert report.version == v
            assert f"Version {v}" in report.report_content

    def test_research_report_with_complex_quality_evaluation(self):
        """Test quality_evaluation with complex nested structure."""
        quality_evaluation = {
            "evaluators": [
                {
                    "id": "eval_001",
                    "name": "Dr. Smith",
                    "scores": {"technical": 9, "clarity": 8, "impact": 9}
                },
                {
                    "id": "eval_002",
                    "name": "Dr. Jones",
                    "scores": {"technical": 8, "clarity": 9, "impact": 8}
                }
            ],
            "aggregate": {
                "mean": 8.5,
                "median": 9,
                "consensus": "approved"
            },
            "comments": ["Excellent work", "Minor revisions needed"]
        }

        report = ResearchReport(
            session_id=1,
            report_content="Complex eval test",
            quality_evaluation=quality_evaluation
        )

        assert len(report.quality_evaluation["evaluators"]) == 2
        assert report.quality_evaluation["evaluators"][0]["name"] == "Dr. Smith"
        assert report.quality_evaluation["aggregate"]["consensus"] == "approved"
        assert "Excellent work" in report.quality_evaluation["comments"]

    def test_research_report_markdown_content(self):
        """Test report with markdown formatted content."""
        markdown_content = """# Executive Summary

## Introduction
This research investigates...

## Methodology
- Data collection
- Analysis
- Results

## Findings
1. First finding
2. Second finding
3. Third finding

## Conclusion
In conclusion...
"""
        report = ResearchReport(
            session_id=1,
            report_content=markdown_content,
            executive_summary="A comprehensive study on..."
        )

        assert "# Executive Summary" in report.report_content
        assert "## Methodology" in report.report_content
        assert "- Data collection" in report.report_content
        assert "1. First finding" in report.report_content
