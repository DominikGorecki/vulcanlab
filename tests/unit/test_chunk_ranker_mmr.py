import math
import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarization.chunk_ranker import (
    compute_similarity,
    rerank_mmr,
    RankedChunk,
    get_chunk_embeddings
)

def test_compute_similarity_identical():
    v1 = [1.0, 0.0, 0.5]
    assert compute_similarity(v1, v1) == pytest.approx(1.0)

def test_compute_similarity_orthogonal():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    assert compute_similarity(v1, v2) == pytest.approx(0.0)

def test_compute_similarity_opposite():
    v1 = [1.0, 1.0]
    v2 = [-1.0, -1.0]
    assert compute_similarity(v1, v2) == pytest.approx(-1.0)

def test_compute_similarity_zero():
    v1 = [0.0, 0.0]
    v2 = [1.0, 1.0]
    assert compute_similarity(v1, v2) == 0.0

def test_rerank_mmr_lambda_1():
    # Lambda = 1.0 should preserve RRF order (pure relevance)
    rc1 = RankedChunk(chunk_id=1, content="c1", word_count=1, rrf_score=0.9)
    rc2 = RankedChunk(chunk_id=2, content="c2", word_count=1, rrf_score=0.8)
    rc3 = RankedChunk(chunk_id=3, content="c3", word_count=1, rrf_score=0.7)
    
    ranked_chunks = [rc1, rc2, rc3]
    embeddings = {
        1: [1.0, 0.0],
        2: [1.0, 0.01], # very similar to 1
        3: [0.0, 1.0]   # different from 1
    }
    
    # top_n = 3
    results = rerank_mmr(ranked_chunks, embeddings, lambda_param=1.0, top_n=3)
    
    assert len(results) == 3
    assert results[0].chunk_id == 1
    assert results[1].chunk_id == 2
    assert results[2].chunk_id == 3
    assert results[0].rank_position == 1
    assert results[1].rank_position == 2
    assert results[2].rank_position == 3

def test_rerank_mmr_lambda_0():
    # Lambda = 0.0 should maximize diversity
    # First selection is always the top relevance (standard MMR)
    rc1 = RankedChunk(chunk_id=1, content="c1", word_count=1, rrf_score=0.9)
    rc2 = RankedChunk(chunk_id=2, content="c2", word_count=1, rrf_score=0.8) # similar to 1
    rc3 = RankedChunk(chunk_id=3, content="c3", word_count=1, rrf_score=0.7) # diverse from 1
    
    ranked_chunks = [rc1, rc2, rc3]
    embeddings = {
        1: [1.0, 0.0],
        2: [0.99, 0.01], # similar to 1
        3: [0.0, 1.0]    # diverse from 1
    }
    
    # With lambda=0, after selecting rc1:
    # rc2 score: 0 * 0.8 - 1 * ~1.0 = -1.0
    # rc3 score: 0 * 0.7 - 1 * 0 = 0.0
    # rc3 should be selected second
    
    results = rerank_mmr(ranked_chunks, embeddings, lambda_param=0.0, top_n=3)
    
    assert len(results) == 3
    assert results[0].chunk_id == 1
    assert results[1].chunk_id == 3
    assert results[2].chunk_id == 2

def test_rerank_mmr_top_n_limit():
    rc1 = RankedChunk(chunk_id=1, content="c1", word_count=1, rrf_score=0.9)
    rc2 = RankedChunk(chunk_id=2, content="c2", word_count=1, rrf_score=0.8)
    
    ranked_chunks = [rc1, rc2]
    embeddings = {1: [1.0, 0.0], 2: [0.0, 1.0]}
    
    results = rerank_mmr(ranked_chunks, embeddings, lambda_param=0.7, top_n=1)
    assert len(results) == 1
    assert results[0].chunk_id == 1

def test_rerank_mmr_missing_embeddings():
    rc1 = RankedChunk(chunk_id=1, content="c1", word_count=1, rrf_score=0.9)
    rc2 = RankedChunk(chunk_id=2, content="c2", word_count=1, rrf_score=0.8)
    
    ranked_chunks = [rc1, rc2]
    embeddings = {1: [1.0, 0.0]} # 2 is missing
    
    results = rerank_mmr(ranked_chunks, embeddings, lambda_param=0.7, top_n=2)
    assert len(results) == 1
    assert results[0].chunk_id == 1

def test_rerank_mmr_empty_input():
    assert rerank_mmr([], {}, 0.7, 5) == []

@patch("vulcanlab.summarization.chunk_ranker.select")
def test_get_chunk_embeddings(mock_select):
    session = MagicMock()
    
    # Mocking Chunk and results
    # Each row is (id, embedding)
    mock_results = [
        (1, [0.1, 0.2]),
        (2, [0.3, 0.4])
    ]
    session.execute.return_value.all.return_value = mock_results
    
    embeddings = get_chunk_embeddings([1, 2, 3], session)
    
    assert len(embeddings) == 2
    assert embeddings[1] == [0.1, 0.2]
    assert embeddings[2] == [0.3, 0.4]
    assert 3 not in embeddings
