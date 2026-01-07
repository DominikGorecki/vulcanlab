"""
Chunking module for simple conversion pipeline.

Creates both heading and content chunks for simple conversion documents.
Follows the two-step architecture:
1. create_heading_chunks_simple() - Creates H1-H5 heading chunks with hierarchy
2. create_content_chunks_simple() - Creates paragraph/table/figure chunks under headings
"""

import logging
import re
import warnings
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, UTC

import spacy

from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.database import get_session

logger = logging.getLogger(__name__)


# Load spaCy model for sentence tokenization
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise ImportError(
        "spaCy model 'en_core_web_sm' not found. "
        "Install with: python -m spacy download en_core_web_sm"
    )

# Chunking constants (from content_chunking.py)
TARGET_WORDS = 200
MAX_WORDS = 300
MIN_CHUNK_WORDS = 50
MIN_OVERLAP_SENTENCES = 2
MAX_OVERLAP_SENTENCES = 3


# ============================================================================
# Helper Functions (from content_chunking.py)
# ============================================================================

def _count_words(text: str) -> int:
    """Count words in text, handling markdown syntax properly."""
    # Remove markdown link syntax, keeping only the link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove formatting markers
    text = re.sub(r'[*_~`]+', '', text)
    # Find all word sequences (alphanumeric + underscore)
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def _is_valid_sentence(sent) -> bool:
    """Check if a spaCy sentence meets validity criteria.

    A valid sentence must have:
    - At least 7 tokens (excluding punctuation)
    AND at least ONE of:
    1. Has verb (VERB/AUX) AND has noun (NOUN/PROPN)
    2. Root token is a verb (VERB/AUX)
    3. Has noun (NOUN/PROPN) AND has subject dependency (any dep containing 'subj')

    Args:
        sent: spaCy Span object representing a sentence.

    Returns:
        True if sentence meets validity criteria, False otherwise.
    """
    # Count tokens excluding punctuation
    tokens = [token for token in sent if not token.is_punct and not token.is_space]

    if len(tokens) < 7:
        return False

    # Check for linguistic features
    has_verb = any(token.pos_ in ['VERB', 'AUX'] for token in tokens)
    has_noun = any(token.pos_ in ['NOUN', 'PROPN'] for token in tokens)
    has_subject = any('subj' in token.dep_ for token in tokens)

    # Find root token
    root_is_verb = False
    for token in tokens:
        if token.dep_ == 'ROOT' and token.pos_ in ['VERB', 'AUX']:
            root_is_verb = True
            break

    # Check validity conditions
    condition_1 = has_verb and has_noun
    condition_2 = root_is_verb
    condition_3 = has_noun and has_subject

    return condition_1 or condition_2 or condition_3


def _get_sentences(text: str) -> List[str]:
    """Split text into valid sentences using spaCy.

    Returns only sentences that meet linguistic validity criteria:
    - At least 7 tokens (excluding punctuation)
    - Contains appropriate grammatical structure (verb+noun, root verb, or noun+subject)

    This matches the logic used in content_chunking.py to ensure
    consistent sentence counting across both pipelines.

    Args:
        text: Text to split into sentences.

    Returns:
        List of valid sentence strings.
    """
    if not text:
        return []
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents
            if sent.text.strip() and _is_valid_sentence(sent)]


def _convert_bullets_to_sentences(text: str) -> str:
    """Convert bullet lists to flowing sentences."""
    lines = text.split('\n')
    result_lines = []
    bullet_buffer = []

    def flush_bullets():
        if bullet_buffer:
            sentences = []
            for bullet in bullet_buffer:
                cleaned = re.sub(r'^[\s]*[-*+]\s*', '', bullet).strip()
                if cleaned:
                    if not cleaned[-1] in '.!?':
                        cleaned += '.'
                    sentences.append(cleaned)
            if sentences:
                result_lines.append(' '.join(sentences))
            bullet_buffer.clear()

    for line in lines:
        if re.match(r'^[\s]*[-*+]\s+', line):
            bullet_buffer.append(line)
        else:
            flush_bullets()
            result_lines.append(line)

    flush_bullets()
    return '\n'.join(result_lines)


def _parse_markdown_structure(content: str) -> Dict[str, List]:
    """Parse markdown into structured elements."""
    lines = content.splitlines()

    headings = []
    paragraphs = []
    tables = []
    figures = []

    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1  # 1-indexed

        # Check for heading
        heading_match = re.match(r'^(#+)\s+(.*)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            if level <= 5:
                headings.append((line_num, level, line))
            i += 1
            continue

        # Check for figure (image)
        if re.match(r'^!\[.*\]\(.*\)', line):
            figures.append((line_num, line))
            i += 1
            continue

        # Check for table (starts with |)
        if line.strip().startswith('|'):
            table_start = line_num
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_end = table_start + len(table_lines) - 1
            tables.append((table_start, table_end, '\n'.join(table_lines)))
            continue

        # Check for paragraph (non-empty, non-special line)
        if line.strip():
            para_start = line_num
            para_lines = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip():
                    break
                if re.match(r'^#+\s+', next_line):
                    break
                if re.match(r'^!\[.*\]\(.*\)', next_line):
                    break
                if next_line.strip().startswith('|'):
                    break
                para_lines.append(next_line)
                i += 1

            para_end = para_start + len(para_lines) - 1
            para_text = '\n'.join(para_lines)
            para_text = _convert_bullets_to_sentences(para_text)
            paragraphs.append((para_start, para_end, para_text))
            continue

        i += 1

    return {
        'headings': headings,
        'paragraphs': paragraphs,
        'tables': tables,
        'figures': figures
    }


def _build_heading_hierarchy(headings: List[Tuple[int, int, str]]) -> Dict[int, List[str]]:
    """Build heading hierarchy for each line number."""
    hierarchy = {}
    current_stack = {}  # level -> heading text

    for line_num, level, text in headings:
        # Extract just the heading text (remove # marks)
        heading_text = re.sub(r'^#+\s+', '', text).strip()

        # Clear deeper levels
        for lvl in list(current_stack.keys()):
            if lvl >= level:
                del current_stack[lvl]

        # Set current level
        current_stack[level] = heading_text

        # Build breadcrumb
        breadcrumb = []
        for lvl in sorted(current_stack.keys()):
            breadcrumb.append(current_stack[lvl])

        hierarchy[line_num] = breadcrumb

    return hierarchy


def _find_heading_for_line(
    line_num: int,
    headings: List[Tuple[int, int, str]],
    heading_hierarchy: Dict[int, List[str]]
) -> Tuple[Optional[int], List[str], int]:
    """Find the heading that contains a given line."""
    best_heading = None
    best_breadcrumb = []
    best_level = 0

    for h_line, h_level, _ in headings:
        if h_line < line_num:
            best_heading = h_line
            best_breadcrumb = heading_hierarchy.get(h_line, [])
            best_level = h_level
        else:
            break

    return best_heading, best_breadcrumb, best_level


def _format_breadcrumb(breadcrumb: List[str]) -> str:
    """Format heading breadcrumb for chunk content."""
    if not breadcrumb:
        return ""
    return ' > '.join(breadcrumb)


def _create_paragraph_chunks(
    paragraphs: List[Tuple[int, int, str]],
    headings: List[Tuple[int, int, str]],
    heading_hierarchy: Dict[int, List[str]],
    min_words: int = MIN_CHUNK_WORDS
) -> List[Dict[str, Any]]:
    """Create chunks from paragraphs, combining short paragraphs under same heading."""
    chunks = []

    # Group paragraphs by their heading
    heading_groups = {}
    for para_start, para_end, para_text in paragraphs:
        h_line, breadcrumb, level = _find_heading_for_line(para_start, headings, heading_hierarchy)

        if h_line not in heading_groups:
            heading_groups[h_line] = {
                'breadcrumb': breadcrumb,
                'level': level,
                'paragraphs': []
            }
        heading_groups[h_line]['paragraphs'].append((para_start, para_end, para_text))

    # Process each heading group
    for h_line, group in heading_groups.items():
        breadcrumb = group['breadcrumb']
        level = group['level']
        paras = group['paragraphs']

        breadcrumb_text = _format_breadcrumb(breadcrumb)
        available_words = MAX_WORDS

        # Accumulator for combining paragraphs
        current_sentences = []
        current_start_line = None
        current_end_line = None
        overlap_sentences = []

        def flush_chunk(force: bool = False):
            """Create a chunk from accumulated sentences."""
            nonlocal current_sentences, current_start_line, current_end_line, overlap_sentences

            if not current_sentences or current_start_line is None:
                current_sentences = []
                current_start_line = None
                current_end_line = None
                return

            chunk_text = ' '.join(current_sentences)
            chunk_word_count = _count_words(chunk_text)

            if not force and chunk_word_count < min_words:
                return

            chunks.append({
                'content': chunk_text,
                'heading_breadcrumbs': breadcrumb_text if breadcrumb_text else None,
                'start_line': current_start_line,
                'end_line': current_end_line,
                'heading_line': h_line,
                'level': level,
                'vector_status': 'to_vec'
            })

            overlap_sentences = current_sentences[-MAX_OVERLAP_SENTENCES:] if len(current_sentences) >= MIN_OVERLAP_SENTENCES else current_sentences[:]

            current_sentences = []
            current_start_line = None
            current_end_line = None

        for para_idx, (para_start, para_end, para_text) in enumerate(paras):
            sentences = _get_sentences(para_text)
            if not sentences:
                continue

            para_words = _count_words(para_text)

            if not current_sentences and overlap_sentences:
                current_sentences.extend(overlap_sentences)

            test_sentences = current_sentences + sentences
            test_words = _count_words(' '.join(test_sentences))

            if test_words <= available_words:
                current_sentences.extend(sentences)
                if current_start_line is None:
                    current_start_line = para_start
                current_end_line = para_end

                current_words = _count_words(' '.join(current_sentences))
                if current_words >= TARGET_WORDS and para_idx < len(paras) - 1:
                    flush_chunk()

            elif para_words <= available_words:
                flush_chunk()

                if overlap_sentences:
                    current_sentences.extend(overlap_sentences)
                current_sentences.extend(sentences)
                current_start_line = para_start
                current_end_line = para_end

            else:
                flush_chunk()

                if overlap_sentences:
                    current_sentences.extend(overlap_sentences)
                    current_start_line = para_start

                for sent in sentences:
                    test_sents = current_sentences + [sent]
                    test_words = _count_words(' '.join(test_sents))

                    if test_words <= available_words:
                        current_sentences.append(sent)
                        if current_start_line is None:
                            current_start_line = para_start
                        current_end_line = para_end
                    else:
                        if current_sentences:
                            if current_start_line is None:
                                current_start_line = para_start
                            current_end_line = para_end
                            flush_chunk()

                        if overlap_sentences:
                            current_sentences.extend(overlap_sentences)
                        current_sentences.append(sent)
                        current_start_line = para_start
                        current_end_line = para_end

        flush_chunk(force=True)

    return chunks


def _create_table_chunks(
    tables: List[Tuple[int, int, str]],
    headings: List[Tuple[int, int, str]],
    heading_hierarchy: Dict[int, List[str]]
) -> List[Dict[str, Any]]:
    """Create chunks for tables."""
    chunks = []

    for table_start, table_end, table_text in tables:
        h_line, breadcrumb, level = _find_heading_for_line(table_start, headings, heading_hierarchy)
        breadcrumb_text = _format_breadcrumb(breadcrumb)

        chunks.append({
            'content': table_text,
            'heading_breadcrumbs': breadcrumb_text if breadcrumb_text else None,
            'start_line': table_start,
            'end_line': table_end,
            'heading_line': h_line,
            'level': level,
            'vector_status': 'tbl'
        })

    return chunks


def _create_figure_chunks(
    figures: List[Tuple[int, str]],
    headings: List[Tuple[int, int, str]],
    heading_hierarchy: Dict[int, List[str]]
) -> List[Dict[str, Any]]:
    """Create chunks for figures."""
    chunks = []

    for fig_line, fig_text in figures:
        h_line, breadcrumb, level = _find_heading_for_line(fig_line, headings, heading_hierarchy)
        breadcrumb_text = _format_breadcrumb(breadcrumb)

        chunks.append({
            'content': fig_text,
            'heading_breadcrumbs': breadcrumb_text if breadcrumb_text else None,
            'start_line': fig_line,
            'end_line': fig_line,
            'heading_line': h_line,
            'level': level,
            'vector_status': 'fig'
        })

    return chunks


def _merge_small_chunks(chunks: List[Dict], min_words: int = MIN_CHUNK_WORDS) -> Tuple[List[Dict], int]:
    """Merge chunks that are below the minimum word count with adjacent chunks."""
    if not chunks:
        return [], 0

    validated_chunks = []
    pending_merge = None
    merge_count = 0

    for chunk in chunks:
        # Skip non-text chunks from word count validation
        if chunk.get('vector_status') in ['tbl', 'fig']:
            if pending_merge:
                validated_chunks.append(pending_merge)
                pending_merge = None
            validated_chunks.append(chunk)
            continue

        content = chunk['content']
        word_count = _count_words(content)

        if word_count < min_words:
            if pending_merge:
                pending_merge['content'] += '\n\n' + chunk['content']
                pending_merge['end_line'] = chunk['end_line']
                if not pending_merge.get('heading_breadcrumbs') and chunk.get('heading_breadcrumbs'):
                    pending_merge['heading_breadcrumbs'] = chunk['heading_breadcrumbs']
                merged_word_count = _count_words(pending_merge['content'])
                if merged_word_count >= min_words:
                    validated_chunks.append(pending_merge)
                    pending_merge = None
                    merge_count += 1
            elif validated_chunks and validated_chunks[-1].get('heading_line') == chunk.get('heading_line'):
                prev_chunk = validated_chunks[-1]
                if prev_chunk.get('vector_status') == 'to_vec':
                    prev_chunk['content'] += '\n\n' + chunk['content']
                    prev_chunk['end_line'] = chunk['end_line']
                    if not prev_chunk.get('heading_breadcrumbs') and chunk.get('heading_breadcrumbs'):
                        prev_chunk['heading_breadcrumbs'] = chunk['heading_breadcrumbs']
                    merge_count += 1
                else:
                    pending_merge = chunk
            else:
                pending_merge = chunk
        else:
            if pending_merge:
                chunk['content'] = pending_merge['content'] + '\n\n' + chunk['content']
                chunk['start_line'] = pending_merge['start_line']
                if not chunk.get('heading_breadcrumbs') and pending_merge.get('heading_breadcrumbs'):
                    chunk['heading_breadcrumbs'] = pending_merge['heading_breadcrumbs']
                merge_count += 1
                pending_merge = None

            validated_chunks.append(chunk)

    if pending_merge:
        if validated_chunks and validated_chunks[-1].get('vector_status') == 'to_vec':
            validated_chunks[-1]['content'] += '\n\n' + pending_merge['content']
            validated_chunks[-1]['end_line'] = pending_merge['end_line']
            if not validated_chunks[-1].get('heading_breadcrumbs') and pending_merge.get('heading_breadcrumbs'):
                validated_chunks[-1]['heading_breadcrumbs'] = pending_merge['heading_breadcrumbs']
            merge_count += 1
        else:
            validated_chunks.append(pending_merge)

    return validated_chunks, merge_count


# ============================================================================
# Original Helper Functions
# ============================================================================

def parse_headings_from_markdown(content: str) -> List[Tuple[int, int, str]]:
    """
    Parse all headings from markdown content.

    Args:
        content: Markdown content

    Returns:
        List of tuples (line_num, level, heading_text)
    """
    headings = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        match = re.match(r'^(#+)\s+(.*)$', line)
        if match:
            level = len(match.group(1))
            if level <= 5:  # Only H1-H5 (skip H6)
                heading_text = match.group(2).strip()
                headings.append((i, level, heading_text))

    logger.debug(f"Parsed {len(headings)} headings (H1-H5)")
    return headings


def calculate_heading_ranges(
    headings: List[Tuple[int, int, str]],
    total_lines: int
) -> List[Tuple[int, int, int, int, str]]:
    """
    Calculate start and end lines for each heading section.

    A heading section extends from the heading line to the line before
    the next heading of equal or higher level (lower number).

    Args:
        headings: List of (line_num, level, heading_text)
        total_lines: Total number of lines in the document

    Returns:
        List of tuples (line_num, level, start_line, end_line, heading_text)
    """
    ranges = []

    for i, (line_num, level, heading_text) in enumerate(headings):
        start_line = line_num

        # Find end: next heading with same or higher level
        end_line = total_lines
        for j in range(i + 1, len(headings)):
            next_level = headings[j][1]
            if next_level <= level:
                end_line = headings[j][0] - 1
                break

        ranges.append((line_num, level, start_line, end_line, heading_text))

    logger.debug(f"Calculated ranges for {len(ranges)} heading sections")
    return ranges


def extract_chunk_content(
    markdown_lines: List[str],
    start_line: int,
    end_line: int
) -> str:
    """
    Extract content for a chunk from markdown lines.

    Args:
        markdown_lines: All lines of markdown content
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed, inclusive)

    Returns:
        Chunk content as string
    """
    # Convert to 0-indexed
    start_idx = start_line - 1
    end_idx = end_line  # end_line is inclusive, so no -1

    chunk_lines = markdown_lines[start_idx:end_idx]
    return '\n'.join(chunk_lines)


# ============================================================================
# New Two-Step Chunking Functions
# ============================================================================

def create_heading_chunks_simple(work_id: int, session: Session) -> List[Chunk]:
    """
    Create heading chunks (H1-H5) with parent hierarchy.

    This is Step 1 of the two-step chunking process.
    Heading chunks serve as scaffolding and are NOT marked for vectorization.

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        List of created heading Chunk records

    Raises:
        ValueError: If work not found or not sanitized
    """
    # Get work
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    # Get SanitizedMarkdown
    sanitized = session.query(SanitizedMarkdown).filter(
        SanitizedMarkdown.work_id == work_id
    ).first()

    if not sanitized:
        raise ValueError(f"Work {work_id} has not been sanitized yet")

    logger.info(f"Creating heading chunks for work {work_id}")

    # Get sanitized content
    content = sanitized.content
    lines = content.splitlines()
    total_lines = len(lines)

    # Parse headings
    headings = parse_headings_from_markdown(content)

    if not headings:
        logger.warning(f"No headings found in sanitized markdown for work {work_id}")
        # NOTE: Must reassign the dict to trigger SQLAlchemy change detection for JSON columns
        new_status = dict(work.processing_status) if work.processing_status else {}
        new_status['simple_conversion_step'] = 'heading_chunks_created'
        new_status['heading_chunk_count'] = 0
        work.processing_status = new_status
        session.commit()
        return []

    # Calculate ranges
    ranges = calculate_heading_ranges(headings, total_lines)

    # Build heading hierarchy for full breadcrumbs
    heading_hierarchy = _build_heading_hierarchy(headings)

    # Track chunk IDs by start_line for parent lookup
    chunk_id_map: Dict[int, int] = {}
    chunks = []

    # Sort by line number to process in document order
    ranges.sort(key=lambda x: x[0])

    for line_num, level, start_line, end_line, heading_text in ranges:
        # Calculate parent_id using same logic as chunk_headings.py
        parent_id = None
        if level > 1:
            # Find nearest heading above with lower level number
            for prev_line, prev_level, prev_start, prev_end, _ in reversed(ranges):
                if prev_start < start_line and prev_level < level:
                    # Check if parent chunk was created
                    if prev_start in chunk_id_map:
                        parent_id = chunk_id_map[prev_start]
                    break

        # Extract content
        chunk_content = extract_chunk_content(lines, start_line, end_line)

        # Get full breadcrumb path
        breadcrumb_list = heading_hierarchy.get(line_num, [])
        breadcrumb_text = _format_breadcrumb(breadcrumb_list)

        # Create chunk
        chunk = Chunk(
            parent_id=parent_id,  # Proper hierarchy
            work_id=work_id,
            level=f"H{level}",
            content=chunk_content,
            start_line=start_line,
            end_line=end_line,
            heading_breadcrumbs=breadcrumb_text if breadcrumb_text else heading_text,
            vector_status="no_vec",  # Headings not vectorized
            embedding=None
        )

        session.add(chunk)
        session.flush()  # Get the ID immediately

        # Track this chunk for parent lookups
        chunk_id_map[start_line] = chunk.id
        chunks.append(chunk)

    logger.info(f"Created {len(chunks)} heading chunks for work {work_id}")

    # Update processing status
    # NOTE: Must reassign the dict to trigger SQLAlchemy change detection for JSON columns
    new_status = dict(work.processing_status) if work.processing_status else {}
    new_status['simple_conversion_step'] = 'heading_chunks_created'
    new_status['heading_chunk_count'] = len(chunks)
    work.processing_status = new_status

    session.commit()

    logger.info(f"Heading chunking complete for work {work_id}")

    return chunks


def create_content_chunks_simple(work_id: int, session: Session) -> List[Chunk]:
    """
    Create content chunks (paragraphs, tables, figures) under heading chunks.

    This is Step 2 of the two-step chunking process.
    Requires heading chunks to exist first.
    Content chunks ARE marked for vectorization.

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        List of created content Chunk records

    Raises:
        ValueError: If work not found or not sanitized
    """
    # Get work and sanitized markdown
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    sanitized = session.query(SanitizedMarkdown).filter(
        SanitizedMarkdown.work_id == work_id
    ).first()

    if not sanitized:
        raise ValueError(f"Work {work_id} has not been sanitized yet")

    logger.info(f"Creating content chunks for work {work_id}")

    content = sanitized.content

    # Step 1: Get existing heading chunks for parent lookup
    heading_chunks = session.query(Chunk).filter(
        Chunk.work_id == work_id,
        Chunk.level.in_(['H1', 'H2', 'H3', 'H4', 'H5'])
    ).all()

    if not heading_chunks:
        logger.warning(f"No heading chunks found for work {work_id}. Run create_heading_chunks_simple() first.")
        return []

    # Build map: start_line -> chunk.id
    heading_chunk_map = {chunk.start_line: chunk.id for chunk in heading_chunks}

    # Step 2: Parse markdown structure
    structure = _parse_markdown_structure(content)
    headings = structure['headings']
    heading_hierarchy = _build_heading_hierarchy(headings)

    logger.debug(f"Found {len(structure['paragraphs'])} paragraphs, {len(structure['tables'])} tables, {len(structure['figures'])} figures")

    # Step 3: Create chunks
    all_chunks = []

    # Paragraph chunks
    para_chunks = _create_paragraph_chunks(
        structure['paragraphs'],
        headings,
        heading_hierarchy
    )
    all_chunks.extend(para_chunks)

    # Table chunks
    table_chunks = _create_table_chunks(
        structure['tables'],
        headings,
        heading_hierarchy
    )
    all_chunks.extend(table_chunks)

    # Figure chunks
    figure_chunks = _create_figure_chunks(
        structure['figures'],
        headings,
        heading_hierarchy
    )
    all_chunks.extend(figure_chunks)

    logger.debug(f"Created {len(para_chunks)} paragraph chunks, {len(table_chunks)} table chunks, {len(figure_chunks)} figure chunks")

    # Merge small chunks
    all_chunks, merge_count = _merge_small_chunks(all_chunks)
    if merge_count > 0:
        logger.debug(f"Merged {merge_count} small chunks")

    # Step 4: Create Chunk records
    chunks_created = []
    skipped_no_parent = 0

    for chunk_data in all_chunks:
        # Find parent_id from heading chunk
        parent_id = None
        heading_line = chunk_data.get('heading_line')

        if heading_line:
            parent_id = heading_chunk_map.get(heading_line)

        # Skip chunks without parent (same as content_chunking.py)
        if parent_id is None:
            skipped_no_parent += 1
            logger.debug(f"Skipping chunk at lines {chunk_data['start_line']}-{chunk_data['end_line']}: no parent heading chunk")
            continue

        # Create chunk
        level = chunk_data['level']
        level_str = f"H{level}-chunk" if level else "chunk"

        # Count sentences for 'chunk' level chunks only (e.g., "H1-chunk", "H2-chunk", "chunk")
        sentence_count = None
        if level_str.endswith('-chunk') or level_str == 'chunk':
            try:
                sentences = _get_sentences(chunk_data['content'])
                sentence_count = len(sentences)
                logger.debug(f"Counted {sentence_count} sentences for chunk at lines {chunk_data['start_line']}-{chunk_data['end_line']}")
            except Exception as e:
                logger.warning(f"Failed to count sentences for chunk at lines {chunk_data['start_line']}-{chunk_data['end_line']}: {e}")
                sentence_count = None

        chunk = Chunk(
            parent_id=parent_id,  # Required parent reference
            work_id=work_id,
            level=level_str,
            content=chunk_data['content'],
            heading_breadcrumbs=chunk_data.get('heading_breadcrumbs'),
            embedding=None,
            start_line=chunk_data['start_line'],
            end_line=chunk_data['end_line'],
            vector_status=chunk_data['vector_status'],  # "to_vec"/"tbl"/"fig"
            sentence_count=sentence_count
        )

        session.add(chunk)
        chunks_created.append(chunk)

    logger.info(f"Created {len(chunks_created)} content chunks for work {work_id}")
    if skipped_no_parent > 0:
        logger.warning(f"Skipped {skipped_no_parent} chunks without parent heading")

    # Update processing status
    # NOTE: Must reassign the dict to trigger SQLAlchemy change detection for JSON columns
    new_status = dict(work.processing_status) if work.processing_status else {}
    new_status['simple_conversion_step'] = 'content_chunks_created'
    new_status['content_chunk_count'] = len(chunks_created)
    new_status['chunk_count'] = new_status.get('heading_chunk_count', 0) + len(chunks_created)
    work.processing_status = new_status

    session.commit()

    logger.info(f"Content chunking complete for work {work_id}")

    return chunks_created


# ============================================================================
# Deprecated Functions
# ============================================================================

def create_chunks_from_sanitized(work_id: int, session: Session) -> List[Chunk]:
    """
    DEPRECATED: Use create_heading_chunks_simple() + create_content_chunks_simple()

    This function is kept for backward compatibility but will be removed.
    """
    warnings.warn(
        "create_chunks_from_sanitized is deprecated. "
        "Use create_heading_chunks_simple() + create_content_chunks_simple() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Call new two-step process
    heading_chunks = create_heading_chunks_simple(work_id, session)
    content_chunks = create_content_chunks_simple(work_id, session)

    return heading_chunks + content_chunks


def create_chunks_standalone(work_id: int) -> int:
    """
    Standalone version for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Number of chunks created

    Raises:
        ValueError: If validation fails
    """
    with get_session() as session:
        chunks = create_chunks_from_sanitized(work_id, session)
        return len(chunks)
