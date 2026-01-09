"""
CollectionItem model for individual items within a collection.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Numeric, func, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import CollectionItemType


class CollectionItem(Base):
    """
    Model representing an item within a collection.

    Attributes:
        id: Primary key.
        collection_id: Foreign key to collections table.
        item_type: Type of the item (excerpt, research_result, research_query).
        link: Relative internal link to the resource.
        note: Optional note about the item.
        order: Numeric order within the collection.
        date_added: Timestamp when record was created.
        last_modified: Timestamp when record was last updated.
    """

    __tablename__ = "collection_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    item_type: Mapped[CollectionItemType] = mapped_column(
        SqlEnum(
            CollectionItemType, 
            name="collection_item_type", 
            native_enum=True,
            values_callable=lambda x: [e.value for e in x]
        ), 
        nullable=False, 
        index=True
    )
    link: Mapped[str] = mapped_column(String(1000), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal('0'), server_default='0', index=True)
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    collection = relationship("Collection", back_populates="items")

    def __repr__(self) -> str:
        # If it's an enum, use .value for cleaner representation
        type_str = self.item_type.value if hasattr(self.item_type, 'value') else self.item_type
        return f"<CollectionItem(id={self.id}, collection_id={self.collection_id}, item_type='{type_str}')>"

