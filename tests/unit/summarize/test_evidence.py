import pytest
from vulcanlab.summarize.evidence import (
    extract_topic_sentences,
    extract_definitions,
    extract_enumerations,
    extract_emphasis_cues,
    extract_keyphrases,
    build_evidence_packet,
    Snippet
)
from vulcanlab.summarize.nlp_utils import segment_sentences_with_lines

@pytest.fixture
def sample_text():
    return """VulcanLab is a specialized toolkit. It refers to the core library for AI research.

A definition is defined as a statement of meaning.

* First item
* Second item
  with multi-line
* Third item

This is a new paragraph. It is very important to note that emphasis matters.

Crucially, we should also test key phrases like machine learning and artificial intelligence.

1. Numbered one
2. Numbered two
"""

@pytest.fixture
def sentences(sample_text):
    return segment_sentences_with_lines(sample_text)

def test_extract_topic_sentences(sample_text, sentences):
    snippets = extract_topic_sentences(sample_text, sentences)
    texts = [s.text for s in snippets]
    assert "VulcanLab is a specialized toolkit." in texts
    assert "A definition is defined as a statement of meaning." in texts
    assert "This is a new paragraph." in texts
    assert all(s.snippet_type == "topic" for s in snippets)

def test_extract_definitions(sentences):
    snippets = extract_definitions("", sentences)
    texts = [s.text for s in snippets]
    
    assert "VulcanLab is a specialized toolkit." in texts
    assert "It refers to the core library for AI research." in texts
    assert "A definition is defined as a statement of meaning." in texts
    assert all(s.snippet_type == "definition" for s in snippets)

def test_extract_enumerations(sample_text):
    snippets = extract_enumerations(sample_text)
    
    # One bullet list and one numbered list
    assert len(snippets) == 2
    assert snippets[0].snippet_type == "enumeration"
    assert "* First item" in snippets[0].text
    assert "* Third item" in snippets[0].text
    assert "1. Numbered one" in snippets[1].text
    assert "2. Numbered two" in snippets[1].text
    
    # Check line numbers (rough check)
    assert snippets[0].start_line < snippets[1].start_line

def test_extract_emphasis_cues(sentences):
    snippets = extract_emphasis_cues("", sentences)
    texts = [s.text for s in snippets]
    
    assert any("important to note" in t for t in texts)
    assert any("Crucially" in t for t in texts)
    assert all(s.snippet_type == "emphasis" for s in snippets)

def test_extract_keyphrases(sample_text):
    # This uses spaCy, so it depends on the model
    keyphrases = extract_keyphrases(sample_text, top_n=30)
    
    assert len(keyphrases) > 0
    # Expected noun chunks (case might vary)
    lowercase_phrases = [p.lower() for p in keyphrases]
    assert any("toolkit" in p for p in lowercase_phrases)
    assert any("machine learning" in p for p in lowercase_phrases)

def test_build_evidence_packet(sample_text, sentences):
    packet = build_evidence_packet(
        sample_text, 
        sentences, 
        heading_path="test/section", 
        start_line=1, 
        end_line=15
    )
    
    assert packet.heading_path == "test/section"
    assert len(packet.snippets) > 0
    assert len(packet.keyphrases) > 0
    assert "by_type" in packet.stats
    
    # Check deduplication (definitions often overlap with topic sentences)
    # "VulcanLab is a specialized toolkit." is both topic and definition.
    # It should only appear once if they have the same line range.
    vulcanlab_snippets = [s for s in packet.snippets if "VulcanLab is a specialized toolkit" in s.text]
    assert len(vulcanlab_snippets) == 1
    # Priority says definitions come first
    assert vulcanlab_snippets[0].snippet_type == "definition"

def test_build_evidence_packet_limit(sample_text, sentences):
    # Set limit to 2
    packet = build_evidence_packet(
        sample_text, 
        sentences, 
        heading_path="test/section", 
        start_line=1, 
        end_line=15,
        max_snippets=2
    )
    
    assert len(packet.snippets) == 2
    # Priorities: definitions (3) > enumerations (2) > topic (rest) > emphasis (rest)
    # The 2 snippets should be definitions.
    assert all(s.snippet_type == "definition" for s in packet.snippets)

def test_edge_cases():
    empty_text = ""
    sentences = []
    
    packet = build_evidence_packet(empty_text, sentences, "empty", 1, 1)
    assert len(packet.snippets) == 0
    assert len(packet.keyphrases) == 0
    assert packet.stats["final_count"] == 0
