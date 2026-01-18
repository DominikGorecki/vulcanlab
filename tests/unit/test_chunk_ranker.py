import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarization.chunk_ranker import (
    build_search_query,
    fuse_rrf,
    RankedChunk,
    rank_content_chunks
)
from vulcanlab.summarization.heading_selector import HeadingInfo
from vulcanlab.data.models.summarize_settings import SummarizeSettings

def test_build_search_query():
    # Test with breadcrumbs
    query = build_search_query("H1 > H2", "My Title")
    assert query == "H1 H2 My Title"
    
    # Test with empty breadcrumbs
    query = build_search_query(None, "Only Title")
    assert query == "Only Title"
    
    # Test with markdown and whitespace
    query = build_search_query("H1 > **Bold**", "  *Italic*  ")
    assert query == "H1 Bold Italic"

def test_fuse_rrf_basic():
    dense_results = [(1, 0.9), (2, 0.8)]
    lexical_results = [(2, 0.5), (3, 0.4)]
    
    class MockChunk:
        def __init__(self, content):
            self.content = content
            self.start_line = 1
            self.end_line = 10
            
    chunk_data_map = {
        1: MockChunk("content one"),
        2: MockChunk("content two words"),
        3: MockChunk("content three words now")
    }
    
    # k=60, top_k=2
    fused = fuse_rrf(dense_results, lexical_results, chunk_data_map, k=60, top_k=2)
    
    assert len(fused) == 2
    # Chunk 2 is in both, should be first
    assert fused[0].chunk_id == 2
    assert fused[0].dense_rank == 2
    assert fused[0].lexical_rank == 1
    # score = 1/(60+2) + 1/(60+1) = 1/62 + 1/61
    expected_score_2 = (1.0/62.0) + (1.0/61.0)
    assert fused[0].rrf_score == pytest.approx(expected_score_2)
    
    # Chunk 1 is only in dense
    assert fused[1].chunk_id == 1
    assert fused[1].dense_rank == 1
    assert fused[1].lexical_rank is None
    # score = 1/(60+1) + 1/(60+999999)
    expected_score_1 = (1.0/61.0) + (1.0/(60+999999))
    assert fused[1].rrf_score == pytest.approx(expected_score_1)

def test_fuse_rrf_top_k():
    dense_results = [(i, 0.9) for i in range(10)]
    lexical_results = []
    chunk_data_map = {i: MagicMock(content="content") for i in range(10)}
    
    fused = fuse_rrf(dense_results, lexical_results, chunk_data_map, k=60, top_k=5)
    assert len(fused) == 5

@patch("vulcanlab.summarization.chunk_ranker.get_chunk_embeddings")
@patch("vulcanlab.summarization.chunk_ranker.search_dense")
@patch("vulcanlab.summarization.chunk_ranker.search_lexical")
def test_rank_content_chunks(mock_lexical, mock_dense, mock_embeddings):
    session = MagicMock()
    heading = HeadingInfo(
        chunk_id=10,
        level="H2",
        start_line=1,
        end_line=10,
        content_word_count=100,
        heading_title="Heading Title"
    )
    settings = SummarizeSettings(
        dense_top_k=5,
        lexical_top_k=5,
        rrf_k=60,
        rrf_top_k=3,
        mmr_lambda=0.7,
        mmr_top_n=5
    )
    
    # Mocking Chunk retrieval
    mock_chunks = [
        MagicMock(id=101, content="chunk 1 content", level="H2-chunk"),
        MagicMock(id=102, content="chunk 2 content with more words", level="H2-chunk")
    ]
    
    # Mock session.execute for Chunk retrieval
    mock_execute = MagicMock()
    mock_execute.scalars.return_value.all.return_value = mock_chunks
    session.execute.return_value = mock_execute
    
    # Mock parent chunk for breadcrumbs
    parent_chunk = MagicMock(id=10, heading_breadcrumbs="H1")
    session.get.return_value = parent_chunk
    
    # Mock search results
    # 102 should be first
    # 102: dense rank 1, lexical rank 1
    # 101: dense rank 2, lexical rank 2
    mock_dense.return_value = [(102, 0.8), (101, 0.7)]
    mock_lexical.return_value = [(102, 0.5), (101, 0.4)]
    
    # Mock embeddings for MMR
    mock_embeddings.return_value = {
        101: [0.1] * 768,
        102: [0.2] * 768
    }
    
    results = rank_content_chunks(heading, session, settings)
    
    assert len(results) == 2
    
    # Verify filtering used dense_lexical_use
    # The first call to execute is for the initial chunk retrieval
    call_args = session.execute.call_args_list[0][0][0]
    sql_query = str(call_args)
    assert "dense_lexical_use" in sql_query
    
    assert results[0].chunk_id == 102
    assert results[0].rank_position == 1
    assert results[1].chunk_id == 101
    assert results[1].rank_position == 2
    assert results[0].mmr_score is not None
    
    mock_dense.assert_called_once()
    mock_lexical.assert_called_once()
    mock_embeddings.assert_called_once()
