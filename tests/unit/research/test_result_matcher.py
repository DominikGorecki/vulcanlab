"""
Unit tests for result_matcher module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from vulcanlab.research.result_matcher import (
    calculate_similarity,
    calculate_quality_score,
    recommend_reuse_strategy,
    match_results_for_question
)
from vulcanlab.data.models.result import Result
from vulcanlab.data.models.query import Query
from vulcanlab.data.models.result_model import ResultModel
from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.enums import CollectionItemType


class TestCalculateSimilarity:
    """Tests for calculate_similarity function."""

    def test_calculate_similarity_identical(self):
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert calculate_similarity(a, b) == pytest.approx(1.0)

    def test_calculate_similarity_orthogonal(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert calculate_similarity(a, b) == pytest.approx(0.0)

    def test_calculate_similarity_opposite(self):
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        assert calculate_similarity(a, b) == pytest.approx(-1.0)

    def test_calculate_similarity_zero_vector(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert calculate_similarity(a, b) == 0.0


class TestCalculateQualityScore:
    """Tests for calculate_quality_score function."""

    def test_calculate_quality_score_range(self):
        """Test that quality score is within [0, 1]."""
        result = Mock(spec=Result)
        result.response_text = "This is a test research result. [Smith 2023]"
        result.created_at = datetime.now(timezone.utc)
        result.model = Mock(spec=ResultModel)
        result.model.name = "gpt-4"
        
        score = calculate_quality_score(result)
        assert 0.0 <= score <= 1.0

    def test_calculate_quality_score_weights(self):
        """Test that quality score correctly reflects quality factors."""
        # Result 1: High quality (long, citations, fresh, high-quality model)
        res1 = Mock(spec=Result)
        res1.response_text = "Detailed analysis. " * 50 + "[Smith 2023] [Jones 2024] [Brown 2022] [White 2021] [Green 2020]"
        res1.created_at = datetime.now(timezone.utc)
        res1.model = Mock(spec=ResultModel)
        res1.model.name = "gpt-4"
        score1 = calculate_quality_score(res1)

        # Result 2: Low quality (short, no citations, old, weak model)
        res2 = Mock(spec=Result)
        res2.response_text = "Short answer."
        res2.created_at = datetime.now(timezone.utc) - timedelta(days=200)
        res2.model = Mock(spec=ResultModel)
        res2.model.name = "gpt-3.5-turbo"
        score2 = calculate_quality_score(res2)

        assert score1 > score2
        # score1 should be reasonably high, score2 should be low
        assert score1 > 0.5
        assert score2 < 0.3


class TestRecommendReuseStrategy:
    """Tests for recommend_reuse_strategy function."""

    def test_recommend_reuse_strategy_new_generation_no_hq(self):
        """Test 'new_generation' if no high-quality results."""
        matched = [{"quality_score": 0.5, "similarity": 0.95}]
        assert recommend_reuse_strategy(matched) == "new_generation"

    def test_recommend_reuse_strategy_exact_reuse(self):
        """Test 'exact_reuse' for 1 high-quality result with high similarity."""
        matched = [{"quality_score": 0.8, "similarity": 0.95}]
        assert recommend_reuse_strategy(matched) == "exact_reuse"

    def test_recommend_reuse_strategy_partial_reuse(self):
        """Test 'partial_reuse' for 1 high-quality result with moderate similarity."""
        matched = [{"quality_score": 0.8, "similarity": 0.88}]
        assert recommend_reuse_strategy(matched) == "partial_reuse"

    def test_recommend_reuse_strategy_ensemble(self):
        """Test 'ensemble' for multiple high-quality results."""
        matched = [
            {"quality_score": 0.8, "similarity": 0.95},
            {"quality_score": 0.85, "similarity": 0.92}
        ]
        assert recommend_reuse_strategy(matched) == "ensemble"


class TestMatchResultsForQuestion:
    """Tests for match_results_for_question function."""

    @patch("vulcanlab.research.result_matcher.create_embeddings")
    def test_match_results_for_question_filtering(self, mock_create_emb):
        """Test that results are filtered by similarity > 0.85."""
        # Mock embeddings model
        mock_emb_model = Mock()
        mock_create_emb.return_value = mock_emb_model
        
        # embed_query side effects: 1. question, 2. result1 (matched), 3. result2 (filtered)
        # Using simple vectors for easy cosine similarity
        mock_emb_model.embed_query.side_effect = [
            [1.0, 0.0],  # question
            [0.9, 0.1],  # result1 (similarity ~ 0.99)
            [0.1, 0.9]   # result2 (similarity ~ 0.11)
        ]

        session = MagicMock()
        
        # Collection items
        item1 = Mock(spec=CollectionItem)
        item1.link = "/rag/1/results/101"
        item1.item_type = CollectionItemType.RESEARCH_RESULT
        
        item2 = Mock(spec=CollectionItem)
        item2.link = "/rag/1/results/102"
        item2.item_type = CollectionItemType.RESEARCH_RESULT
        
        # Mock session.execute for items_query
        mock_execute = Mock()
        mock_execute.scalars.return_value.all.return_value = [item1, item2]
        session.execute.return_value = mock_execute

        # Result 1 (Matches)
        res1 = Mock(spec=Result)
        res1.id = 101
        res1.query_id = 1
        res1.response_text = "Matched result content."
        res1.created_at = datetime.now(timezone.utc)
        res1.model = None
        
        q1 = Mock(spec=Query)
        q1.original_query = "Original query 1"
        q1.embedding_original = [0.9, 0.1]
        
        # Result 2 (Filtered out)
        res2 = Mock(spec=Result)
        res2.id = 102
        res2.query_id = 2
        res2.response_text = "Other result content."
        res2.created_at = datetime.now(timezone.utc)
        res2.model = None
        
        q2 = Mock(spec=Query)
        q2.original_query = "Original query 2"
        q2.embedding_original = [0.1, 0.9]

        def mock_get(model, ident):
            if model == Result:
                if ident == 101: return res1
                if ident == 102: return res2
            if model == Query:
                if ident == 1: return q1
                if ident == 2: return q2
            return None
        session.get.side_effect = mock_get

        # Call function
        results = match_results_for_question("Test question?", 1, session)
        
        assert len(results) == 1
        assert results[0]["result_id"] == 101
        assert results[0]["similarity"] > 0.85

    @patch("vulcanlab.research.result_matcher.create_embeddings")
    def test_match_results_for_question_sorting(self, mock_create_emb):
        """Test that results are sorted by quality_score DESC."""
        mock_emb_model = Mock()
        mock_create_emb.return_value = mock_emb_model
        # All have same high similarity
        mock_emb_model.embed_query.return_value = [1.0, 0.0]

        session = MagicMock()
        
        item1 = Mock(spec=CollectionItem)
        item1.link = "/results/1"
        item1.item_type = CollectionItemType.RESEARCH_RESULT
        
        item2 = Mock(spec=CollectionItem)
        item2.link = "/results/2"
        item2.item_type = CollectionItemType.RESEARCH_RESULT
        
        mock_execute = Mock()
        mock_execute.scalars.return_value.all.return_value = [item1, item2]
        session.execute.return_value = mock_execute

        # Result 1: High quality
        res_high = Mock(spec=Result)
        res_high.id = 1
        res_high.query_id = 1
        res_high.response_text = "Detailed analysis. " * 50 + "[Ref 2023] [Ref 2024]"
        res_high.created_at = datetime.now(timezone.utc)
        res_high.model = None
        
        # Result 2: Low quality
        res_low = Mock(spec=Result)
        res_low.id = 2
        res_low.query_id = 2
        res_low.response_text = "Brief."
        res_low.created_at = datetime.now(timezone.utc)
        res_low.model = None
        
        q = Mock(spec=Query)
        q.original_query = "Query"
        q.embedding_original = [1.0, 0.0]

        def mock_get(model, ident):
            if model == Result:
                return res_high if ident == 1 else res_low
            if model == Query:
                return q
            return None
        session.get.side_effect = mock_get

        # Call function
        results = match_results_for_question("Test?", 1, session)
        
        assert len(results) == 2
        assert results[0]["result_id"] == 1  # res_high should be first
        assert results[0]["quality_score"] > results[1]["quality_score"]
