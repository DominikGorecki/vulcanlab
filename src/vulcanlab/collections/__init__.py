"""
Core CRUD operations for collections and collection items.
"""

import re
from typing import List, Optional, Tuple
from decimal import Decimal

from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session

from ..data.models.collection import Collection
from ..data.models.collection_item import CollectionItem
from ..data.models.enums import CollectionItemType

# Link validation patterns as constants
EXCERPT_PATTERN = r'^/search/result/(\d+)/(\d+)/(\d+)$'
RESEARCH_RESULT_PATTERN = r'^/rag/(\d+)/results/(\d+)$'
RESEARCH_QUERY_PATTERN = r'^/rag/(\d+)$'


def validate_item_link(item_type: CollectionItemType, link: str) -> bool:
    """
    Validate that a link matches the expected pattern for its item type.

    Args:
        item_type: The type of item (excerpt, research_result, research_query).
        link: The link to validate.

    Returns:
        True if the link is valid, False otherwise.
    """
    if item_type == CollectionItemType.EXCERPT:
        return bool(re.match(EXCERPT_PATTERN, link))
    elif item_type == CollectionItemType.RESEARCH_RESULT:
        return bool(re.match(RESEARCH_RESULT_PATTERN, link))
    elif item_type == CollectionItemType.RESEARCH_QUERY:
        return bool(re.match(RESEARCH_QUERY_PATTERN, link))
    return False


# --- Collection CRUD ---

def create_collection(
    session: Session,
    name: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Collection:
    """Create a new collection."""
    collection = Collection(
        name=name,
        description=description,
        tags=tags or []
    )
    session.add(collection)
    session.flush()  # To get the ID
    return collection


def get_collection(session: Session, collection_id: int) -> Optional[Collection]:
    """
    Get a collection by ID, including item_count.
    """
    count_subquery = (
        select(func.count(CollectionItem.id))
        .where(CollectionItem.collection_id == Collection.id)
        .scalar_subquery()
        .label("item_count")
    )

    query = select(Collection, count_subquery).where(Collection.id == collection_id)
    result = session.execute(query).first()
    
    if not result:
        return None
        
    collection, item_count = result
    collection.item_count = item_count or 0
    return collection


def list_collections(
    session: Session,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Collection], int]:
    """
    List collections with optional tag filtering, search, and pagination.
    
    Includes item_count for each collection.
    
    Returns:
        Tuple of (list of collections, total count).
    """
    # Subquery for item count
    count_subquery = (
        select(func.count(CollectionItem.id))
        .where(CollectionItem.collection_id == Collection.id)
        .scalar_subquery()
        .label("item_count")
    )

    query = select(Collection, count_subquery)
    count_query = select(func.count()).select_from(Collection)

    if tag:
        # JSONB containment operator ?
        query = query.where(Collection.tags.contains([tag]))
        count_query = count_query.where(Collection.tags.contains([tag]))

    if search:
        search_filter = (Collection.name.ilike(f"%{search}%")) | (Collection.description.ilike(f"%{search}%"))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = session.execute(count_query).scalar_one()
    
    # Order by created_at desc for recent first
    query = query.order_by(Collection.created_at.desc()).offset(skip).limit(limit)
    
    results = session.execute(query).all()
    
    collections = []
    for collection, item_count in results:
        collection.item_count = item_count or 0
        collections.append(collection)
    
    return collections, total


def update_collection(
    session: Session,
    collection_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Optional[Collection]:
    """Update an existing collection."""
    collection = get_collection(session, collection_id)
    if not collection:
        return None

    if name is not None:
        collection.name = name
    if description is not None:
        collection.description = description
    if tags is not None:
        collection.tags = tags

    return collection


def delete_collection(session: Session, collection_id: int) -> bool:
    """Delete a collection. Associated items are deleted via CASCADE."""
    collection = get_collection(session, collection_id)
    if not collection:
        return False
    
    session.delete(collection)
    return True


# --- CollectionItem CRUD ---

def add_item_to_collection(
    session: Session,
    collection_id: int,
    item_type: CollectionItemType,
    link: str,
    note: Optional[str] = None,
    order: Optional[Decimal] = None
) -> CollectionItem:
    """
    Add a new item to a collection.
    
    Raises:
        ValueError: If the link is invalid for the item_type.
    """
    if not validate_item_link(item_type, link):
        raise ValueError(f"Invalid link format for item type {item_type}: {link}")

    # If order is not provided, append to the end
    if order is None:
        max_order_query = select(func.max(CollectionItem.order)).where(CollectionItem.collection_id == collection_id)
        current_max = session.execute(max_order_query).scalar()
        
        if current_max is None:
            order = Decimal('1')
        else:
            # Increment by 1 from the ceiling of the current max to ensure no decimals
            # e.g., 12.8 -> ceil(12.8) + 1 = 13 + 1 = 14
            import math
            order = Decimal(str(math.ceil(float(current_max)) + 1))

    item = CollectionItem(
        collection_id=collection_id,
        item_type=item_type,
        link=link,
        note=note,
        order=order
    )
    session.add(item)
    session.flush()
    return item


def update_collection_item(
    session: Session,
    item_id: int,
    note: Optional[str] = None,
    order: Optional[Decimal] = None
) -> Optional[CollectionItem]:
    """Update a collection item's note or order."""
    item = session.get(CollectionItem, item_id)
    if not item:
        return None

    if note is not None:
        item.note = note
    if order is not None:
        item.order = order

    return item


def delete_collection_item(session: Session, item_id: int) -> bool:
    """Delete a single collection item."""
    item = session.get(CollectionItem, item_id)
    if not item:
        return False
    
    session.delete(item)
    return True


def bulk_delete_collection_items(session: Session, item_ids: List[int]) -> int:
    """Delete multiple collection items by ID."""
    if not item_ids:
        return 0
    
    stmt = delete(CollectionItem).where(CollectionItem.id.in_(item_ids))
    result = session.execute(stmt)
    return result.rowcount

