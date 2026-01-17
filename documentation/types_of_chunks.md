# Types of Chunks in the chunks table

For a given work (document) from the `works` table takes the markdown in `sanitized_markdown.content` (FK to `works`: `sanitized_markdown.work_id`) and breaks it down into searchable "chunks" into the `chunks` table (FK to works: `chunks.works_id`).

The table `chunks` in our DB holds the searchable data we can use for RAG, searching, etc. It has the following columns that are important:
1. `work_id` - points back to the `works` table
2. `parent_id` - points back to other chunks based on the hierarchy of the document
3. `level` - indicates heading level `H#` -- also indicates if it's a **HEADING CHUNK** or a **CONTENT CHUNK**:
   * Heading Chunks - `H#` -- does not have "chunk" 
   * Content Chunks - `H#-chunk` -- contains the word "chunk"
4. `content` - content; heading chunks (not content chunks) always start with a title (first line of the heading-chunk)
5. `embeddings` - Dense embeddings -- only content-chunks have embeddings. These are embeddings based on the `chunks.content` column
6. `content_vector` - Lexical embeddings -- both heading-chunks and content-chunks have lexical embeddings. These are embeddings on the `chunks.content` column.
7. `start_line` - Start line of the content in `sanitized_markdown.content` -- where this chunk begins in the content
8. `end_line` - Similar as above, but for the end_line--where this content ends in `sanitized_markdown.content` 
9. `vector_status` - this indicates the following based on what is in the column:
    * `no_vec`: Row should never have dense vector embeddings
    * `to_vec`: Row is scheduled to have dense vector embeddings fetched, but currently doesn't have it. Once they are fetched, the `embeddings` are updated and this is changed to `vec`
    * `vec`: Row has dense vector embeddings for the content
    * `vec_err`: Some error fetching, generating, or saving vector embeddings
10. `heading_breadcrumbs`: the heading breadcrumbs for the chunk -- shows all the headings walking up the `parent_id` (first line of content) -- more useful for heading-chunks
11. `sentence_count`: number of sentences in the chunk content

## Relationship Diagram

```
┌─────────────────┐
│     works       │
│  (id, title...) │
└────────┬────────┘
         │
         │ work_id (FK)
         ▼
┌─────────────────────┐
│  sanitized_markdown │
│   (id, work_id,     │
│    content, ...)    │
└────────┬────────────┘
         │
         │ content is chunked into
         ▼
┌───────────────────────────────────────────────────┐
│                     chunks                         │
│  (id, work_id, parent_id, level, content, ...)    │
│                                                    │
│  ┌─────────────────┐      ┌─────────────────────┐ │
│  │  Heading Chunk  │──┐   │   Heading Chunk     │ │
│  │  (H1, H2, etc.) │  │   │   (H2, H3, etc.)    │ │
│  └─────────────────┘  │   └──────────┬──────────┘ │
│                       │              │            │
│         parent_id─────┘    parent_id─┘            │
│                       │              │            │
│                       ▼              ▼            │
│              ┌─────────────────────────────┐      │
│              │      Content Chunk          │      │
│              │  (H1-chunk, H2-chunk, etc.) │      │
│              └─────────────────────────────┘      │
└───────────────────────────────────────────────────┘
```

## The `heading_breadcrumbs` Format

The `heading_breadcrumbs` column stores the full path from root to the current chunk's heading hierarchy, using `" > "` (space-greater-than-space) as the delimiter.

**Format:** `"Root Heading > Child Heading > Grandchild Heading"`

**Examples:**
- `"Chapter 1 > Section 1.2 > Subsection 1.2.3"`
- `"Introduction > Background > Historical Context"`
- `"Part I > Chapter 3 > Methods > Data Collection"`

The breadcrumb is built by:
1. Walking up the `parent_id` chain to the root
2. Taking the first line of each heading chunk's content
3. Stripping any leading `#` markdown characters
4. Joining with `" > "` in root-to-leaf order

## Heading Chunks vs. Content Chunks 

As explained above, we can tell a heading-chunk because it will not have "-chunk" in the `level` column. We generally don't use these heading-chunks for searching (no embeddings in content are too large) we will use heading-chunks for:

* Grouping
* Understanding where content-chunks sit
* etc

## Hierarchy of Chunks

1. Top level chunks do not have a parent - `parent_id` IS NULL and should ALWAYS be heading-chunks
2. Children can be heading-chunks or content-chunks
3. content-chunks ALWAYS have a heading-chunk as a parent
4. A parent chunk holds all the content of a child-chunk