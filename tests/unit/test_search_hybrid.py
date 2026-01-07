import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.search.search_hybrid import search_hybrid

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def mock_results():
    # Helper to create mock results
    def _create_result(id, score_key, score_val):
        return {
            "id": id,
            "content_preview": f"Content {id}",
            "breadcrumb": f"Path > {id}",
            "level": "H1",
            "work_id": 1,
            "work_title": "Title",
            "work_authors": "Author",
            "work_year": 2024,
            "start_line": 1,
            "end_line": 10,
            score_key: score_val
        }
    return _create_result

def test_search_hybrid_overlapping(mock_session, mock_results):
    # Setup overlapping results
    lexical_res = [
        mock_results(1, "rank_score", 0.9),
        mock_results(2, "rank_score", 0.8)
    ]
    dense_res = [
        mock_results(2, "similarity_score", 0.95),
        mock_results(3, "similarity_score", 0.85)
    ]

    with patch("vulcanlab.search.search_hybrid.search_lexical", return_value=(lexical_res, 2)), \
         patch("vulcanlab.search.search_hybrid.search_dense", return_value=(dense_res, 2)):
        
        results, stats, total = search_hybrid("test query", mock_session, rrf_k=60)
        
        assert total == 3
        assert stats["fused_count"] == 3
        assert stats["dense_candidates"] == 2
        assert stats["lexical_candidates"] == 2
        
        # Result 2 should be first as it's in both
        assert results[0]["id"] == 2
        assert results[0]["dense_rank"] == 1
        assert results[0]["lexical_rank"] == 2
        
        # Check RRF score for result 2
        # k=60, dense_rank=1, lexical_rank=2, weights=0.5
        # score = 0.5/(60+1) + 0.5/(60+2)
        expected_score = (0.5 / 61) + (0.5 / 62)
        assert results[0]["rrf_score"] == pytest.approx(expected_score)

def test_search_hybrid_non_overlapping(mock_session, mock_results):
    lexical_res = [mock_results(1, "rank_score", 0.9)]
    dense_res = [mock_results(2, "similarity_score", 0.95)]

    with patch("vulcanlab.search.search_hybrid.search_lexical", return_value=(lexical_res, 1)), \
         patch("vulcanlab.search.search_hybrid.search_dense", return_value=(dense_res, 1)):
        
        results, stats, total = search_hybrid("test query", mock_session)
        
        assert total == 2
        # Both weights are 0.5. 
        # Result 2 (dense rank 1) vs Result 1 (lexical rank 1)
        # RRF score for both will be 0.5/(60+1) + 0.5/(60+999999) which is basically the same
        # Sorting might be stable or dependent on RRF score.
        assert results[0]["rrf_score"] == results[1]["rrf_score"]

def test_search_hybrid_empty_one_set(mock_session, mock_results):
    lexical_res = []
    dense_res = [mock_results(1, "similarity_score", 0.95)]

    with patch("vulcanlab.search.search_hybrid.search_lexical", return_value=(lexical_res, 0)), \
         patch("vulcanlab.search.search_hybrid.search_dense", return_value=(dense_res, 1)):
        
        results, stats, total = search_hybrid("test query", mock_session)
        
        assert total == 1
        assert results[0]["id"] == 1
        assert results[0]["dense_rank"] == 1
        assert results[0]["lexical_rank"] is None

def test_search_hybrid_pagination(mock_session, mock_results):
    # 5 results total
    lexical_res = [mock_results(i, "rank_score", 1.0/i) for i in range(1, 6)]
    dense_res = []

    with patch("vulcanlab.search.search_hybrid.search_lexical", return_value=(lexical_res, 5)), \
         patch("vulcanlab.search.search_hybrid.search_dense", return_value=(dense_res, 0)):
        
        # Page 1, size 2
        results, stats, total = search_hybrid("test", mock_session, page=1, page_size=2)
        assert len(results) == 2
        assert total == 5
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2
        
        # Page 2, size 2
        results, stats, total = search_hybrid("test", mock_session, page=2, page_size=2)
        assert len(results) == 2
        assert results[0]["id"] == 3
        assert results[1]["id"] == 4

def test_search_hybrid_weight_normalization(mock_session, mock_results):
    lexical_res = [mock_results(1, "rank_score", 0.9)]
    dense_res = [mock_results(1, "similarity_score", 0.9)]

    with patch("vulcanlab.search.search_hybrid.search_lexical", return_value=(lexical_res, 1)), \
         patch("vulcanlab.search.search_hybrid.search_dense", return_value=(dense_res, 1)):
        
        # weights 1, 3 -> normalized to 0.25, 0.75
        results, stats, total = search_hybrid(
            "test", mock_session, dense_weight=1.0, lexical_weight=3.0
        )
        
        # score = 0.25/(60+1) + 0.75/(60+1) = 1.0/61
        assert results[0]["rrf_score"] == pytest.approx(1.0 / 61)

