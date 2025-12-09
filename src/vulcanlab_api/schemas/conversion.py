"""
Pydantic schemas for Conversion router.
"""

from pydantic import BaseModel, ConfigDict, Field


class IOFolderDataResponse(BaseModel):
    """Response containing input and processed file data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "input_files": ["cognitive_psychology.pdf", "memory_handbook.pdf"],
                "processed_files": [
                    "learning_theory|42|.pdf|.style.md|.hier.md|.toc_titles.md",
                    "perception_basics|43|.pdf|.style.md|.toc_titles.md"
                ],
            }
        }
    )

    input_files: list[str] = Field(
        default_factory=list,
        description="List of unprocessed input files",
    )
    processed_files: list[str] = Field(
        default_factory=list,
        description="List of processed files in pipe-separated format: basename|id|variant1|variant2|...",
    )


class ConvertFileRequest(BaseModel):
    """Request to convert a file."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "cognitive_psychology.pdf",
            }
        }
    )

    filename: str = Field(
        ...,
        description="Name of the file to convert (must exist in input directory)",
    )


class ConvertFileResponse(BaseModel):
    """Response after file conversion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Conversion completed successfully",
                "input_file": "cognitive_psychology.pdf",
                "output_files": [
                    "cognitive_psychology.pdf",
                    "cognitive_psychology.style.md",
                    "cognitive_psychology.hier.md",
                    "cognitive_psychology.toc_titles.md"
                ],
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether the conversion was successful",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    input_file: str = Field(
        ...,
        description="Input filename that was converted",
    )
    output_files: list[str] = Field(
        default_factory=list,
        description="List of output files created",
    )
    error: str | None = Field(
        default=None,
        description="Error message if conversion failed",
    )


class InspectionItemSchema(BaseModel):
    """Schema for a single inspection item."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "inspect_style_hier",
                "available": True,
                "files_checked": ["test.style.md", "test.hier.md"],
            }
        }
    )

    name: str = Field(
        ...,
        description="Machine-readable inspection name",
    )
    available: bool = Field(
        ...,
        description="Whether the required files exist for this inspection",
    )
    files_checked: list[str] = Field(
        default_factory=list,
        description="List of filenames that were checked for this inspection",
    )


class ConversionInspectionResponse(BaseModel):
    """Response containing inspection options for a converted file."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "name": "inspect_style_hier",
                        "available": True,
                        "files_checked": ["test.style.md", "test.hier.md"],
                    },
                    {
                        "name": "inspect_toc_titles",
                        "available": True,
                        "files_checked": ["test.toc_titles.md"],
                    },
                    {
                        "name": "inspect_titles",
                        "available": False,
                        "files_checked": ["test.titles.md"],
                    },
                    {
                        "name": "inspect_title_changes",
                        "available": False,
                        "files_checked": ["test.title_changes.md"],
                    },
                    {
                        "name": "inspect_original_md",
                        "available": True,
                        "files_checked": ["test.md"],
                    },
                ]
            }
        }
    )

    items: list[InspectionItemSchema] = Field(
        default_factory=list,
        description="List of inspection items in priority order",
    )


class FileContentResponse(BaseModel):
    """Response containing markdown file content."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "# Chapter 1\n\n## Introduction\n\nThis is the content...",
                "filename": "test.style.md",
            }
        }
    )

    content: str = Field(
        ...,
        description="Markdown file content",
    )
    filename: str = Field(
        ...,
        description="Filename of the content",
    )


class FileContentUpdateRequest(BaseModel):
    """Request to update markdown file content."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "# Updated Chapter 1\n\n## Introduction\n\nThis is the updated content...",
            }
        }
    )

    content: str = Field(
        ...,
        description="New markdown content to save",
    )


class FileMetricsSchema(BaseModel):
    """Structural metrics for a markdown file."""

    total_headings: int = Field(..., description="Total number of headings")
    h1_h2_count: int = Field(..., description="Number of H1 and H2 headings")
    max_depth: int = Field(..., description="Maximum heading depth")
    avg_depth: float = Field(..., description="Average heading depth")
    coverage_score: float = Field(..., description="Coverage score (0-1)")
    hierarchy_score: float = Field(..., description="Hierarchy score (0-1)")
    chunkability_score: float = Field(..., description="Chunkability score (0-1)")
    target_size_sections: int = Field(..., description="Number of target-sized sections")
    small_sections: int = Field(..., description="Number of small sections")
    large_sections: int = Field(..., description="Number of large sections")
    level_jump_count: int = Field(..., description="Number of level jumps")
    penalty_total: float = Field(..., description="Total penalties applied")
    final_score: float = Field(..., description="Final weighted score")


class FileSuggestionResponse(BaseModel):
    """Response containing comparison metrics and suggestion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "style_metrics": {
                    "total_headings": 45,
                    "h1_h2_count": 8,
                    "max_depth": 4,
                    "avg_depth": 2.5,
                    "coverage_score": 0.75,
                    "hierarchy_score": 0.82,
                    "chunkability_score": 0.65,
                    "target_size_sections": 20,
                    "small_sections": 10,
                    "large_sections": 5,
                    "level_jump_count": 3,
                    "penalty_total": 5.0,
                    "final_score": 0.72,
                },
                "hier_metrics": {
                    "total_headings": 52,
                    "h1_h2_count": 10,
                    "max_depth": 4,
                    "avg_depth": 2.8,
                    "coverage_score": 0.85,
                    "hierarchy_score": 0.88,
                    "chunkability_score": 0.78,
                    "target_size_sections": 28,
                    "small_sections": 8,
                    "large_sections": 3,
                    "level_jump_count": 2,
                    "penalty_total": 0.0,
                    "final_score": 0.84,
                },
                "winner": "hier",
                "score_difference": 0.12,
            }
        }
    )

    style_metrics: FileMetricsSchema = Field(
        ...,
        description="Metrics for style.md file",
    )
    hier_metrics: FileMetricsSchema = Field(
        ...,
        description="Metrics for hier.md file",
    )
    winner: str = Field(
        ...,
        description="Suggested winner: 'style' or 'hier'",
    )
    score_difference: float = Field(
        ...,
        description="Absolute difference between scores",
    )


class FileSelectionRequest(BaseModel):
    """Request to select a file as the main version."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_type": "hier",
            }
        }
    )

    file_type: str = Field(
        ...,
        description="Type of file to select: 'style' or 'hier'",
    )


class FileSelectionResponse(BaseModel):
    """Response after selecting a file."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Successfully copied hier.md to test.md",
                "output_file": "test.md",
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether the selection was successful",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    output_file: str = Field(
        ...,
        description="Path to the output file created",
    )


class GenerateTocTitlesResponse(BaseModel):
    """Response for generating TOC titles file."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Successfully generated toc_titles.md from PDF bookmarks",
                "file_created": "document.toc_titles.md",
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether the generation was successful",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    file_created: str = Field(
        ...,
        description="Name of the file that was created",
    )


class ManualPromptResponse(BaseModel):
    """Response containing the manual prompt content for TOC titles extraction."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "You are an expert at analyzing academic PDFs...",
            }
        }
    )

    content: str = Field(
        ...,
        description="The manual prompt markdown content",
    )


class ReadinessCheckResponse(BaseModel):
    """Response for checking if a file is ready to be added to the database."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ready": True,
                "reasons": [],
                "base_name": "cognitive_psychology",
            }
        }
    )

    ready: bool = Field(
        ...,
        description="Whether the file is ready to be added to database",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="List of reasons why the file is not ready (empty if ready)",
    )
    base_name: str = Field(
        ...,
        description="Base name of the file",
    )


class AddWorkRequest(BaseModel):
    """Request to add a work to the database."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Cognitive Psychology: A Student's Handbook",
                "authors": "Michael Eysenck, Mark Keane",
                "year": 2020,
                "publisher": "Psychology Press",
                "isbn": "978-1138482678",
                "edition": "8th Edition",
                "volume": None,
                "issue": None,
                "pages": None,
                "url": None,
                "city": "London",
                "institution": None,
                "editor": None,
            }
        }
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title of the work (required)",
    )
    authors: str | None = Field(
        default=None,
        max_length=1000,
        description="Author(s) of the work (optional)",
    )
    year: int | None = Field(
        default=None,
        ge=1000,
        le=9999,
        description="Year of publication (optional, must be 4 digits)",
    )
    publisher: str | None = Field(
        default=None,
        max_length=255,
        description="Publisher name (optional)",
    )
    isbn: str | None = Field(
        default=None,
        max_length=20,
        description="ISBN for books (optional)",
    )
    edition: str | None = Field(
        default=None,
        max_length=100,
        description="Edition information (optional)",
    )
    volume: str | None = Field(
        default=None,
        max_length=50,
        description="Volume number for journals/periodicals (optional)",
    )
    issue: str | None = Field(
        default=None,
        max_length=50,
        description="Issue number for journals/periodicals (optional)",
    )
    pages: str | None = Field(
        default=None,
        max_length=50,
        description="Page range (optional)",
    )
    url: str | None = Field(
        default=None,
        max_length=1000,
        description="URL for the work (optional)",
    )
    city: str | None = Field(
        default=None,
        max_length=100,
        description="City of publication (optional)",
    )
    institution: str | None = Field(
        default=None,
        max_length=255,
        description="Institution for theses/dissertations (optional)",
    )
    editor: str | None = Field(
        default=None,
        max_length=1000,
        description="Editor(s) of the work (optional)",
    )


class AddWorkResponse(BaseModel):
    """Response after adding a work to the database."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Successfully added work to database",
                "work_id": 42,
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether the work was successfully added",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    work_id: int = Field(
        ...,
        description="ID of the created work",
    )


class DeleteConversionResponse(BaseModel):
    """Response after deleting a conversion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Successfully deleted 5 files and database entry for test",
                "deleted_files": ["test.pdf", "test.md", "test.style.md", "test.hier.md", "test.toc_titles.md"],
                "io_file_deleted": True,
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether the conversion was successfully deleted",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    deleted_files: list[str] = Field(
        default_factory=list,
        description="List of filenames that were deleted",
    )
    io_file_deleted: bool = Field(
        ...,
        description="Whether the database entry was deleted",
    )


class ParseCitationRequest(BaseModel):
    """Request to parse a citation with LLM."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "citation_text": "Friston, K. (2012). Prediction, perception and agency. International Journal of Psychophysiology, 83(2), 248-252.",
                "citation_format": "APA",
            }
        }
    )

    citation_text: str = Field(
        ...,
        min_length=10,
        description="The citation text to parse",
    )
    citation_format: str = Field(
        ...,
        description="Citation format: APA, MLA, or Chicago",
    )


class ParseCitationResponse(BaseModel):
    """Response from LLM citation parsing."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "title": "Prediction, perception and agency",
                "authors": ["Friston, K."],
                "year": 2012,
                "publisher": None,
                "isbn": None,
                "doi": None,
                "container_title": "International Journal of Psychophysiology",
                "volume": "83",
                "issue": "2",
                "pages": "248-252",
                "url": None,
                "work_type": "article",
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether parsing was successful",
    )
    title: str | None = Field(
        default=None,
        description="Extracted title",
    )
    authors: list[str] | None = Field(
        default=None,
        description="List of author names",
    )
    year: int | None = Field(
        default=None,
        description="Publication year",
    )
    publisher: str | None = Field(
        default=None,
        description="Publisher name",
    )
    isbn: str | None = Field(
        default=None,
        description="ISBN",
    )
    doi: str | None = Field(
        default=None,
        description="DOI",
    )
    container_title: str | None = Field(
        default=None,
        description="Journal or book title",
    )
    volume: str | None = Field(
        default=None,
        description="Volume number",
    )
    issue: str | None = Field(
        default=None,
        description="Issue number",
    )
    pages: str | None = Field(
        default=None,
        description="Page range",
    )
    url: str | None = Field(
        default=None,
        description="URL",
    )
    work_type: str | None = Field(
        default=None,
        description="Type of work",
    )


