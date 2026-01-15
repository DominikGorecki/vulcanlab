import pytest
from unittest.mock import patch, MagicMock
from vulcanlab.summarize.nlp_utils import (
    segment_sentences,
    map_char_offset_to_line,
    segment_sentences_with_lines,
    detect_paragraph_boundaries,
    load_spacy_model,
    SentenceSpan,
    SentenceWithLines,
    ParagraphSpan
)

def test_map_char_offset_to_line():
    text = "Line 1\nLine 2\nLine 3"
    assert map_char_offset_to_line(text, 0) == 1
    assert map_char_offset_to_line(text, 5) == 1
    assert map_char_offset_to_line(text, 7) == 2
    assert map_char_offset_to_line(text, 13) == 2
    assert map_char_offset_to_line(text, 14) == 3
    assert map_char_offset_to_line(text, 100) == 3
    assert map_char_offset_to_line(text, -1) == 1

def test_segment_sentences_basic():
    text = "This is a sentence. This is another one."
    sentences = segment_sentences(text)
    assert len(sentences) == 2
    assert sentences[0].text == "This is a sentence."
    assert sentences[0].start_char == 0
    assert sentences[0].end_char == 19
    assert sentences[1].text == "This is another one."
    assert sentences[1].start_char == 20
    assert sentences[1].end_char == 40

def test_segment_sentences_empty():
    assert segment_sentences("") == []
    assert segment_sentences(None) == []

def test_segment_sentences_no_punctuation():
    text = "Just a single sentence without punctuation"
    sentences = segment_sentences(text)
    assert len(sentences) == 1
    assert sentences[0].text == text

def test_segment_sentences_with_lines():
    text = "Line one.\nLine two spans\ntwo lines. Line three."
    results = segment_sentences_with_lines(text)
    
    assert len(results) == 3
    assert results[0].text == "Line one."
    assert results[0].start_line == 1
    assert results[0].end_line == 1
    
    assert "Line two spans" in results[1].text
    assert results[1].start_line == 2
    assert results[1].end_line == 3
    
    assert results[2].text == "Line three."
    assert results[2].start_line == 3
    assert results[2].end_line == 3

def test_detect_paragraph_boundaries():
    text = "Para 1.\n\nPara 2\nwith multiple lines.\n\nPara 3."
    paras = detect_paragraph_boundaries(text)
    
    assert len(paras) == 3
    assert paras[0].text == "Para 1."
    assert paras[0].start_line == 1
    assert paras[0].end_line == 1
    
    assert "Para 2" in paras[1].text
    assert paras[1].start_line == 3
    assert paras[1].end_line == 4
    
    assert paras[2].text == "Para 3."
    assert paras[2].start_line == 6
    assert paras[2].end_line == 6

def test_detect_paragraph_boundaries_empty():
    assert detect_paragraph_boundaries("") == []
    assert detect_paragraph_boundaries(None) == []

@patch("spacy.load")
def test_load_spacy_model_error(mock_load):
    mock_load.side_effect = OSError("Model not found")
    
    # We need to reset the cached _nlp if it was already loaded in other tests
    import vulcanlab.summarize.nlp_utils
    vulcanlab.summarize.nlp_utils._nlp = None
    
    with pytest.raises(ImportError) as excinfo:
        load_spacy_model("missing_model")
    
    assert "is not installed" in str(excinfo.value)
