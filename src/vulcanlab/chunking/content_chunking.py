"""Content-aware chunking for vector embeddings.

This module creates paragraph-level chunks from sanitized markdown documents,
using content-aware strategies including:
- Paragraph chunks with sentence overlap
- Heading hierarchy breadcrumbs
- Special handling for tables and figures

Usage:
    from vulcanlab.chunking.content_chunking import chunk_content
    count = chunk_content(work_id=1, verbose=True)

Examples:
    # Chunk all content for work ID 1
    from vulcanlab.chunking.content_chunking import chunk_content
    num_chunks = chunk_content(1)
    print(f"Created {num_chunks} chunks")

Raises:
    HashMismatchError: If file hashes don't match stored values.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import spacy

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Chunk, Work
from vulcanlab.sanitization.extract_titles import HashMismatchError
from vulcanlab.utils.file_utils import compute_file_hash, get_path_resolver

# Configure logging
logger = logging.getLogger(__name__)


# Initialize path resolver
resolver = get_path_resolver()


# Load spaCy model for sentence tokenization
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise ImportError(
        "spaCy model 'en_core_web_sm' not found. "
        "Install with: python -m spacy download en_core_web_sm"
    )

# Chunking constants
TARGET_WORDS = 200
MAX_WORDS = 300
MIN_CHUNK_WORDS = 50  # Minimum words for a valid chunk
MIN_OVERLAP_SENTENCES = 2
MAX_OVERLAP_SENTENCES = 3
PARAGRAPH_BREAK_OVERLAP = 3


def _count_words(text: str) -> int:
    """Count words in text, handling markdown syntax properly.

    This improved version:
    - Removes markdown link syntax [text](url) and keeps only 'text'
    - Removes formatting markers (*,_,~,`)
    - Splits on word boundaries to count actual words

    Args:
        text: Text to count words in.

    Returns:
        Number of words in the text.
    """
    # Remove markdown link syntax, keeping only the link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove formatting markers
    text = re.sub(r'[*_~`]+', '', text)
    # Find all word sequences (alphanumeric + underscore)
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def _get_sentences(text: str) -> list[str]:
    """Split text into sentences using spaCy."""
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def _convert_bullets_to_sentences(text: str) -> str:
    """Convert bullet lists to flowing sentences.

    Args:
        text: Text potentially containing bullet lists.

    Returns:
        Text with bullets converted to sentences.
    """
    lines = text.split('\n')
    result_lines = []
    bullet_buffer = []

    def flush_bullets():
        if bullet_buffer:
            # Join bullets into sentences
            sentences = []
            for bullet in bullet_buffer:
                # Remove bullet marker and clean
                cleaned = re.sub(r'^[\s]*[-*+]\s*', '', bullet).strip()
                if cleaned:
                    # Ensure it ends with punctuation
                    if not cleaned[-1] in '.!?':
                        cleaned += '.'
                    sentences.append(cleaned)
            if sentences:
                result_lines.append(' '.join(sentences))
            bullet_buffer.clear()

    for line in lines:
        # Check if line is a bullet
        if re.match(r'^[\s]*[-*+]\s+', line):
            bullet_buffer.append(line)
        else:
            flush_bullets()
            result_lines.append(line)

    flush_bullets()
    return '\n'.join(result_lines)


def _parse_markdown_structure(content: str) -> dict:
    """Parse markdown into structured elements.

    Returns:
        Dictionary with:
        - headings: list of (line_num, level, text)
        - paragraphs: list of (start_line, end_line, text)
        - tables: list of (start_line, end_line, text)
        - figures: list of (line_num, text)
    """
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
            # Continue until blank line or special element
            while i < len(lines):
                next_line = lines[i]
                # Stop at blank line
                if not next_line.strip():
                    break
                # Stop at heading
                if re.match(r'^#+\s+', next_line):
                    break
                # Stop at figure
                if re.match(r'^!\[.*\]\(.*\)', next_line):
                    break
                # Stop at table
                if next_line.strip().startswith('|'):
                    break
                para_lines.append(next_line)
                i += 1

            para_end = para_start + len(para_lines) - 1
            para_text = '\n'.join(para_lines)
            # Convert bullets to sentences
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


def _build_heading_hierarchy(headings: list[tuple[int, int, str]]) -> dict[int, list[str]]:
    """Build heading hierarchy for each line number.

    Args:
        headings: List of (line_num, level, text).

    Returns:
        Dictionary mapping line numbers to heading hierarchy [H1, H2, H3].
    """
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
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> tuple[Optional[int], list[str], int]:
    """Find the heading that contains a given line.

    Args:
        line_num: Line number to find heading for.
        headings: List of (line_num, level, text).
        heading_hierarchy: Dictionary mapping heading line numbers to breadcrumbs.

    Returns:
        Tuple of (heading_line_num, breadcrumb_list, level).
    """
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


def _format_breadcrumb(breadcrumb: list[str]) -> str:
    """Format heading breadcrumb for chunk content."""
    if not breadcrumb:
        return ""
    return ' > '.join(breadcrumb)


def _create_paragraph_chunks(
    paragraphs: list[tuple[int, int, str]],
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]],
    min_words: int = MIN_CHUNK_WORDS
) -> list[dict]:
    """Create chunks from paragraphs, combining short paragraphs under same heading.

    Paragraphs under the same heading are combined until reaching TARGET_WORDS
    or MAX_WORDS. A new chunk is only created when:
    - Adding the next paragraph would exceed MAX_WORDS
    - We hit a new heading
    - We finish all paragraphs

    Args:
        paragraphs: List of (start_line, end_line, text) tuples.
        headings: List of (line_num, level, text) tuples.
        heading_hierarchy: Dictionary mapping line numbers to breadcrumbs.
        min_words: Minimum word count for chunks (default: MIN_CHUNK_WORDS).

    Returns:
        List of chunk dictionaries with keys:
        - content: Chunk text (without breadcrumb)
        - heading_breadcrumbs: Breadcrumb string (e.g., "H1 > H2 > H3") or None
        - start_line: First paragraph start line
        - end_line: Last paragraph end line
        - heading_line: Line number of heading (for parent lookup)
        - level: Heading level (e.g., 2 for H2)
        - vector_status: 'to_vec'
    """
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
        # Breadcrumbs no longer count against MAX_WORDS (stored separately)
        available_words = MAX_WORDS

        # Accumulator for combining paragraphs
        current_sentences = []
        current_start_line = None
        current_end_line = None

        # Track overlap sentences for continuity between chunks
        overlap_sentences = []

        def flush_chunk(force: bool = False):
            """Create a chunk from accumulated sentences.

            Args:
                force: If True, create chunk even if below minimum word count.
                       Used at end of heading groups to avoid losing content.
            """
            nonlocal current_sentences, current_start_line, current_end_line, overlap_sentences

            if not current_sentences or current_start_line is None:
                # Nothing to flush, or only overlap sentences (no actual paragraph content yet)
                current_sentences = []
                current_start_line = None
                current_end_line = None
                return

            chunk_text = ' '.join(current_sentences)
            chunk_word_count = _count_words(chunk_text)

            # Check minimum word count (unless forced)
            if not force and chunk_word_count < min_words:
                # Don't flush yet - keep accumulating
                return

            # Store content and breadcrumbs separately
            chunks.append({
                'content': chunk_text,
                'heading_breadcrumbs': breadcrumb_text if breadcrumb_text else None,
                'start_line': current_start_line,
                'end_line': current_end_line,
                'heading_line': h_line,
                'level': level,
                'vector_status': 'to_vec'
            })

            # Set overlap for next chunk
            overlap_sentences = current_sentences[-MAX_OVERLAP_SENTENCES:] if len(current_sentences) >= MIN_OVERLAP_SENTENCES else current_sentences[:]

            # Reset accumulator
            current_sentences = []
            current_start_line = None
            current_end_line = None

        for para_idx, (para_start, para_end, para_text) in enumerate(paras):
            sentences = _get_sentences(para_text)
            if not sentences:
                continue

            para_words = _count_words(para_text)

            # If this is first content in a new chunk, add overlap from previous
            if not current_sentences and overlap_sentences:
                current_sentences.extend(overlap_sentences)

            # Check if adding this paragraph would exceed MAX_WORDS
            test_sentences = current_sentences + sentences
            test_words = _count_words(' '.join(test_sentences))

            if test_words <= available_words:
                # Paragraph fits - add to current chunk
                current_sentences.extend(sentences)
                if current_start_line is None:
                    current_start_line = para_start
                current_end_line = para_end

                # If we've reached TARGET_WORDS and there are more paragraphs, flush
                current_words = _count_words(' '.join(current_sentences))
                if current_words >= TARGET_WORDS and para_idx < len(paras) - 1:
                    flush_chunk()

            elif para_words <= available_words:
                # Paragraph doesn't fit with current, but fits on its own
                # Flush current chunk first
                flush_chunk()

                # Start new chunk with overlap + this paragraph
                if overlap_sentences:
                    current_sentences.extend(overlap_sentences)
                current_sentences.extend(sentences)
                current_start_line = para_start
                current_end_line = para_end

            else:
                # Paragraph too long - need to split it
                # First flush any accumulated content
                flush_chunk()

                # Add overlap to start
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
                        # Flush and start new chunk with overlap
                        if current_sentences:
                            # Use para_start/para_end since we're splitting within paragraph
                            if current_start_line is None:
                                current_start_line = para_start
                            current_end_line = para_end
                            flush_chunk()

                        # Start new chunk with overlap + this sentence
                        if overlap_sentences:
                            current_sentences.extend(overlap_sentences)
                        current_sentences.append(sent)
                        current_start_line = para_start
                        current_end_line = para_end

        # Flush any remaining content for this heading (force=True to avoid losing content)
        flush_chunk(force=True)

    return chunks


def _create_table_chunks(
    tables: list[tuple[int, int, str]],
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> list[dict]:
    """Create chunks for tables."""
    chunks = []

    for table_start, table_end, table_text in tables:
        h_line, breadcrumb, level = _find_heading_for_line(table_start, headings, heading_hierarchy)
        breadcrumb_text = _format_breadcrumb(breadcrumb)

        # Store content and breadcrumbs separately
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
    figures: list[tuple[int, str]],
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> list[dict]:
    """Create chunks for figures."""
    chunks = []

    for fig_line, fig_text in figures:
        h_line, breadcrumb, level = _find_heading_for_line(fig_line, headings, heading_hierarchy)
        breadcrumb_text = _format_breadcrumb(breadcrumb)

        # Store content and breadcrumbs separately
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


def _merge_small_chunks(chunks: list[dict], min_words: int = MIN_CHUNK_WORDS, verbose: bool = False) -> tuple[list[dict], int]:
    """Merge chunks that are below the minimum word count with adjacent chunks.

    Strategy:
    - Iterate through chunks and find those below minimum
    - Attempt to merge small chunks with the previous chunk if they share the same heading
    - If no previous chunk exists or headings differ, merge with the next chunk
    - Track number of merges for logging

    Args:
        chunks: List of chunk dictionaries to validate and merge.
        min_words: Minimum word count threshold.
        verbose: Whether to print merge information.

    Returns:
        Tuple of (merged_chunks_list, merge_count).
    """
    if not chunks:
        return [], 0

    validated_chunks = []
    pending_merge = None
    merge_count = 0

    for i, chunk in enumerate(chunks):
        # Skip non-text chunks (tables, figures) from word count validation
        if chunk.get('vector_status') in ['tbl', 'fig']:
            if pending_merge:
                # Can't merge text with table/figure - flush pending
                validated_chunks.append(pending_merge)
                pending_merge = None
            validated_chunks.append(chunk)
            continue

        # Extract just the content text (without breadcrumb for counting)
        content = chunk['content']
        # Count words in the actual content
        word_count = _count_words(content)

        if word_count < min_words:
            if verbose:
                print(f"  Found small chunk ({word_count} words) at lines {chunk['start_line']}-{chunk['end_line']}")

            if pending_merge:
                # Merge this small chunk with the previous pending small chunk
                pending_merge['content'] += '\n\n' + chunk['content']
                pending_merge['end_line'] = chunk['end_line']
                # Keep the first breadcrumb (they should be the same under same heading)
                if not pending_merge.get('heading_breadcrumbs') and chunk.get('heading_breadcrumbs'):
                    pending_merge['heading_breadcrumbs'] = chunk['heading_breadcrumbs']
                # Update word count check
                merged_word_count = _count_words(pending_merge['content'])
                if merged_word_count >= min_words:
                    # Now meets minimum - flush it
                    validated_chunks.append(pending_merge)
                    pending_merge = None
                    merge_count += 1
                    if verbose:
                        print(f"    Merged with previous small chunk -> {merged_word_count} words")
                # else: keep accumulating in pending_merge
            elif validated_chunks and validated_chunks[-1].get('heading_line') == chunk.get('heading_line'):
                # Merge with previous chunk if same heading
                prev_chunk = validated_chunks[-1]
                # Only merge text chunks, not tables/figures
                if prev_chunk.get('vector_status') == 'to_vec':
                    prev_chunk['content'] += '\n\n' + chunk['content']
                    prev_chunk['end_line'] = chunk['end_line']
                    # Keep the first breadcrumb (they should be the same under same heading)
                    if not prev_chunk.get('heading_breadcrumbs') and chunk.get('heading_breadcrumbs'):
                        prev_chunk['heading_breadcrumbs'] = chunk['heading_breadcrumbs']
                    merge_count += 1
                    if verbose:
                        new_word_count = _count_words(prev_chunk['content'])
                        print(f"    Merged with previous chunk -> {new_word_count} words")
                else:
                    # Previous is table/figure, save this as pending
                    pending_merge = chunk
            else:
                # No previous chunk or different heading - save as pending
                pending_merge = chunk
        else:
            # Chunk meets minimum requirements
            if pending_merge:
                # Merge pending small chunk with this chunk
                chunk['content'] = pending_merge['content'] + '\n\n' + chunk['content']
                chunk['start_line'] = pending_merge['start_line']
                # Keep the first breadcrumb (they should be the same under same heading)
                if not chunk.get('heading_breadcrumbs') and pending_merge.get('heading_breadcrumbs'):
                    chunk['heading_breadcrumbs'] = pending_merge['heading_breadcrumbs']
                merge_count += 1
                if verbose:
                    new_word_count = _count_words(chunk['content'])
                    print(f"    Merged pending chunk with current -> {new_word_count} words")
                pending_merge = None

            validated_chunks.append(chunk)

    # Handle any remaining pending merge at the end
    if pending_merge:
        if validated_chunks and validated_chunks[-1].get('vector_status') == 'to_vec':
            # Merge with last chunk if it's a text chunk
            validated_chunks[-1]['content'] += '\n\n' + pending_merge['content']
            validated_chunks[-1]['end_line'] = pending_merge['end_line']
            # Keep the first breadcrumb (they should be the same under same heading)
            if not validated_chunks[-1].get('heading_breadcrumbs') and pending_merge.get('heading_breadcrumbs'):
                validated_chunks[-1]['heading_breadcrumbs'] = pending_merge['heading_breadcrumbs']
            merge_count += 1
            if verbose:
                new_word_count = _count_words(validated_chunks[-1]['content'])
                print(f"    Merged final pending chunk with last chunk -> {new_word_count} words")
        else:
            # Keep even if small (edge case: only chunk or can't merge)
            validated_chunks.append(pending_merge)
            if verbose:
                word_count = _count_words(pending_merge['content'])
                print(f"    Kept final small chunk ({word_count} words) - no merge possible")

    return validated_chunks, merge_count


def chunk_content(work_id: int, verbose: bool = False, min_chunk_words: int = MIN_CHUNK_WORDS) -> int:
    """Chunk content from a work into the database.

    Args:
        work_id: ID of the work in the database.
        verbose: Whether to print progress information.
        min_chunk_words: Minimum word count for chunks (default: 50).
                        Chunks below this will be merged with adjacent chunks.

    Returns:
        Number of chunks created.

    Raises:
        ValueError: If work not found or required files missing from database.
        HashMismatchError: If file hashes don't match stored values.
        FileNotFoundError: If files referenced in database don't exist on disk.
    """
    with get_session() as session:
        # Step 1: Get work and validate files metadata exists
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")

        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")

        # Step 2: Lookup sanitized file from files JSON
        if "sanitized" not in work.files:
            raise ValueError(
                f"Work {work_id} does not have 'sanitized' in files metadata. "
                f"Run: venv\\Scripts\\python -m vulcanlab.sanitization.apply_title_changes_cli {work_id}"
            )

        sanitized_path = resolver.resolve_work_path(work, "sanitized")
        sanitized_stored_hash = work.files["sanitized"].get("hash")

        if verbose:
            print(f"Processing work {work_id}: {work.title}")
            print(f"Sanitized markdown: {sanitized_path}")

        # Step 3: Validate file exists on disk
        if not sanitized_path.exists():
            raise FileNotFoundError(
                f"Sanitized file not found on disk: {sanitized_path}\n"
                f"Referenced in work {work_id}, key 'sanitized'"
            )

        # Step 4: Validate hash
        sanitized_current_hash = compute_file_hash(sanitized_path)

        if verbose:
            print(f"Validating sanitized hash: ", end="")
        if sanitized_current_hash != sanitized_stored_hash:
            if verbose:
                print("MISMATCH")
            raise HashMismatchError(sanitized_stored_hash, sanitized_current_hash)
        if verbose:
            print("OK")

        # Step 5: Read content for parsing
        content = sanitized_path.read_text(encoding='utf-8')

        # Step 6: Parse markdown structure
        structure = _parse_markdown_structure(content)
        headings = structure['headings']
        heading_hierarchy = _build_heading_hierarchy(headings)

        if verbose:
            print(f"Found {len(headings)} headings, {len(structure['paragraphs'])} paragraphs, "
                  f"{len(structure['tables'])} tables, {len(structure['figures'])} figures")

        # Step 7: Create chunks
        all_chunks = []

        # Paragraph chunks
        para_chunks = _create_paragraph_chunks(
            structure['paragraphs'], headings, heading_hierarchy, min_chunk_words
        )
        all_chunks.extend(para_chunks)

        # Table chunks
        table_chunks = _create_table_chunks(
            structure['tables'], headings, heading_hierarchy
        )
        all_chunks.extend(table_chunks)

        # Figure chunks
        figure_chunks = _create_figure_chunks(
            structure['figures'], headings, heading_hierarchy
        )
        all_chunks.extend(figure_chunks)

        if verbose:
            print(f"Created {len(para_chunks)} paragraph chunks, "
                  f"{len(table_chunks)} table chunks, {len(figure_chunks)} figure chunks")

        # Step 7.5: Merge small chunks to ensure minimum word count
        all_chunks, merge_count = _merge_small_chunks(all_chunks, min_chunk_words, verbose)

        if verbose and merge_count > 0:
            print(f"Merged {merge_count} small chunks")
            print(f"Final chunk count: {len(all_chunks)}")

        # Step 8: Get existing heading chunks for parent lookup
        heading_chunks = session.query(Chunk).filter(
            Chunk.work_id == work_id,
            Chunk.level.in_(['H1', 'H2', 'H3', 'H4', 'H5'])
        ).all()

        # Map start_line to chunk id
        heading_chunk_map = {chunk.start_line: chunk.id for chunk in heading_chunks}

        # Step 9: Save chunks to database (only those with parent heading chunks)
        chunks_created = 0
        skipped_no_parent = 0

        for chunk_data in all_chunks:
            # Find parent_id from heading chunk
            parent_id = None
            heading_line = chunk_data.get('heading_line')

            if heading_line:
                parent_id = heading_chunk_map.get(heading_line)

            # Skip chunks without a parent heading chunk
            if parent_id is None:
                skipped_no_parent += 1
                if verbose:
                    print(f"  Skipping chunk at lines {chunk_data['start_line']}-{chunk_data['end_line']}: no parent heading chunk")
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
                    if verbose:
                        logger.info(f"Counted {sentence_count} sentences for chunk at lines {chunk_data['start_line']}-{chunk_data['end_line']}")
                except Exception as e:
                    logger.warning(f"Failed to count sentences for chunk at lines {chunk_data['start_line']}-{chunk_data['end_line']}: {e}")
                    sentence_count = None

            chunk = Chunk(
                parent_id=parent_id,
                work_id=work_id,
                level=level_str,
                content=chunk_data['content'],
                heading_breadcrumbs=chunk_data.get('heading_breadcrumbs'),
                embedding=None,
                start_line=chunk_data['start_line'],
                end_line=chunk_data['end_line'],
                vector_status=chunk_data['vector_status'],
                sentence_count=sentence_count
            )

            session.add(chunk)
            chunks_created += 1

            if verbose and chunks_created <= 5:
                status = chunk_data['vector_status']
                print(f"  Created {level_str} chunk (lines {chunk_data['start_line']}-{chunk_data['end_line']}, {status})")

        if verbose and chunks_created > 5:
            print(f"  ... and {chunks_created - 5} more chunks")

        # Commit chunks first
        session.commit()

        # Update processing status
        work.processing_status = {**(work.processing_status or {}), "content_chunks": "completed"}
        session.add(work)
        session.commit()
        session.refresh(work)

        if verbose:
            print(f"\nTotal: {chunks_created} chunks created for work {work_id}")
            if skipped_no_parent:
                print(f"Skipped: {skipped_no_parent} chunks had no parent heading chunk")
            print(f"Updated processing_status: content_chunks=completed")

        return chunks_created
