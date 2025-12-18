"""
Pydantic schemas for chunk operations API.

Schemas for chunk search, deletion, and descendant preview endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field


class ChunkSearchResult(BaseModel):
    """Single chunk result from search."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "content_preview": "This is a preview of the chunk content truncated to 100 characters...",
                "heading_breadcrumbs": "Chapter 1 > Introduction > Overview",
                "level": "H3",
                "work_id": 5,
                "start_line": 42,
                "end_line": 58,
            }
        }
    )

    id: int = Field(
        ...,
        description="Chunk ID",
        gt=0,
    )
    content_preview: str = Field(
        ...,
        description="Truncated content preview (first 100 characters)",
        max_length=100,
    )
    heading_breadcrumbs: str | None = Field(
        default=None,
        description="Breadcrumb trail of section headings (e.g., 'H1 > H2 > H3')",
    )
    level: str = Field(
        ...,
        description="Hierarchy level (H1, H2, H3, H4, H5, sentence, chunk)",
    )
    work_id: int = Field(
        ...,
        description="ID of the work this chunk belongs to",
        gt=0,
    )
    start_line: int = Field(
        ...,
        description="Line number where chunk begins in markdown",
        ge=0,
    )
    end_line: int = Field(
        ...,
        description="Line number where chunk ends in markdown",
        ge=0,
    )


class PaginationInfo(BaseModel):
    """Pagination metadata."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 25,
                "total_results": 100,
                "has_next": True,
                "has_prev": False,
            }
        }
    )

    page: int = Field(
        ...,
        description="Current page number",
        ge=1,
    )
    page_size: int = Field(
        ...,
        description="Number of results per page",
        ge=1,
    )
    total_results: int = Field(
        ...,
        description="Total number of matching results",
        ge=0,
    )
    has_next: bool = Field(
        ...,
        description="Whether there is a next page",
    )
    has_prev: bool = Field(
        ...,
        description="Whether there is a previous page",
    )


class ChunkSearchResponse(BaseModel):
    """Response for chunk search endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "id": 123,
                        "content_preview": "This is a preview...",
                        "heading_breadcrumbs": "Chapter 1 > Introduction",
                        "level": "H2",
                        "work_id": 5,
                        "start_line": 42,
                        "end_line": 58,
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 25,
                    "total_results": 100,
                    "has_next": True,
                    "has_prev": False,
                },
            }
        }
    )

    results: list[ChunkSearchResult] = Field(
        ...,
        description="List of matching chunks",
    )
    pagination: PaginationInfo = Field(
        ...,
        description="Pagination information",
    )


class DescendantInfo(BaseModel):
    """Information about a chunk descendant."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 456,
                "level": "H3",
                "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1",
            }
        }
    )

    id: int = Field(
        ...,
        description="Chunk ID",
        gt=0,
    )
    level: str = Field(
        ...,
        description="Hierarchy level (H1, H2, H3, H4, H5, sentence, chunk)",
    )
    heading_breadcrumbs: str | None = Field(
        default=None,
        description="Breadcrumb trail of section headings",
    )


class DescendantsResponse(BaseModel):
    """Response for descendants preview endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "descendants": [
                    {
                        "id": 456,
                        "level": "H3",
                        "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1",
                    },
                    {
                        "id": 457,
                        "level": "H4",
                        "heading_breadcrumbs": "Chapter 1 > Section 1.1 > Subsection 1.1.1 > Detail",
                    },
                ],
                "total_count": 2,
            }
        }
    )

    descendants: list[DescendantInfo] = Field(
        ...,
        description="List of descendant chunks",
    )
    total_count: int = Field(
        ...,
        description="Total number of descendants",
        ge=0,
    )


class ChunkDeleteResponse(BaseModel):
    """Response for chunk deletion endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deleted_chunk_id": 123,
                "descendants_deleted": [456, 457, 458],
                "total_deleted": 4,
            }
        }
    )

    deleted_chunk_id: int = Field(
        ...,
        description="ID of the deleted chunk",
        gt=0,
    )
    descendants_deleted: list[int] = Field(
        ...,
        description="IDs of descendant chunks that were also deleted",
    )
    total_deleted: int = Field(
        ...,
        description="Total number of chunks deleted (parent + descendants)",
        ge=1,
    )
