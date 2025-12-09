"""IO File model for tracking input and output files."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from ..database import Base


class FileType(str, enum.Enum):
    """File type enumeration."""

    INPUT = "input"
    TO_CONVERT = "to_convert"


class IOFile(Base):
    """Model for tracking files in input and output directories.

    This table keeps track of all files found during directory scans,
    allowing efficient comparison and avoiding repeated hash computations.
    """

    __tablename__ = "io_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String, nullable=False, index=True)
    file_type: Mapped[FileType] = mapped_column(SQLEnum(FileType), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<IOFile(id={self.id}, filename='{self.filename}', type='{self.file_type.value}')>"
