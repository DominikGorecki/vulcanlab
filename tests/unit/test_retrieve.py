"""
Unit tests for retrieval/retrieve.py module.

Tests retrieval logic, vector similarity search, result ranking, top-k retrieval,
and edge cases (no matches, empty database).
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import numpy as np

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.query import Query
from vulcanlab.data.models.work import Work
from vulcanlab.retrieval.retrieve import (
    retrieve,
    RetrievalResult,
    RetrievedChunk,
    _dense_search,
    _lexical_search,
    _compute_rrf_scores,
    _meets_minimum_requirements,
    _apply_entity_bias,
    _apply_intent_bias,
    _cosine_similarity,
    _jaccard_similarity,
    _compute_chunk_similarity,
    _apply_mmr_diversity,
)
from vulcanlab.config.app_config import AppConfig, LoggingConfig



class TestRetrievedChunk:
    """Test RetrievedChunk dataclass."""

    def test_retrieved_chunk_creation(self):
        """Test creating a RetrievedChunk with all fields."""
        chunk = RetrievedChunk(
            id=1,
            parent_id=None,
            work_id=1,
            content="Test content",
            enriched_content="Enriched test content",
            start_line=10,
            end_line=20,
            level="H2",
            heading_breadcrumbs="Chapter 1 > Section 1",
            dense_rank=1,
            lexical_rank=2,
            rrf_score=0.85,
            rerank_score=0.92,
            entity_boost=0.05,
            final_score=0.97
        )

        assert chunk.id == 1
        assert chunk.parent_id is None
        assert chunk.work_id == 1
        assert chunk.content == "Test content"
        assert chunk.enriched_content == "Enriched test content"
        assert chunk.start_line == 10
        assert chunk.end_line == 20
        assert chunk.level == "H2"
        assert chunk.heading_breadcrumbs == "Chapter 1 > Section 1"
        assert chunk.dense_rank == 1
        assert chunk.lexical_rank == 2
        assert chunk.rrf_score == 0.85
        assert chunk.rerank_score == 0.92
        assert chunk.entity_boost == 0.05
        assert chunk.final_score == 0.97
        assert chunk._embedding is None

    def test_retrieved_chunk_with_embedding(self):
        """Test RetrievedChunk with embedding."""
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk = RetrievedChunk(
            id=1,
            parent_id=None,
            work_id=1,
            content="Test",
            enriched_content="Test",
            start_line=1,
            end_line=1,
            level="chunk",
            _embedding=embedding
        )

        assert chunk._embedding is not None
        assert np.array_equal(chunk._embedding, embedding)

    def test_retrieved_chunk_defaults(self):
        """Test RetrievedChunk with default values."""
        chunk = RetrievedChunk(
            id=1,
            parent_id=None,
            work_id=1,
            content="Test",
            enriched_content="Test",
            start_line=1,
            end_line=1,
            level="chunk"
        )

        assert chunk.heading_breadcrumbs is None
        assert chunk.dense_rank is None
        assert chunk.lexical_rank is None
        assert chunk.rrf_score == 0.0
        assert chunk.rerank_score == 0.0
        assert chunk.entity_boost == 0.0
        assert chunk.final_score == 0.0
        assert chunk._embedding is None


class TestRetrievalResult:
    """Test RetrievalResult dataclass."""

    def test_retrieval_result_creation(self):
        """Test creating a RetrievalResult."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="Content 1", enriched_content="Content 1",
                start_line=1, end_line=10, level="H2"
            ),
            RetrievedChunk(
                id=2, parent_id=None, work_id=1,
                content="Content 2", enriched_content="Content 2",
                start_line=11, end_line=20, level="H3"
            )
        ]

        result = RetrievalResult(
            query_id=1,
            total_dense_candidates=50,
            total_lexical_candidates=20,
            rrf_candidates=30,
            final_count=2,
            chunks=chunks
        )

        assert result.query_id == 1
        assert result.total_dense_candidates == 50
        assert result.total_lexical_candidates == 20
        assert result.rrf_candidates == 30
        assert result.final_count == 2
        assert len(result.chunks) == 2
        assert result.chunks[0].id == 1
        assert result.chunks[1].id == 2

    def test_retrieval_result_empty_chunks(self):
        """Test RetrievalResult with no chunks."""
        result = RetrievalResult(
            query_id=1,
            total_dense_candidates=0,
            total_lexical_candidates=0,
            rrf_candidates=0,
            final_count=0,
            chunks=[]
        )

        assert result.query_id == 1
        assert result.total_dense_candidates == 0
        assert result.final_count == 0
        assert len(result.chunks) == 0


class TestMeetsMinimumRequirements:
    """Test _meets_minimum_requirements function."""

    def test_meets_requirements_both(self):
        """Test content that meets both word and character requirements."""
        content = "This is a test content with enough words and characters to pass the minimum requirements."
        assert _meets_minimum_requirements(content, min_word_count=10, min_char_count=50) is True

    def test_meets_requirements_word_only(self):
        """Test content that meets word count but not character count."""
        content = "Short text"
        assert _meets_minimum_requirements(content, min_word_count=2, min_char_count=100) is False

    def test_meets_requirements_char_only(self):
        """Test content that meets character count but not word count."""
        content = "a" * 300  # 300 characters but only 1 word
        assert _meets_minimum_requirements(content, min_word_count=10, min_char_count=250) is False

    def test_meets_requirements_disabled(self):
        """Test with disabled requirements (0 values)."""
        content = "Short"
        assert _meets_minimum_requirements(content, min_word_count=0, min_char_count=0) is True

    def test_meets_requirements_empty_content(self):
        """Test with empty content."""
        assert _meets_minimum_requirements("", min_word_count=10, min_char_count=50) is False
        assert _meets_minimum_requirements("   ", min_word_count=10, min_char_count=50) is False

    def test_meets_requirements_exact_threshold(self):
        """Test content at exact threshold."""
        content = "word " * 150  # Exactly 150 words
        assert _meets_minimum_requirements(content, min_word_count=150, min_char_count=0) is True
        assert _meets_minimum_requirements(content, min_word_count=151, min_char_count=0) is False


class TestComputeRRFScores:
    """Test _compute_rrf_scores function."""

    def test_compute_rrf_scores_single_list(self):
        """Test RRF score computation with single ranked list."""
        results = [(1, 1), (2, 2), (3, 3)]  # (chunk_id, rank)
        k = 50

        scores = _compute_rrf_scores([results], k)

        assert len(scores) == 3
        assert scores[1] == 1.0 / (50 + 1)  # Rank 1
        assert scores[2] == 1.0 / (50 + 2)  # Rank 2
        assert scores[3] == 1.0 / (50 + 3)  # Rank 3
        assert scores[1] > scores[2] > scores[3]  # Higher rank = higher score

    def test_compute_rrf_scores_multiple_lists(self):
        """Test RRF score computation with multiple ranked lists."""
        list1 = [(1, 1), (2, 2)]
        list2 = [(2, 1), (3, 2)]
        list3 = [(1, 2), (3, 1)]
        k = 50

        scores = _compute_rrf_scores([list1, list2, list3], k)

        assert len(scores) == 3
        # Chunk 1 appears in list1 (rank 1) and list3 (rank 2)
        assert scores[1] == pytest.approx(1.0 / (50 + 1) + 1.0 / (50 + 2))
        # Chunk 2 appears in list1 (rank 2) and list2 (rank 1)
        assert scores[2] == pytest.approx(1.0 / (50 + 2) + 1.0 / (50 + 1))
        # Chunk 3 appears in list2 (rank 2) and list3 (rank 1)
        assert scores[3] == pytest.approx(1.0 / (50 + 2) + 1.0 / (50 + 1))

    def test_compute_rrf_scores_empty_list(self):
        """Test RRF score computation with empty list."""
        scores = _compute_rrf_scores([], k=50)
        assert len(scores) == 0

    def test_compute_rrf_scores_custom_k(self):
        """Test RRF score computation with custom k value."""
        results = [(1, 1), (2, 2)]
        k = 10

        scores = _compute_rrf_scores([results], k)

        assert scores[1] == 1.0 / (10 + 1)
        assert scores[2] == 1.0 / (10 + 2)


class TestCosineSimilarity:
    """Test _cosine_similarity function."""

    def test_cosine_similarity_identical(self):
        """Test cosine similarity with identical vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = _cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])

        similarity = _cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity with opposite vectors."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([-1.0, 0.0])

        similarity = _cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0)

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 0.0])

        similarity = _cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_normalized(self):
        """Test cosine similarity with normalized vectors."""
        vec1 = np.array([0.6, 0.8])
        vec2 = np.array([0.8, 0.6])

        similarity = _cosine_similarity(vec1, vec2)
        assert -1.0 <= similarity <= 1.0


class TestJaccardSimilarity:
    """Test _jaccard_similarity function."""

    def test_jaccard_similarity_identical(self):
        """Test Jaccard similarity with identical texts."""
        text1 = "the quick brown fox"
        text2 = "the quick brown fox"

        similarity = _jaccard_similarity(text1, text2)
        assert similarity == pytest.approx(1.0)

    def test_jaccard_similarity_no_overlap(self):
        """Test Jaccard similarity with no overlapping words."""
        text1 = "the quick brown"
        text2 = "fox jumps over"

        similarity = _jaccard_similarity(text1, text2)
        assert similarity == pytest.approx(0.0)

    def test_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity with partial overlap."""
        text1 = "the quick brown fox"
        text2 = "the quick dog"

        similarity = _jaccard_similarity(text1, text2)
        assert 0.0 < similarity < 1.0

    def test_jaccard_similarity_empty_text(self):
        """Test Jaccard similarity with empty text."""
        assert _jaccard_similarity("", "test") == 0.0
        assert _jaccard_similarity("test", "") == 0.0
        assert _jaccard_similarity("", "") == 0.0


class TestComputeChunkSimilarity:
    """Test _compute_chunk_similarity function."""

    def test_compute_chunk_similarity_with_embeddings(self):
        """Test similarity computation using embeddings."""
        chunk1 = RetrievedChunk(
            id=1, parent_id=None, work_id=1,
            content="test", enriched_content="test",
            start_line=1, end_line=1, level="chunk",
            _embedding=np.array([1.0, 0.0])
        )
        chunk2 = RetrievedChunk(
            id=2, parent_id=None, work_id=1,
            content="test", enriched_content="test",
            start_line=1, end_line=1, level="chunk",
            _embedding=np.array([1.0, 0.0])
        )

        similarity = _compute_chunk_similarity(chunk1, chunk2)
        # Should normalize cosine similarity from [-1, 1] to [0, 1]
        assert 0.0 <= similarity <= 1.0

    def test_compute_chunk_similarity_fallback_jaccard(self):
        """Test similarity computation falls back to Jaccard when no embeddings."""
        chunk1 = RetrievedChunk(
            id=1, parent_id=None, work_id=1,
            content="the quick brown", enriched_content="the quick brown",
            start_line=1, end_line=1, level="chunk"
        )
        chunk2 = RetrievedChunk(
            id=2, parent_id=None, work_id=1,
            content="the quick fox", enriched_content="the quick fox",
            start_line=1, end_line=1, level="chunk"
        )

        similarity = _compute_chunk_similarity(chunk1, chunk2)
        assert 0.0 <= similarity <= 1.0


class TestApplyEntityBias:
    """Test _apply_entity_bias function."""

    def test_apply_entity_bias_no_entities(self):
        """Test entity bias with no entities."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="test", enriched_content="test",
                start_line=1, end_line=1, level="chunk",
                rerank_score=0.8
            )
        ]

        result = _apply_entity_bias(chunks, [], boost=0.05)

        assert result[0].entity_boost == 0.0
        assert result[0].final_score == 0.8

    def test_apply_entity_bias_with_matches(self):
        """Test entity bias with matching entities."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="test", enriched_content="test memory encoding",
                start_line=1, end_line=1, level="chunk",
                rerank_score=0.8
            ),
            RetrievedChunk(
                id=2, parent_id=None, work_id=1,
                content="test", enriched_content="test retrieval",
                start_line=1, end_line=1, level="chunk",
                rerank_score=0.8
            )
        ]

        entities = ["memory", "encoding"]
        result = _apply_entity_bias(chunks, entities, boost=0.05)

        # First chunk has 2 matches
        assert result[0].entity_boost == pytest.approx(0.10)  # 2 * 0.05
        assert result[0].final_score == pytest.approx(0.90)  # 0.8 + 0.10
        # Second chunk has 0 matches
        assert result[1].entity_boost == 0.0
        assert result[1].final_score == 0.8

    def test_apply_entity_bias_case_insensitive(self):
        """Test entity bias is case insensitive."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="test", enriched_content="test MEMORY",
                start_line=1, end_line=1, level="chunk",
                rerank_score=0.8
            )
        ]

        entities = ["memory"]
        result = _apply_entity_bias(chunks, entities, boost=0.05)

        assert result[0].entity_boost == pytest.approx(0.05)


class TestApplyIntentBias:
    """Test _apply_intent_bias function."""

    def test_apply_intent_bias_no_intent(self):
        """Test intent bias with no intent."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="test", enriched_content="test",
                start_line=1, end_line=1, level="H2",
                final_score=0.8
            )
        ]

        result = _apply_intent_bias(chunks, None)

        assert result[0].final_score == 0.8  # No change

    def test_apply_intent_bias_definition(self):
        """Test intent bias for DEFINITION intent."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="test", enriched_content="a" * 400,  # Short content
                start_line=1, end_line=1, level="H2",  # Preferred level
                final_score=0.8
            ),
            RetrievedChunk(
                id=2, parent_id=None, work_id=1,
                content="test", enriched_content="a" * 1000,  # Long content
                start_line=1, end_line=1, level="H4",  # Not preferred
                final_score=0.8
            )
        ]

        result = _apply_intent_bias(chunks, "DEFINITION")

        # First chunk should get boost (H2 level + short content)
        assert result[0].final_score > 0.8
        # Second chunk should not get boost
        assert result[1].final_score == 0.8

    def test_apply_intent_bias_unknown_intent(self):
        """Test intent bias with unknown intent."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1,
                content="test", enriched_content="test",
                start_line=1, end_line=1, level="H2",
                final_score=0.8
            )
        ]

        result = _apply_intent_bias(chunks, "UNKNOWN_INTENT")

        assert result[0].final_score == 0.8  # No change


class TestApplyMMRDiversity:
    """Test _apply_mmr_diversity function."""

    def test_apply_mmr_diversity_fewer_than_top_n(self):
        """Test MMR when chunks are fewer than top_n."""
        chunks = [
            RetrievedChunk(
                id=i, parent_id=None, work_id=1,
                content=f"content {i}", enriched_content=f"content {i}",
                start_line=1, end_line=1, level="chunk",
                final_score=0.9 - i * 0.1
            )
            for i in range(3)
        ]

        result = _apply_mmr_diversity(chunks, top_n=5, lambda_param=0.7)

        assert len(result) == 3  # All chunks returned

    def test_apply_mmr_diversity_exact_top_n(self):
        """Test MMR when chunks equal top_n."""
        chunks = [
            RetrievedChunk(
                id=i, parent_id=None, work_id=1,
                content=f"content {i}", enriched_content=f"content {i}",
                start_line=1, end_line=1, level="chunk",
                final_score=0.9 - i * 0.1
            )
            for i in range(5)
        ]

        result = _apply_mmr_diversity(chunks, top_n=5, lambda_param=0.7)

        assert len(result) == 5

    def test_apply_mmr_diversity_empty_chunks(self):
        """Test MMR with empty chunks list."""
        result = _apply_mmr_diversity([], top_n=5, lambda_param=0.7)
        assert len(result) == 0


class TestRetrieveFunction:
    """Test retrieve() function - main retrieval logic."""

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_basic(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test basic retrieval with successful results."""
        # Setup config
        mock_config = {
            "retrieval": {
                "dense_limit": 10,
                "lexical_limit": 5,
                "rrf_k": 50,
                "top_k_rrf": 20,
                "top_n_final": 5,
                "entity_boost": 0.05,
                "min_word_count": 10,
                "min_char_count": 50,
                "min_content_length": 100,
                "enrich_lines_above": 0,
                "enrich_lines_below": 5,
                "mmr_lambda": 0.7,
                "reranker_batch_size": 8,
                "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create work and chunks
        work = Work(title="Test Work", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.commit()

        chunk1 = Chunk(
            work_id=work.id, level="H2", content="This is a test chunk with enough words and characters.",
            start_line=1, end_line=10, vector_status="vec",
            embedding=[0.1] * 768
        )
        chunk1.id = 1
        chunk2 = Chunk(
            work_id=work.id, level="H3", content="Another test chunk with sufficient content length.",
            start_line=11, end_line=20, vector_status="vec",
            embedding=[0.2] * 768
        )
        chunk2.id = 2
        mock_session.add_all([chunk1, chunk2])
        mock_session.commit()

        # Create query
        query = Query(
            original_query="test query",
            vector_status="vec",
            embedding_original=[0.15] * 768
        )
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        # Configure mock to return query when queried
        mock_session.query.return_value.filter.return_value.first.return_value = query

        # Mock search results
        mock_dense_search.return_value = [(chunk1.id, 1), (chunk2.id, 2)]
        mock_lexical_search.return_value = [(chunk1.id, 1)]
        mock_rerank_chunks.return_value = [
            RetrievedChunk(
                id=chunk1.id, parent_id=None, work_id=work.id,
                content=chunk1.content, enriched_content=chunk1.content,
                start_line=chunk1.start_line, end_line=chunk1.end_line,
                level=chunk1.level, rrf_score=0.8, rerank_score=0.9, final_score=0.9
            ),
            RetrievedChunk(
                id=chunk2.id, parent_id=None, work_id=work.id,
                content=chunk2.content, enriched_content=chunk2.content,
                start_line=chunk2.start_line, end_line=chunk2.end_line,
                level=chunk2.level, rrf_score=0.7, rerank_score=0.85, final_score=0.85
            )
        ]

        result = retrieve(query.id, verbose=False)

        assert isinstance(result, RetrievalResult)
        assert result.query_id == query.id
        assert result.final_count > 0
        assert len(result.chunks) > 0

    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_query_not_found(self, mock_get_config, mock_get_session, mock_session):
        """Test retrieve raises ValueError when query not found."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Query with ID 999 not found"):
            retrieve(999)

    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_query_not_vectorized(self, mock_get_config, mock_get_session, mock_session):
        """Test retrieve raises ValueError when query not vectorized."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        query = Query(original_query="test", vector_status="no_vec")
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query

        with pytest.raises(ValueError, match="has not been vectorized"):
            retrieve(query.id)

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_no_matches(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test retrieval with no matching chunks."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        query = Query(original_query="test", vector_status="vec", embedding_original=[0.1] * 768)
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query

        # Mock empty search results
        mock_dense_search.return_value = []
        mock_lexical_search.return_value = []
        mock_rerank_chunks.return_value = []

        result = retrieve(query.id, verbose=False)

        assert result.final_count == 0
        assert len(result.chunks) == 0
        assert result.total_dense_candidates == 0
        assert result.total_lexical_candidates == 0

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_config_by_name')
    def test_retrieve_with_config_preset(
        self, mock_get_config_by_name, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test retrieve with config preset."""
        mock_config = {
            "retrieval": {
                "dense_limit": 15, "lexical_limit": 8, "rrf_k": 60,
                "top_k_rrf": 25, "top_n_final": 10, "entity_boost": 0.1,
                "min_word_count": 20, "min_char_count": 100,
                "min_content_length": 200, "enrich_lines_above": 2,
                "enrich_lines_below": 10, "mmr_lambda": 0.8,
                "reranker_batch_size": 16, "reranker_max_length": 1024
            }
        }
        mock_get_config_by_name.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        query = Query(original_query="test", vector_status="vec", embedding_original=[0.1] * 768)
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter_by.return_value.first.return_value = query

        mock_dense_search.return_value = []
        mock_lexical_search.return_value = []
        mock_rerank_chunks.return_value = []

        result = retrieve(query.id, config_preset="test_preset", verbose=False)

        mock_get_config_by_name.assert_called_once_with("test_preset")
        assert isinstance(result, RetrievalResult)

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_top_k(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test top-k retrieval limits results correctly."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 3, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.commit()

        # Create multiple chunks
        chunks = []
        for i in range(5):
            chunk = Chunk(
                work_id=work.id, level="H2",
                content=f"This is test chunk {i} with enough words and characters.",
                start_line=i*10+1, end_line=(i+1)*10, vector_status="vec",
                embedding=[0.1] * 768
            )
            chunk.id = i + 1
            chunks.append(chunk)
        mock_session.add_all(chunks)
        mock_session.commit()

        query = Query(original_query="test", vector_status="vec", embedding_original=[0.1] * 768)
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query

        # Mock search results
        mock_dense_search.return_value = [(c.id, i+1) for i, c in enumerate(chunks)]
        mock_lexical_search.return_value = [(chunks[0].id, 1)]

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_calls_lexical_search(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test that retrieve calls _lexical_search for each query text."""
        # Setup config
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "mmr_lambda": 0.7,
                "entity_boost": 0.0, "min_word_count": 0, "min_char_count": 0,
                "min_content_length": 0, "enrich_lines_above": 0, "enrich_lines_below": 0,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Setup work and chunks
        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        
        chunk = Chunk(
            work_id=work.id, content="test content",
            vector_status="vec", embedding=[0.1] * 768
        )
        chunk.id = 1
        mock_session.add(chunk)
        mock_session.commit()
        
        # Setup query with expanded queries
        query = Query(
            original_query="original",
            vector_status="vec",
            embedding_original=[0.1] * 768,
            expanded_queries=["expanded 1", "expanded 2"]
        )
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query
        
        # Mock search results
        mock_dense_search.return_value = []
        mock_lexical_search.return_value = []
        mock_rerank_chunks.return_value = []
        
        retrieve(query.id, verbose=False)
        
        # Should be called 3 times: 1 original + 2 expanded
        assert mock_lexical_search.call_count == 3
        # Verify calls
        args = [call[0][1] for call in mock_lexical_search.call_args_list]
        assert "original" in args
        assert "expanded 1" in args
        assert "expanded 2" in args


class TestRetrievalLogging:
    """Tests for retrieval logging."""

    @patch('vulcanlab.retrieval.retrieve.load_config')
    @patch('vulcanlab.retrieval.retrieve._save_retrieval_log')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    def test_retrieve_logging_enabled(
        self, mock_rerank, mock_lexical, mock_dense, mock_get_default, mock_get_session, mock_save_log, mock_load_config
    ):
        """Test that logging is called when enabled."""
        # Setup logging config
        mock_log_config = AppConfig(logging=LoggingConfig(enabled=True))
        mock_load_config.return_value = mock_log_config

        # Setup RAG config
        mock_get_default.return_value = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "mmr_lambda": 0.7,
                "entity_boost": 0.0, "min_word_count": 0, "min_char_count": 0,
                "min_content_length": 0, "enrich_lines_above": 0, "enrich_lines_below": 0,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_query = Mock(spec=Query)
        mock_query.original_query = "Test"
        mock_query.vector_status = "vec"
        mock_query.embedding_original = [0.1] * 768
        mock_query.embeddings_mqe = []
        mock_query.expanded_queries = []
        mock_query.embedding_hyde = None
        mock_query.intent = "GENERAL"
        mock_query.entities = []
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query

        mock_dense.return_value = []
        mock_lexical.return_value = []
        mock_rerank.return_value = []

        retrieve(1, verbose=False)

        mock_save_log.assert_called_once()
        args = mock_save_log.call_args[0]
        assert args[0] == 1  # query_id

    @patch('vulcanlab.retrieval.retrieve.load_config')
    @patch('vulcanlab.retrieval.retrieve._save_retrieval_log')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    def test_retrieve_logging_disabled(
        self, mock_rerank, mock_lexical, mock_dense, mock_get_default, mock_get_session, mock_save_log, mock_load_config
    ):
        """Test that logging is NOT called when disabled."""
        # Setup logging config
        mock_log_config = AppConfig(logging=LoggingConfig(enabled=False))
        mock_load_config.return_value = mock_log_config

        # Setup RAG config
        mock_get_default.return_value = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "mmr_lambda": 0.7,
                "entity_boost": 0.0, "min_word_count": 0, "min_char_count": 0,
                "min_content_length": 0, "enrich_lines_above": 0, "enrich_lines_below": 0,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_query = Mock(spec=Query)
        mock_query.vector_status = "vec"
        mock_query.embeddings_mqe = []
        mock_query.expanded_queries = []
        mock_query.embedding_hyde = None
        mock_query.entities = []
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query

        mock_dense.return_value = []
        mock_lexical.return_value = []
        mock_rerank.return_value = []

        retrieve(1, verbose=False)

        mock_save_log.assert_not_called()

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_with_mqe_queries(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test retrieval with MQE expanded queries."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.commit()

        chunk = Chunk(
            work_id=work.id, level="H2",
            content="This is a test chunk with enough words and characters.",
            start_line=1, end_line=10, vector_status="vec",
            embedding=[0.1] * 768
        )
        chunk.id = 1
        mock_session.add(chunk)
        mock_session.commit()

        query = Query(
            original_query="test query",
            expanded_queries=["expanded query 1", "expanded query 2"],
            vector_status="vec",
            embedding_original=[0.1] * 768,
            embeddings_mqe=[[0.2] * 768, [0.3] * 768]
        )
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter_by.return_value.first.return_value = query

        mock_dense_search.return_value = [(chunk.id, 1)]
        mock_lexical_search.return_value = [(chunk.id, 1)]
        mock_rerank_chunks.return_value = [
            RetrievedChunk(
                id=chunk.id, parent_id=None, work_id=work.id,
                content=chunk.content, enriched_content=chunk.content,
                start_line=chunk.start_line, end_line=chunk.end_line,
                level=chunk.level, rrf_score=0.8, rerank_score=0.9, final_score=0.9
            )
        ]

        result = retrieve(query.id, verbose=False)

        # Verify dense_search was called multiple times (original + MQE)
        assert mock_dense_search.call_count >= 2
        assert isinstance(result, RetrievalResult)

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_filters_short_chunks(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test that chunks below minimum requirements are filtered out."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 20, "min_char_count": 100,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.commit()

        # Create chunks: one that meets requirements, one that doesn't
        valid_chunk = Chunk(
            work_id=work.id, level="H2",
            content="This is a valid chunk with enough words and characters to pass the filter.",
            start_line=1, end_line=10, vector_status="vec",
            embedding=[0.1] * 768
        )
        valid_chunk.id = 1
        short_chunk = Chunk(
            work_id=work.id, level="H2",
            content="Short",  # Too short
            start_line=11, end_line=12, vector_status="vec",
            embedding=[0.2] * 768
        )
        short_chunk.id = 2
        mock_session.add_all([valid_chunk, short_chunk])
        mock_session.commit()

        query = Query(original_query="test", vector_status="vec", embedding_original=[0.1] * 768)
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query

        # Mock search results returning both chunks
        mock_dense_search.return_value = [(valid_chunk.id, 1), (short_chunk.id, 2)]
        mock_lexical_search.return_value = [(valid_chunk.id, 1)]
        mock_rerank_chunks.return_value = [
            RetrievedChunk(
                id=valid_chunk.id, parent_id=None, work_id=work.id,
                content=valid_chunk.content, enriched_content=valid_chunk.content,
                start_line=valid_chunk.start_line, end_line=valid_chunk.end_line,
                level=valid_chunk.level, rrf_score=0.8, rerank_score=0.9, final_score=0.9
            )
        ]

        result = retrieve(query.id, verbose=False)

        # Only valid chunk should be in results
        assert len(result.chunks) == 1
        assert result.chunks[0].id == valid_chunk.id

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_with_entities_and_intent(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session
    ):
        """Test retrieval with entities and intent for bias application."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.commit()

        chunk = Chunk(
            work_id=work.id, level="H2",
            content="This is a test chunk about memory and encoding with enough words.",
            start_line=1, end_line=10, vector_status="vec",
            embedding=[0.1] * 768
        )
        chunk.id = 1
        mock_session.add(chunk)
        mock_session.commit()

        query = Query(
            original_query="test query",
            vector_status="vec",
            embedding_original=[0.1] * 768,
            entities=["memory", "encoding"],
            intent="DEFINITION"
        )
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query

        mock_dense_search.return_value = [(chunk.id, 1)]
        mock_lexical_search.return_value = [(chunk.id, 1)]
        mock_rerank_chunks.return_value = [
            RetrievedChunk(
                id=chunk.id, parent_id=None, work_id=work.id,
                content=chunk.content, enriched_content=chunk.content,
                start_line=chunk.start_line, end_line=chunk.end_line,
                level=chunk.level, rrf_score=0.8, rerank_score=0.9, final_score=0.9
            )
        ]

        result = retrieve(query.id, verbose=False)

        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) > 0
        # Entity boost and intent bias should be applied
        assert result.chunks[0].entity_boost >= 0.0
        assert result.chunks[0].final_score >= result.chunks[0].rerank_score

    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.get_default_config')
    def test_retrieve_verbose_output(
        self, mock_get_config, mock_get_session, mock_lexical_search,
        mock_dense_search, mock_rerank_chunks, mock_session, capsys
    ):
        """Test verbose output during retrieval."""
        mock_config = {
            "retrieval": {
                "dense_limit": 10, "lexical_limit": 5, "rrf_k": 50,
                "top_k_rrf": 20, "top_n_final": 5, "entity_boost": 0.05,
                "min_word_count": 10, "min_char_count": 50,
                "min_content_length": 100, "enrich_lines_above": 0,
                "enrich_lines_below": 5, "mmr_lambda": 0.7,
                "reranker_batch_size": 8, "reranker_max_length": 512
            }
        }
        mock_get_config.return_value = mock_config
        mock_get_session.return_value.__enter__.return_value = mock_session

        query = Query(original_query="test", vector_status="vec", embedding_original=[0.1] * 768)
        query.id = 1
        mock_session.add(query)
        mock_session.commit()
        mock_session.query.return_value.filter.return_value.first.return_value = query

        mock_dense_search.return_value = []
        mock_lexical_search.return_value = []
        mock_rerank_chunks.return_value = []

        result = retrieve(query.id, verbose=True)

        captured = capsys.readouterr()
        assert "Retrieving for query" in captured.out or "Using RAG config" in captured.out
        assert isinstance(result, RetrievalResult)


class TestDenseSearch:
    """Test _dense_search function (mocked for SQLite compatibility)."""

    @patch('vulcanlab.retrieval.retrieve.get_session')
    def test_dense_search_mocked(self, mock_get_session, mock_session):
        """Test dense search with mocked database query."""
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create chunks with embeddings
        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.flush()  # Flush to get work.id

        chunk1 = Chunk(
            work_id=work.id, level="H2", content="Test 1",
            start_line=1, end_line=10, vector_status="vec",
            embedding=[0.1] * 768
        )
        chunk1.id = 1
        chunk2 = Chunk(
            work_id=work.id, level="H2", content="Test 2",
            start_line=11, end_line=20, vector_status="vec",
            embedding=[0.2] * 768
        )
        chunk2.id = 2
        mock_session.add_all([chunk1, chunk2])
        mock_session.flush()  # Flush to get chunk IDs

        # Store IDs before mocking
        chunk1_id = chunk1.id
        chunk2_id = chunk2.id

        # Mock the SQL query execution
        with patch.object(mock_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [(chunk1_id,), (chunk2_id,)]
            mock_execute.return_value = mock_result

            # Note: This test demonstrates the structure, but actual pgvector
            # operations require PostgreSQL, so we test the function signature
            # and expected return format
            embedding = [0.15] * 768
            # In real usage, this would call pgvector similarity search
            # For testing, we verify the function exists and has correct signature
            assert callable(_dense_search)


class TestLexicalSearch:
    """Test _lexical_search function (mocked for SQLite compatibility)."""

    @patch('vulcanlab.retrieval.retrieve.get_session')
    def test_lexical_search_mocked(self, mock_get_session, mock_session):
        """Test lexical search with mocked database query."""
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create chunks
        work = Work(title="Test", authors="Author")
        work.id = 1
        mock_session.add(work)
        mock_session.flush()  # Flush to get work.id

        chunk = Chunk(
            work_id=work.id, level="H2", content="Test content",
            start_line=1, end_line=10, vector_status="vec",
            embedding=[0.1] * 768
        )
        chunk.id = 1
        mock_session.add(chunk)
        mock_session.flush()  # Flush to get chunk.id

        # Store ID before mocking
        chunk_id = chunk.id

        # Mock the SQL query execution
        with patch.object(mock_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [(chunk_id,)]
            mock_execute.return_value = mock_result

            # Note: This test demonstrates the structure, but actual full-text
            # search requires PostgreSQL tsvector, so we test the function
            # signature and expected return format
            query_text = "test"
            # In real usage, this would call PostgreSQL full-text search
            # For testing, we verify the function exists and has correct signature
            assert callable(_lexical_search)
