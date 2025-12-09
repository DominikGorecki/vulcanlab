"""
Pydantic schemas for Corpus router.

The corpus represents works that have completed both content and heading chunking,
making them ready for vectorization and RAG operations.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ChunkVectorStats(BaseModel):
    """Statistics on chunk vectorization status."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "no_vec": 150,
                "to_vec": 50,
                "vec": 200,
                "vec_err": 5
            }
        }
    )

    no_vec: int = Field(
        ...,
        ge=0,
        description="Number of chunks not yet marked for vectorization"
    )
    to_vec: int = Field(
        ...,
        ge=0,
        description="Number of chunks marked for vectorization but not yet processed"
    )
    vec: int = Field(
        ...,
        ge=0,
        description="Number of chunks successfully vectorized"
    )
    vec_err: int = Field(
        ...,
        ge=0,
        description="Number of chunks that failed vectorization"
    )


class CorpusStatsResponse(BaseModel):
    """Response containing corpus statistics."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_works": 12,
                "chunk_stats": {
                    "no_vec": 150,
                    "to_vec": 50,
                    "vec": 200,
                    "vec_err": 5
                }
            }
        }
    )

    total_works: int = Field(
        ...,
        ge=0,
        description="Total number of works in the corpus"
    )
    chunk_stats: ChunkVectorStats = Field(
        ...,
        description="Breakdown of chunk counts by vectorization status"
    )


class CorpusWorkListItem(BaseModel):
    """A single work in the corpus list."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 5,
                "title": "Cognitive Psychology: A Student's Handbook",
                "authors": "Eysenck, Michael W.; Keane, Mark T.",
                "sanitized_path": "c:\\output\\eysenck_cognitive.sanitized.md"
            }
        }
    )

    id: int = Field(..., description="Work ID")
    title: str = Field(..., description="Work title")
    authors: Optional[str] = Field(None, description="Author(s)")
    sanitized_path: str = Field(..., description="Path to sanitized markdown file")


class CorpusWorksResponse(BaseModel):
    """Response containing list of corpus works."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "works": [
                    {
                        "id": 5,
                        "title": "Cognitive Psychology: A Student's Handbook",
                        "authors": "Eysenck, Michael W.; Keane, Mark T.",
                        "sanitized_path": "c:\\output\\eysenck_cognitive.sanitized.md"
                    }
                ],
                "total": 1
            }
        }
    )

    works: list[CorpusWorkListItem] = Field(
        ...,
        description="List of works in the corpus"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of works"
    )


class CorpusWorkDetailResponse(BaseModel):
    """Detailed information about a corpus work."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 5,
                "title": "Cognitive Psychology: A Student's Handbook",
                "authors": "Eysenck, Michael W.; Keane, Mark T.",
                "year": 2020,
                "publisher": "Psychology Press",
                "sanitized_path": "c:\\output\\eysenck_cognitive.sanitized.md",
                "sanitized_hash": "a3b4c5d6e7f8g9h0..."
            }
        }
    )

    id: int = Field(..., description="Work ID")
    title: str = Field(..., description="Work title")
    authors: Optional[str] = Field(None, description="Author(s)")
    year: Optional[int] = Field(None, description="Publication year")
    publisher: Optional[str] = Field(None, description="Publisher")
    sanitized_path: str = Field(..., description="Path to sanitized markdown file")
    sanitized_hash: str = Field(..., description="SHA-256 hash of sanitized file")


class SanitizedContentResponse(BaseModel):
    """Response containing sanitized markdown content."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "# Chapter 1: Introduction\n\nCognitive psychology is...",
                "filename": "eysenck_cognitive.sanitized.md",
                "work_id": 5,
                "work_title": "Cognitive Psychology: A Student's Handbook"
            }
        }
    )

    content: str = Field(..., description="Sanitized markdown file content")
    filename: str = Field(..., description="Filename of the sanitized file")
    work_id: int = Field(..., description="Work ID")
    work_title: str = Field(..., description="Work title")
