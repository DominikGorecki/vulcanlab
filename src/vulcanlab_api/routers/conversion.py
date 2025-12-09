"""
Conversion Router - Document conversion operations.

Endpoints:
    GET  /conv/io-folder-data - Get input/output folder data
    POST /conv/convert-file   - Convert a file from input folder
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from vulcanlab_api.schemas.conversion import (
    AddWorkRequest,
    AddWorkResponse,
    ConversionInspectionResponse,
    ConvertFileRequest,
    ConvertFileResponse,
    DeleteConversionResponse,
    FileContentResponse,
    FileContentUpdateRequest,
    FileMetricsSchema,
    FileSelectionRequest,
    FileSelectionResponse,
    FileSuggestionResponse,
    GenerateTocTitlesResponse,
    InspectionItemSchema,
    IOFolderDataResponse,
    ManualPromptResponse,
    ParseCitationRequest,
    ParseCitationResponse,
    ReadinessCheckResponse,
)
from vulcanlab.config import load_config
from vulcanlab.config.io_folder_data import get_io_folder_data
from vulcanlab.conversions.conv_pdf2md import convert_pdf_to_markdown
from vulcanlab.conversions.conv_epub2md import convert_epub_to_markdown
from vulcanlab.conversions.inspection import get_conversion_inspection
from vulcanlab.conversions.pdf_bookmarks2toc import extract_bookmarks_to_toc
from vulcanlab.conversions.style_v_hier import compare_and_select, compute_final_score, extract_headings, ChunkSizeConfig, ScoringWeights
from vulcanlab.data.database import get_session
from vulcanlab.data.models.io_file import IOFile
from vulcanlab.sanitization.extract_titles import extract_titles
from vulcanlab.sanitization.apply_title_edits import apply_title_edits
from vulcanlab.sanitization.delete_conversion import delete_conversion

router = APIRouter()


@router.get(
    "/io-folder-data",
    response_model=IOFolderDataResponse,
    summary="Get input/output folder data",
    description="Scan input and output directories to get lists of unprocessed and processed files.",
    responses={
        200: {"description": "IO folder data retrieved successfully"},
        500: {"description": "Error scanning directories"},
    },
)
async def get_io_folder_data_endpoint() -> IOFolderDataResponse:
    """
    Get input and output folder data.
    
    Scans the input directory for unprocessed files and the output directory
    for processed files that haven't been added to the database yet.
    
    Returns:
    - input_files: List of filenames in input directory
    - processed_files: List of pipe-separated strings with format:
      basename|id|variant1|variant2|...
    """
    try:
        io_data = get_io_folder_data()
        
        # Transform ProcessedFile objects to pipe-separated format
        # Format: basename|id|variant1|variant2|...
        processed_files_formatted = []
        for pf in io_data.processed_files:
            # Use io_file_id (database ID) instead of hash
            id_str = str(pf.io_file_id) if pf.io_file_id is not None else ""
            variants_str = "|".join(pf.variants)
            pipe_format = f"{pf.base_name}|{id_str}|{variants_str}"
            processed_files_formatted.append(pipe_format)
        
        return IOFolderDataResponse(
            input_files=io_data.input_files,
            processed_files=processed_files_formatted,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning IO folders: {str(e)}",
        ) from e


@router.post(
    "/convert-file",
    response_model=ConvertFileResponse,
    summary="Convert file from input folder",
    description="Convert a PDF file from the input folder to markdown format.",
    responses={
        200: {"description": "Conversion completed successfully"},
        400: {"description": "Invalid request or file not found"},
        500: {"description": "Conversion failed"},
    },
)
async def convert_file_endpoint(request: ConvertFileRequest) -> ConvertFileResponse:
    """
    Convert a file from the input directory to markdown.
    
    This is a blocking operation that will convert the file using the
    conv_pdf2md module with compare=True and use_gpu=True.
    
    The conversion may take several minutes depending on file size.
    
    Args:
        request: ConvertFileRequest with filename
        
    Returns:
        ConvertFileResponse with success status and output files
    """
    try:
        # Load config to get input/output directories
        config = load_config()
        input_dir = Path(config.paths.input_dir)
        output_dir = Path(config.paths.output_dir)
        
        # Validate input file exists
        input_file_path = input_dir / request.filename
        if not input_file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input file not found: {request.filename}",
            )
        
        if not input_file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a file: {request.filename}",
            )
        
        # Validate it's a PDF or EPUB file
        file_ext = input_file_path.suffix.lower()
        if file_ext not in [".pdf", ".epub"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF and EPUB files are supported, got: {file_ext}",
            )
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare output path
        filename_stem = input_file_path.stem
        output_path = output_dir / f"{filename_stem}.md"
        
        # List the output files that were created
        output_files = []

        if file_ext == ".pdf":
            # Convert the PDF with compare=True, use_gpu=True, verbose=True
            convert_pdf_to_markdown(
                pdf_path=input_file_path,
                output_path=output_path,
                verbose=True,
                compare=True,
                use_gpu=True,
            )
            
            expected_files = [
                f"{filename_stem}.pdf",
                f"{filename_stem}.style.md",
                f"{filename_stem}.hier.md",
                f"{filename_stem}.toc_titles.md",
            ]
        else:
            # Convert the EPUB
            convert_epub_to_markdown(
                epub_path=input_file_path,
                output_path=output_path,
                verbose=True,
            )
            
            expected_files = [
                f"{filename_stem}.epub",
                f"{filename_stem}.md",
                f"{filename_stem}.toc_titles.md",
            ]
        
        for expected_file in expected_files:
            file_path = output_dir / expected_file
            if file_path.exists():
                output_files.append(expected_file)
        
        return ConvertFileResponse(
            success=True,
            message=f"Successfully converted {request.filename}",
            input_file=request.filename,
            output_files=output_files,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except FileExistsError as e:
        # Handle the case where PDF already exists in output directory
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        # Catch any conversion errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}",
        ) from e


@router.get(
    "/inspection/{io_file_id}",
    response_model=ConversionInspectionResponse,
    summary="Get conversion inspection options",
    description="Get available inspection options for a converted file based on what artifacts exist.",
    responses={
        200: {"description": "Inspection options retrieved successfully"},
        404: {"description": "File not found"},
        500: {"description": "Error checking inspection options"},
    },
)
async def get_inspection_options(io_file_id: int) -> ConversionInspectionResponse:
    """
    Get inspection options for a converted file.
    
    This endpoint checks what conversion artifacts are available (style.md, hier.md,
    toc_titles.md, etc.) and returns a list of inspection options that can be
    viewed or generated.
    
    Args:
        io_file_id: ID of the file in the io_files table
        
    Returns:
        ConversionInspectionResponse with list of inspection items
    """
    try:
        inspection_items = get_conversion_inspection(io_file_id)
        
        # Convert to schema objects
        items_schema = [
            InspectionItemSchema(
                name=item.name,
                available=item.available,
                files_checked=item.files_checked
            )
            for item in inspection_items
        ]
        
        return ConversionInspectionResponse(items=items_schema)
        
    except ValueError as e:
        # File not found or invalid
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking inspection options: {str(e)}",
        ) from e


@router.post(
    "/generate-toc-titles/{io_file_id}",
    response_model=GenerateTocTitlesResponse,
    summary="Generate TOC titles file",
    description="Generate a toc_titles.md file by extracting bookmarks from the source PDF.",
    responses={
        200: {"description": "TOC titles generated successfully"},
        404: {"description": "File not found"},
        500: {"description": "Error generating TOC titles"},
    },
)
async def generate_toc_titles(io_file_id: int) -> GenerateTocTitlesResponse:
    """
    Generate TOC titles file from PDF bookmarks.
    
    This endpoint attempts to extract bookmarks from the source PDF and create
    a toc_titles.md file. If an error occurs, it creates the file with error details.
    
    Args:
        io_file_id: ID of the file in the io_files table
        
    Returns:
        GenerateTocTitlesResponse with success status and file details
    """
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            # Detach from session
            session.expunge(io_file)
        
        # Extract base name (everything before first dot)
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename} (no extension found)",
            )
        
        base_name = filename[:first_dot]
        
        # Get directories from config
        config = load_config()
        input_dir = Path(config.paths.input_dir)
        output_dir = Path(config.paths.output_dir)
        
        # Locate the source PDF in input directory
        pdf_path = input_dir / filename
        if not pdf_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source PDF not found: {filename}",
            )
        
        # Define output path
        output_path = output_dir / f"{base_name}.toc_titles.md"
        
        # Attempt to extract bookmarks
        try:
            toc_content = extract_bookmarks_to_toc(
                pdf_path=pdf_path,
                output_path=output_path,
                verbose=False
            )
            
            if not toc_content:
                # No bookmarks found - create error file
                error_message = "***ERROR***\n\nNo bookmarks found in PDF"
                output_path.write_text(error_message, encoding="utf-8")
                
                return GenerateTocTitlesResponse(
                    success=False,
                    message="No bookmarks found in PDF. Created error file.",
                    file_created=output_path.name,
                )
            
            return GenerateTocTitlesResponse(
                success=True,
                message=f"Successfully generated toc_titles.md from PDF bookmarks ({len(toc_content.split(chr(10)))} lines)",
                file_created=output_path.name,
            )
            
        except Exception as extract_error:
            # Error during extraction - create error file
            error_message = f"***ERROR***\n\n{str(extract_error)}"
            output_path.write_text(error_message, encoding="utf-8")
            
            return GenerateTocTitlesResponse(
                success=False,
                message=f"Error extracting TOC: {str(extract_error)}. Created error file.",
                file_created=output_path.name,
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating TOC titles: {str(e)}",
        ) from e


@router.get(
    "/file-content/{io_file_id}/{file_type}",
    response_model=FileContentResponse,
    summary="Get markdown file content",
    description="Retrieve the content of a style.md or hier.md file.",
    responses={
        200: {"description": "File content retrieved successfully"},
        404: {"description": "File not found"},
        400: {"description": "Invalid file type"},
    },
)
async def get_file_content(io_file_id: int, file_type: str) -> FileContentResponse:
    """
    Get the content from a markdown file.
    
    For 'style' and 'hier' files, returns extracted titles (headings) only.
    For 'toc_titles' and 'base' files, returns the raw markdown content.
    
    Args:
        io_file_id: ID of the file in the io_files table
        file_type: Type of file ('style', 'hier', 'toc_titles', or 'base')
        
    Returns:
        FileContentResponse with content
    """
    if file_type not in ("style", "hier", "toc_titles", "base"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file_type: {file_type}. Must be 'style', 'hier', 'toc_titles', or 'base'",
        )
    
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Construct file path
        if file_type == "base":
            target_filename = f"{base_name}.md"
        else:
            target_filename = f"{base_name}.{file_type}.md"
        file_path = output_dir / target_filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {target_filename}",
            )
        
        # For toc_titles and base, return raw markdown content
        if file_type in ("toc_titles", "base"):
            content = file_path.read_text(encoding="utf-8")
        else:
            # For style and hier, extract titles using the extract_titles function
            titles_list = extract_titles(file_path)
            # Convert list to newline-separated string
            content = "\n".join(titles_list)
        
        return FileContentResponse(
            content=content,
            filename=target_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file content: {str(e)}",
        ) from e


@router.put(
    "/file-content/{io_file_id}/{file_type}",
    response_model=FileContentResponse,
    summary="Update markdown file content",
    description="Apply title edits to a style.md or hier.md file based on line numbers.",
    responses={
        200: {"description": "File content updated successfully"},
        404: {"description": "File not found"},
        400: {"description": "Invalid file type or content"},
    },
)
async def update_file_content(
    io_file_id: int,
    file_type: str,
    request: FileContentUpdateRequest
) -> FileContentResponse:
    """
    Update a markdown file's content.
    
    For 'style' and 'hier' files: Applies title edits in the format "line_num: title"
    to the actual markdown file by modifying specific lines.
    
    For 'toc_titles' files: Replaces the entire file content with the provided content.
    
    Special formats for style/hier:
    - "123: # New Title" - Replace line 123 with new title
    - "123: ***MISSING***" - Skip (no change)
    - "123: -" - Remove heading markers from line 123
    - "123: --" - Replace line 123 with blank line
    
    Args:
        io_file_id: ID of the file in the io_files table
        file_type: Type of file ('style', 'hier', or 'toc_titles')
        request: For style/hier: title edits. For toc_titles: raw markdown content
        
    Returns:
        FileContentResponse with updated content
    """
    if file_type not in ("style", "hier", "toc_titles"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file_type: {file_type}. Must be 'style', 'hier', or 'toc_titles'",
        )
    
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Construct file path
        target_filename = f"{base_name}.{file_type}.md"
        file_path = output_dir / target_filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {target_filename}",
            )
        
        # Handle toc_titles differently - save raw markdown
        if file_type == "toc_titles":
            file_path.write_text(request.content, encoding="utf-8")
            updated_content = request.content
        else:
            # For style and hier, apply title edits
            apply_title_edits(file_path, request.content)
            
            # Extract and return the updated titles
            titles_list = extract_titles(file_path)
            updated_content = "\n".join(titles_list)
        
        return FileContentResponse(
            content=updated_content,
            filename=target_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying title edits: {str(e)}",
        ) from e


@router.get(
    "/suggestion/{io_file_id}",
    response_model=FileSuggestionResponse,
    summary="Get file comparison suggestion",
    description="Compare style.md and hier.md files and suggest the better one.",
    responses={
        200: {"description": "Suggestion generated successfully"},
        404: {"description": "Files not found"},
        500: {"description": "Error generating suggestion"},
    },
)
async def get_file_suggestion(io_file_id: int) -> FileSuggestionResponse:
    """
    Compare style and hier files and suggest the better one.
    
    Uses the compare_and_select() function from style_v_hier module to analyze
    both files and return detailed metrics plus a recommendation.
    
    This is a dry-run operation - it does NOT copy any files.
    
    Args:
        io_file_id: ID of the file in the io_files table
        
    Returns:
        FileSuggestionResponse with metrics and winner
    """
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Construct file paths
        style_path = output_dir / f"{base_name}.style.md"
        hier_path = output_dir / f"{base_name}.hier.md"
        
        if not style_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Style file not found: {style_path.name}",
            )
        
        if not hier_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hier file not found: {hier_path.name}",
            )
        
        # Analyze both files
        weights = ScoringWeights()
        chunk_config = ChunkSizeConfig()
        
        # Process style file
        style_headings = extract_headings(style_path)
        style_lines = len(style_path.read_text(encoding='utf-8').splitlines())
        style_metrics = compute_final_score(style_headings, style_lines, weights, chunk_config)
        
        # Process hier file
        hier_headings = extract_headings(hier_path)
        hier_lines = len(hier_path.read_text(encoding='utf-8').splitlines())
        hier_metrics = compute_final_score(hier_headings, hier_lines, weights, chunk_config)
        
        # Determine winner
        score_diff = abs(style_metrics.final_score - hier_metrics.final_score)
        
        if score_diff < 0.01:
            # Use tie-breaking rules
            if style_metrics.chunkability_score != hier_metrics.chunkability_score:
                winner = "style" if style_metrics.chunkability_score > hier_metrics.chunkability_score else "hier"
            elif style_metrics.level_jump_count != hier_metrics.level_jump_count:
                winner = "style" if style_metrics.level_jump_count < hier_metrics.level_jump_count else "hier"
            elif style_metrics.h1_h2_count != hier_metrics.h1_h2_count:
                winner = "style" if style_metrics.h1_h2_count > hier_metrics.h1_h2_count else "hier"
            else:
                winner = "hier"  # Default to hier
        else:
            winner = "style" if style_metrics.final_score > hier_metrics.final_score else "hier"
        
        # Convert metrics to schema
        style_metrics_schema = FileMetricsSchema(
            total_headings=style_metrics.total_headings,
            h1_h2_count=style_metrics.h1_h2_count,
            max_depth=style_metrics.max_depth,
            avg_depth=style_metrics.avg_depth,
            coverage_score=style_metrics.coverage_score,
            hierarchy_score=style_metrics.hierarchy_score,
            chunkability_score=style_metrics.chunkability_score,
            target_size_sections=style_metrics.target_size_sections,
            small_sections=style_metrics.small_sections,
            large_sections=style_metrics.large_sections,
            level_jump_count=style_metrics.level_jump_count,
            penalty_total=style_metrics.penalty_total,
            final_score=style_metrics.final_score,
        )
        
        hier_metrics_schema = FileMetricsSchema(
            total_headings=hier_metrics.total_headings,
            h1_h2_count=hier_metrics.h1_h2_count,
            max_depth=hier_metrics.max_depth,
            avg_depth=hier_metrics.avg_depth,
            coverage_score=hier_metrics.coverage_score,
            hierarchy_score=hier_metrics.hierarchy_score,
            chunkability_score=hier_metrics.chunkability_score,
            target_size_sections=hier_metrics.target_size_sections,
            small_sections=hier_metrics.small_sections,
            large_sections=hier_metrics.large_sections,
            level_jump_count=hier_metrics.level_jump_count,
            penalty_total=hier_metrics.penalty_total,
            final_score=hier_metrics.final_score,
        )
        
        return FileSuggestionResponse(
            style_metrics=style_metrics_schema,
            hier_metrics=hier_metrics_schema,
            winner=winner,
            score_difference=score_diff,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating suggestion: {str(e)}",
        ) from e


@router.post(
    "/select-file/{io_file_id}",
    response_model=FileSelectionResponse,
    summary="Select a file as main version",
    description="Copy the selected file (style or hier) to <base>.md as the main version.",
    responses={
        200: {"description": "File selected successfully"},
        404: {"description": "File not found"},
        400: {"description": "Invalid file type or file already exists"},
    },
)
async def select_file(
    io_file_id: int,
    request: FileSelectionRequest
) -> FileSelectionResponse:
    """
    Select a file as the main version.
    
    Copies the selected file (style.md or hier.md) to <base>.md.
    
    Args:
        io_file_id: ID of the file in the io_files table
        request: File type to select ('style' or 'hier')
        
    Returns:
        FileSelectionResponse with success status
    """
    file_type = request.file_type
    
    if file_type not in ("style", "hier"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file_type: {file_type}. Must be 'style' or 'hier'",
        )
    
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Construct paths
        source_path = output_dir / f"{base_name}.{file_type}.md"
        target_path = output_dir / f"{base_name}.md"
        
        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source file not found: {source_path.name}",
            )
        
        # Check if target already exists
        if target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Output file already exists: {target_path.name}. Delete it first.",
            )
        
        # Copy file
        import shutil
        shutil.copy2(source_path, target_path)
        
        return FileSelectionResponse(
            success=True,
            message=f"Successfully copied {source_path.name} to {target_path.name}",
            output_file=target_path.name,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error selecting file: {str(e)}",
        ) from e


@router.get(
    "/manual-prompt-toc-titles",
    response_model=ManualPromptResponse,
    summary="Get manual TOC titles prompt",
    description="Retrieve the manual prompt for extracting TOC titles using an LLM.",
    responses={
        200: {"description": "Manual prompt retrieved successfully"},
        500: {"description": "Error reading prompt file"},
    },
)
async def get_manual_prompt_toc_titles() -> ManualPromptResponse:
    """
    Get the manual prompt content for TOC titles extraction.

    This endpoint loads the active toc_extraction template from the database,
    falling back to the manual_prompt__toc_titles.md file if no template exists.
    Users can copy and paste this prompt to their favorite LLM along with the PDF
    to manually extract TOC titles.

    Returns:
        ManualPromptResponse with the prompt content
    """
    try:
        # Import template loader
        from vulcanlab.data.template_loader import load_template

        # Define fallback function that reads from file
        def get_fallback_prompt() -> str:
            from pathlib import Path as PathLib

            # Get the project root (where src/ is located)
            current_file = PathLib(__file__).resolve()
            src_dir = current_file.parent.parent.parent
            prompt_path = src_dir / "vulcanlab" / "conversions" / "manual_prompt__toc_titles.md"

            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt file not found at: {prompt_path}")

            return prompt_path.read_text(encoding="utf-8")

        # Load template from database with file fallback
        template = load_template("toc_extraction", get_fallback_prompt)

        # Since this template has no variables, the template string is the content
        content = template.template

        return ManualPromptResponse(content=content)

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manual prompt file not found: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading manual prompt: {str(e)}",
        ) from e


@router.get(
    "/readiness/{io_file_id}",
    response_model=ReadinessCheckResponse,
    summary="Check if file is ready to be added to database",
    description="Validates that required files exist and are error-free before adding to database.",
    responses={
        200: {"description": "Readiness check completed"},
        404: {"description": "File not found"},
        500: {"description": "Error checking readiness"},
    },
)
async def check_readiness(io_file_id: int) -> ReadinessCheckResponse:
    """
    Check if a converted file is ready to be added to the database.
    
    Validates:
    1. <base_name>.md exists
    2. <base_name>.toc_titles.md exists
    3. <base_name>.toc_titles.md does not contain ***ERROR***
    
    Args:
        io_file_id: ID of the file in the io_files table
        
    Returns:
        ReadinessCheckResponse with readiness status and reasons
    """
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Check for required files
        reasons = []
        
        # 1. Check if <base_name>.md exists
        md_path = output_dir / f"{base_name}.md"
        if not md_path.exists():
            reasons.append("Base markdown file is missing")
        
        # 2. Check if <base_name>.toc_titles.md exists
        toc_titles_path = output_dir / f"{base_name}.toc_titles.md"
        if not toc_titles_path.exists():
            reasons.append("Table of contents file is missing. Generate it first.")
        else:
            # 3. Check if toc_titles.md contains ***ERROR***
            try:
                toc_content = toc_titles_path.read_text(encoding="utf-8")
                if "***ERROR***" in toc_content:
                    reasons.append("Table of contents file contains errors. Fix them before proceeding.")
            except Exception as e:
                reasons.append(f"Could not read table of contents file: {str(e)}")
        
        # Determine if ready
        ready = len(reasons) == 0
        
        return ReadinessCheckResponse(
            ready=ready,
            reasons=reasons,
            base_name=base_name,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking readiness: {str(e)}",
        ) from e


@router.post(
    "/add-to-database/{io_file_id}",
    response_model=AddWorkResponse,
    summary="Add converted file to database",
    description="Create a new work entry in the database with bibliographic metadata.",
    responses={
        200: {"description": "Work added successfully"},
        400: {"description": "Validation error or duplicate work"},
        404: {"description": "File not found"},
        500: {"description": "Error adding work to database"},
    },
)
async def add_to_database(
    io_file_id: int,
    request: AddWorkRequest
) -> AddWorkResponse:
    """
    Add a converted file to the database as a new work.
    
    This endpoint calls create_new_work to insert bibliographic metadata
    and file references into the works table.
    
    Args:
        io_file_id: ID of the file in the io_files table
        request: Bibliographic metadata for the work
        
    Returns:
        AddWorkResponse with success status and work ID
    """
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory and construct markdown path
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        markdown_path = output_dir / f"{base_name}.md"
        
        # Validate markdown file exists
        if not markdown_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Markdown file not found: {markdown_path.name}",
            )
        
        # Import create_new_work and DuplicateWorkError
        from vulcanlab.conversions.new_work import create_new_work, DuplicateWorkError
        
        # Call create_new_work
        try:
            work = create_new_work(
                title=request.title,
                markdown_path=markdown_path,
                authors=request.authors,
                year=request.year,
                publisher=request.publisher,
                isbn=request.isbn,
                edition=request.edition,
                volume=request.volume,
                issue=request.issue,
                pages=request.pages,
                url=request.url,
                city=request.city,
                institution=request.institution,
                editor=request.editor,
                check_duplicates=True,
                verbose=False,
            )
            
            return AddWorkResponse(
                success=True,
                message=f"Successfully added work '{request.title}' to database",
                work_id=work.id,
            )
            
        except DuplicateWorkError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate work: {str(e)}",
            ) from e
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {str(e)}",
            ) from e
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding work to database: {str(e)}",
        ) from e


@router.post(
    "/parse-citation-llm",
    response_model=ParseCitationResponse,
    summary="Parse citation using LLM",
    description="Use LLM to parse a citation string and extract bibliographic metadata.",
    responses={
        200: {"description": "Citation parsed successfully"},
        400: {"description": "Invalid citation text or format"},
        500: {"description": "LLM parsing error"},
    },
)
async def parse_citation_llm(
    request: ParseCitationRequest
) -> ParseCitationResponse:
    """
    Parse a citation string using LLM.

    This endpoint uses the LIGHT tier LLM to extract bibliographic
    metadata from citation text in APA, MLA, or Chicago formats.

    Args:
        request: Citation text and format

    Returns:
        ParseCitationResponse with extracted fields
    """
    try:
        from vulcanlab.utils.llm_citation_parser import parse_citation_with_llm

        # Parse citation
        citation = parse_citation_with_llm(
            citation_text=request.citation_text,
            citation_format=request.citation_format,
        )

        # Convert to response schema
        return ParseCitationResponse(
            success=True,
            title=citation.title,
            authors=citation.authors,
            year=citation.year,
            publisher=citation.publisher,
            isbn=citation.isbn,
            doi=citation.doi,
            container_title=citation.container_title,
            volume=citation.volume,
            issue=citation.issue,
            pages=citation.pages,
            url=citation.url,
            work_type=citation.work_type,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation parsing error: {str(e)}",
        ) from e


@router.get(
    "/original-markdown/{io_file_id}",
    response_model=FileContentResponse,
    summary="Get original markdown file content",
    description="Retrieve the content of the markdown file corresponding to the given IOFile ID.",
    responses={
        200: {"description": "File content retrieved successfully"},
        404: {"description": "File not found"},
    },
)
async def get_original_markdown(io_file_id: int) -> FileContentResponse:
    """
    Get the content of the markdown file corresponding to the given IOFile ID.
    
    This endpoint takes the IOFile ID (which might point to an EPUB/PDF or a markdown file),
    derives the base name, and finds the corresponding <base_name>.md in the output directory.
    
    Args:
        io_file_id: ID of the file in the io_files table
        
    Returns:
        FileContentResponse with content
    """
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Construct markdown file path
        target_filename = f"{base_name}.md"
        file_path = output_dir / target_filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Original markdown file not found: {target_filename}",
            )
            
        content = file_path.read_text(encoding="utf-8")
        
        return FileContentResponse(
            content=content,
            filename=target_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file content: {str(e)}",
        ) from e


@router.put(
    "/original-markdown/{io_file_id}",
    response_model=FileContentResponse,
    summary="Update original markdown file content",
    description="Update the content of the markdown file corresponding to the given IOFile ID.",
    responses={
        200: {"description": "File content updated successfully"},
        404: {"description": "File not found"},
    },
)
async def update_original_markdown(
    io_file_id: int,
    request: FileContentUpdateRequest
) -> FileContentResponse:
    """
    Update the content of the markdown file corresponding to the given IOFile ID.
    
    This endpoint takes the IOFile ID (which might point to an EPUB/PDF or a markdown file),
    derives the base name, and overwrites the corresponding <base_name>.md in the output directory.
    
    Args:
        io_file_id: ID of the file in the io_files table
        request: New content
        
    Returns:
        FileContentResponse with updated content
    """
    try:
        # Get the file from database
        with get_session() as session:
            io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
            
            if not io_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File with ID {io_file_id} not found in database",
                )
            
            session.expunge(io_file)
        
        # Extract base name
        filename = io_file.filename
        first_dot = filename.find('.')
        if first_dot == -1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename format: {filename}",
            )
        
        base_name = filename[:first_dot]
        
        # Get output directory
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        
        # Construct markdown file path
        target_filename = f"{base_name}.md"
        file_path = output_dir / target_filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Original markdown file not found: {target_filename}",
            )
            
        file_path.write_text(request.content, encoding="utf-8")
        
        return FileContentResponse(
            content=request.content,
            filename=target_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating file content: {str(e)}",
        ) from e


@router.delete(
    "/delete/{io_file_id}",
    response_model=DeleteConversionResponse,
    summary="Delete conversion and associated files",
    description="Delete all files associated with a conversion and remove the database entry.",
    responses={
        200: {"description": "Conversion deleted successfully"},
        404: {"description": "File not found"},
        500: {"description": "Error deleting conversion"},
    },
)
async def delete_conversion_endpoint(io_file_id: int) -> DeleteConversionResponse:
    """
    Delete a conversion and all associated files.

    This endpoint:
    1. Deletes ALL files in the output directory with the same base name
    2. Deletes the io_file database entry

    Warning: This operation is not recoverable.

    Args:
        io_file_id: ID of the file in the io_files table

    Returns:
        DeleteConversionResponse with deletion details
    """
    try:
        result = delete_conversion(io_file_id=io_file_id, verbose=False)

        return DeleteConversionResponse(
            success=result["success"],
            message=result["message"],
            deleted_files=result["deleted_files"],
            io_file_deleted=result["io_file_deleted"],
        )

    except ValueError as e:
        # File not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversion: {str(e)}",
        ) from e
