"""
Unit tests for SummarizeSettings model.
Implementation of Ticket: work-summarization.T03
"""

import pytest
from vulcanlab.data.models.summarize_settings import SummarizeSettings


class TestSummarizeSettingsCreation:
    """Test basic model creation and default values."""

    def test_create_settings_basic(self):
        """Test creating SummarizeSettings with specified fields."""
        settings = SummarizeSettings(
            h1_always_summarize=False,
            h2_top_percent=50,
            h3_salience_threshold=0.6,
            h4_salience_threshold=0.8,
            definition_density_weight=0.4,
            list_density_weight=0.1,
            keyphrase_novelty_weight=0.1,
            location_prior_weight=0.2,
            heading_depth_weight=0.2
        )

        assert settings.h1_always_summarize is False
        assert settings.h2_top_percent == 50
        assert settings.h3_salience_threshold == 0.6
        assert settings.h4_salience_threshold == 0.8
        assert settings.definition_density_weight == 0.4
        assert settings.list_density_weight == 0.1
        assert settings.keyphrase_novelty_weight == 0.1
        assert settings.location_prior_weight == 0.2
        assert settings.heading_depth_weight == 0.2

    def test_summarize_settings_defaults(self):
        """Test that SummarizeSettings has correct default values."""
        settings = SummarizeSettings()

        # Defaults matching migration 029 and T03 spec
        assert settings.h1_always_summarize is True
        assert settings.h2_top_percent == 100
        assert settings.h3_salience_threshold == 0.5
        assert settings.h4_salience_threshold == 0.7
        assert settings.definition_density_weight == 0.3
        assert settings.list_density_weight == 0.2
        assert settings.keyphrase_novelty_weight == 0.2
        assert settings.location_prior_weight == 0.15
        assert settings.heading_depth_weight == 0.15

    def test_repr(self):
        """Test __repr__ method."""
        settings = SummarizeSettings(id=1)
        assert "<SummarizeSettings(id=1)>" == repr(settings)
