"""
Sanitization Router - Content sanitization operations.

Endpoints:
    GET  /sanitization/works                              - List all works
    GET  /sanitization/work/{work_id}                     - Get work detail
    POST /sanitization/work/{work_id}/extract-titles      - Extract titles
    POST /sanitization/work/{work_id}/suggest-title-changes - Suggest changes
    POST /sanitization/work/{work_id}/apply-title-changes - Apply changes
    POST /sanitization/work/{work_id}/skip-apply          - Skip and copy
    POST /sanitization/work/{work_id}/skip-apply          - Skip and copy
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.sanitization import (
    extract_titles_from_work,
    suggest_heading_changes_from_work,
    apply_title_changes_from_work,
    skip_apply_from_work,
    build_prompt_for_work,
    save_title_changes_from_response,
    verify_title_changes_integrity,
    HashMismatchError,
)
from vulcanlab.utils.file_utils import compute_file_hash, set_file_writable, set_file_readonly, get_path_resolver
from vulcanlab.config import load_config


# Initialize path resolver
resolver = get_path_resolver()
from vulcanlab_api.schemas.sanitization import (
    # Legacy schemas removed
    # New work-based schemas
    WorkListResponse,
    WorkListItem,
    WorkDetailResponse,
    FileStatusInfo,
    ExtractTitlesFromWorkRequest,
    ExtractTitlesFromWorkResponse,
    SuggestTitleChangesRequest,
    SuggestTitleChangesResponse,
    ApplyTitleChangesRequest,
    ApplyTitleChangesResponse,
    SkipApplyRequest,
    SkipApplyResponse,
    TitlesContentResponse,
    UpdateTitlesContentRequest,
    PromptForWorkResponse,
    ManualTitleChangesRequest,
    ManualTitleChangesResponse,
    VerifyTitleChangesRequest,
    VerifyTitleChangesResponse,
    TitleChangesContentResponse,
    UpdateTitleChangesContentRequest,
    AddSanitizedMarkdownRequest,
    AddSanitizedMarkdownResponse,
    # Interactive table schemas
    HeadingRow,
    HeadingTableResponse,
    UpdateHeadingTableRequest,
)

router = APIRouter()


def _check_file_status(work: Work, file_key: str) -> FileStatusInfo:
    """Check the status of a file in the work's files metadata.
    
    Args:
        work: Work object.
        file_key: Key in the files JSON.
    
    Returns:
        FileStatusInfo with existence, path, hash, and validation status.
    """
    if not work.files or file_key not in work.files:
        return FileStatusInfo(
            exists=False,
            path=None,
            hash=None,
            hash_match=None,
            error=None
        )
    
    file_path = resolver.resolve_work_path(work, file_key)
    stored_hash = work.files[file_key]["hash"]

    # Check if file exists on disk
    if not file_path.exists():
        return FileStatusInfo(
            exists=True,
            path=file_path.name,
            hash=stored_hash,
            hash_match=False,
            error=f"File not found on disk: {file_path.name}"
        )
    
    # Compute current hash and compare
    try:
        current_hash = compute_file_hash(file_path)
        hash_match = current_hash == stored_hash
        
        return FileStatusInfo(
            exists=True,
            path=file_path.name,
            hash=stored_hash,
            hash_match=hash_match,
            error=None if hash_match else f"Hash mismatch: stored={stored_hash[:16]}..., current={current_hash[:16]}..."
        )
    except Exception as e:
        return FileStatusInfo(
            exists=True,
            path=file_path.name,
            hash=stored_hash,
            hash_match=False,
            error=f"Error computing hash: {str(e)}"
        )


@router.get(
    "/works",
    response_model=WorkListResponse,
    summary="List all works",
    description="Get a list of all works in the database with their sanitization status.",
)
async def list_works() -> WorkListResponse:
    """
    List all works with their sanitization status.
    
    Returns works sorted by ID descending (newest first).
    """
    with get_session() as session:
        works = session.query(Work).order_by(Work.id.desc()).all()
        
        work_items = []
        needs_sanitization = 0
        
        for work in works:
            has_sanitized = bool(work.files and "sanitized" in work.files)
            has_original_markdown = bool(work.files and "original_markdown" in work.files)
            
            if not has_sanitized and has_original_markdown:
                needs_sanitization += 1
            
            work_items.append(WorkListItem(
                id=work.id,
                title=work.title,
                authors=work.authors,
                year=work.year,
                work_type=work.work_type,
                has_sanitized=has_sanitized,
                has_original_markdown=has_original_markdown,
            ))
        
        return WorkListResponse(
            works=work_items,
            total=len(work_items),
            needs_sanitization=needs_sanitization,
        )


@router.get(
    "/work/{work_id}",
    response_model=WorkDetailResponse,
    summary="Get work detail",
    description="Get detailed information about a work including all file statuses.",
)
async def get_work_detail(work_id: int) -> WorkDetailResponse:
    """
    Get detailed work information with file status validation.
    
    Checks existence and hash validation for all sanitization-related files.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        # Check status of all relevant files
        original_markdown_status = _check_file_status(work, "original_markdown")
        titles_status = _check_file_status(work, "titles")
        title_changes_status = _check_file_status(work, "title_changes")
        sanitized_status = _check_file_status(work, "sanitized")
        
        return WorkDetailResponse(
            id=work.id,
            title=work.title,
            authors=work.authors,
            year=work.year,
            work_type=work.work_type,
            original_markdown=original_markdown_status,
            titles=titles_status,
            title_changes=title_changes_status,
            sanitized=sanitized_status,
        )


@router.post(
    "/work/{work_id}/extract-titles",
    response_model=ExtractTitlesFromWorkResponse,
    summary="Extract titles from work",
    description="Extract all headings from a work's markdown file.",
)
async def extract_titles_from_work_endpoint(
    work_id: int,
    request: ExtractTitlesFromWorkRequest
) -> ExtractTitlesFromWorkResponse:
    """
    Extract titles/headings from a work's markdown file.
    
    Creates a .titles.md file and updates the work's files metadata.
    """
    try:
        output_path = extract_titles_from_work(
            work_id=work_id,
            source_key=request.source_key,
            force=request.force,
            verbose=False
        )
        
        return ExtractTitlesFromWorkResponse(
            success=True,
            output_path=str(output_path),
            message=f"Titles extracted successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract titles: {str(e)}"
        )


@router.post(
    "/work/{work_id}/suggest-title-changes",
    response_model=SuggestTitleChangesResponse,
    summary="Suggest title changes",
    description="Use AI to suggest heading hierarchy improvements for a work.",
)
async def suggest_title_changes_endpoint(
    work_id: int,
    request: SuggestTitleChangesRequest
) -> SuggestTitleChangesResponse:
    """
    Generate AI-suggested title changes for a work.
    
    Analyzes the document structure using LLM and creates a .title_changes.md file.
    """
    try:
        output_path = suggest_heading_changes_from_work(
            work_id=work_id,
            source_key=request.source_key,
            use_full_model=request.use_full_model,
            force=request.force,
            verbose=False
        )
        
        return SuggestTitleChangesResponse(
            success=True,
            output_path=str(output_path),
            message=f"Title changes suggested successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest title changes: {str(e)}"
        )


@router.post(
    "/work/{work_id}/apply-title-changes",
    response_model=ApplyTitleChangesResponse,
    summary="Apply title changes",
    description="Apply the suggested title changes to create a sanitized markdown file.",
)
async def apply_title_changes_endpoint(
    work_id: int,
    request: ApplyTitleChangesRequest
) -> ApplyTitleChangesResponse:
    """
    Apply title changes to create sanitized markdown.
    
    Reads the .title_changes.md file and applies modifications to create .sanitized.md.
    """
    try:
        output_path = apply_title_changes_from_work(
            work_id=work_id,
            source_key=request.source_key,
            force=request.force,
            verbose=False
        )
        
        return ApplyTitleChangesResponse(
            success=True,
            output_path=str(output_path),
            message=f"Title changes applied successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply title changes: {str(e)}"
        )


@router.post(
    "/work/{work_id}/skip-apply",
    response_model=SkipApplyResponse,
    summary="Skip sanitization",
    description="Skip title changes and copy original markdown to sanitized version.",
)
async def skip_apply_endpoint(
    work_id: int,
    request: SkipApplyRequest
) -> SkipApplyResponse:
    """
    Skip sanitization and copy original to sanitized.
    
    Useful when the document doesn't need heading corrections.
    """
    try:
        output_path = skip_apply_from_work(
            work_id=work_id,
            source_key=request.source_key,
            force=request.force,
            verbose=False
        )
        
        return SkipApplyResponse(
            success=True,
            output_path=str(output_path),
            message=f"Original copied to sanitized: {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip-apply: {str(e)}"
        )


@router.post(
    "/work/{work_id}/verify-title-changes",
    response_model=VerifyTitleChangesResponse,
    summary="Verify title changes integrity",
    description="Verify that title changes file is consistent with titles and markdown files, and update hash if valid.",
)
async def verify_title_changes(
    work_id: int,
    request: VerifyTitleChangesRequest
) -> VerifyTitleChangesResponse:
    """
    Verify title changes file integrity and update hash.
    
    Validates that:
    - Titles file hash is correct
    - Every line in title_changes exists in titles file
    - Every line in titles file has a heading in markdown
    - Updates title_changes hash if all checks pass
    """
    try:
        result = verify_title_changes_integrity(
            work_id=work_id,
            source_key=request.source_key,
            verbose=False
        )
        
        return VerifyTitleChangesResponse(
            success=result["success"],
            message=result["message"],
            errors=result.get("errors", [])
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify title changes: {str(e)}"
        )


@router.get(
    "/work/{work_id}/prompt",
    response_model=PromptForWorkResponse,
    summary="Get LLM prompt for title changes",
    description="Build and return the LLM prompt for suggesting title changes without executing it.",
)
async def get_prompt_for_work(
    work_id: int,
    source_key: str = "original_markdown",
    force: bool = False
) -> PromptForWorkResponse:
    """
    Get the LLM prompt for suggesting title changes.
    
    This endpoint builds the prompt that would be sent to the LLM, allowing
    manual execution in an external LLM interface or inspection before running.
    """
    try:
        result = build_prompt_for_work(
            work_id=work_id,
            source_key=source_key,
            force=force
        )
        
        return PromptForWorkResponse(
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
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build prompt: {str(e)}"
        )


@router.post(
    "/work/{work_id}/manual-title-changes",
    response_model=ManualTitleChangesResponse,
    summary="Save manually generated title changes",
    description="Save title changes from a manually executed LLM response.",
)
async def save_manual_title_changes(
    work_id: int,
    request: ManualTitleChangesRequest
) -> ManualTitleChangesResponse:
    """
    Save title changes from a manual LLM response.
    
    Takes the raw response text from a manually executed LLM prompt and
    processes it to create a title_changes file, updating the database.
    """
    try:
        output_path = save_title_changes_from_response(
            work_id=work_id,
            source_key=request.source_key,
            llm_response=request.llm_response,
            force=request.force
        )
        
        return ManualTitleChangesResponse(
            success=True,
            output_path=str(output_path),
            message=f"Title changes saved successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save title changes: {str(e)}"
        )


@router.get(
    "/work/{work_id}/title-changes/content",
    response_model=TitleChangesContentResponse,
    summary="Get title changes file content",
    description="Retrieve the content of a work's title_changes file for viewing/editing.",
)
async def get_title_changes_content(work_id: int) -> TitleChangesContentResponse:
    """
    Get the content of a work's title_changes file.
    
    Retrieves the raw markdown content from the title_changes file referenced
    in work.files["title_changes"].
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "title_changes" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a title_changes file"
            )
        
        title_changes_info = work.files["title_changes"]
        title_changes_path = Path(title_changes_info["path"])
        
        if not title_changes_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Title changes file not found on disk: {title_changes_path}"
            )
        
        # Read file content
        try:
            content = title_changes_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read title changes file: {str(e)}"
            )
        
        # Get current hash
        current_hash = compute_file_hash(title_changes_path)
        
        return TitleChangesContentResponse(
            content=content,
            filename=title_changes_path.name,
            hash=current_hash
        )


@router.put(
    "/work/{work_id}/title-changes/content",
    response_model=TitleChangesContentResponse,
    summary="Update title changes file content",
    description="Update the content of a work's title_changes file and update its hash.",
)
async def update_title_changes_content(
    work_id: int,
    request: UpdateTitleChangesContentRequest
) -> TitleChangesContentResponse:
    """
    Update the content of a work's title_changes file.
    
    Writes the new content to the file, computes a new hash, and updates
    the work.files["title_changes"]["hash"] in the database.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "title_changes" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a title_changes file"
            )
        
        title_changes_info = work.files["title_changes"]
        title_changes_path = Path(title_changes_info["path"])
        
        if not title_changes_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Title changes file not found on disk: {title_changes_path}"
            )
        
        # Make file writable
        try:
            set_file_writable(title_changes_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to make file writable: {str(e)}"
            )
        
        # Write new content
        try:
            title_changes_path.write_text(request.content, encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write file: {str(e)}"
            )
        
        # Make file read-only again
        try:
            set_file_readonly(title_changes_path)
        except Exception as e:
            # Not critical, log but continue
            print(f"Warning: Failed to set file read-only: {e}")
        
        # Compute new hash
        new_hash = compute_file_hash(title_changes_path)
        
        # Update work.files with new hash
        updated_files = dict(work.files) if work.files else {}
        updated_files["title_changes"] = {
            "path": title_changes_path.name,
            "hash": new_hash
        }
        work.files = updated_files
        
        session.commit()
        session.refresh(work)
        
        return TitleChangesContentResponse(
            content=request.content,
            filename=title_changes_path.name,
            hash=new_hash
        )


@router.get(
    "/work/{work_id}/titles/content",
    response_model=TitlesContentResponse,
    summary="Get titles file content",
    description="Retrieve the content of a work's titles file for viewing/editing.",
)
async def get_titles_content(work_id: int) -> TitlesContentResponse:
    """
    Get the content of a work's titles file.
    
    Retrieves the raw markdown content from the titles file referenced
    in work.files["titles"].
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a titles file"
            )
        
        titles_info = work.files["titles"]
        titles_path = Path(titles_info["path"])
        
        if not titles_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Titles file not found on disk: {titles_path}"
            )
        
        # Read file content
        try:
            content = titles_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read titles file: {str(e)}"
            )
        
        # Get current hash
        current_hash = compute_file_hash(titles_path)
        
        return TitlesContentResponse(
            content=content,
            filename=titles_path.name,
            hash=current_hash
        )


@router.put(
    "/work/{work_id}/titles/content",
    response_model=TitlesContentResponse,
    summary="Update titles file content",
    description="Update the content of a work's titles file and update its hash.",
)
async def update_titles_content(
    work_id: int,
    request: UpdateTitlesContentRequest
) -> TitlesContentResponse:
    """
    Update the content of a work's titles file.
    
    Writes the new content to the file, computes a new hash, and updates
    the work.files["titles"]["hash"] in the database.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a titles file"
            )
        
        titles_info = work.files["titles"]
        titles_path = Path(titles_info["path"])
        
        if not titles_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Titles file not found on disk: {titles_path}"
            )
        
        # Make file writable
        try:
            set_file_writable(titles_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to make file writable: {str(e)}"
            )
        
        # Write new content
        try:
            titles_path.write_text(request.content, encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write file: {str(e)}"
            )
        
        # Make file read-only again
        try:
            set_file_readonly(titles_path)
        except Exception as e:
            # Not critical, log but continue
            print(f"Warning: Failed to set file read-only: {e}")
        
        # Compute new hash of the titles file
        new_hash = compute_file_hash(titles_path)
        
        # Update work.files with new hash
        # Must create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files["titles"] = {
            "path": titles_path.name,
            "hash": new_hash
        }
        work.files = updated_files
        
        session.commit()
        session.refresh(work)
        
        return TitlesContentResponse(
            content=request.content,
            filename=titles_path.name,
            hash=new_hash
        )


@router.post(
    "/add-sanitized",
    response_model=AddSanitizedMarkdownResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add sanitized markdown directly",
    description="Create a new work with sanitized markdown content directly, skipping the conversion and sanitization workflow.",
)
async def add_sanitized_markdown(
    request: AddSanitizedMarkdownRequest
) -> AddSanitizedMarkdownResponse:
    """
    Add a new work with pre-sanitized markdown content.
    
    Creates a .sanitized.md file in the output directory and a database entry
    with the bibliographic information. The work.toc is set to empty since
    sanitization is being skipped.
    
    This is useful for documents that are already clean and don't need
    the standard sanitization workflow.
    """
    import re
    
    try:
        # Validate filename (alphanumeric, underscores, hyphens only)
        if not re.match(r'^[a-zA-Z0-9_-]+$', request.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename must contain only alphanumeric characters, underscores, and hyphens"
            )
        
        # Get output directory from config
        config = load_config()
        output_dir = Path(config.paths.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the sanitized file path
        sanitized_path = output_dir / f"{request.filename}.sanitized.md"
        
        # Check if file already exists
        if sanitized_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file with this name already exists: {sanitized_path.name}"
            )
        
        # Write the sanitized content
        sanitized_path.write_text(request.content, encoding='utf-8')
        
        # Compute content hash
        content_hash = compute_file_hash(sanitized_path)
        
        # Set file to read-only
        set_file_readonly(sanitized_path)
        
        # Check for duplicate content
        with get_session() as session:
            existing_work = session.query(Work).filter(
                Work.content_hash == content_hash
            ).first()
            
            if existing_work:
                # Remove the file we just created
                set_file_writable(sanitized_path)
                sanitized_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A work with the same content already exists (ID: {existing_work.id}, Title: '{existing_work.title}')"
                )
        
        # Create files metadata
        files_metadata = {
            "sanitized": {
                "path": sanitized_path.name,
                "hash": content_hash
            }
        }
        
        # Create the work entry
        work = Work(
            title=request.title,
            markdown_path=sanitized_path.name,
            authors=request.authors,
            year=request.year,
            publisher=request.publisher,
            isbn=request.isbn,
            abstract=request.edition,  # Store edition in abstract field
            content_hash=content_hash,
            toc=[],  # Empty TOC since we're skipping sanitization
            files=files_metadata
        )
        
        # Insert into database
        with get_session() as session:
            session.add(work)
            session.commit()
            session.refresh(work)
            work_id = work.id
        
        return AddSanitizedMarkdownResponse(
            success=True,
            work_id=work_id,
            output_path=str(sanitized_path),
            message=f"Work created successfully with ID {work_id}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add sanitized markdown: {str(e)}"
        )





# Interactive title changes table endpoints

@router.get(
    "/work/{work_id}/title-changes/table",
    response_model=HeadingTableResponse,
    summary="Get title changes as interactive table data",
    description="Fetch all headings from source markdown merged with title changes suggestions for table display.",
)
async def get_title_changes_table(work_id: int) -> HeadingTableResponse:
    """
    Get title changes as structured table data (all headings merged).

    Returns ALL headings from the source markdown file, with:
    - Lines in title_changes.md: use their suggested action/title
    - Lines NOT in title_changes.md: default to original heading/title (NO_CHANGE)

    This provides complete document context for the interactive table editor.
    """
    from vulcanlab.sanitization.title_changes_interactive import get_title_changes_table_data
    from vulcanlab.utils.file_utils import compute_file_hash

    try:
        # Get merged table data from module
        table_data = get_title_changes_table_data(
            work_id=work_id,
            source_key="original_markdown"
        )

        # Get title_changes file info for hash and filename
        with get_session() as session:
            work = session.query(Work).filter(Work.id == work_id).first()

            if not work:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work with ID {work_id} not found"
                )

            # Get title_changes file info (may not exist yet)
            title_changes_key = "title_changes"
            if title_changes_key in work.files:
                title_changes_info = work.files[title_changes_key]
                filename = Path(title_changes_info["path"]).name
                file_hash = title_changes_info["hash"]
            else:
                # File doesn't exist yet - use placeholder values
                filename = f"work_{work_id}.title_changes.md"
                file_hash = ""

        return HeadingTableResponse(
            work_id=table_data["work_id"],
            source_file=table_data["source_file"],
            rows=table_data["rows"],
            filename=filename,
            hash=file_hash
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File hash mismatch: {str(e)}"
        )


@router.put(
    "/work/{work_id}/title-changes/table",
    response_model=HeadingTableResponse,
    summary="Save title changes from interactive table data",
    description="Update title changes file from table data. Only actual changes are saved to the file.",
)
async def update_title_changes_table(
    work_id: int,
    request: UpdateHeadingTableRequest
) -> HeadingTableResponse:
    """
    Save table data back to .title_changes.md file.

    The backend filters rows to only save actual changes:
    - Only rows where suggested_action != original_heading OR suggested_title != original_title
    - If all rows are NO_CHANGE, creates empty changes section (valid state)
    """
    from vulcanlab.sanitization.title_changes_interactive import reconstruct_title_changes_markdown
    from vulcanlab.utils.file_utils import (
        compute_file_hash,
        set_file_writable,
        set_file_readonly,
        is_file_readonly
    )

    try:
        with get_session() as session:
            work = session.query(Work).filter(Work.id == work_id).first()

            if not work:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work with ID {work_id} not found"
                )

            if not work.files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Work {work_id} has no files metadata"
                )

            # Get source_file path from first row or construct from work files
            if not request.rows:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No rows provided in request"
                )

            # Determine source file from work.files
            if "original_markdown" in work.files:
                markdown_path = resolver.resolve_work_path(work, "original_markdown")
                source_file = f"./{markdown_path.name}"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Work does not have original_markdown in files metadata"
                )

            # Convert Pydantic models to dicts for module function
            rows_data = [row.model_dump() for row in request.rows]

            # Reconstruct markdown content
            markdown_content = reconstruct_title_changes_markdown(
                source_file=source_file,
                rows=rows_data
            )

            # Determine title_changes file path
            title_changes_key = "title_changes"
            if title_changes_key in work.files:
                # Update existing file
                title_changes_path = resolver.resolve_work_path(work, title_changes_key)
            else:
                # Create new file
                output_dir = markdown_path.parent
                title_changes_path = output_dir / f"{markdown_path.stem}.title_changes.md"

            # Make file writable if it exists and is read-only
            if title_changes_path.exists() and is_file_readonly(title_changes_path):
                set_file_writable(title_changes_path)

            # Write content
            title_changes_path.write_text(markdown_content, encoding='utf-8')

            # Set read-only
            set_file_readonly(title_changes_path)

            # Compute new hash
            new_hash = compute_file_hash(title_changes_path)

            # Update work.files metadata
            updated_files = dict(work.files) if work.files else {}
            updated_files[title_changes_key] = {
                "path": title_changes_path.name,
                "hash": new_hash
            }
            work.files = updated_files

            session.commit()
            session.refresh(work)

            return HeadingTableResponse(
                work_id=work_id,
                source_file=source_file,
                rows=request.rows,
                filename=title_changes_path.name,
                hash=new_hash
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
