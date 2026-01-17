import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarization.prompt_generator import (
    format_section,
    format_context_headings,
    batch_headings,
    assemble_prompts,
    generate_prompts,
    PromptBatch,
    HeadingWithChunks,
    PromptBudget
)
from vulcanlab.summarization.heading_selector import HeadingInfo
from vulcanlab.summarization.chunk_ranker import RankedChunk

class MockSettings:
    def __init__(self):
        self.max_llm_calls = 5
        self.max_tokens_per_call = 1000
        self.tokens_per_word = 1.0
        self.h1_h2_min_chunks = 2
        self.h3_min_chunks = 1

def create_heading(chunk_id, level, title, start=10, end=20):
    return HeadingInfo(
        chunk_id=chunk_id,
        level=level,
        start_line=start,
        end_line=end,
        content_word_count=0,
        heading_title=title
    )

def create_ranked_chunk(chunk_id, content, start=15, end=18):
    return RankedChunk(
        chunk_id=chunk_id,
        content=content,
        word_count=len(content.split()),
        start_line=start,
        end_line=end
    )

def test_format_section():
    heading = create_heading(1, "H1", "Main Section", 10, 50)
    chunks = [
        create_ranked_chunk(101, "First chunk content", 11, 15),
        create_ranked_chunk(102, "Second chunk content", 20, 25)
    ]
    
    formatted = format_section(heading, chunks)
    
    assert "# Main Section" in formatted
    assert "-- id: 1" in formatted
    assert "-- lines: 10-50" in formatted
    assert "First chunk content" in formatted
    assert "-- chunk_id: 101, lines: 11-15" in formatted
    assert "Second chunk content" in formatted
    assert "-- chunk_id: 102, lines: 20-25" in formatted

def test_format_context_headings():
    all_headings = [
        create_heading(1, "H1", "H1"),
        create_heading(2, "H2", "H2"),
        create_heading(3, "H2", "H3"),
        create_heading(4, "H3", "H4"),
        create_heading(5, "H3", "H5")
    ]
    
    # Batch is H3 (index 2) and H4 (index 3)
    formatted = format_context_headings(all_headings, 2, 3)
    
    assert "## Previous context (headings only):" in formatted
    assert "- H1" in formatted
    assert "- H2" in formatted
    assert "## Subsequent context (headings only):" in formatted
    assert "- H5" in formatted
    # Should NOT contain current batch headings in context
    assert "- H3" not in formatted
    assert "- H4" not in formatted

def test_batch_headings_respects_token_limit():
    settings = MockSettings()
    settings.max_tokens_per_call = 10 # very small
    
    # Title (1) + Chunks (2) = 3 tokens each
    hwcs = [
        HeadingWithChunks(create_heading(1, "H1", "T1"), [create_ranked_chunk(101, "c1 c2")]),
        HeadingWithChunks(create_heading(2, "H1", "T2"), [create_ranked_chunk(102, "c3 c4")]),
        HeadingWithChunks(create_heading(3, "H1", "T3"), [create_ranked_chunk(103, "c5 c6")]),
        HeadingWithChunks(create_heading(4, "H1", "T4"), [create_ranked_chunk(104, "c7 c8")]),
    ]
    
    batches = batch_headings(hwcs, settings.max_tokens_per_call, settings.tokens_per_word)
    
    # Each heading is 3 tokens. Max 10.
    # Batch 1: T1, T2, T3 (9 tokens)
    # Batch 2: T4 (3 tokens)
    assert len(batches) == 2
    assert len(batches[0]) == 3
    assert len(batches[1]) == 1

def test_batch_headings_single_large_heading():
    settings = MockSettings()
    settings.max_tokens_per_call = 5
    
    # Title (1) + Chunks (10) = 11 tokens (exceeds 5)
    hwcs = [
        HeadingWithChunks(create_heading(1, "H1", "T1"), [create_ranked_chunk(101, " ".join(["word"]*10))]),
        HeadingWithChunks(create_heading(2, "H1", "T2"), [create_ranked_chunk(102, "c1")]),
    ]
    
    batches = batch_headings(hwcs, settings.max_tokens_per_call, settings.tokens_per_word)
    
    # Large heading gets its own batch
    assert len(batches) == 2
    assert len(batches[0]) == 1
    assert batches[0][0].heading.chunk_id == 1

@patch("vulcanlab.summarization.prompt_generator.get_active_template")
def test_assemble_prompts(mock_get_template):
    mock_get_template.return_value = "Context:\n{context_headings}\n\nSections:\n{sections_content}"
    
    settings = MockSettings()
    all_headings = [
        create_heading(1, "H1", "H1"),
        create_heading(2, "H1", "H2")
    ]
    hwcs = [
        HeadingWithChunks(all_headings[0], [create_ranked_chunk(101, "content1")]),
        HeadingWithChunks(all_headings[1], [create_ranked_chunk(102, "content2")])
    ]
    
    session = MagicMock()
    batches = assemble_prompts(hwcs, all_headings, session, settings)
    
    assert len(batches) == 1
    prompt = batches[0].content
    assert "Sections:" in prompt
    assert "# H1" in prompt
    assert "content1" in prompt
    assert "# H2" in prompt
    assert "content2" in prompt
    assert batches[0].heading_ids == [1, 2]

@patch("vulcanlab.summarization.prompt_generator.select_headings_for_summarization")
@patch("vulcanlab.summarization.prompt_generator.rank_content_chunks")
@patch("vulcanlab.summarization.prompt_generator.get_active_template")
def test_generate_prompts_integration(mock_get_template, mock_rank, mock_select):
    mock_get_template.return_value = "{sections_content}"
    
    h1 = create_heading(1, "H1", "H1")
    mock_select.return_value = [h1]
    
    c1 = create_ranked_chunk(101, "chunk1")
    mock_rank.return_value = [c1]
    
    settings = MockSettings()
    session = MagicMock()
    
    batches = generate_prompts(123, session, settings)
    
    assert len(batches) == 1
    assert "# H1" in batches[0].content
    assert "chunk1" in batches[0].content
    assert batches[0].heading_ids == [1]
    mock_select.assert_called_once_with(123, session, settings)
    mock_rank.assert_called_once_with(h1, session, settings)
