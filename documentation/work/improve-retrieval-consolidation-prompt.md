
## Goals:
The goals of this work is to:
1. Remove the requirement of referencing the sanitized markdown documents 
2. Improve the context produced for the RAG -- make the final context groupings more complete

## How it Currently
This is currently how retrieval, consolidation, and augmentation work: [rag-process-details](/documentation/rag-process-details.md)

## Improving Retrieval

For step 3 as outlined in the above linked document for "The Bridge (Preparation & Enrichment):
* For content enrichment do not read the local sanitized markdown file, instead walk up the parents (parent_id) until we have a chunk that is at least Min_Word_Count based on the settings.
* Include the whole chunk if it's less than Max_Word_Count (expose new setting in RAG configuration and settings -> RAG_settings)
* If the chunk is more than Max_Word_Count, then contaminate content above and below the chunk so that it fits within the allowed word count 
    - you can determine what lines to focus on based on the start_line and end_line of the original chunk and the start_line of the parent, larger chunk
    - If we are over by 100 words, then remove 50 words above the chunk and 50 words below the chunk
    - exceptions:  if we are at the top of the chunk then we can remove all 100 words (in this example) from the bottom; if we're at the end, we can remove from the beginning 
    - Title should be taken from the parent chunk being used
    - Example output:
    ```
    ## Parent Chunk Title
    ### Extra title in parent not modified
    ... content from parent chunk concatenated above. 
    ### H3 Chunk returned
    Include content from original chunk as well as surrounding content as much as possible. ...
    ```
    - Do not remove or modify any titles when concatenating
* Remove the min_char_count setting and implementation in retrieval -- we'll focus on words and sentences only
* Since we're relying now on min_word_count, remove min_char_count 
* Note, attempt to perform enrichment but if you can't based on the above, the remove item from 
    
