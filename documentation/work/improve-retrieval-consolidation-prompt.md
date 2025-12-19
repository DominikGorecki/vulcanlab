## Goals:
The goals of this work is to:
1. Remove the requirement of referencing the sanitized markdown documents 
2. Improve the context produced for the RAG -- make the final context groupings more complete

## How it Currently
This is currently how retrieval, consolidation, and augmentation work: [rag-process-details](/documentation/rag-process-details.md)

## Improving Retrieval

For step 3 as outlined in the above linked document for "The Bridge (Preparation & Enrichment):
* For content enrichment do not read the local sanitized markdown file, instead walk up the parents (parent_id) until we have a chunk that is at least Min_Word_Count based on the settings.
* Include the whole chunk if it's less than `max_word_count` (expose new setting in RAG configuration and settings -> RAG_settings) -- also append to the content of the enriched chunk the title from heading_breadcrumbs if they exist (if it's a non-content chunk which is fine, it will be right in the content)
* If the chunk is more than `max_word_count`, then concatenate content above and below the chunk so that it fits within the allowed word count 
    - you can determine what lines to focus on based on the start_line and end_line of the original chunk and the start_line of the parent, larger chunk
    - Example: if we are over by 100 words, then remove 50 words above the chunk and 50 words below the chunk
    - exceptions:  if we are at the top of the chunk then we can remove all 100 words (in this example) from the bottom; if we're at the end, we can remove from the beginning 
    - Title should be taken from the parent chunk being used (heading_breadcrumbs if it's not null or just from the content)
    - Example output:
    ```
    ## Parent Chunk Title
    ### Extra title in parent not modified
    ... content from parent chunk concatenated above. 
    ### H3 Chunk returned
    Include content from original chunk as well as surrounding content as much as possible. ...
    ```
    - Do not remove or modify any titles when concatenating
* Note, attempt to perform enrichment but if you can't based on the above, the remove item from 
* Since we're relying now on min_word_count and the algorithm explained above, remove:
    * min_char_count 
    * min_content_length 
    * enrich_lines_above and enrich_lines_below
    * Remove from implementation and setting and ui
* Update existing templates with new schema with default values for each new property:
    * `max_word_count` - 750
* Now we are ready for Deep Reranking (BGE)

## Improving Consolidation
1. Hierarchical Analysis -- continue to group by `word_id` and `parent_id`
2. Merging Logic
    * Adjacency merging -- Similar logic for this, but use the parent chunk instead of reaching back to the sanitized markdown file--since this group should share the same parent, all the content should be there. use the start_line and end_line of the children and parent to figure out what lines to merge.
    * Parent-level replacement -- if more than 65% (`coverage_threshold`) of the content based on character count (characters in child chunks in group (or merged chunks) / parent chunk), replace the group with the parent. Ensure the parent has a title (if content-chunk it's in the heading_breadcrumbs, if it's a heading chunk it's in the content so just include the content if it's a heading chunk).
3. Every consolidated group retrains Heading Chain (breadcrumbs) or the title of the heading chunk from the content:
    * If we the top level chunk is a content chunk, use heading breadcrumbs
    * If the top level chunk is a heading chunk, the title will be the first line of the content

Note: In the ui I don't see `coverage_threshold` -- it should be exposed

You can remove `enrich_from_md` from the settings and implementation as well as UI. 

## Final notes

Do the research to make sure this doesn't have any issues and it will work. Ensure that any changes to the settings object for rag (rag_config in the DB) have a migration and any new items are updated in all existing templates (anything in that table, really). Ideally migrations are simple sql files. Finally, ensure init_db.py is updated because migrations are never run on fresh installs. 
    
