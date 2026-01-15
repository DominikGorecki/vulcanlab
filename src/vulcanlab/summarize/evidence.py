from dataclasses import dataclass, field
import re
from typing import List, Dict, Any, Optional
from vulcanlab.summarize.nlp_utils import (
    SentenceWithLines,
    detect_paragraph_boundaries,
    load_spacy_model,
    map_char_offset_to_line,
    process_text_in_chunks,
    SPACY_MAX_LENGTH
)

@dataclass(frozen=True)
class Snippet:
    """
    A specific extracted piece of information from the source text.
    """
    text: str
    start_line: int
    end_line: int
    snippet_type: str  # e.g., "topic", "definition", "enumeration", "emphasis"

@dataclass
class EvidencePacket:
    """
    A collection of evidence extracted from a specific document section.
    """
    heading_path: str
    line_start: int
    line_end: int
    snippets: List[Snippet] = field(default_factory=list)
    keyphrases: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

def extract_topic_sentences(text: str, sentences_with_lines: List[SentenceWithLines]) -> List[Snippet]:
    """
    Identifies the first sentence of each paragraph.
    Uses paragraph boundaries to avoid cross-paragraph sentence merging.
    """
    if not text:
        return []
    
    paragraphs = detect_paragraph_boundaries(text)
    snippets = []
    
    from vulcanlab.summarize.nlp_utils import segment_sentences
    
    for para in paragraphs:
        # Segment sentences for this paragraph specifically to ensure
        # the first sentence is truly the first sentence of this paragraph.
        para_sentences = segment_sentences(para.text)
        if para_sentences:
            first_sent_text = para_sentences[0].text
            
            # Map back to original line numbers
            # We can use map_char_offset_to_line with the absolute offset
            start_line = map_char_offset_to_line(text, para.start_char + para_sentences[0].start_char)
            # end_line estimate
            end_line = map_char_offset_to_line(text, para.start_char + para_sentences[0].end_char - 1)
            
            snippets.append(Snippet(
                text=first_sent_text,
                start_line=start_line,
                end_line=end_line,
                snippet_type="topic"
            ))
            
    return snippets

def extract_definitions(text: str, sentences_with_lines: List[SentenceWithLines]) -> List[Snippet]:
    """
    Detects sentences that look like definitions using regex patterns.
    """
    # Patterns: "X is...", "X refers to...", "defined as...", "we call...", "known as..."
    patterns = [
        r"\b\w+\b\s+is\s+[^.!?]+",
        r"\b\w+\b\s+refers\s+to\s+[^.!?]+",
        r"\bdefined\s+as\b",
        r"\bwe\s+call\b",
        r"\bknown\s+as\b"
    ]
    combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)
    
    snippets = []
    for sent in sentences_with_lines:
        if combined_pattern.search(sent.text):
            snippets.append(Snippet(
                text=sent.text,
                start_line=sent.start_line,
                end_line=sent.end_line,
                snippet_type="definition"
            ))
            
    return snippets

def extract_enumerations(text: str) -> List[Snippet]:
    """
    Detects bullet lists and numbered lists.
    Preserves complete list blocks, including multi-line items.
    """
    lines = text.splitlines(keepends=True)
    # Pattern for start of a list item
    item_pattern = re.compile(r'^\s*([-*+]|\d+[.)])\s+')
    # Pattern for an empty line (often ends a list if not followed by another item)
    empty_pattern = re.compile(r'^\s*$')
    
    snippets = []
    in_list = False
    list_start_line = -1
    current_list_lines = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        is_item = bool(item_pattern.match(line))
        is_empty = bool(empty_pattern.match(line))
        
        if is_item:
            if not in_list:
                in_list = True
                list_start_line = line_num
            current_list_lines.append(line)
        elif in_list:
            # We are in a list, check if this line continues it
            # It continues if it's indented OR if it's not an empty line 
            # (simple heuristic: lists blocks are usually dense)
            if not is_empty:
                current_list_lines.append(line)
            else:
                # Empty line: check ahead if there's another list item soon
                # For now, let's just end the list on an empty line to be safe
                # unless we want to support lists with empty lines between items.
                # Actually, many markdown lists HAVE empty lines between items.
                # Let's peek ahead.
                found_next_item = False
                for j in range(i + 1, min(i + 3, len(lines))):
                    if item_pattern.match(lines[j]):
                        found_next_item = True
                        break
                
                if found_next_item:
                    current_list_lines.append(line)
                else:
                    # End of list block
                    snippets.append(Snippet(
                        text="".join(current_list_lines).strip(),
                        start_line=list_start_line,
                        end_line=line_num - 1,
                        snippet_type="enumeration"
                    ))
                    in_list = False
                    current_list_lines = []
        
    # Handle list at the end of text
    if in_list:
        snippets.append(Snippet(
            text="".join(current_list_lines).strip(),
            start_line=list_start_line,
            end_line=len(lines),
            snippet_type="enumeration"
        ))
        
    return snippets

def extract_emphasis_cues(text: str, sentences_with_lines: List[SentenceWithLines]) -> List[Snippet]:
    """
    Returns sentences containing emphasis markers.
    """
    keywords = ["key", "important", "in summary", "note that", "crucially", "essential"]
    pattern = re.compile(r"\b(" + "|".join(keywords) + r")\b", re.IGNORECASE)
    
    snippets = []
    for sent in sentences_with_lines:
        if pattern.search(sent.text):
            snippets.append(Snippet(
                text=sent.text,
                start_line=sent.start_line,
                end_line=sent.end_line,
                snippet_type="emphasis"
            ))
            
    return snippets

def _extract_noun_chunks(text: str, nlp) -> List[str]:
    """Helper to extract noun chunks from a single chunk of text."""
    doc = nlp(text)
    phrases = []
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        phrase = re.sub(r'^[-*+]\s+', '', phrase)
        words = phrase.split()
        if len(words) >= 2 or (len(words) == 1 and words[0][0].isupper()):
            if len(phrase) > 2:
                phrases.append(phrase)
    return phrases


def extract_keyphrases(text: str, top_n: int = 20) -> List[str]:
    """
    Uses spaCy noun chunks to extract key phrases.
    Handles large texts by processing in chunks.
    """
    if not text:
        return []

    # Use chunked processing for large texts
    phrases = process_text_in_chunks(text, _extract_noun_chunks)

    # Count frequencies and return top-N
    from collections import Counter
    counts = Counter(phrases)
    # Filter out common pronouns if they slipped through
    stop_phrases = {"It", "This", "They", "We", "I", "You"}
    filtered_results = [p for p, count in counts.most_common(top_n * 2) if p not in stop_phrases]

    return filtered_results[:top_n]

def build_evidence_packet(
    content: str, 
    sentences_with_lines: List[SentenceWithLines],
    heading_path: str, 
    start_line: int, 
    end_line: int, 
    max_snippets: int = 40
) -> EvidencePacket:
    """
    Builds a complete EvidencePacket by combining all extraction methods.
    """
    # 1. Extract everything
    topic_snippets = extract_topic_sentences(content, sentences_with_lines)
    definition_snippets = extract_definitions(content, sentences_with_lines)
    enum_snippets = extract_enumerations(content)
    emphasis_snippets = extract_emphasis_cues(content, sentences_with_lines)
    
    # 2. Keyphrases
    keyphrases = extract_keyphrases(content)
    
    # 3. Combine and Prioritize
    # Order: definitions > enumerations > topic sentences > emphasis
    all_snippets = []
    all_snippets.extend(definition_snippets)
    all_snippets.extend(enum_snippets)
    all_snippets.extend(topic_snippets)
    all_snippets.extend(emphasis_snippets)
    
    # 4. Deduplicate overlapping snippets
    # If two snippets have the same line range, or one is contained in another, prefer the higher priority one.
    unique_snippets = []
    seen_ranges = set()
    
    # We process in priority order, so first one to claim a range wins (if exact match)
    # For overlaps, it's more complex. For now let's deduplicate exact text or line ranges.
    for s in all_snippets:
        range_key = (s.start_line, s.end_line)
        if range_key not in seen_ranges:
            unique_snippets.append(s)
            seen_ranges.add(range_key)
            
    # 5. Trim to max_snippets
    final_snippets = unique_snippets[:max_snippets]
    
    # 6. Stats
    stats = {
        "total_extracted": len(all_snippets),
        "deduplicated": len(unique_snippets),
        "final_count": len(final_snippets),
        "by_type": {
            "definition": len([s for s in final_snippets if s.snippet_type == "definition"]),
            "enumeration": len([s for s in final_snippets if s.snippet_type == "enumeration"]),
            "topic": len([s for s in final_snippets if s.snippet_type == "topic"]),
            "emphasis": len([s for s in final_snippets if s.snippet_type == "emphasis"]),
        }
    }
    
    return EvidencePacket(
        heading_path=heading_path,
        line_start=start_line,
        line_end=end_line,
        snippets=final_snippets,
        keyphrases=keyphrases,
        stats=stats
    )
