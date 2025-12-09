"""
API router for prompt template management.

Provides CRUD endpoints for managing versioned prompt templates.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from vulcanlab.data.database import get_db_session
from vulcanlab.data.models.prompt_template import PromptTemplate
from vulcanlab.data.models.prompt_meta import PromptMeta
from vulcanlab_api.schemas.templates import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    FunctionTemplateSummary,
    TemplateSummary,
    TemplateListResponse,
    PromptMetaCreate,
    PromptMetaUpdate,
    PromptMetaResponse,
)

router = APIRouter(prefix="/settings/templates", tags=["Settings"])


@router.get("/", response_model=TemplateListResponse)
def list_all_templates(session: Session = Depends(get_db_session)):
    """List all template functions with version summaries.

    Returns a grouped list of all prompt templates organized by function tag,
    with summary information for each version including which version is active.
    """
    # Get all templates ordered by function_tag and version
    all_templates = session.query(PromptTemplate).order_by(
        PromptTemplate.function_tag,
        desc(PromptTemplate.version)
    ).all()

    # Group by function_tag
    grouped = {}
    for template in all_templates:
        if template.function_tag not in grouped:
            grouped[template.function_tag] = []
        grouped[template.function_tag].append(template)

    # Build response
    function_summaries = []
    for function_tag, templates in grouped.items():
        active_version = None
        version_summaries = []

        for template in templates:
            if template.is_active:
                active_version = template.version
            version_summaries.append(TemplateSummary(
                version=template.version,
                title=template.title,
                is_active=template.is_active,
                created_at=template.created_at
            ))

        function_summaries.append(FunctionTemplateSummary(
            function_tag=function_tag,
            active_version=active_version,
            versions=version_summaries
        ))

    return TemplateListResponse(templates=function_summaries)


@router.get("/{function_tag}", response_model=List[PromptTemplateResponse])
def get_templates_for_function(
    function_tag: str,
    session: Session = Depends(get_db_session)
):
    """Get all versions for a specific function tag.

    Returns all template versions for the given function_tag,
    ordered by version number (newest first). Includes variable
    metadata from prompt_meta if available.

    Args:
        function_tag: The function identifier (e.g., 'query_expansion')

    Returns:
        List of template versions with variable metadata

    Raises:
        404: If no templates found for the function_tag
    """
    templates = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag
    ).order_by(desc(PromptTemplate.version)).all()

    if not templates:
        raise HTTPException(
            status_code=404,
            detail=f"No templates found for function_tag: {function_tag}"
        )

    # Get prompt_meta for this function_tag
    prompt_meta = session.query(PromptMeta).filter(
        PromptMeta.function_tag == function_tag
    ).first()

    # Add variables to each template response
    result = []
    for template in templates:
        template_dict = {
            "id": template.id,
            "function_tag": template.function_tag,
            "version": template.version,
            "title": template.title,
            "template_content": template.template_content,
            "is_active": template.is_active,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "variables": prompt_meta.variables if prompt_meta else None
        }
        result.append(template_dict)

    return result


@router.get("/{function_tag}/{version}", response_model=PromptTemplateResponse)
def get_template_version(
    function_tag: str,
    version: int,
    session: Session = Depends(get_db_session)
):
    """Get a specific template version.

    Retrieves the complete template data for a specific function and version.

    Args:
        function_tag: The function identifier
        version: The version number

    Returns:
        Complete template data including content

    Raises:
        404: If template not found
    """
    template = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.version == version
    ).first()

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {function_tag} v{version}"
        )

    return template


@router.post("/{function_tag}", response_model=PromptTemplateResponse, status_code=201)
def create_new_version(
    function_tag: str,
    template_data: PromptTemplateCreate,
    session: Session = Depends(get_db_session)
):
    """Create a new version for a function tag.

    Creates a new template version with auto-incremented version number.
    The new version is created as inactive by default.

    Args:
        function_tag: The function identifier
        template_data: Template title and content

    Returns:
        Created template with assigned version number

    Raises:
        400: If template_content has invalid PromptTemplate format
    """
    # Get the highest existing version for this function_tag
    max_version_result = session.query(
        PromptTemplate.version
    ).filter(
        PromptTemplate.function_tag == function_tag
    ).order_by(desc(PromptTemplate.version)).first()

    new_version = 1 if max_version_result is None else max_version_result[0] + 1

    # Create new template (not active by default)
    new_template = PromptTemplate(
        function_tag=function_tag,
        version=new_version,
        title=template_data.title,
        template_content=template_data.template_content,
        is_active=False
    )

    session.add(new_template)
    session.commit()
    session.refresh(new_template)

    return new_template


@router.put("/{function_tag}/{version}", response_model=PromptTemplateResponse)
def update_template(
    function_tag: str,
    version: int,
    template_data: PromptTemplateUpdate,
    session: Session = Depends(get_db_session)
):
    """Update an existing template's content (overwrite).

    Updates the title and/or content of an existing template version.
    This modifies the template in-place without creating a new version.

    Args:
        function_tag: The function identifier
        version: The version number to update
        template_data: Updated title and/or content

    Returns:
        Updated template

    Raises:
        404: If template not found
        400: If template_content has invalid PromptTemplate format
    """
    template = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.version == version
    ).first()

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {function_tag} v{version}"
        )

    # Update fields if provided
    if template_data.title is not None:
        template.title = template_data.title
    if template_data.template_content is not None:
        template.template_content = template_data.template_content

    session.commit()
    session.refresh(template)

    return template


@router.put("/{function_tag}/{version}/activate", response_model=PromptTemplateResponse)
def set_active_version(
    function_tag: str,
    version: int,
    session: Session = Depends(get_db_session)
):
    """Set a specific version as the active template for a function tag.

    Activates the specified template version and deactivates all other
    versions for the same function_tag. Only one template per function
    can be active at a time.

    Args:
        function_tag: The function identifier
        version: The version number to activate

    Returns:
        Activated template

    Raises:
        404: If template not found
    """
    # Verify the target template exists
    target_template = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.version == version
    ).first()

    if not target_template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {function_tag} v{version}"
        )

    # Deactivate all other versions for this function_tag
    session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.is_active == True
    ).update({"is_active": False})

    # Activate the target version
    target_template.is_active = True

    session.commit()
    session.refresh(target_template)

    return target_template
