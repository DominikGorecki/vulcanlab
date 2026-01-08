"""
Pydantic schemas for Collections and Collection Items.
"""

from datetime import datetime
from typing import List, Optional, Union, Literal
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from vulcanlab.data.models.enums import CollectionItemType


# --- Collection Item Schemas ---

class CollectionItemBase(BaseModel):
    """Base schema for collection item data."""
    item_type: CollectionItemType = Field(..., description="Type of the item")
    link: str = Field(..., description="Relative internal link to the resource")
    note: Optional[str] = Field(None, description="Optional note about the item")
    order: Decimal = Field(default=Decimal('0'), description="Numeric order within the collection")


class CollectionItemCreate(BaseModel):
    """Schema for adding an item to a collection."""
    item_type: CollectionItemType = Field(..., description="Type of the item")
    link: str = Field(..., description="Relative internal link to the resource")
    note: Optional[str] = Field(None, description="Optional note about the item")
    order: Optional[Decimal] = Field(None, description="Numeric order within the collection. If not provided, it will be auto-calculated.")


class CollectionItemUpdate(BaseModel):
    """Schema for updating a collection item."""
    note: Optional[str] = Field(None, description="Optional note about the item")
    order: Optional[Decimal] = Field(None, description="Numeric order within the collection")


class CollectionItemResponse(CollectionItemBase):
    """Schema for a collection item in API responses."""
    id: int
    collection_id: int
    date_added: datetime
    last_modified: datetime

    model_config = ConfigDict(from_attributes=True)


class BulkDeleteRequest(BaseModel):
    """Schema for bulk deleting collection items."""
    item_ids: List[int] = Field(..., description="List of item IDs to delete")


# --- Metadata Enrichment Schemas ---

class ExcerptMetadata(BaseModel):
    """Metadata for an excerpt item."""
    type: Literal["excerpt"] = "excerpt"
    work_id: int
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    heading_breadcrumbs: Optional[str] = None
    excerpt_preview: str


class ResearchResultMetadata(BaseModel):
    """Metadata for a research result item."""
    type: Literal["research_result"] = "research_result"
    query_id: int
    result_id: int
    query_text: str
    content_preview: str


class ResearchQueryMetadata(BaseModel):
    """Metadata for a research query item."""
    type: Literal["research_query"] = "research_query"
    query_id: int
    query_text: str


CollectionItemMetadata = Union[ExcerptMetadata, ResearchResultMetadata, ResearchQueryMetadata]


# --- Collection Schemas ---

class CollectionBase(BaseModel):
    """Base schema for collection data."""
    name: str = Field(..., description="Name of the collection", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the collection")
    tags: List[str] = Field(default_factory=list, description="List of tags for the collection")


class CollectionCreate(CollectionBase):
    """Schema for creating a new collection."""
    pass


class CollectionUpdate(BaseModel):
    """Schema for updating an existing collection."""
    name: Optional[str] = Field(None, description="Name of the collection", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the collection")
    tags: Optional[List[str]] = Field(None, description="List of tags for the collection")


class CollectionResponse(CollectionBase):
    """Schema for a collection in API responses."""
    id: int
    item_count: int = Field(0, description="Number of items in the collection")
    items: Optional[List[CollectionItemResponse]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionListResponse(BaseModel):
    """Schema for a paginated list of collections."""
    collections: List[CollectionResponse]
    total: int
    page: int
    page_size: int
