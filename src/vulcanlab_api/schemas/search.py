"""
Pydantic schemas for search operations API.

Schemas for lexical, dense, and hybrid search endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class SearchResult(BaseModel):
    """Single search result with content and metadata."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "content_preview": "Memory systems in the brain include working memory, episodic memory...",
                "breadcrumb": "Chapter 3 > Cognitive Processes > Memory Systems",
                "level": "H3",
                "work_id": 5,
                "work_title": "Cognitive Psychology: A Student's Handbook",
                "work_authors": "Eysenck, M. W., & Keane, M. T.",
                "work_year": 2015,
                "start_line": 142,
                "end_line": 158,
                "rank_score": 0.87654
            }
        }
    )

    id: int = Field(..., description="Chunk ID", gt=0)
    content_preview: str = Field(..., description="Content preview (100 words)")
    breadcrumb: str = Field(..., description="Hierarchical breadcrumb trail")
    level: str = Field(..., description="Chunk level (H1-H5, sentence, chunk)")
    work_id: int = Field(..., description="Work ID", gt=0)
    work_title: str = Field(..., description="Work title")
    work_authors: Optional[str] = Field(None, description="Work authors")
    work_year: Optional[int] = Field(None, description="Publication year")
    start_line: int = Field(..., description="Start line number", ge=0)
    end_line: int = Field(..., description="End line number", ge=0)
    rank_score: float = Field(..., description="Relevance score (ts_rank)", ge=0.0)


class PaginationInfo(BaseModel):
    """Pagination metadata for search results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20,
                "total_results": 157,
                "has_next": True,
                "has_prev": False
            }
        }
    )

    page: int = Field(..., description="Current page number", ge=1)
    page_size: int = Field(..., description="Results per page", ge=1)
    total_results: int = Field(..., description="Total matching results", ge=0)
    has_next: bool = Field(..., description="Whether next page exists")
    has_prev: bool = Field(..., description="Whether previous page exists")


class LexicalSearchResponse(BaseModel):
    """Response for lexical search endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "id": 123,
                        "content_preview": "Memory systems in the brain...",
                        "breadcrumb": "Chapter 3 > Memory Systems",
                        "level": "H2",
                        "work_id": 5,
                        "work_title": "Cognitive Psychology",
                        "work_authors": "Eysenck & Keane",
                        "work_year": 2015,
                        "start_line": 142,
                        "end_line": 158,
                        "rank_score": 0.87654
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_results": 157,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }
    )

    results: list[SearchResult] = Field(..., description="List of search results")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")


class DenseSearchResult(BaseModel):
    """Single dense search result with similarity score."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "content_preview": "Memory systems in the brain include working memory, episodic memory...",
                "breadcrumb": "Chapter 3 > Cognitive Processes > Memory Systems",
                "level": "H3",
                "work_id": 5,
                "work_title": "Cognitive Psychology: A Student's Handbook",
                "work_authors": "Eysenck, M. W., & Keane, M. T.",
                "work_year": 2015,
                "start_line": 142,
                "end_line": 158,
                "similarity_score": 0.87654
            }
        }
    )

    id: int = Field(..., description="Chunk ID", gt=0)
    content_preview: str = Field(..., description="Content preview (100 words)")
    breadcrumb: str = Field(..., description="Hierarchical breadcrumb trail")
    level: str = Field(..., description="Chunk level (H1-H5, sentence, chunk)")
    work_id: int = Field(..., description="Work ID", gt=0)
    work_title: str = Field(..., description="Work title")
    work_authors: Optional[str] = Field(None, description="Work authors")
    work_year: Optional[int] = Field(None, description="Publication year")
    start_line: int = Field(..., description="Start line number", ge=0)
    end_line: int = Field(..., description="End line number", ge=0)
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)", ge=0.0, le=1.0)


class DenseSearchResponse(BaseModel):
    """Response for dense search endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "id": 123,
                        "content_preview": "Memory systems in the brain...",
                        "breadcrumb": "Chapter 3 > Memory Systems",
                        "level": "H2",
                        "work_id": 5,
                        "work_title": "Cognitive Psychology",
                        "work_authors": "Eysenck & Keane",
                        "work_year": 2015,
                        "start_line": 142,
                        "end_line": 158,
                        "similarity_score": 0.87654
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_results": 157,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }
    )

    results: list[DenseSearchResult] = Field(..., description="List of search results")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")


class RRFStats(BaseModel):
    """Metadata for Reciprocal Rank Fusion (RRF)."""

    dense_candidates: int = Field(..., description="Number of dense search candidates")
    lexical_candidates: int = Field(..., description="Number of lexical search candidates")
    fused_count: int = Field(..., description="Total unique results after fusion")
    rrf_k: int = Field(..., description="RRF constant k used for fusion")


class HybridSearchResult(BaseModel):
    """Single hybrid search result with RRF score and component ranks."""

    id: int = Field(..., description="Chunk ID", gt=0)
    content_preview: str = Field(..., description="Content preview (100 words)")
    breadcrumb: str = Field(..., description="Hierarchical breadcrumb trail")
    level: str = Field(..., description="Chunk level (H1-H5, sentence, chunk)")
    work_id: int = Field(..., description="Work ID", gt=0)
    work_title: str = Field(..., description="Work title")
    work_authors: Optional[str] = Field(None, description="Work authors")
    work_year: Optional[int] = Field(None, description="Publication year")
    start_line: int = Field(..., description="Start line number", ge=0)
    end_line: int = Field(..., description="End line number", ge=0)
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion score", ge=0.0)
    dense_rank: Optional[int] = Field(None, description="Rank in dense search results (1-based)")
    lexical_rank: Optional[int] = Field(None, description="Rank in lexical search results (1-based)")


class HybridSearchResponse(BaseModel):
    """Response for hybrid search endpoint."""

    results: list[HybridSearchResult] = Field(..., description="List of fused search results")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")
    rrf_stats: RRFStats = Field(..., description="RRF fusion metadata")
