"""
Unit tests for research_planner module.

Tests analyze_collection, generate_research_plan, and validate_research_plan functions.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from vulcanlab.research.research_planner import (
    analyze_collection,
    generate_research_plan,
    validate_research_plan,
    ResearchPlan,
    SubQuestion,
)
from vulcanlab.data.models.collection import Collection
from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.enums import CollectionItemType
from vulcanlab.data.models.result import Result
from vulcanlab.data.models.work import Work


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def sample_collection():
    """Create a sample collection for testing."""
    collection = Collection(
        id=1,
        name="Test Collection",
        description="A test collection for research planning",
        tags=["research", "testing"]
    )
    return collection


@pytest.fixture
def sample_items():
    """Create sample collection items."""
    return [
        CollectionItem(
            id=1,
            collection_id=1,
            item_type=CollectionItemType.EXCERPT,
            link="/search/result/1/2/3",
            note="Key finding about topic A",
            order=Decimal("1.0")
        ),
        CollectionItem(
            id=2,
            collection_id=1,
            item_type=CollectionItemType.RESEARCH_RESULT,
            link="/rag/5/results/10",
            note="Analysis of topic B",
            order=Decimal("2.0")
        ),
        CollectionItem(
            id=3,
            collection_id=1,
            item_type=CollectionItemType.RESEARCH_QUERY,
            link="/rag/5",
            note="Query about topic C",
            order=Decimal("3.0")
        ),
    ]


@pytest.fixture
def valid_research_plan():
    """Create a valid research plan for testing."""
    return {
        "research_goal": "Understand the impact of AI on software development",
        "key_themes": ["automation", "productivity", "code quality"],
        "sub_questions": [
            {
                "id": "sq1",
                "question": "How does AI automation affect developer productivity?",
                "rationale": "This is foundational to understanding the broader impact",
                "estimated_tokens": 30000,
                "relevant_items": [1, 2]
            },
            {
                "id": "sq2",
                "question": "What are the trade-offs in code quality when using AI tools?",
                "rationale": "Quality concerns are critical for adoption",
                "estimated_tokens": 25000,
                "relevant_items": [2, 3]
            }
        ],
        "synthesis_approach": "Compare and contrast findings across themes to generate comprehensive report"
    }


class TestAnalyzeCollection:
    """Tests for analyze_collection function."""

    def test_analyze_collection_returns_correct_structure(
        self, mock_session, sample_collection, sample_items
    ):
        """Test that analyze_collection returns correct metadata structure."""
        # Setup mock session to return collection and items
        def mock_get(model, ident):
            if model == Collection:
                return sample_collection
            return None
        mock_session.get.side_effect = mock_get

        # Mock count query results
        count_result = [
            (CollectionItemType.EXCERPT, 1),
            (CollectionItemType.RESEARCH_RESULT, 1),
            (CollectionItemType.RESEARCH_QUERY, 1)
        ]
        count_mock = Mock()
        count_mock.all.return_value = count_result

        # Mock items query results
        items_mock = Mock()
        items_scalars = Mock()
        items_scalars.all.return_value = sample_items
        items_mock.scalars.return_value = items_scalars

        # Configure execute to return appropriate mocks
        mock_session.execute.side_effect = [count_mock, items_mock]

        # Call analyze_collection
        result = analyze_collection(1, mock_session)

        # Assertions
        assert result["collection_id"] == 1
        assert result["name"] == "Test Collection"
        assert result["description"] == "A test collection for research planning"
        assert result["tags"] == ["research", "testing"]
        assert result["item_count"] == 3
        assert result["items_by_type"]["excerpt"] == 1
        assert result["items_by_type"]["research_result"] == 1
        assert result["items_by_type"]["research_query"] == 1
        assert len(result["items"]) == 3

    def test_analyze_collection_includes_item_notes_and_types(
        self, mock_session, sample_collection, sample_items
    ):
        """Test that analyze_collection includes item notes and types."""
        def mock_get(model, ident):
            if model == Collection:
                return sample_collection
            return None
        mock_session.get.side_effect = mock_get

        # Mock count query
        count_result = [(CollectionItemType.EXCERPT, 3)]
        count_mock = Mock()
        count_mock.all.return_value = count_result

        # Mock items query
        items_mock = Mock()
        items_scalars = Mock()
        items_scalars.all.return_value = sample_items
        items_mock.scalars.return_value = items_scalars

        mock_session.execute.side_effect = [count_mock, items_mock]

        result = analyze_collection(1, mock_session)

        # Check first item details
        item_0 = result["items"][0]
        assert item_0["id"] == 1
        assert item_0["type"] == "excerpt"
        assert item_0["link"] == "/search/result/1/2/3"
        assert item_0["note"] == "Key finding about topic A"

        # Check second item
        item_1 = result["items"][1]
        assert item_1["type"] == "research_result"
        assert item_1["note"] == "Analysis of topic B"

    def test_analyze_collection_includes_previews_and_metadata(
        self, mock_session, sample_collection
    ):
        """Test that analyze_collection includes research result previews and work metadata."""
        mock_session.get.side_effect = None # Reset side effect if any
        
        # 1. Setup CollectionItem with RESEARCH_RESULT
        item_result = CollectionItem(
            id=10,
            collection_id=1,
            item_type=CollectionItemType.RESEARCH_RESULT,
            link="/rag/5/results/100",
            note="Result note",
            order=Decimal("1.0")
        )
        
        # 2. Setup CollectionItem with EXCERPT
        item_excerpt = CollectionItem(
            id=11,
            collection_id=1,
            item_type=CollectionItemType.EXCERPT,
            link="/search/result/1/200/3",
            note="Excerpt note",
            order=Decimal("2.0")
        )
        
        # 3. Setup mock returns for session.get
        mock_result = Result(id=100, response_text="This is a long response text that should be truncated if it exceeds 200 characters.")
        mock_work = Work(id=200, title="Test Book", authors="John Doe", year=2024)
        
        def mock_get(model, ident):
            if model == Collection:
                return sample_collection
            if model == Result and ident == 100:
                return mock_result
            if model == Work and ident == 200:
                return mock_work
            return None
            
        mock_session.get.side_effect = mock_get

        # Mock count query
        count_mock = Mock()
        count_mock.all.return_value = [
            (CollectionItemType.RESEARCH_RESULT, 1),
            (CollectionItemType.EXCERPT, 1)
        ]

        # Mock items query
        items_mock = Mock()
        items_scalars = Mock()
        items_scalars.all.return_value = [item_result, item_excerpt]
        items_mock.scalars.return_value = items_scalars

        mock_session.execute.side_effect = [count_mock, items_mock]

        # Call function
        result = analyze_collection(1, mock_session)

        # Assertions for RESEARCH_RESULT
        item_0 = result["items"][0]
        assert item_0["type"] == "research_result"
        assert "preview" in item_0
        assert item_0["preview"] == mock_result.response_text

        # Assertions for EXCERPT
        item_1 = result["items"][1]
        assert item_1["type"] == "excerpt"
        assert "metadata" in item_1
        assert item_1["metadata"]["title"] == "Test Book"
        assert item_1["metadata"]["authors"] == "John Doe"
        assert item_1["metadata"]["year"] == 2024

    def test_analyze_collection_raises_error_if_not_found(self, mock_session):
        """Test that analyze_collection raises ValueError if collection not found."""
        mock_session.get.side_effect = None
        mock_session.get.return_value = None

        with pytest.raises(ValueError, match="Collection 999 not found"):
            analyze_collection(999, mock_session)


class TestGenerateResearchPlan:
    """Tests for generate_research_plan function."""

    def test_generate_research_plan_calls_llm_with_correct_format(
        self, valid_research_plan
    ):
        """Test that generate_research_plan calls LLM with formatted prompt."""
        collection_data = {
            "collection_id": 1,
            "name": "Test Collection",
            "description": "Test description",
            "tags": ["test"],
            "item_count": 2,
            "items_by_type": {
                "excerpt": 1,
                "research_result": 1,
                "research_query": 0
            },
            "items": [
                {
                    "id": 1,
                    "type": "excerpt",
                    "link": "/search/result/1/2/3",
                    "note": "Test note",
                    "preview": None
                }
            ]
        }

        # Mock LLM client
        mock_llm = Mock()
        mock_llm.generate.return_value = json.dumps(valid_research_plan)

        # Call generate_research_plan
        result = generate_research_plan(collection_data, mock_llm)

        # Verify LLM was called
        assert mock_llm.generate.called
        call_args = mock_llm.generate.call_args[0][0]
        assert "Test Collection" in call_args
        assert "Test description" in call_args

        # Verify result structure
        assert result["research_goal"] == valid_research_plan["research_goal"]
        assert len(result["sub_questions"]) == 2

    def test_generate_research_plan_parses_valid_json_correctly(
        self, valid_research_plan
    ):
        """Test that generate_research_plan correctly parses valid JSON response."""
        collection_data = {
            "collection_id": 1,
            "name": "Test",
            "description": "Test",
            "tags": [],
            "item_count": 1,
            "items_by_type": {"excerpt": 1, "research_result": 0, "research_query": 0},
            "items": []
        }

        mock_llm = Mock()
        mock_llm.generate.return_value = json.dumps(valid_research_plan)

        result = generate_research_plan(collection_data, mock_llm)

        assert result["research_goal"] == valid_research_plan["research_goal"]
        assert result["key_themes"] == valid_research_plan["key_themes"]
        assert len(result["sub_questions"]) == 2
        assert result["sub_questions"][0]["id"] == "sq1"

    def test_generate_research_plan_raises_error_on_invalid_json(self):
        """Test that generate_research_plan raises error on invalid JSON response."""
        collection_data = {
            "collection_id": 1,
            "name": "Test",
            "description": "Test",
            "tags": [],
            "item_count": 1,
            "items_by_type": {"excerpt": 1, "research_result": 0, "research_query": 0},
            "items": []
        }

        mock_llm = Mock()
        mock_llm.generate.return_value = "This is not valid JSON"

        with pytest.raises(ValueError, match="not valid JSON"):
            generate_research_plan(collection_data, mock_llm)


class TestValidateResearchPlan:
    """Tests for validate_research_plan function."""

    def test_validate_research_plan_accepts_valid_plan(self, valid_research_plan):
        """Test that validate_research_plan accepts a valid plan."""
        # Should not raise any exception
        validate_research_plan(valid_research_plan)

    def test_validate_research_plan_rejects_missing_research_goal(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects plan missing research_goal."""
        invalid_plan = valid_research_plan.copy()
        del invalid_plan["research_goal"]

        with pytest.raises(ValueError, match="Missing required field: research_goal"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_missing_sub_questions(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects plan missing sub_questions."""
        invalid_plan = valid_research_plan.copy()
        del invalid_plan["sub_questions"]

        with pytest.raises(ValueError, match="Missing required field: sub_questions"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_empty_sub_questions_list(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects plan with empty sub_questions."""
        invalid_plan = valid_research_plan.copy()
        invalid_plan["sub_questions"] = []

        with pytest.raises(ValueError, match="sub_questions must contain at least 1 item"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_sub_question_missing_estimated_tokens(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects sub_question missing estimated_tokens."""
        invalid_plan = valid_research_plan.copy()
        invalid_plan["sub_questions"][0] = {
            "id": "sq1",
            "question": "Test question",
            "rationale": "Test rationale"
            # Missing estimated_tokens
        }

        with pytest.raises(ValueError, match="missing required field: estimated_tokens"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_sub_question_missing_relevant_items(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects sub_question missing relevant_items."""
        invalid_plan = valid_research_plan.copy()
        # Create a new dict for the sub-question to avoid modifying the fixture
        subq = invalid_plan["sub_questions"][0].copy()
        del subq["relevant_items"]
        invalid_plan["sub_questions"] = [subq]

        with pytest.raises(ValueError, match="missing required field: relevant_items"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_invalid_estimated_tokens(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects invalid estimated_tokens."""
        invalid_plan = valid_research_plan.copy()
        invalid_plan["sub_questions"][0]["estimated_tokens"] = -100

        with pytest.raises(ValueError, match="must be a positive integer"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_empty_research_goal(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects empty research_goal."""
        invalid_plan = valid_research_plan.copy()
        invalid_plan["research_goal"] = ""

        with pytest.raises(ValueError, match="must be a non-empty string"):
            validate_research_plan(invalid_plan)

    def test_validate_research_plan_rejects_empty_question(
        self, valid_research_plan
    ):
        """Test that validate_research_plan rejects empty question."""
        invalid_plan = valid_research_plan.copy()
        invalid_plan["sub_questions"][0]["question"] = "   "

        with pytest.raises(ValueError, match="question must be a non-empty string"):
            validate_research_plan(invalid_plan)
