"""
Summarize settings model for salience-based node selection.

This module defines the SummarizeSettings model for storing configuration
parameters used in the work summarization process.
"""

from datetime import datetime
from sqlalchemy import Integer, Float, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SummarizeSettings(Base):
    """
    Model representing configuration for salience-based summarization.

    Attributes:
        id: Primary key.
        h1_always_summarize: Whether to always deep-summarize H1 nodes.
        h2_top_percent: Top N% of H2 nodes by salience to summarize.
        h3_salience_threshold: Minimum salience for H3 nodes.
        h4_salience_threshold: Minimum salience for H4+ nodes.
        definition_density_weight: Weight for definition density in salience.
        list_density_weight: Weight for list density in salience.
        keyphrase_novelty_weight: Weight for keyphrase novelty in salience.
        location_prior_weight: Weight for intro/conclusion boost in salience.
        heading_depth_weight: Weight for heading depth in salience.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "summarize_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    h1_always_summarize: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    h2_top_percent: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    h3_salience_threshold: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    h4_salience_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    definition_density_weight: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    list_density_weight: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    keyphrase_novelty_weight: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    location_prior_weight: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    heading_depth_weight: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)

    def __init__(self, **kwargs):
        """Initialize with defaults for Python-side usage."""
        kwargs.setdefault('h1_always_summarize', True)
        kwargs.setdefault('h2_top_percent', 100)
        kwargs.setdefault('h3_salience_threshold', 0.5)
        kwargs.setdefault('h4_salience_threshold', 0.7)
        kwargs.setdefault('definition_density_weight', 0.3)
        kwargs.setdefault('list_density_weight', 0.2)
        kwargs.setdefault('keyphrase_novelty_weight', 0.2)
        kwargs.setdefault('location_prior_weight', 0.15)
        kwargs.setdefault('heading_depth_weight', 0.15)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<SummarizeSettings(id={self.id})>"
