"""
Collections Router - Research organization and item grouping.
"""

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulcanlab.data.database import get_session
from vulcanlab.data.models.collection import Collection
from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.query import Query as QueryModel
from vulcanlab.data.models.result import Result
from vulcanlab.data.models.enums import CollectionItemType
from vulcanlab.collections import (
    create_collection as core_create_collection,
    get_collection as core_get_collection,
    list_collections as core_list_collections,
    update_collection as core_update_collection,
    delete_collection as core_delete_collection,
    add_item_to_collection as core_add_item,
    update_collection_item as core_update_item,
    delete_collection_item as core_delete_item,
    bulk_delete_collection_items as core_bulk_delete,
    EXCERPT_PATTERN,
    RESEARCH_RESULT_PATTERN,
    RESEARCH_QUERY_PATTERN,
)
from vulcanlab_api.schemas.collections import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionListResponse,
    CollectionItemCreate,
    CollectionItemUpdate,
    CollectionItemResponse,
    BulkDeleteRequest,
    CollectionItemMetadata,
    ExcerptMetadata,
    ResearchResultMetadata,
    ResearchQueryMetadata,
)

router = APIRouter()


# --- Collection Endpoints ---

@router.get(
    "/",
    response_model=CollectionListResponse,
    summary="List collections",
    description="Get a paginated list of collections with optional tag and search filtering.",
)
async def list_collections(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List collections with pagination and filtering."""
    try:
        skip = (page - 1) * page_size
        with get_session() as session:
            collections, total = core_list_collections(
                session=session,
                tag=tag,
                search=search,
                skip=skip,
                limit=page_size
            )
            
            return CollectionListResponse(
                collections=[CollectionResponse.model_validate(c) for c in collections],
                total=total,
                page=page,
                page_size=page_size
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.post(
    "/",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection",
    description="Create a new research collection.",
)
async def create_collection(collection_data: CollectionCreate):
    """Create a new collection."""
    try:
        with get_session() as session:
            collection = core_create_collection(
                session=session,
                name=collection_data.name,
                description=collection_data.description,
                tags=collection_data.tags
            )
            session.commit()
            
            # Re-fetch to get item_count (which will be 0)
            return CollectionResponse.model_validate(core_get_collection(session, collection.id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Get collection",
    description="Get a specific collection by ID, including its items.",
)
async def get_collection(collection_id: int):
    """Get a collection by ID."""
    try:
        with get_session() as session:
            collection = core_get_collection(session, collection_id)
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_id} not found"
                )
            
            # Populate items explicitly for the schema
            items_query = select(CollectionItem).where(CollectionItem.collection_id == collection_id).order_by(CollectionItem.order.asc())
            items = session.execute(items_query).scalars().all()
            
            response = CollectionResponse.model_validate(collection)
            response.items = [CollectionItemResponse.model_validate(i) for i in items]
            return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}"
        )


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Update collection",
    description="Update collection metadata (name, description, tags).",
)
async def update_collection(collection_id: int, update_data: CollectionUpdate):
    """Update a collection's metadata."""
    try:
        with get_session() as session:
            collection = core_update_collection(
                session=session,
                collection_id=collection_id,
                name=update_data.name,
                description=update_data.description,
                tags=update_data.tags
            )
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_id} not found"
                )
            session.commit()
            
            # Re-fetch to get computed item_count
            return CollectionResponse.model_validate(core_get_collection(session, collection.id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update collection: {str(e)}"
        )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection",
    description="Delete a collection and all its items (cascade).",
)
async def delete_collection(collection_id: int):
    """Delete a collection."""
    try:
        with get_session() as session:
            success = core_delete_collection(session, collection_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_id} not found"
                )
            session.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )


# --- Collection Item Endpoints ---

@router.post(
    "/{collection_id}/items",
    response_model=CollectionItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to collection",
    description="Add a new research item (excerpt, result, or query) to a collection.",
)
async def add_item(collection_id: int, item_data: CollectionItemCreate):
    """Add a new item to a collection."""
    try:
        with get_session() as session:
            # Check if collection exists
            collection = session.get(Collection, collection_id)
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_id} not found"
                )
            
            item = core_add_item(
                session=session,
                collection_id=collection_id,
                item_type=item_data.item_type,
                link=item_data.link,
                note=item_data.note,
                order=item_data.order
            )
            session.commit()
            session.refresh(item)
            return CollectionItemResponse.model_validate(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add item: {str(e)}"
        )


@router.patch(
    "/{collection_id}/items/{item_id}",
    response_model=CollectionItemResponse,
    summary="Update collection item",
    description="Update an item's note or display order.",
)
async def update_item(collection_id: int, item_id: int, update_data: CollectionItemUpdate):
    """Update a collection item."""
    try:
        with get_session() as session:
            item = core_update_item(
                session=session,
                item_id=item_id,
                note=update_data.note,
                order=update_data.order
            )
            if not item or item.collection_id != collection_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {item_id} not found in collection {collection_id}"
                )
            session.commit()
            session.refresh(item)
            return CollectionItemResponse.model_validate(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete(
    "/{collection_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection item",
    description="Remove a single item from a collection.",
)
async def delete_item(collection_id: int, item_id: int):
    """Delete an item from a collection."""
    try:
        with get_session() as session:
            item = session.get(CollectionItem, item_id)
            if not item or item.collection_id != collection_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {item_id} not found in collection {collection_id}"
                )
            
            session.delete(item)
            session.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )


@router.delete(
    "/{collection_id}/items",
    summary="Bulk delete collection items",
    description="Remove multiple items from a collection at once.",
)
async def bulk_delete_items(collection_id: int, request: BulkDeleteRequest):
    """Bulk delete items from a collection."""
    try:
        with get_session() as session:
            # We should ideally verify all item_ids belong to collection_id
            # but for simplicity we filter by both in the core logic or here
            stmt = select(CollectionItem.id).where(
                (CollectionItem.id.in_(request.item_ids)) & 
                (CollectionItem.collection_id == collection_id)
            )
            valid_ids = session.execute(stmt).scalars().all()
            
            count = core_bulk_delete(session, list(valid_ids))
            session.commit()
            return {"deleted_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete items: {str(e)}"
        )


# --- Metadata Enrichment ---

@router.get(
    "/{collection_id}/items/{item_id}/metadata",
    response_model=CollectionItemMetadata,
    summary="Get item metadata",
    description="Get enriched metadata for a collection item based on its source resource.",
)
async def get_item_metadata(collection_id: int, item_id: int):
    """Get enriched metadata for an item."""
    try:
        with get_session() as session:
            item = session.get(CollectionItem, item_id)
            if not item or item.collection_id != collection_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {item_id} not found in collection {collection_id}"
                )
            
            if item.item_type == CollectionItemType.EXCERPT:
                match = re.match(EXCERPT_PATTERN, item.link)
                if not match:
                    raise HTTPException(status_code=400, detail="Invalid excerpt link format")
                
                work_id, start_line, end_line = map(int, match.groups())
                
                work = session.get(Work, work_id)
                if not work:
                    return ExcerptMetadata(
                        work_id=work_id,
                        title="Source Deleted",
                        excerpt_preview="The original work has been removed."
                    )
                
                # Query chunk for content and breadcrumbs
                # We try to find the chunk that matches the start_line
                chunk_query = select(Chunk).where(
                    (Chunk.work_id == work_id) & 
                    (Chunk.start_line == start_line)
                )
                chunk = session.execute(chunk_query).scalars().first()
                
                content = chunk.content if chunk else "Content not found"
                # Simple word-based truncation
                words = content.split()
                preview = " ".join(words[:75]) + ("..." if len(words) > 75 else "")
                
                return ExcerptMetadata(
                    work_id=work_id,
                    title=work.title,
                    authors=work.authors,
                    year=work.year,
                    heading_breadcrumbs=chunk.heading_breadcrumbs if chunk else None,
                    excerpt_preview=preview
                )
                
            elif item.item_type == CollectionItemType.RESEARCH_RESULT:
                match = re.match(RESEARCH_RESULT_PATTERN, item.link)
                if not match:
                    raise HTTPException(status_code=400, detail="Invalid research result link format")
                
                query_id, result_id = map(int, match.groups())
                
                query_rec = session.get(QueryModel, query_id)
                result_rec = session.get(Result, result_id)
                
                if not query_rec or not result_rec:
                    return ResearchResultMetadata(
                        query_id=query_id,
                        result_id=result_id,
                        query_text="Source Deleted",
                        content_preview="The original query or result has been removed."
                    )
                
                words = result_rec.response_text.split()
                preview = " ".join(words[:75]) + ("..." if len(words) > 75 else "")
                
                return ResearchResultMetadata(
                    query_id=query_id,
                    result_id=result_id,
                    query_text=query_rec.original_query,
                    content_preview=preview
                )
                
            elif item.item_type == CollectionItemType.RESEARCH_QUERY:
                match = re.match(RESEARCH_QUERY_PATTERN, item.link)
                if not match:
                    raise HTTPException(status_code=400, detail="Invalid research query link format")
                
                query_id = int(match.groups()[0])
                query_rec = session.get(QueryModel, query_id)
                
                if not query_rec:
                    return ResearchQueryMetadata(
                        query_id=query_id,
                        query_text="Source Deleted"
                    )
                
                return ResearchQueryMetadata(
                    query_id=query_id,
                    query_text=query_rec.original_query
                )
                
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported item type: {item.item_type}")
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metadata: {str(e)}"
        )
