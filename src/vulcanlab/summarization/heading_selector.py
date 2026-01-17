from dataclasses import dataclass
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.summarize_settings import SummarizeSettings

@dataclass
class HeadingInfo:
    """Dataclass for heading selection results."""
    chunk_id: int
    level: str
    start_line: int
    end_line: int
    content_word_count: int
    heading_title: str

def get_heading_chunks(work_id: int, session: Session) -> List[HeadingInfo]:
    """
    Query chunks where level does NOT contain "-chunk" and order by start_line.
    Extracts first line of content as heading_title and counts words.
    """
    stmt = (
        select(Chunk)
        .where(Chunk.work_id == work_id)
        .where(~Chunk.level.contains("-chunk"))
        .order_by(Chunk.start_line)
    )
    chunks = session.execute(stmt).scalars().all()
    
    headings = []
    for chunk in chunks:
        # Extract first line of content as heading_title
        # Pattern: content.split('\n')[0].lstrip('#').strip()
        lines = chunk.content.split('\n')
        first_line = lines[0] if lines else ""
        heading_title = first_line.lstrip('#').strip()
        
        # Count words in content field using simple split()
        word_count = len(chunk.content.split())
        
        headings.append(HeadingInfo(
            chunk_id=chunk.id,
            level=chunk.level,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            content_word_count=word_count,
            heading_title=heading_title
        ))
    return headings

def filter_by_word_count(headings: List[HeadingInfo], min_words: int) -> List[HeadingInfo]:
    """
    Remove headings where content_word_count < min_words.
    """
    return [h for h in headings if h.content_word_count >= min_words]

def enforce_heading_budget(headings: List[HeadingInfo], max_total_words: int) -> List[HeadingInfo]:
    """
    Calculate total words from all heading_titles.
    If over budget, iteratively remove lowest-level headings with shortest content.
    Continue until under budget.
    """
    def get_total_title_words(h_list: List[HeadingInfo]) -> int:
        return sum(len(h.heading_title.split()) for h in h_list)

    def level_rank(h: HeadingInfo) -> int:
        """Helper to extract level number, higher is lower priority (e.g., H5=5, H1=1)."""
        try:
            # Handle cases like 'H1', 'H2', etc.
            if h.level.startswith('H') and h.level[1:].isdigit():
                return int(h.level[1:])
        except (ValueError, IndexError):
            pass
        return 99  # Put unknown levels at lowest priority

    current_headings = list(headings)
    
    # Iteratively remove until under budget or no headings left
    while current_headings and get_total_title_words(current_headings) > max_total_words:
        # Find heading to remove: highest level rank (lowest level) 
        # and then shortest content word count.
        to_remove = max(
            current_headings,
            key=lambda h: (level_rank(h), -h.content_word_count)
        )
        current_headings.remove(to_remove)
        
    return current_headings

def select_headings_for_summarization(
    work_id: int, 
    session: Session, 
    settings: SummarizeSettings
) -> List[HeadingInfo]:
    """
    Main entry point to select, filter, and budget headings for summarization.
    """
    headings = get_heading_chunks(work_id, session)
    headings = filter_by_word_count(headings, settings.min_heading_word_count)
    headings = enforce_heading_budget(headings, settings.max_total_heading_words)
    return headings
