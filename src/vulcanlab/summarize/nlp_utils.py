from dataclasses import dataclass
import spacy
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class SentenceSpan:
    text: str
    start_char: int
    end_char: int

@dataclass
class SentenceWithLines:
    text: str
    start_char: int
    end_char: int
    start_line: int
    end_line: int

@dataclass
class ParagraphSpan:
    text: str
    start_char: int
    end_char: int
    start_line: int
    end_line: int

_nlp = None

# Maximum text size for spaCy processing (slightly under 1M to be safe)
SPACY_MAX_LENGTH = 900_000


def process_text_in_chunks(text: str, processor_func, max_length: int = SPACY_MAX_LENGTH):
    """
    Process large text in chunks, calling processor_func on each chunk.
    processor_func should take (text, nlp_model) and return a list of results.
    Results from all chunks are combined.
    """
    if not text:
        return []

    nlp = load_spacy_model()

    if len(text) <= max_length:
        return processor_func(text, nlp)

    logger.info(f"Processing {len(text):,} chars in chunks for NLP")
    all_results = []
    current_pos = 0

    while current_pos < len(text):
        remaining = len(text) - current_pos

        if remaining <= max_length:
            chunk = text[current_pos:]
        else:
            boundary = _find_chunk_boundary_simple(text, current_pos + max_length)
            chunk = text[current_pos:boundary]

        chunk_results = processor_func(chunk, nlp)
        all_results.extend(chunk_results)

        current_pos += len(chunk)

    return all_results


def _find_chunk_boundary_simple(text: str, target_size: int) -> int:
    """
    Find a good boundary point near target_size.
    """
    search_start = max(0, target_size - 10000)
    search_end = min(len(text), target_size + 10000)
    search_region = text[search_start:search_end]

    last_break = search_region.rfind('\n\n', 0, target_size - search_start)
    if last_break != -1:
        return search_start + last_break + 2

    last_newline = search_region.rfind('\n', 0, target_size - search_start)
    if last_newline != -1:
        return search_start + last_newline + 1

    return target_size


def load_spacy_model(model_name: str = "en_core_web_sm"):
    """
    Lazy loads and caches a spaCy model.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load(model_name, disable=["ner", "lemmatizer"])
        except OSError:
            logger.error(f"spaCy model '{model_name}' not found. Please install it using: python -m spacy download {model_name}")
            raise ImportError(f"spaCy model '{model_name}' is not installed. Run 'python -m spacy download {model_name}' to install it.")
    return _nlp

def map_char_offset_to_line(text: str, char_offset: int) -> int:
    """
    Maps a character offset to a 1-indexed line number.
    """
    if char_offset < 0:
        return 1
    return text.count("\n", 0, char_offset) + 1

def _segment_sentences_single(text: str, offset: int = 0) -> List[SentenceSpan]:
    """
    Segments a single chunk of text into sentences using spaCy.
    Offset is added to char positions when processing chunks.
    """
    if not text:
        return []

    nlp = load_spacy_model()
    doc = nlp(text)

    sentences = []
    for sent in doc.sents:
        sentences.append(SentenceSpan(
            text=sent.text.strip(),
            start_char=sent.start_char + offset,
            end_char=sent.end_char + offset
        ))
    return sentences


def _find_chunk_boundary(text: str, target_size: int) -> int:
    """
    Find a good boundary point (paragraph break) near target_size.
    Returns the character index to split at.
    """
    # Look for paragraph break (double newline) near target size
    # Search in a window around target_size
    search_start = max(0, target_size - 10000)
    search_end = min(len(text), target_size + 10000)
    search_region = text[search_start:search_end]

    # Find last paragraph break before target
    last_break = search_region.rfind('\n\n', 0, target_size - search_start)
    if last_break != -1:
        return search_start + last_break + 2  # After the newlines

    # Fall back to single newline
    last_newline = search_region.rfind('\n', 0, target_size - search_start)
    if last_newline != -1:
        return search_start + last_newline + 1

    # Last resort: just split at target
    return target_size


def segment_sentences(text: str) -> List[SentenceSpan]:
    """
    Segments text into sentences using spaCy.
    For texts exceeding spaCy's limit, processes in chunks.
    """
    if not text:
        return []

    # If text is small enough, process directly
    if len(text) <= SPACY_MAX_LENGTH:
        return _segment_sentences_single(text)

    # Process in chunks for large texts
    logger.info(f"Text length {len(text):,} exceeds spaCy limit, processing in chunks")
    sentences = []
    current_pos = 0

    while current_pos < len(text):
        remaining = len(text) - current_pos

        if remaining <= SPACY_MAX_LENGTH:
            # Last chunk
            chunk = text[current_pos:]
            chunk_sentences = _segment_sentences_single(chunk, offset=current_pos)
            sentences.extend(chunk_sentences)
            break

        # Find a good boundary
        boundary = _find_chunk_boundary(text, current_pos + SPACY_MAX_LENGTH)
        chunk = text[current_pos:boundary]

        chunk_sentences = _segment_sentences_single(chunk, offset=current_pos)
        sentences.extend(chunk_sentences)

        current_pos = boundary

    logger.info(f"Processed {len(text):,} chars in chunks, found {len(sentences)} sentences")
    return sentences

def segment_sentences_with_lines(text: str) -> List[SentenceWithLines]:
    """
    Segments text into sentences and includes line number mapping.
    """
    if not text:
        return []
        
    sentences = segment_sentences(text)
    
    results = []
    for sent in sentences:
        start_line = map_char_offset_to_line(text, sent.start_char)
        # Use end_char - 1 to get the line where the content ends, 
        # avoiding skipping to the next line if the sentence ends with a newline
        end_line = map_char_offset_to_line(text, max(sent.start_char, sent.end_char - 1))
        results.append(SentenceWithLines(
            text=sent.text,
            start_char=sent.start_char,
            end_char=sent.end_char,
            start_line=start_line,
            end_line=end_line
        ))
    return results

def detect_paragraph_boundaries(text: str) -> List[ParagraphSpan]:
    """
    Identifies paragraph boundaries based on double newlines.
    """
    if not text:
        return []
        
    import re
    paragraphs = []
    # Find all sequences of 2 or more newlines
    breaks = list(re.finditer(r'\n\n+', text))
    
    current_pos = 0
    for b in breaks:
        end = b.start()
        para_content = text[current_pos:end]
        stripped_content = para_content.strip()
        
        if stripped_content:
            # Find exact start of non-whitespace content within the chunk
            rel_start = para_content.find(stripped_content)
            p_start = current_pos + rel_start
            p_end = p_start + len(stripped_content)
            
            paragraphs.append(ParagraphSpan(
                text=stripped_content,
                start_char=p_start,
                end_char=p_end,
                start_line=map_char_offset_to_line(text, p_start),
                end_line=map_char_offset_to_line(text, p_end)
            ))
        current_pos = b.end()
    
    # Handle the last paragraph
    last_content = text[current_pos:]
    stripped_last = last_content.strip()
    if stripped_last:
        rel_start = last_content.find(stripped_last)
        p_start = current_pos + rel_start
        p_end = p_start + len(stripped_last)
        
        paragraphs.append(ParagraphSpan(
            text=stripped_last,
            start_char=p_start,
            end_char=p_end,
            start_line=map_char_offset_to_line(text, p_start),
            end_line=map_char_offset_to_line(text, p_end)
        ))
        
    return paragraphs
