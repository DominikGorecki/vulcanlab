A new feature that is linked from the left nav called "Summarize" that summarizes any work in our corpus.

[work-summary-strategy](../work-summary-strategy.md) - Use this as the strategy for how to create summaries based on the chunks (src/vulcanlab/data/models/chunk.py). For a given work, use this strategy to create data into a new table (summary_nodes) that has:

* gist,
* key points,
* definitions,
* key terms,
* examples
* reference back to selected chunk 
* reference back to start_line and end_line of the sanitized markdown

with reference back to the chunk_id so we can lookup the chunk itself

The chunks tables holds chunks at different levels and content chunks. Heading level chunks holds content in chunks.content but they aren't used for searching (dense or lexical).

Here is how to recognize a heading level chunk:
* chunks.level = "H1|H2|H3|H4|H5..."
* Note--the level doesn't have "chunk" in it

Here is how to recognize content level chunks:
* chunks.level = "H1-chunk|H2-chunk|H3-chunk|H4-chunk|H5-chunk..."
* Note--the level DOES have "chunk" in it

In the strategy document when it says node, think of these **heading level chunks** that we select that encompass the whole document

A heading-level chunk could have nested content, for example and "H2" level chunk should have all the other "H3" chunks nested inside. The "H3" level will reference the "H2" level chunk at by chunks.parent_id. This is important because when we're reconstructing a work, we don't want to pass in or read the same information twice.

One approach might be to first read the highest level chunks first (H1) and if those chunks are too big as nodes based on the strategy, attempt to go down to the next level (H2). There could be omitted content in the H2 level chunks, but we can use the start_line and end_line to reconstruct all the content we want. Example where H2 chunks would have missing contents:
```
# H1 Heading

THIS CONTENT WOULD BE MISSING

## H2 1.1 Heading

1.1 content

## H2 1.2 Heading

1.2 content
```

So in this case H1 chunk would have everything in it, and H2 chunks would just have their content. Note the `THIS CONTENT WOULD BE MISSING` would be missing from the H2 chunks. We can make judgments and adjust accordingly based on the line numbers of the markdown (start_line and end_line). 

We should select all the chunks in a way that encompasses the whole work. In our example we might need to create 3 new `summary_nodes`:
* 2 H2 full nodes that point back to the H2 level chunks (start_line and end_line match 1:1)
* 1 H1 node that points back to the H1 nodes and the start_line matches, but the end_line is before the first H2 start_line

## Front End Flow
1. In the "Corpus" page we should have a "summarize" button that generates all the data for a that work (new table that has gist, key points, definitions, key terms, examples for all the selected level)
2. In a new "Summarize" page (linked from left nav bar) show all the works that have summary_nodes
3. On this page, a user can select to either generate or view (if they are generated) an outline, chapter / section summary, key concepts, abstract

When we have our summary_nodes we can easily generate the following (may require additional LLM calls):
1. Abstract
2. Outline*
3. Chapter summaries*
4. Section summaries*
3. Key concepts / terms*

The above that has a start (*) should reference the work and try to reference the start_line and end_line even if there are multiple references for one thing. That is a key term might have a reference to multiple start_line and end_lines. 

All this should be kept in a new table or tables--whatever would eb the best pattern. 
