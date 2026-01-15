import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarize.salience import (
    SalienceWeights,
    load_salience_weights,
    score_heading_depth,
    score_definition_density,
    score_list_density,
    score_keyphrase_novelty,
    score_location_prior,
    compute_salience_score,
    passes_threshold
)
from vulcanlab.data.models.summarize_settings import SummarizeSettings

def test_score_heading_depth():
    assert score_heading_depth("H1") == 1.0
    assert score_heading_depth("H2") == 0.8
    assert score_heading_depth("H3") == 0.6
    assert score_heading_depth("H4") == 0.4
    assert score_heading_depth("H5") == 0.2
    assert score_heading_depth("h1") == 1.0
    assert score_heading_depth("Unknown") == 0.1

def test_score_definition_density():
    # Case with definitions
    content = "A computer is a machine. A cat refers to a feline. We define logic as reasoning."
    # Patterns: "computer is", "cat refers to", "define logic as" (wait, my pattern was "(\w+)\s+(is|are|refers?\s+to|means?|defined\s+as)")
    # "computer is" -> match
    # "cat refers to" -> match
    # "define logic as" -> no match with current pattern, but "logic is" would.
    # Let's check my pattern again: r"(\w+)\s+(is|are|refers?\s+to|means?|defined\s+as)"
    # Ah, "defined as" not "define ... as".
    
    score = score_definition_density(content)
    assert score > 0
    
    # Case with no definitions
    content_no_def = "This is just some text with no clear definitions in it."
    # "This is" might match if "This" is considered a word.
    # Actually "This is" fits (\w+)\s+(is).
    
    content_really_no_def = "Running jumping swimming. One two three."
    assert score_definition_density(content_really_no_def) == 0.0
    
    # Empty case
    assert score_definition_density("") == 0.0
    assert score_definition_density("   ") == 0.0

def test_score_list_density():
    # Bullet points
    content_bullets = "- Item 1\n* Item 2\n+ Item 3\nNot a list item"
    assert score_list_density(content_bullets) == 0.75
    
    # Numbered items
    content_numbers = "1. First\n2) Second\n(a) Third\nJust text"
    assert score_list_density(content_numbers) == 0.75
    
    # No list
    content_no_list = "Paragraph one.\nParagraph two."
    assert score_list_density(content_no_list) == 0.0
    
    # Empty
    assert score_list_density("") == 0.0

def test_score_keyphrase_novelty():
    seen = {"machine learning", "neural networks"}
    content = "Deep learning is related to neural networks but uses new algorithms."
    
    # "Deep learning" is new, "neural networks" is seen.
    # The actual extraction depends on spaCy, so we'll just check if it returns a value
    score = score_keyphrase_novelty(content, seen)
    assert 0.0 <= score <= 1.0
    assert "deep learning" in seen
    
    # All seen
    seen_all = {"deep learning", "algorithms"}
    content_all_seen = "Deep learning algorithms."
    score_all_seen = score_keyphrase_novelty(content_all_seen, seen_all)
    assert score_all_seen == 0.0

def test_score_location_prior():
    # Intro (first 10%)
    assert score_location_prior(0, 10) == 1.0
    # Conclusion (last 10%)
    assert score_location_prior(9, 10) == 1.0
    # Middle
    assert score_location_prior(5, 10) == 0.0
    # Edge case: 1 chunk
    assert score_location_prior(0, 1) == 1.0

def test_compute_salience_score():
    weights = SalienceWeights(
        h1_always_summarize=True,
        h2_top_percent=100,
        h3_salience_threshold=0.5,
        h4_salience_threshold=0.7,
        definition_density_weight=0.2,
        list_density_weight=0.2,
        keyphrase_novelty_weight=0.2,
        location_prior_weight=0.2,
        heading_depth_weight=0.2
    )
    
    seen = set()
    # Content that should score high in most categories
    content = "- A cat is a feline.\n- It refers to animals."
    # s_depth(H1) = 1.0
    # s_def > 0
    # s_list = 1.0
    # s_novelty = 1.0
    # s_loc(0, 10) = 1.0
    
    score = compute_salience_score(content, "H1", weights, seen, 0, 10)
    assert 0.0 <= score <= 1.0
    assert score > 0.5 # Should be relatively high

def test_passes_threshold():
    weights = SalienceWeights(
        h1_always_summarize=True,
        h2_top_percent=100,
        h3_salience_threshold=0.5,
        h4_salience_threshold=0.7,
        definition_density_weight=0.2,
        list_density_weight=0.2,
        keyphrase_novelty_weight=0.2,
        location_prior_weight=0.2,
        heading_depth_weight=0.2
    )
    
    # H1
    assert passes_threshold(0.1, "H1", weights) is True
    
    # H2 (always True for now, top_percent handled elsewhere)
    assert passes_threshold(0.1, "H2", weights) is True
    
    # H3
    assert passes_threshold(0.6, "H3", weights) is True
    assert passes_threshold(0.4, "H3", weights) is False
    
    # H4
    assert passes_threshold(0.8, "H4", weights) is True
    assert passes_threshold(0.6, "H4", weights) is False

def test_load_salience_weights():
    mock_session = MagicMock()
    mock_settings = SummarizeSettings(
        h1_always_summarize=False,
        h3_salience_threshold=0.8
    )
    
    mock_query = mock_session.query.return_value
    mock_order_by = mock_query.order_by.return_value
    mock_order_by.first.return_value = mock_settings
    
    weights = load_salience_weights(mock_session)
    assert weights.h1_always_summarize is False
    assert weights.h3_salience_threshold == 0.8
    assert weights.h4_salience_threshold == 0.7 # Default

def test_load_salience_weights_empty():
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value
    mock_order_by = mock_query.order_by.return_value
    mock_order_by.first.return_value = None
    
    weights = load_salience_weights(mock_session)
    assert weights.h1_always_summarize is True # Default
    assert weights.h3_salience_threshold == 0.5 # Default
