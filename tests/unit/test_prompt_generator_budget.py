import pytest
from vulcanlab.summarization.prompt_generator import (
    estimate_tokens, 
    calculate_total_budget, 
    prune_to_budget,
    HeadingWithChunks,
    get_heading_level
)
from vulcanlab.summarization.chunk_ranker import RankedChunk
from vulcanlab.summarization.heading_selector import HeadingInfo

class MockSettings:
    def __init__(self):
        self.max_llm_calls = 5
        self.max_tokens_per_call = 1000
        self.tokens_per_word = 1.0
        self.h1_h2_min_chunks = 2
        self.h3_min_chunks = 1

def create_hwc(chunk_id, level, title, chunk_contents):
    heading = HeadingInfo(
        chunk_id=chunk_id,
        level=level,
        start_line=0,
        end_line=0,
        content_word_count=0,
        heading_title=title
    )
    chunks = [
        RankedChunk(chunk_id=i, content=content, word_count=len(content.split()))
        for i, content in enumerate(chunk_contents)
    ]
    return HeadingWithChunks(heading=heading, ranked_chunks=chunks)

def test_estimate_tokens():
    assert estimate_tokens("one two three", 1.0) == 3
    assert estimate_tokens("one two three", 0.5) == 1
    assert estimate_tokens("", 1.0) == 0
    assert estimate_tokens(None, 1.0) == 0

def test_get_heading_level():
    assert get_heading_level("H1") == 1
    assert get_heading_level("H5") == 5
    assert get_heading_level("Introduction") == 99
    assert get_heading_level("") == 99

def test_calculate_total_budget():
    settings = MockSettings()
    hwcs = [
        create_hwc(1, "H1", "Title 1", ["chunk1", "chunk2"]),
        create_hwc(2, "H2", "Title 2", ["chunk3"])
    ]
    # Title 1 (2 words) + chunk1 (1) + chunk2 (1) = 4
    # Title 2 (2) + chunk3 (1) = 3
    # Total = 7
    total, max_budget = calculate_total_budget(hwcs, settings)
    assert total == 7
    assert max_budget == 5000

def test_prune_to_budget_no_pruning_needed():
    settings = MockSettings()
    hwcs = [create_hwc(1, "H1", "Title", ["chunk1", "chunk2"])]
    # Total = 1 + 1 + 1 = 3
    pruned = prune_to_budget(hwcs, 10, settings)
    assert len(pruned) == 1
    assert len(pruned[0].ranked_chunks) == 2

def test_prune_to_budget_removes_from_lowest_level_first():
    settings = MockSettings()
    settings.tokens_per_word = 1.0
    hwcs = [
        create_hwc(1, "H1", "H1Title", ["c1", "c2", "c3"]), # 1+3=4
        create_hwc(2, "H3", "H3Title", ["c4", "c5", "c6"]), # 1+3=4
    ]
    # Total = 8. Budget = 6.
    # H3 is lower than H1. H3 should be pruned first.
    # H3 has 3 chunks, min is 1. We should remove 2 chunks from H3.
    # Total will be 4 (H1) + 2 (H3: Title + 1 chunk) = 6.
    total, _ = calculate_total_budget(hwcs, settings)
    pruned = prune_to_budget(hwcs, 6, settings)
    
    assert len(pruned) == 2
    h1 = next(h for h in pruned if h.heading.level == "H1")
    h3 = next(h for h in pruned if h.heading.level == "H3")
    
    assert len(h1.ranked_chunks) == 3
    assert len(h3.ranked_chunks) == 1

def test_prune_to_budget_respects_min_chunks():
    settings = MockSettings()
    hwcs = [
        create_hwc(1, "H1", "Title1", ["c1", "c2"]), # 1+2=3
        create_hwc(2, "H3", "Title2", ["c3"]),       # 1+1=2
    ]
    # Total = 5. Budget = 4.
    # Both are at their minimum (H1=2, H3=1).
    # Pruning should remove the lowest level heading entirely.
    pruned = prune_to_budget(hwcs, 4, settings)
    
    assert len(pruned) == 1
    assert pruned[0].heading.level == "H1"
    assert len(pruned[0].ranked_chunks) == 2

def test_prune_to_budget_removes_entire_heading_when_at_min():
    settings = MockSettings()
    hwcs = [
        create_hwc(1, "H1", "T1", ["c1", "c2"]), # 3 tokens
        create_hwc(2, "H2", "T2", ["c3", "c4"]), # 3 tokens
    ]
    # Total = 6. Budget = 3.
    # Both at min 2. Should remove one H2.
    pruned = prune_to_budget(hwcs, 3, settings)
    assert len(pruned) == 1
    assert pruned[0].heading.level == "H1"

def test_prune_to_budget_complex_scenario():
    settings = MockSettings()
    hwcs = [
        create_hwc(1, "H1", "T1", ["c1", "c2", "c3"]), # 4
        create_hwc(2, "H2", "T2", ["c4", "c5", "c6"]), # 4
        create_hwc(3, "H3", "T3", ["c7", "c8"]),       # 3
    ]
    # Total = 11. Budget = 8.
    # 1. Prune H3 from 2 down to 1 chunk. Total = 10.
    # 2. H3 is at min. Prune H2 from 3 down to 2. Total = 9.
    # 3. H1 from 3 down to 2. Total = 8.
    # Wait, my logic picks "lowest level with spare". 
    # H3 is level 3. H2 is 2. H1 is 1.
    # H3 has spare (2 > 1). Prune H3. Total 10.
    # H2 has spare (3 > 2). Prune H2. Total 9.
    # H1 has spare (3 > 2). Prune H1. Total 8.
    # Correct.
    
    pruned = prune_to_budget(hwcs, 8, settings)
    h1 = next(h for h in pruned if h.heading.chunk_id == 1)
    h2 = next(h for h in pruned if h.heading.chunk_id == 2)
    h3 = next(h for h in pruned if h.heading.chunk_id == 3)
    
    assert len(h1.ranked_chunks) == 2
    assert len(h2.ranked_chunks) == 2
    assert len(h3.ranked_chunks) == 1

def test_prune_to_budget_empty_list():
    settings = MockSettings()
    assert prune_to_budget([], 100, settings) == []

def test_prune_to_budget_all_at_min_still_over():
    settings = MockSettings()
    hwcs = [
        create_hwc(1, "H1", "T1", ["c1", "c2"]), # 3 tokens
    ]
    # Total 3, budget 1. At min 2.
    # Should remove the heading.
    pruned = prune_to_budget(hwcs, 1, settings)
    assert len(pruned) == 0

def test_prune_to_budget_removes_lowest_ranked_chunk_within_level():
    settings = MockSettings()
    # Create two H3 headings, both with 2 chunks.
    # Total = (Title1 + c1 + c2) + (Title2 + c3 + c4) = 3 + 3 = 6
    # Budget = 5.
    # It should prune one chunk from one of the H3 headings.
    # Our logic picks the one with "most chunks", if equal, first one.
    hwcs = [
        create_hwc(1, "H3", "T1", ["c1", "c2"]), 
        create_hwc(2, "H3", "T2", ["c3", "c4"]),
    ]
    pruned = prune_to_budget(hwcs, 5, settings)
    assert len(pruned) == 2
    # One should have 2 chunks, the other 1.
    counts = sorted([len(h.ranked_chunks) for h in pruned])
    assert counts == [1, 2]

def test_prune_to_budget_single_heading_single_chunk():
    settings = MockSettings()
    hwcs = [create_hwc(1, "H1", "T1", ["c1"])]
    # Total = 2. Budget = 1.
    # At min 2 chunks for H1? Wait, if it only has 1 chunk to begin with...
    # The logic says if len(hc.ranked_chunks) > min_chunks. 
    # If it has 1 chunk and min is 2, it's already below min chunks.
    # So it won't prune the chunk, it will remove the whole heading.
    pruned = prune_to_budget(hwcs, 1, settings)
    assert len(pruned) == 0

def test_estimate_tokens_with_ratio():
    assert estimate_tokens("one two three four", 0.75) == 3 # 4 * 0.75 = 3
    assert estimate_tokens("one two three", 0.75) == 2 # 3 * 0.75 = 2.25 -> 2
