"""HeadingModifications model for storing large document heading changes."""

from sqlalchemy import Column, Integer, Text, Boolean, Enum as SQLEnum, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from ..database import Base
from .enums import ModificationAction


class HeadingModification(Base):
    """Stores heading-level modifications for Step 2B (large documents)."""

    __tablename__ = 'heading_modifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    line_number = Column(Integer, nullable=False)
    original_heading = Column(Text, nullable=False)
    modified_heading = Column(Text, nullable=True)  # Null if action=REMOVE
    action = Column(SQLEnum(ModificationAction, name='modification_action', values_callable=lambda x: [e.value for e in x]), nullable=False)
    vectorize_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_heading_modifications_work_id', 'work_id'),
        Index('ix_heading_modifications_work_line', 'work_id', 'line_number'),
    )

    def __repr__(self):
        return f"<HeadingModification(id={self.id}, work_id={self.work_id}, line={self.line_number}, action={self.action.value})>"
