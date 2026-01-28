"""
Unit tests for the expansions API endpoints.

Tests the expansion CRUD and operation endpoints in vulcanlab_api.routers.expansions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from vulcanlab_api.routers.expansions import (
    create_expansion,
    list_expansions,
    get_expansion,
    get_section,
    run_breakdown,
    expand_section_endpoint,
    generate_section_endpoint,
    save_manual_response_endpoint,
    combine_sections_endpoint,
    run_automatic,
    get_expansion_for_result,
)
from vulcanlab_api.schemas.expansions import (
    CreateExpansionRequest,
    ManualResponseRequest,
)
from vulcanlab.data.models.expansion import (
    ExpansionMode,
    ExpansionStatus,
    SectionStatus,
)


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_result():
    """Create a mock Result object."""
    result = MagicMock()
    result.id = 123
    result.query_id = 100
    result.response_text = "This is a test answer about working memory..."
    result.created_at = datetime.now()
    return result


@pytest.fixture
def mock_expansion():
    """Create a mock AnswerExpansion object."""
    expansion = MagicMock()
    expansion.id = 456
    expansion.result_id = 123
    expansion.query_id = 100
    expansion.mode = ExpansionMode.AUTOMATIC
    expansion.status = ExpansionStatus.CREATED
    expansion.combined_report = None
    expansion.expansion_metadata = None
    expansion.created_at = datetime.now()
    expansion.updated_at = datetime.now()
    return expansion


@pytest.fixture
def mock_section():
    """Create a mock ExpansionSection object."""
    section = MagicMock()
    section.id = 1
    section.expansion_id = 456
    section.order = 1
    section.heading = "Introduction to Working Memory"
    section.summary = "Overview of working memory concepts"
    section.expansion_prompt = "Explain the key components of working memory"
    section.expanded_queries = None
    section.hyde_answer = None
    section.intent = None
    section.entities = None
    section.clean_retrieval_context = None
    section.augmented_prompt = None
    section.response_text = None
    section.status = SectionStatus.PENDING
    section.error_message = None
    section.created_at = datetime.now()
    section.updated_at = datetime.now()
    return section


@pytest.fixture
def mock_completed_section():
    """Create a mock completed ExpansionSection object."""
    section = MagicMock()
    section.id = 1
    section.expansion_id = 456
    section.order = 1
    section.heading = "Introduction to Working Memory"
    section.summary = "Overview of working memory concepts"
    section.expansion_prompt = "Explain the key components of working memory"
    section.expanded_queries = {"queries": ["What is working memory?"]}
    section.hyde_answer = "Working memory is a cognitive system..."
    section.intent = "DEFINITION"
    section.entities = {"entities": ["working memory"]}
    section.clean_retrieval_context = {"chunks": []}
    section.augmented_prompt = "Based on the context..."
    section.response_text = "Working memory is a fundamental cognitive process..."
    section.status = SectionStatus.COMPLETED
    section.error_message = None
    section.created_at = datetime.now()
    section.updated_at = datetime.now()
    return section


def create_mock_session_with_result(result, expansion=None):
    """Create a mock session that returns the specified result and expansion."""
    session = MagicMock()
    query_mock = MagicMock()

    # Configure query mock for different filter calls
    def filter_side_effect(*args, **kwargs):
        return query_mock

    query_mock.filter = MagicMock(side_effect=filter_side_effect)

    # Default first() returns
    def first_returns():
        # This will be called multiple times, return result first, then expansion
        return result

    query_mock.first = MagicMock(side_effect=[result, expansion])

    session.query = MagicMock(return_value=query_mock)
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.flush = MagicMock()

    return session


# =============================================================================
# Test: create_expansion
# =============================================================================


@pytest.mark.asyncio
async def test_create_expansion_returns_id(mock_result):
    """Test that POST /expansions/ creates record and returns expansion_id."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        # Result exists, no existing expansion
        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(side_effect=[mock_result, None])

        session.query = MagicMock(return_value=query)
        session.add = MagicMock()
        session.commit = MagicMock()

        # Mock the expansion getting an ID after commit
        def set_expansion_id(exp):
            exp.id = 456

        session.add.side_effect = set_expansion_id

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        request = CreateExpansionRequest(result_id=123, mode="automatic")
        response = await create_expansion(request)

        assert response.expansion_id == 456
        assert response.status == "created"
        assert "successfully" in response.message.lower()


@pytest.mark.asyncio
async def test_create_expansion_invalid_result():
    """Test that POST /expansions/ returns 404 for nonexistent result."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        # Result does not exist
        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=None)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        request = CreateExpansionRequest(result_id=999, mode="automatic")

        with pytest.raises(HTTPException) as exc_info:
            await create_expansion(request)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_expansion_duplicate(mock_result, mock_expansion):
    """Test that POST /expansions/ returns 409 if expansion already exists."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        # Result exists, expansion also exists
        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(side_effect=[mock_result, mock_expansion])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        request = CreateExpansionRequest(result_id=123, mode="automatic")

        with pytest.raises(HTTPException) as exc_info:
            await create_expansion(request)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail.lower()


# =============================================================================
# Test: list_expansions
# =============================================================================


@pytest.mark.asyncio
async def test_list_expansions_pagination(mock_expansion, mock_section):
    """Test that GET /expansions/ returns paginated list."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        # For count
        query.count = MagicMock(return_value=10)

        # For listing
        query.order_by = MagicMock(return_value=query)
        query.offset = MagicMock(return_value=query)
        query.limit = MagicMock(return_value=query)
        query.all = MagicMock(side_effect=[[mock_expansion], [mock_section]])

        query.filter = MagicMock(return_value=query)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        response = await list_expansions(offset=0, limit=10)

        assert response.total == 10
        assert len(response.expansions) == 1
        assert response.expansions[0].id == 456


# =============================================================================
# Test: get_expansion
# =============================================================================


@pytest.mark.asyncio
async def test_get_expansion_detail(mock_expansion, mock_section):
    """Test that GET /expansions/{id} returns full detail with sections."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.order_by = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_expansion)
        query.all = MagicMock(return_value=[mock_section])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        response = await get_expansion(456)

        assert response.id == 456
        assert response.result_id == 123
        assert len(response.sections) == 1
        assert response.sections[0].heading == "Introduction to Working Memory"


@pytest.mark.asyncio
async def test_get_expansion_not_found():
    """Test that GET /expansions/{id} returns 404 for nonexistent expansion."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=None)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_expansion(999)

        assert exc_info.value.status_code == 404


# =============================================================================
# Test: run_breakdown
# =============================================================================


@pytest.mark.asyncio
async def test_breakdown_updates_status(mock_expansion, mock_result):
    """Test that POST /expansions/{id}/breakdown updates status and creates sections."""
    mock_expansion.status = ExpansionStatus.CREATED

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.create_langchain_chat') as mock_llm, \
         patch('vulcanlab_api.routers.expansions.generate_breakdown_prompt') as mock_prompt, \
         patch('vulcanlab_api.routers.expansions.parse_breakdown_response') as mock_parse, \
         patch('vulcanlab_api.routers.expansions.validate_answer_length') as mock_validate, \
         patch('vulcanlab_api.routers.expansions.estimate_answer_tokens') as mock_estimate:

        session = MagicMock()
        query = MagicMock()

        # First query: expansion, second: section count, third: result, fourth: sections
        query.filter = MagicMock(return_value=query)
        query.count = MagicMock(return_value=0)  # No existing sections
        query.first = MagicMock(side_effect=[mock_expansion, mock_result])
        query.order_by = MagicMock(return_value=query)

        # Create mock sections after breakdown
        mock_created_section = MagicMock()
        mock_created_section.id = 1
        mock_created_section.order = 1
        mock_created_section.heading = "Section 1"
        mock_created_section.summary = "Summary 1"
        mock_created_section.status = SectionStatus.PENDING
        mock_created_section.error_message = None

        query.all = MagicMock(return_value=[mock_created_section])

        session.query = MagicMock(return_value=query)
        session.add = MagicMock()
        session.commit = MagicMock()

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        # Mock LLM
        mock_llm_stack = MagicMock()
        mock_llm_client = MagicMock()
        mock_llm_stack.chat = mock_llm_client
        mock_llm.return_value = mock_llm_stack

        # Mock structured output
        mock_structured = MagicMock()
        mock_llm_client.with_structured_output = MagicMock(return_value=mock_structured)
        mock_structured.invoke = MagicMock(return_value=MagicMock())

        # Mock prompt and parse
        mock_prompt.return_value = "Test prompt"
        mock_section_data = MagicMock()
        mock_section_data.order = 1
        mock_section_data.heading = "Section 1"
        mock_section_data.summary = "Summary 1"
        mock_section_data.expansion_prompt = "Prompt 1"
        mock_parse.return_value = [mock_section_data]

        mock_estimate.return_value = 1000

        response = await run_breakdown(456)

        assert response.expansion_id == 456
        assert response.status == "breakdown_complete"
        assert response.section_count == 1


@pytest.mark.asyncio
async def test_breakdown_already_done(mock_expansion):
    """Test that POST /expansions/{id}/breakdown returns 409 if already done."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_expansion)
        query.count = MagicMock(return_value=5)  # Sections already exist

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await run_breakdown(456)

        assert exc_info.value.status_code == 409
        assert "already completed" in exc_info.value.detail.lower()


# =============================================================================
# Test: expand_section_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_expand_section_success(mock_expansion, mock_section):
    """Test that POST /expansions/{id}/sections/{id}/expand runs expansion."""
    mock_section.status = SectionStatus.PENDING

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.create_langchain_chat') as mock_llm, \
         patch('vulcanlab_api.routers.expansions.expand_section') as mock_expand:

        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(side_effect=[mock_section, mock_expansion])

        session.query = MagicMock(return_value=query)
        session.commit = MagicMock()

        def refresh_side_effect(section):
            section.status = SectionStatus.READY

        session.refresh = MagicMock(side_effect=refresh_side_effect)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_llm_stack = MagicMock()
        mock_llm.return_value = mock_llm_stack

        response = await expand_section_endpoint(456, 1)

        assert response.section_id == 1
        assert response.expansion_id == 456
        mock_expand.assert_called_once()


@pytest.mark.asyncio
async def test_expand_section_not_found():
    """Test that expand returns 404 for nonexistent section."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=None)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await expand_section_endpoint(456, 999)

        assert exc_info.value.status_code == 404


# =============================================================================
# Test: generate_section_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_generate_section_success(mock_section):
    """Test that POST /expansions/{id}/sections/{id}/generate runs generation."""
    mock_section.status = SectionStatus.READY

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.create_langchain_chat') as mock_llm, \
         patch('vulcanlab_api.routers.expansions.generate_section') as mock_generate:

        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_section)

        session.query = MagicMock(return_value=query)

        def refresh_side_effect(section):
            section.status = SectionStatus.COMPLETED

        session.refresh = MagicMock(side_effect=refresh_side_effect)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_llm_stack = MagicMock()
        mock_llm.return_value = mock_llm_stack

        response = await generate_section_endpoint(456, 1)

        assert response.section_id == 1
        mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_section_not_ready(mock_section):
    """Test that generate returns 400 if section is not ready."""
    mock_section.status = SectionStatus.PENDING  # Not ready

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_section)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await generate_section_endpoint(456, 1)

        assert exc_info.value.status_code == 400
        assert "not ready" in exc_info.value.detail.lower()


# =============================================================================
# Test: save_manual_response_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_manual_response_success(mock_section):
    """Test that POST /expansions/{id}/sections/{id}/manual saves response."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.save_manual_response') as mock_save:

        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_section)

        session.query = MagicMock(return_value=query)

        def refresh_side_effect(section):
            section.status = SectionStatus.COMPLETED

        session.refresh = MagicMock(side_effect=refresh_side_effect)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        request = ManualResponseRequest(response_text="Manual response text")
        response = await save_manual_response_endpoint(456, 1, request)

        assert response.section_id == 1
        mock_save.assert_called_once_with(1, "Manual response text", session)


# =============================================================================
# Test: combine_sections_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_combine_requires_all_complete(mock_expansion, mock_section):
    """Test that combine returns 400 if sections not all completed."""
    mock_section.status = SectionStatus.PENDING  # Not completed

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_expansion)
        query.all = MagicMock(return_value=[mock_section])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await combine_sections_endpoint(456)

        assert exc_info.value.status_code == 400
        assert "not completed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_combine_success(mock_expansion, mock_completed_section):
    """Test that combine succeeds when all sections completed."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.combine_sections') as mock_combine:

        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_expansion)
        query.all = MagicMock(return_value=[mock_completed_section])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_combine.return_value = "Combined report content..."

        response = await combine_sections_endpoint(456)

        assert response.expansion_id == 456
        assert response.status == "completed"
        mock_combine.assert_called_once()


# =============================================================================
# Test: run_automatic
# =============================================================================


@pytest.mark.asyncio
async def test_run_automatic_mode(mock_expansion, mock_section):
    """Test that POST /expansions/{id}/run executes full pipeline."""
    mock_expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.run_breakdown') as mock_breakdown, \
         patch('vulcanlab_api.routers.expansions.expand_section_endpoint') as mock_expand, \
         patch('vulcanlab_api.routers.expansions.generate_section_endpoint') as mock_generate, \
         patch('vulcanlab_api.routers.expansions.combine_sections_endpoint') as mock_combine:

        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_expansion)
        query.all = MagicMock(return_value=[mock_section])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        # Mock successful operations
        mock_expand.return_value = MagicMock(status="ready")
        mock_generate.return_value = MagicMock(status="completed")
        mock_combine.return_value = MagicMock(status="completed")

        response = await run_automatic(456)

        assert response.expansion_id == 456
        assert response.sections_processed == 1


@pytest.mark.asyncio
async def test_run_automatic_already_completed(mock_expansion):
    """Test that run_automatic returns 400 if already completed."""
    mock_expansion.status = ExpansionStatus.COMPLETED

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_expansion)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await run_automatic(456)

        assert exc_info.value.status_code == 400
        assert "already completed" in exc_info.value.detail.lower()


# =============================================================================
# Test: get_expansion_for_result
# =============================================================================


@pytest.mark.asyncio
async def test_get_expansion_for_result_exists(mock_result, mock_expansion):
    """Test that GET /expansions/by-result/{id} returns expansion if exists."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(side_effect=[mock_result, mock_expansion])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        response = await get_expansion_for_result(123)

        assert response.result_id == 123
        assert response.has_expansion is True
        assert response.expansion_id == 456


@pytest.mark.asyncio
async def test_get_expansion_for_result_not_exists(mock_result):
    """Test that GET /expansions/by-result/{id} returns has_expansion=False if no expansion."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(side_effect=[mock_result, None])

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        response = await get_expansion_for_result(123)

        assert response.result_id == 123
        assert response.has_expansion is False
        assert response.expansion_id is None


@pytest.mark.asyncio
async def test_get_expansion_for_result_invalid_result():
    """Test that GET /expansions/by-result/{id} returns 404 for invalid result."""
    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session:
        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=None)

        session.query = MagicMock(return_value=query)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_expansion_for_result(999)

        assert exc_info.value.status_code == 404


# =============================================================================
# Test: retry_failed_section
# =============================================================================


@pytest.mark.asyncio
async def test_retry_failed_section(mock_section):
    """Test that a failed section can be retried via expand endpoint."""
    mock_section.status = SectionStatus.FAILED

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.create_langchain_chat') as mock_llm, \
         patch('vulcanlab_api.routers.expansions.expand_section') as mock_expand:

        session = MagicMock()
        query = MagicMock()

        mock_expansion = MagicMock()
        mock_expansion.status = ExpansionStatus.SECTIONS_IN_PROGRESS

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(side_effect=[mock_section, mock_expansion])

        session.query = MagicMock(return_value=query)
        session.commit = MagicMock()

        def refresh_side_effect(section):
            section.status = SectionStatus.READY

        session.refresh = MagicMock(side_effect=refresh_side_effect)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_llm_stack = MagicMock()
        mock_llm.return_value = mock_llm_stack

        response = await expand_section_endpoint(456, 1)

        assert response.section_id == 1
        # The expand was called, indicating retry worked
        mock_expand.assert_called_once()


@pytest.mark.asyncio
async def test_retry_failed_section_generate():
    """Test that a failed section can be retried via generate endpoint."""
    mock_section = MagicMock()
    mock_section.id = 1
    mock_section.expansion_id = 456
    mock_section.status = SectionStatus.FAILED  # Failed status allows retry

    with patch('vulcanlab_api.routers.expansions.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.expansions.create_langchain_chat') as mock_llm, \
         patch('vulcanlab_api.routers.expansions.generate_section') as mock_generate:

        session = MagicMock()
        query = MagicMock()

        query.filter = MagicMock(return_value=query)
        query.first = MagicMock(return_value=mock_section)

        session.query = MagicMock(return_value=query)

        def refresh_side_effect(section):
            section.status = SectionStatus.COMPLETED

        session.refresh = MagicMock(side_effect=refresh_side_effect)

        mock_get_session.return_value.__enter__ = MagicMock(return_value=session)
        mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_llm_stack = MagicMock()
        mock_llm.return_value = mock_llm_stack

        # Since status is FAILED, it should be allowed to retry generate
        response = await generate_section_endpoint(456, 1)

        assert response.section_id == 1
        mock_generate.assert_called_once()
