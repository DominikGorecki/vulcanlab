import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarization.heading_selector import (
    HeadingInfo,
    get_heading_chunks,
    filter_by_word_count,
    enforce_heading_budget,
    select_headings_for_summarization
)
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.summarize_settings import SummarizeSettings

def test_heading_info_dataclass():
    h = HeadingInfo(
        chunk_id=1,
        level="H1",
        start_line=10,
        end_line=20,
        content_word_count=100,
        heading_title="Test Heading"
    )
    assert h.chunk_id == 1
    assert h.level == "H1"
    assert h.content_word_count == 100
    assert h.heading_title == "Test Heading"

def test_get_heading_chunks():
    # Mock session and chunks
    mock_session = MagicMock()
    
    mock_chunks = [
        Chunk(id=1, work_id=1, level="H1", content="# Heading 1\nSome text", start_line=1, end_line=5),
        Chunk(id=2, work_id=1, level="H1-chunk", content="More text", start_line=6, end_line=10),
        Chunk(id=3, work_id=1, level="H2", content="## Heading 2\nMore text here", start_line=11, end_line=15),
    ]
    
    # Configure mock session to return our chunks (excluding the H1-chunk)
    mock_session.execute.return_value.scalars.return_value.all.return_value = [
        mock_chunks[0], mock_chunks[2]
    ]
    
    headings = get_heading_chunks(work_id=1, session=mock_session)
    
    assert len(headings) == 2
    assert headings[0].chunk_id == 1
    assert headings[0].level == "H1"
    assert headings[0].heading_title == "Heading 1"
    # Content is "# Heading 1\nSome text". split() gives ['#', 'Heading', '1', 'Some', 'text']
    assert headings[0].content_word_count == 5
    
    assert headings[1].chunk_id == 3
    assert headings[1].level == "H2"
    assert headings[1].heading_title == "Heading 2"

def test_filter_by_word_count():
    headings = [
        HeadingInfo(1, "H1", 1, 10, 100, "H1"),
        HeadingInfo(2, "H2", 11, 20, 50, "H2"),
        HeadingInfo(3, "H3", 21, 30, 10, "H3"),
    ]
    
    filtered = filter_by_word_count(headings, min_words=50)
    assert len(filtered) == 2
    assert filtered[0].chunk_id == 1
    assert filtered[1].chunk_id == 2
    
    filtered_none = filter_by_word_count(headings, min_words=1000)
    assert len(filtered_none) == 0

def test_enforce_heading_budget():
    headings = [
        # titles have 1 word each
        HeadingInfo(1, "H1", 1, 10, 1000, "Title1"), # level 1
        HeadingInfo(2, "H2", 11, 20, 500, "Title2"), # level 2
        HeadingInfo(3, "H3", 21, 30, 100, "Title3"), # level 3
        HeadingInfo(4, "H3", 31, 40, 200, "Title4"), # level 3
    ]
    
    # Budget of 3 words means we must remove 1 heading
    # Level 3 is lowest. Among Level 3s, Title3 (100 words) is shorter than Title4 (200 words).
    # So Title3 should be removed first.
    budgeted = enforce_heading_budget(headings, max_total_words=3)
    assert len(budgeted) == 3
    assert budgeted[0].chunk_id == 1
    assert budgeted[1].chunk_id == 2
    assert budgeted[2].chunk_id == 4
    
    # Budget of 2 words
    # Next to remove is Title4 (remaining Level 3)
    budgeted = enforce_heading_budget(headings, max_total_words=2)
    assert len(budgeted) == 2
    assert budgeted[0].chunk_id == 1
    assert budgeted[1].chunk_id == 2
    
    # Budget of 1 word
    # Next to remove is Title2 (lowest level among H1, H2)
    budgeted = enforce_heading_budget(headings, max_total_words=1)
    assert len(budgeted) == 1
    assert budgeted[0].chunk_id == 1

def test_enforce_heading_budget_tie_breaking():
    headings = [
        HeadingInfo(1, "H3", 1, 10, 100, "T1"),
        HeadingInfo(2, "H3", 11, 20, 100, "T2"),
    ]
    # Both same level and same word count. Should remove one of them.
    budgeted = enforce_heading_budget(headings, max_total_words=1)
    assert len(budgeted) == 1

def test_enforce_heading_budget_empty():
    assert enforce_heading_budget([], 10) == []

def test_select_headings_for_summarization():
    mock_session = MagicMock()
    # Create settings mock without using the real model if possible, 
    # but since it's a simple dataclass-like Base model, it's fine.
    mock_settings = MagicMock(spec=SummarizeSettings)
    mock_settings.min_heading_word_count = 50
    mock_settings.max_total_heading_words = 2
    
    with patch("vulcanlab.summarization.heading_selector.get_heading_chunks") as mock_get:
        mock_get.return_value = [
            HeadingInfo(1, "H1", 1, 10, 60, "H1 Title"),   # 2 words in title
            HeadingInfo(2, "H2", 11, 20, 10, "H2 Small"),  # 2 words in title, but small content
            HeadingInfo(3, "H2", 21, 30, 100, "H2 Big"),    # 2 words in title
            HeadingInfo(4, "H3", 31, 40, 100, "H3 Big"),    # 2 words in title
        ]
        
        results = select_headings_for_summarization(1, mock_session, mock_settings)
        
        # 1. H2 Small (id=2) filtered by word count (10 < 50)
        # 2. Remaining: id=1 (H1), id=3 (H2), id=4 (H3)
        # 3. Titles: "H1 Title" (2), "H2 Big" (2), "H3 Big" (2) -> total 6
        # 4. Budget is 2 words.
        # 5. Remove id=4 (H3) -> total 4
        # 6. Remove id=3 (H2) -> total 2
        # 7. Final should be just id=1
        
        assert len(results) == 1
        assert results[0].chunk_id == 1
