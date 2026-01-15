# Ticket: work-summarization.T06 - Node Selection Module

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement node selection logic to determine which heading-level chunks should be summarized
* Handle parent-child relationships to avoid content duplication
* Apply salience-based filtering using configurable thresholds

## Phase

* Core Modules

## Scope

### In scope

* src/vulcanlab/summarize/node_selector.py module
* Load heading-level chunks for a work (H1-H5, excluding H*-chunk content chunks)
* Compute salience scores for all heading chunks
* Apply threshold filtering based on SummarizeSettings
* Handle content gaps between heading levels (the "missing content" problem from spec)
* Determine start_line/end_line for summary nodes (may differ from chunk boundaries)
* Return ordered list of SelectedNode objects ready for summarization

### Out of scope

* Actual summarization (T07, T08)
* Evidence extraction (T05)
* Database writes (T08)

## Dependencies

* Depends on: T03 (models), T04 (salience scoring)
* Unblocks: T08

## Implementation plan

1. Create src/vulcanlab/summarize/node_selector.py
2. Define dataclasses:
   - `SelectedNode(chunk_id: int, level: str, content: str, heading_path: str, start_line: int, end_line: int, salience_score: float, has_content_gap: bool)`
3. Implement `load_heading_chunks(work_id: int, session: Session) -> list[Chunk]`:
   - Query chunks where level IN ('H1', 'H2', 'H3', 'H4', 'H5')
   - Order by start_line
4. Implement `detect_content_gaps(chunks: list[Chunk]) -> dict[int, tuple[int, int]]`:
   - For each chunk, check if there's content before first child
   - Return mapping of chunk_id -> (gap_start_line, gap_end_line)
5. Implement `build_chunk_tree(chunks: list[Chunk]) -> dict`:
   - Build parent-child hierarchy using parent_id
   - Track which chunks have children
6. Implement `compute_effective_boundaries(chunk: Chunk, children: list[Chunk]) -> tuple[int, int]`:
   - If chunk has children, effective end_line is before first child start
   - Otherwise, use chunk's own end_line
7. Implement `select_nodes_for_summarization(work_id: int, session: Session) -> list[SelectedNode]`:
   - Load heading chunks
   - Build chunk tree
   - Load salience weights from settings
   - For each chunk, compute salience score
   - Apply threshold filtering (H1 always if setting, H2 by top %, H3+ by threshold)
   - For selected chunks with content gaps, create additional node for gap content
   - Return SelectedNode list in document order
8. Implement `get_content_for_node(node: SelectedNode, work_id: int, session: Session) -> str`:
   - Reconstruct content from sanitized markdown using line numbers
   - Handle case where node spans partial chunk
* Patterns to apply:
  * Session passed explicitly
  * Core Module independence
  * Query patterns using SQLAlchemy
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `load_heading_chunks` filters out content-level chunks (H*-chunk)
  * `load_heading_chunks` returns chunks in document order
  * `detect_content_gaps` identifies content before first child heading
  * `build_chunk_tree` correctly establishes parent-child relationships
  * `compute_effective_boundaries` adjusts end_line for parent with children
  * `select_nodes_for_summarization` respects H1 always-summarize setting
  * `select_nodes_for_summarization` applies H2 top-percent filtering
  * `select_nodes_for_summarization` applies H3+ threshold filtering
  * Content gap nodes are created when needed
  * Empty work (no chunks) returns empty list
  * Work with only content chunks (no headings) returns empty list
* Suggested locations:
  * tests/unit/summarize/test_node_selector.py
* Mocking/fakes needed:
  * Mock session with fake chunk data
  * Mock SummarizeSettings

## Acceptance criteria (checklist)

* [ ] Heading-level chunks correctly identified and loaded
* [ ] Content-level chunks (H*-chunk) excluded
* [ ] Salience scores computed for all heading chunks
* [ ] H1 always-summarize setting respected
* [ ] H2 top-percent filtering works correctly
* [ ] H3+ threshold filtering works correctly
* [ ] Content gaps detected and handled
* [ ] Effective boundaries computed for parent-child relationships
* [ ] SelectedNode list returned in document order
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Load a work with nested headings (H1 > H2 > H3)
  2. Run `select_nodes_for_summarization(work_id, session)`
  3. Verify returned nodes match expected selection
  4. Check that content gaps are identified
* Expected results:
  * Appropriate nodes selected based on settings
  * No duplicate content coverage
  * Line ranges are accurate

## Notes

* Requirements covered: R1, R3, R4
* The "content gap" problem: H1 may have content before first H2 that isn't in any H2 chunk
* Solution: create a virtual node for the gap content pointing to H1 chunk
* Keyphrase novelty tracking requires processing nodes in order
* Consider caching salience weights per summarization run
* Level detection: check if level contains "-chunk" to distinguish heading vs content chunks
