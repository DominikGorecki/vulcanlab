import re
from dataclasses import dataclass
from typing import Set, Optional
from sqlalchemy.orm import Session
from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab.summarize.nlp_utils import load_spacy_model, process_text_in_chunks

@dataclass
class SalienceWeights:
    h1_always_summarize: bool
    h2_top_percent: int
    h3_salience_threshold: float
    h4_salience_threshold: float
    definition_density_weight: float
    list_density_weight: float
    keyphrase_novelty_weight: float
    location_prior_weight: float
    heading_depth_weight: float

def load_salience_weights(session: Session) -> SalienceWeights:
    """
    Fetches the latest salience weights from the database.
    If no settings exist, returns a default set of weights.
    """
    settings = session.query(SummarizeSettings).order_by(SummarizeSettings.id.desc()).first()
    
    if not settings:
        # Fallback to defaults defined in the model if none found in DB
        settings = SummarizeSettings()
        
    return SalienceWeights(
        h1_always_summarize=settings.h1_always_summarize,
        h2_top_percent=settings.h2_top_percent,
        h3_salience_threshold=settings.h3_salience_threshold,
        h4_salience_threshold=settings.h4_salience_threshold,
        definition_density_weight=settings.definition_density_weight,
        list_density_weight=settings.list_density_weight,
        keyphrase_novelty_weight=settings.keyphrase_novelty_weight,
        location_prior_weight=settings.location_prior_weight,
        heading_depth_weight=settings.heading_depth_weight
    )

def score_heading_depth(level: str) -> float:
    """
    Scores heading depth: H1 -> 1.0, H2 -> 0.8, H3 -> 0.6, H4 -> 0.4, H5 -> 0.2
    """
    depth_map = {
        "H1": 1.0,
        "H2": 0.8,
        "H3": 0.6,
        "H4": 0.4,
        "H5": 0.2
    }
    # Case-insensitive lookup, default to lowest score if not found
    return depth_map.get(level.upper(), 0.1)

def score_definition_density(content: str) -> float:
    """
    Detects definition density using regex patterns.
    Normalized by content length (words).
    """
    if not content or not content.strip():
        return 0.0
    
    # Patterns from spec: "X is...", "defined as...", "refers to...", "we call..."
    patterns = [
        r"\w+\s+(?:is|are|refers\s+to|means|defined\s+as)",
        r"we\s+call\s+\w+",
        r"definition\s+of\s+\w+"
    ]
    
    total_matches = 0
    for pattern in patterns:
        total_matches += len(re.findall(pattern, content, re.IGNORECASE))
    
    word_count = len(content.split())
    if word_count == 0:
        return 0.0
        
    # Density: number of definitions per 100 words, capped at 1.0
    # A density of 2 definitions per 100 words is considered high (1.0)
    density = (total_matches / word_count) * 50 
    return min(1.0, density)

def score_list_density(content: str) -> float:
    """
    Calculates list density (bullets, numbered items).
    Normalized by content length (lines).
    """
    if not content or not content.strip():
        return 0.0
        
    # Patterns from spec:
    # r"^[\s]*[-*+]\s"
    # r"^[\s]*\d+[.)]\s"
    # r"^[\s]*\([a-z0-9]+\)\s"
    bullet_pattern = r"^[\s]*[-*+]\s"
    number_pattern = r"^[\s]*\d+[.)]\s"
    paren_pattern = r"^[\s]*\([a-z0-9]+\)\s"
    
    lines = content.splitlines()
    if not lines:
        return 0.0
        
    list_items = 0
    for line in lines:
        if re.search(bullet_pattern, line) or \
           re.search(number_pattern, line) or \
           re.search(paren_pattern, line):
            list_items += 1
            
    # Density: ratio of list lines to total lines
    return list_items / len(lines)

def _extract_keyphrases_from_chunk(text: str, nlp) -> list:
    """Helper to extract keyphrases from a single chunk of text."""
    doc = nlp(text)
    keyphrases = []

    # Extract noun phrases
    for chunk in doc.noun_chunks:
        phrase = chunk.text.lower().strip()
        if len(phrase.split()) > 0:
            keyphrases.append(phrase)

    # Extract capitalized terms (not starting sentences)
    for token in doc:
        if token.is_upper or (token.is_title and not token.is_sent_start):
            keyphrases.append(token.text.lower().strip())

    return keyphrases


def score_keyphrase_novelty(content: str, seen_keyphrases: Set[str]) -> float:
    """
    Scores based on ratio of new vs. previously seen keyphrases.
    Extracts noun phrases and capitalized terms.
    Handles large texts by processing in chunks.
    """
    if not content or not content.strip():
        return 0.0

    # Use chunked processing for large texts
    all_keyphrases = process_text_in_chunks(content, _extract_keyphrases_from_chunk)
    current_keyphrases = set(all_keyphrases)

    if not current_keyphrases:
        return 0.0

    novel_count = 0
    for kp in current_keyphrases:
        if kp not in seen_keyphrases:
            novel_count += 1
            seen_keyphrases.add(kp)

    return novel_count / len(current_keyphrases)

def score_location_prior(chunk_index: int, total_chunks: int) -> float:
    """
    Boosts first 10% and last 10% of document.
    """
    if total_chunks <= 1:
        return 1.0
        
    position = chunk_index / (total_chunks - 1)
    
    if position <= 0.1 or position >= 0.9:
        return 1.0
    
    return 0.0

def compute_salience_score(
    chunk_content: str,
    heading_level: str,
    weights: SalienceWeights,
    seen_keyphrases: Set[str],
    chunk_index: int,
    total_chunks: int
) -> float:
    """
    Composite score calculation with configurable weights.
    """
    s_depth = score_heading_depth(heading_level)
    s_def = score_definition_density(chunk_content)
    s_list = score_list_density(chunk_content)
    s_novelty = score_keyphrase_novelty(chunk_content, seen_keyphrases)
    s_loc = score_location_prior(chunk_index, total_chunks)
    
    score = (
        s_depth * weights.heading_depth_weight +
        s_def * weights.definition_density_weight +
        s_list * weights.list_density_weight +
        s_novelty * weights.keyphrase_novelty_weight +
        s_loc * weights.location_prior_weight
    )
    
    # Normalize total score to 0-1 range if weights sum to 1.0
    # The weights from settings are expected to be normalized but we'll return raw weighted sum
    return min(1.0, max(0.0, score))

def passes_threshold(score: float, level: str, weights: SalienceWeights) -> bool:
    """
    Filters chunks based on salience thresholds from settings.
    """
    level = level.upper()
    
    if level == "H1":
        return weights.h1_always_summarize
        
    if level == "H2":
        # H2 top percent logic is handled in node selection (T06)
        # Here we just check if it's generally allowed
        return True
        
    if level == "H3":
        return score >= weights.h3_salience_threshold
        
    # H4, H5, etc.
    return score >= weights.h4_salience_threshold
