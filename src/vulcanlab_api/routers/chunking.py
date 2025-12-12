"""
Chunking Router - Chunking operations for works with sanitized files.

Endpoints:
    GET  /chunking/works                                              - List works with sanitized files
    GET  /chunking/work/{work_id}                                     - Get work detail
    GET  /chunking/work/{work_id}/sanitized/content                   - Get sanitized content
    PUT  /chunking/work/{work_id}/sanitized/content                   - Update sanitized content
    POST /chunking/work/{work_id}/extract-sanitized-titles            - Extract sanitized titles
    GET  /chunking/work/{work_id}/san-titles/content                  - Get sanitized titles content
    PUT  /chunking/work/{work_id}/san-titles/content                  - Update sanitized titles content
    GET  /chunking/work/{work_id}/vec-suggestions/table               - Get vec suggestions as table data
    PUT  /chunking/work/{work_id}/vec-suggestions/table               - Update vec suggestions from table data
    GET  /chunking/work/{work_id}/vec-suggestions/prompt              - Get LLM prompt for vec suggestions
    POST /chunking/work/{work_id}/vec-suggestions/manual              - Save manual vec suggestions response
    POST /chunking/work/{work_id}/vec-suggestions/run                 - Run vec suggestions with LLM
    POST /chunking/work/{work_id}/vec-suggestions/manual-all-vectorize - Generate all-VECTORIZE suggestions
    POST /chunking/work/{work_id}/apply-heading-chunks                - Apply heading chunking
    POST /chunking/work/{work_id}/apply-content-chunks                - Apply content chunking
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.sanitization import extract_titles_from_work, HashMismatchError
from vulcanlab.chunking.chunk_headings import chunk_headings
from vulcanlab.chunking.content_chunking import chunk_content
from vulcanlab.utils.file_utils import compute_file_hash, set_file_writable, set_file_readonly, get_path_resolver


# Initialize path resolver
resolver = get_path_resolver()
from vulcanlab_api.schemas.chunking import (
    WorkListResponse,
    WorkListItem,
    WorkDetailResponse,
    FileStatusInfo,
    SanitizedContentResponse,
    UpdateSanitizedContentRequest,
    ExtractSanitizedTitlesRequest,
    ExtractSanitizedTitlesResponse,
    SanTitlesContentResponse,
    UpdateSanTitlesContentRequest,
    VecSuggestionsPromptResponse,
    ManualVecSuggestionsRequest,
    ManualVecSuggestionsResponse,
    RunVecSuggestionsRequest,
    RunVecSuggestionsResponse,
    ManualAllVectorizeRequest,
    ManualAllVectorizeResponse,
    ApplyHeadingChunksResponse,
    ApplyContentChunksResponse,
    VecSuggestionRow,
    VecSuggestionsTableResponse,
    UpdateVecSuggestionsTableRequest,
)

router = APIRouter(tags=["chunking"])


def _get_file_status(work: Work, file_key: str) -> FileStatusInfo:
    """Helper to get file status information."""
    if not work.files or file_key not in work.files:
        return FileStatusInfo(exists=False, path=None, hash=None, hash_match=None)

    file_path = resolver.resolve_work_path(work, file_key)
    stored_hash = work.files[file_key]["hash"]

    if not file_path.exists():
        return FileStatusInfo(
            exists=False,
            path=file_path.name,
            hash=stored_hash,
            hash_match=False
        )

    current_hash = compute_file_hash(file_path)
    hash_match = current_hash == stored_hash

    return FileStatusInfo(
        exists=True,
        path=file_path.name,
        hash=stored_hash,
        hash_match=hash_match
    )


@router.get(
    "/works",
    response_model=WorkListResponse,
    summary="List works with sanitized files",
    description="Returns all works that have sanitized files ready for chunking.",
)
async def list_works_for_chunking() -> WorkListResponse:
    """List all works that have sanitized files."""
    with get_session() as session:
        works = session.query(Work).order_by(Work.updated_at.desc()).all()
    
        work_items = []
        for work in works:
            # Only include works that have sanitized file
            if not work.files or "sanitized" not in work.files:
                continue
            
            # Get processing status
            heading_status = None
            content_status = None
            if work.processing_status:
                heading_status = work.processing_status.get("heading_chunks")
                content_status = work.processing_status.get("content_chunks")
            
            work_items.append(
                WorkListItem(
                    id=work.id,
                    title=work.title,
                    authors=work.authors,
                    year=work.year,
                    work_type=work.work_type,
                    has_sanitized=True,
                    heading_chunks_status=heading_status,
                    content_chunks_status=content_status,
                )
            )
        
        return WorkListResponse(works=work_items, total=len(work_items))


@router.get(
    "/work/{work_id}",
    response_model=WorkDetailResponse,
    summary="Get work detail",
    description="Returns detailed information about a work including file statuses.",
)
async def get_work_detail(work_id: int) -> WorkDetailResponse:
    """Get detailed work information."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        # Get file statuses
        file_statuses = {
            "sanitized": _get_file_status(work, "sanitized"),
            "sanitized_titles": _get_file_status(work, "sanitized_titles"),
            "vec_suggestions": _get_file_status(work, "vec_suggestions"),
        }
        
        return WorkDetailResponse(
            id=work.id,
            title=work.title,
            authors=work.authors,
            year=work.year,
            work_type=work.work_type,
            files=file_statuses,
            processing_status=work.processing_status,
        )


@router.get(
    "/work/{work_id}/sanitized/content",
    response_model=SanitizedContentResponse,
    summary="Get sanitized file content",
    description="Returns the content of the sanitized file.",
)
async def get_sanitized_content(work_id: int) -> SanitizedContentResponse:
    """Get sanitized file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "sanitized" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have sanitized file"
            )
        
        file_path = resolver.resolve_work_path(work, "sanitized")
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized file not found on disk: {file_path}"
            )
        
        content = file_path.read_text(encoding='utf-8')
        current_hash = compute_file_hash(file_path)
        
        return SanitizedContentResponse(
            content=content,
            filename=file_path.name,
            current_hash=current_hash
        )


@router.put(
    "/work/{work_id}/sanitized/content",
    response_model=SanitizedContentResponse,
    summary="Update sanitized file content",
    description="Updates the content of the sanitized file and recalculates hash.",
)
async def update_sanitized_content(
    work_id: int,
    request: UpdateSanitizedContentRequest
) -> SanitizedContentResponse:
    """Update sanitized file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "sanitized" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have sanitized file"
            )
        
        file_path = resolver.resolve_work_path(work, "sanitized")
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized file not found on disk: {file_path}"
            )
        
        try:
            # Make file writable if it's read-only
            set_file_writable(file_path)
            
            # Write new content
            file_path.write_text(request.content, encoding='utf-8')
            
            # Set back to read-only
            set_file_readonly(file_path)
            
            # Compute new hash
            new_hash = compute_file_hash(file_path)
            
            # Update work.files with new hash (recreate dict to trigger SQLAlchemy change detection)
            updated_files = dict(work.files)
            updated_files["sanitized"] = {
                "path": file_path.name,
                "hash": new_hash
            }
            work.files = updated_files
            
            session.commit()
            session.refresh(work)
            
            return SanitizedContentResponse(
                content=request.content,
                filename=file_path.name,
                current_hash=new_hash
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update sanitized file: {e}"
            )


@router.post(
    "/work/{work_id}/extract-sanitized-titles",
    response_model=ExtractSanitizedTitlesResponse,
    summary="Extract sanitized titles",
    description="Extracts titles from sanitized markdown file.",
)
async def extract_sanitized_titles(
    work_id: int,
    request: ExtractSanitizedTitlesRequest
) -> ExtractSanitizedTitlesResponse:
    """Extract titles from sanitized file."""
    try:
        output_path = extract_titles_from_work(
            work_id=work_id,
            source_key="sanitized",
            force=request.force,
            verbose=True
        )
        
        return ExtractSanitizedTitlesResponse(
            success=True,
            message="Successfully extracted sanitized titles",
            output_path=str(output_path)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract titles: {e}"
        )


@router.get(
    "/work/{work_id}/san-titles/content",
    response_model=SanTitlesContentResponse,
    summary="Get sanitized titles content",
    description="Returns the content of the sanitized_titles file.",
)
async def get_san_titles_content(work_id: int) -> SanTitlesContentResponse:
    """Get sanitized titles file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "sanitized_titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have sanitized_titles file"
            )
        
        file_path = resolver.resolve_work_path(work, "sanitized_titles")
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized titles file not found on disk: {file_path}"
            )
        
        content = file_path.read_text(encoding='utf-8')
        current_hash = compute_file_hash(file_path)
        
        return SanTitlesContentResponse(
            content=content,
            filename=file_path.name,
            current_hash=current_hash
        )


@router.put(
    "/work/{work_id}/san-titles/content",
    response_model=SanTitlesContentResponse,
    summary="Update sanitized titles content",
    description="Updates the content of the sanitized_titles file and recalculates hash.",
)
async def update_san_titles_content(
    work_id: int,
    request: UpdateSanTitlesContentRequest
) -> SanTitlesContentResponse:
    """Update sanitized titles file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "sanitized_titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have sanitized_titles file"
            )
        
        file_path = resolver.resolve_work_path(work, "sanitized_titles")
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized titles file not found on disk: {file_path}"
            )
        
        try:
            # Make file writable if it's read-only
            set_file_writable(file_path)
            
            # Write new content
            file_path.write_text(request.content, encoding='utf-8')
            
            # Set back to read-only
            set_file_readonly(file_path)
            
            # Compute new hash
            new_hash = compute_file_hash(file_path)
            
            # Update work.files with new hash (recreate dict to trigger SQLAlchemy change detection)
            updated_files = dict(work.files)
            updated_files["sanitized_titles"] = {
                "path": file_path.name,
                "hash": new_hash
            }
            work.files = updated_files
            
            session.commit()
            session.refresh(work)
            
            return SanTitlesContentResponse(
                content=request.content,
                filename=file_path.name,
                current_hash=new_hash
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update sanitized titles file: {e}"
            )


@router.post(
    "/work/{work_id}/apply-heading-chunks",
    response_model=ApplyHeadingChunksResponse,
    summary="Apply heading chunks",
    description="Runs chunk_headings to create heading-based chunks.",
)
async def apply_heading_chunks(work_id: int) -> ApplyHeadingChunksResponse:
    """Apply heading chunking."""
    try:
        chunks_created = chunk_headings(work_id=work_id, verbose=True)
        
        return ApplyHeadingChunksResponse(
            success=True,
            message=f"Successfully created {chunks_created} heading chunks",
            chunks_created=chunks_created
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply heading chunks: {e}"
        )


@router.post(
    "/work/{work_id}/apply-content-chunks",
    response_model=ApplyContentChunksResponse,
    summary="Apply content chunks",
    description="Runs content_chunking to create paragraph-based chunks.",
)
async def apply_content_chunks(work_id: int) -> ApplyContentChunksResponse:
    """Apply content chunking."""
    try:
        chunks_created = chunk_content(work_id=work_id, verbose=True)
        
        return ApplyContentChunksResponse(
            success=True,
            message=f"Successfully created {chunks_created} content chunks",
            chunks_created=chunks_created
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply content chunks: {e}"
        )


@router.get(
    "/work/{work_id}/vec-suggestions/prompt",
    response_model=VecSuggestionsPromptResponse,
    summary="Get LLM prompt for vec suggestions",
    description="Builds and returns the LLM prompt for generating vectorization suggestions.",
)
async def get_vec_suggestions_prompt(work_id: int) -> VecSuggestionsPromptResponse:
    """Get the LLM prompt for vec suggestions."""
    from vulcanlab.chunking import build_prompt_for_vec_suggestions
    
    try:
        result = build_prompt_for_vec_suggestions(work_id=work_id, verbose=False)
        
        return VecSuggestionsPromptResponse(
            prompt=result["prompt"],
            work_title=result["work_title"],
            work_authors=result["work_authors"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build prompt: {e}"
        )


@router.post(
    "/work/{work_id}/vec-suggestions/manual",
    response_model=ManualVecSuggestionsResponse,
    summary="Save manual vec suggestions response",
    description="Parses and saves a manually provided LLM response for vec suggestions.",
)
async def save_manual_vec_suggestions(
    work_id: int,
    request: ManualVecSuggestionsRequest
) -> ManualVecSuggestionsResponse:
    """Save manual vec suggestions from LLM response."""
    from vulcanlab.chunking import save_vec_suggestions_from_response
    
    try:
        output_path = save_vec_suggestions_from_response(
            work_id=work_id,
            response_text=request.response_text,
            force=request.force,
            verbose=True
        )
        
        return ManualVecSuggestionsResponse(
            success=True,
            message=f"Successfully saved vec suggestions to {output_path.name}",
            output_path=str(output_path)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save vec suggestions: {e}"
        )


@router.post(
    "/work/{work_id}/vec-suggestions/run",
    response_model=RunVecSuggestionsResponse,
    summary="Run vec suggestions with LLM",
    description="Runs the full LLM-based vec suggestions generation with the FULL model.",
)
async def run_vec_suggestions(
    work_id: int,
    request: RunVecSuggestionsRequest
) -> RunVecSuggestionsResponse:
    """Run vec suggestions with LLM."""
    from vulcanlab.chunking import suggest_chunks_from_work

    try:
        output_path = suggest_chunks_from_work(
            work_id=work_id,
            use_full_model=True,
            force=request.force,
            verbose=True
        )

        return RunVecSuggestionsResponse(
            success=True,
            message=f"Successfully generated vec suggestions to {output_path.name}",
            output_path=str(output_path)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run vec suggestions: {e}"
        )


@router.post(
    "/work/{work_id}/vec-suggestions/manual-all-vectorize",
    response_model=ManualAllVectorizeResponse,
    summary="Generate vec suggestions with all VECTORIZE",
    description="Generates vec suggestions file marking all headings as VECTORIZE (no LLM needed).",
)
async def manual_all_vectorize(
    work_id: int,
    request: ManualAllVectorizeRequest
) -> ManualAllVectorizeResponse:
    """Generate vec suggestions with all headings marked as VECTORIZE."""
    from vulcanlab.chunking.suggested_chunks import generate_all_vectorize_suggestions

    try:
        output_path = generate_all_vectorize_suggestions(
            work_id=work_id,
            force=request.force,
            verbose=True
        )

        return ManualAllVectorizeResponse(
            success=True,
            message=f"Successfully generated all-VECTORIZE suggestions to {output_path.name}",
            output_path=str(output_path)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate all-vectorize suggestions: {e}"
        )


@router.get(
    "/work/{work_id}/vec-suggestions/table",
    response_model=VecSuggestionsTableResponse,
    summary="Get vec suggestions as table data",
    description="Returns ALL headings from sanitized.md merged with vectorization decisions from sanitized.vec_sugg.md.",
)
async def get_vec_suggestions_table(work_id: int) -> VecSuggestionsTableResponse:
    """Get vec suggestions as structured table data."""
    from vulcanlab.chunking.vec_suggestions_interactive import get_vec_suggestions_table_data

    try:
        # Get merged table data (this will auto-detect vec_sugg file if it exists on disk)
        table_data = get_vec_suggestions_table_data(work_id=work_id, force=False)

        # Get file info for hash and filename
        # Try database first, then fall back to auto-detected path from table_data
        with get_session() as session:
            work = session.query(Work).filter(Work.id == work_id).first()

            if not work:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work with ID {work_id} not found"
                )

            if not work.files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work {work_id} has no files metadata"
                )

            # Check if vec_suggestions is in database metadata - use exact key 'vec_suggestions'
            if "vec_suggestions" in work.files:
                vec_sugg_info = work.files["vec_suggestions"]
                
                # Ensure we have the required fields
                if not isinstance(vec_sugg_info, dict) or "path" not in vec_sugg_info:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Invalid vec_suggestions metadata structure in work {work_id}"
                    )

                vec_sugg_path = resolver.resolve_work_path(work, "vec_suggestions")

                # Debug logging
                print(f"[DEBUG] get_vec_suggestions_table: work_id={work_id}, vec_sugg_path={vec_sugg_path}, exists={vec_sugg_path.exists()}")

                # Verify file actually exists on disk
                if not vec_sugg_path.exists():
                    # File is in database but doesn't exist on disk - try auto-detection
                    if "vec_sugg_path" in table_data:
                        vec_sugg_path = Path(table_data["vec_sugg_path"]).resolve()
                        if not vec_sugg_path.exists():
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Vec suggestions file not found on disk. Database path: {work.files['vec_suggestions']['path']}, Auto-detected path: {vec_sugg_path}"
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Vec suggestions file not found on disk: {vec_sugg_path}. File is registered in database at path: {work.files['vec_suggestions']['path']}"
                        )
                
                filename = vec_sugg_path.name
                file_hash = vec_sugg_info.get("hash") or compute_file_hash(vec_sugg_path)
            elif "vec_sugg_path" in table_data:
                # File exists on disk but not in database - use auto-detected path
                vec_sugg_path = Path(table_data["vec_sugg_path"]).resolve()
                if not vec_sugg_path.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Vec suggestions file not found on disk: {vec_sugg_path}"
                    )
                filename = vec_sugg_path.name
                file_hash = table_data.get("vec_sugg_hash") or compute_file_hash(vec_sugg_path)
            else:
                # No vec_suggestions file found at all
                available_keys = list(work.files.keys()) if work.files else []
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work {work_id} does not have 'vec_suggestions' in files metadata. Available keys: {available_keys}. Please generate vec suggestions first."
                )

        return VecSuggestionsTableResponse(
            work_id=table_data["work_id"],
            rows=table_data["rows"],
            filename=filename,
            hash=file_hash
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch - file may have been modified externally: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load vec suggestions table: {e}"
        )


@router.put(
    "/work/{work_id}/vec-suggestions/table",
    response_model=VecSuggestionsTableResponse,
    summary="Update vec suggestions from table data",
    description="Saves table data back to the vec_suggestions file.",
)
async def update_vec_suggestions_table(
    work_id: int,
    request: UpdateVecSuggestionsTableRequest
) -> VecSuggestionsTableResponse:
    """Update vec suggestions file from table data."""
    from vulcanlab.chunking.vec_suggestions_interactive import (
        get_vec_suggestions_table_data,
        reconstruct_vec_suggestions_markdown
    )

    try:
        # Validate work exists and has vec_suggestions file
        with get_session() as session:
            work = session.query(Work).filter(Work.id == work_id).first()

            if not work:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work with ID {work_id} not found"
                )

            if not work.files or "vec_suggestions" not in work.files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work {work_id} does not have vec_suggestions file"
                )

            vec_sugg_info = work.files["vec_suggestions"]
            vec_sugg_path = resolver.resolve_work_path(work, "vec_suggestions")

        # Debug logging
        print(f"[DEBUG] update_vec_suggestions_table: work_id={work_id}, vec_sugg_path={vec_sugg_path}, exists={vec_sugg_path.exists()}")

        # Reconstruct markdown from table data
        rows_dict = [row.model_dump() for row in request.rows]
        markdown_content = reconstruct_vec_suggestions_markdown(rows_dict)

        # Write file (make writable, write, set read-only)
        set_file_writable(vec_sugg_path)
        vec_sugg_path.write_text(markdown_content, encoding='utf-8')
        set_file_readonly(vec_sugg_path)

        # Update hash in database
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        new_hash = compute_file_hash(vec_sugg_path)
        with get_session() as session:
            work = session.query(Work).filter(Work.id == work_id).first()
            
            if not work:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work with ID {work_id} not found"
                )
            
            # Create new dict to trigger SQLAlchemy change detection
            updated_files = dict(work.files) if work.files else {}
            updated_files["vec_suggestions"] = {
                "path": vec_sugg_path.name,
                "hash": new_hash
            }
            work.files = updated_files
            session.commit()
            session.refresh(work)

        # Return updated table data
        updated_table_data = get_vec_suggestions_table_data(work_id=work_id, force=False)

        return VecSuggestionsTableResponse(
            work_id=updated_table_data["work_id"],
            rows=updated_table_data["rows"],
            filename=vec_sugg_path.name,
            hash=new_hash
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch - file may have been modified externally: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vec suggestions: {e}"
        )
