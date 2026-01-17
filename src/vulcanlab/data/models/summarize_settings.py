"""
SummarizeSettings model for storing global summarization configuration.
"""

from datetime import datetime

from sqlalchemy import Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SummarizeSettings(Base):
    """
    Model representing global configuration for the work summarization process.

    Attributes:
        id: Primary key.
        min_heading_word_count: Minimum words in a heading section to trigger summarization.
        max_total_heading_words: Maximum total words allowed in combined heading content.
        dense_top_k: Number of chunks to retrieve via dense search.
        lexical_top_k: Number of chunks to retrieve via lexical search.
        rrf_k: RRF constant for rank fusion.
        rrf_top_k: Top K results to keep after RRF fusion.
        mmr_lambda: Diversity parameter for MMR (0.0 to 1.0).
        mmr_top_n: Final number of chunks to select via MMR.
        max_llm_calls: Maximum number of LLM calls per summarization task.
        max_tokens_per_call: Maximum tokens allowed per LLM call.
        tokens_per_word: Conversion factor for estimating tokens from words.
        h1_h2_min_chunks: Minimum chunks required for H1/H2 levels.
        h3_min_chunks: Minimum chunks required for H3 level.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "summarize_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    min_heading_word_count: Mapped[int] = mapped_column(Integer, default=500)
    max_total_heading_words: Mapped[int] = mapped_column(Integer, default=2500)
    dense_top_k: Mapped[int] = mapped_column(Integer, default=7)
    lexical_top_k: Mapped[int] = mapped_column(Integer, default=7)
    rrf_k: Mapped[int] = mapped_column(Integer, default=60)
    rrf_top_k: Mapped[int] = mapped_column(Integer, default=7)
    mmr_lambda: Mapped[float] = mapped_column(Float, default=0.7)
    mmr_top_n: Mapped[int] = mapped_column(Integer, default=5)
    max_llm_calls: Mapped[int] = mapped_column(Integer, default=5)
    max_tokens_per_call: Mapped[int] = mapped_column(Integer, default=15000)
    tokens_per_word: Mapped[float] = mapped_column(Float, default=0.75)
    h1_h2_min_chunks: Mapped[int] = mapped_column(Integer, default=2)
    h3_min_chunks: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<SummarizeSettings(id={self.id})>"
