"""
Experiment models for LLM response evaluation and comparison.

This module defines models for storing evaluation experiments, including
experiments, prompts, answer pairs, evaluations, dimensions, and results.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


class Experiment(Base):
    """
    Model representing an evaluation experiment.

    An experiment compares two sets of answers (x vs y) using a judge LLM
    to evaluate them blindly across multiple dimensions.

    Attributes:
        id: Primary key.
        name: Human-readable name for the experiment.
        description_x: Description of answer set X (e.g., "GPT-4 answers").
        description_y: Description of answer set Y (e.g., "Claude answers").
        model_x: Model name used for answer set X.
        model_y: Model name used for answer set Y.
        judge_model: Model name used as the evaluation judge.
        eval_template_id: Foreign key to prompt template used for evaluation.
        created_at: Timestamp when experiment was created.
        updated_at: Timestamp when experiment was last updated.
    """

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description_x: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_y: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_x: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_y: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    judge_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    eval_template_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,  # Nullable until T06 integrates with templates
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    # Relationships
    dimensions: Mapped[list["ExperimentDimension"]] = relationship(
        "ExperimentDimension",
        back_populates="experiment",
        cascade="all, delete-orphan"
    )
    prompts: Mapped[list["ExperimentPrompt"]] = relationship(
        "ExperimentPrompt",
        back_populates="experiment",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Experiment."""
        return f"<Experiment(id={self.id}, name='{self.name}')>"


class ExperimentDimension(Base):
    """
    Model representing a scoring dimension for an experiment.

    Each experiment can have multiple custom dimensions (e.g., factual_correctness,
    completeness, coherence) used to evaluate answer pairs.

    Attributes:
        id: Primary key.
        experiment_id: Foreign key to parent experiment.
        dimension_name: Name of the dimension (e.g., "factual_correctness").
        display_order: Order in which dimension should be displayed.
    """

    __tablename__ = "experiment_dimensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dimension_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="dimensions"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "dimension_name",
            name="uq_experiment_dimension_name"
        ),
    )

    def __repr__(self) -> str:
        """String representation of ExperimentDimension."""
        return (
            f"<ExperimentDimension(id={self.id}, "
            f"experiment_id={self.experiment_id}, "
            f"dimension_name='{self.dimension_name}')>"
        )


class ExperimentPrompt(Base):
    """
    Model representing a test prompt within an experiment.

    Each experiment can have multiple prompts to evaluate different scenarios.

    Attributes:
        id: Primary key.
        experiment_id: Foreign key to parent experiment.
        prompt_text: The actual prompt/question text.
        created_at: Timestamp when prompt was added.
    """

    __tablename__ = "experiment_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="prompts"
    )
    answers: Mapped[list["ExperimentAnswer"]] = relationship(
        "ExperimentAnswer",
        back_populates="prompt",
        cascade="all, delete-orphan"
    )

    @property
    def updated_at(self) -> datetime:
        """Provide updated_at as created_at for API compatibility."""
        return self.created_at

    def __repr__(self) -> str:
        """String representation of ExperimentPrompt."""
        truncated = (
            self.prompt_text[:50] + "..."
            if len(self.prompt_text) > 50
            else self.prompt_text
        )
        return (
            f"<ExperimentPrompt(id={self.id}, "
            f"experiment_id={self.experiment_id}, "
            f"prompt='{truncated}')>"
        )


class ExperimentAnswer(Base):
    """
    Model representing a pair of answers to be evaluated.

    Each answer pair contains answer_x and answer_y, which are randomly
    mapped to answer_a and answer_b for blind evaluation.

    Attributes:
        id: Primary key.
        prompt_id: Foreign key to parent prompt.
        answer_x: First answer (from model X).
        answer_y: Second answer (from model Y).
        is_x_mapped_to_a: Random boolean indicating mapping.
            True: answer_x -> answer_a, answer_y -> answer_b
            False: answer_x -> answer_b, answer_y -> answer_a
        created_at: Timestamp when answer pair was added.
    """

    __tablename__ = "experiment_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiment_prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    answer_x: Mapped[str] = mapped_column(Text, nullable=False)
    answer_y: Mapped[str] = mapped_column(Text, nullable=False)
    is_x_mapped_to_a: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    # Relationships
    prompt: Mapped["ExperimentPrompt"] = relationship(
        "ExperimentPrompt",
        back_populates="answers"
    )
    evaluation: Mapped[Optional["ExperimentEvaluation"]] = relationship(
        "ExperimentEvaluation",
        back_populates="answer",
        cascade="all, delete-orphan",
        uselist=False  # One-to-one relationship
    )

    @property
    def answer_a(self) -> str:
        """Get answer mapped to position A (blind randomized)."""
        return self.answer_x if self.is_x_mapped_to_a else self.answer_y

    @property
    def answer_b(self) -> str:
        """Get answer mapped to position B (blind randomized)."""
        return self.answer_y if self.is_x_mapped_to_a else self.answer_x

    @property
    def updated_at(self) -> datetime:
        """Provide updated_at as created_at for API compatibility."""
        return self.created_at

    def __repr__(self) -> str:
        """String representation of ExperimentAnswer."""
        return (
            f"<ExperimentAnswer(id={self.id}, "
            f"prompt_id={self.prompt_id}, "
            f"is_x_mapped_to_a={self.is_x_mapped_to_a})>"
        )


class ExperimentEvaluation(Base):
    """
    Model representing an evaluation of an answer pair.

    Each evaluation includes an overall score and justification.
    Individual dimension scores are stored in ExperimentDimensionResult.

    Attributes:
        id: Primary key.
        answer_id: Foreign key to answer pair being evaluated (one-to-one).
        overall_score: Overall comparison score (-10 to 10).
            +10 = Answer X much better, 0 = tie, -10 = Answer Y much better.
        justification: Text explanation of the evaluation.
        created_at: Timestamp when evaluation was submitted.
    """

    __tablename__ = "experiment_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    answer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiment_answers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One evaluation per answer pair
        index=True
    )
    overall_score: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("overall_score >= -10 AND overall_score <= 10"),
        nullable=False
    )
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    # Relationships
    answer: Mapped["ExperimentAnswer"] = relationship(
        "ExperimentAnswer",
        back_populates="evaluation"
    )
    dimension_results: Mapped[list["ExperimentDimensionResult"]] = relationship(
        "ExperimentDimensionResult",
        back_populates="evaluation",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of ExperimentEvaluation."""
        return (
            f"<ExperimentEvaluation(id={self.id}, "
            f"answer_id={self.answer_id}, "
            f"overall_score={self.overall_score})>"
        )


class ExperimentDimensionResult(Base):
    """
    Model representing a score for a specific dimension in an evaluation.

    Each evaluation has multiple dimension results (one per dimension).
    Dimension names are denormalized for query efficiency.

    Attributes:
        id: Primary key.
        evaluation_id: Foreign key to parent evaluation.
        dimension_name: Name of the dimension being scored (denormalized).
        score: Comparison score for this dimension (-10 to 10).
    """

    __tablename__ = "experiment_dimension_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("experiment_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dimension_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("score >= -10 AND score <= 10"),
        nullable=False
    )

    # Relationships
    evaluation: Mapped["ExperimentEvaluation"] = relationship(
        "ExperimentEvaluation",
        back_populates="dimension_results"
    )

    def __repr__(self) -> str:
        """String representation of ExperimentDimensionResult."""
        return (
            f"<ExperimentDimensionResult(id={self.id}, "
            f"evaluation_id={self.evaluation_id}, "
            f"dimension_name='{self.dimension_name}', "
            f"score={self.score})>"
        )
