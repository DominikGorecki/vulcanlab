# Summarize Feature

Read [Types of Chunks](../types_of_chunks.md) to understand how chunks work in our system.

## Summarize Algorithm for Long Content 
After we ingest and vectorize a document, we have these tools to build an intelligent system for summarizing large documents:
1. Dense vector embeddings (`chunks.embeddings`)
2. Lexical embeddings for chunks (`chunks.content_vector`)
3. Start line and end line of the sanitized content (`chunks.start_line` and `chunks_end_line`)
4. 

### Step 1: Determine Which Heading-Chunks to Include
1. List all the heading chunks (chunks where level doesn't have "-chunk") ordered by `start_line` from smallest to largest -- preserver the order because it's important. We'll call these our "work_headings" that we need to summarize

2. Clean the "work_headings" list:
    * Remove any items from the list where `content` is shorter than 500 words -- make this adjustable in settings
    * For all the "heading-chunks" in the "work-headings" list, read the first line of each item in `content` -- these will be our "work-headings-headings"
    * If the total word count of all our headings is more than 2,500 (configurable in settings) then we need to remove from our list 
        * Remove lowest level headings with the shortest content until we hit our 2,500 max target for for the words in ALL the "work-headings-headings"

2. For each "heading-chunk" in the "work_headings":
    * Generate a list of child "content-chunks" ordered by start_line (this is where the parent_id is the id of the chunk from the list). Keep this list ordered, because it's important. We'll call this the "content-chunks" for a given "heading-chunk"
    * Take the "heading-chunk" `chunks.heading_breadcrumbs` and use it to perform a search against the "content-chunks" of it's children:
        * Dense search - top 7
        * Lexical search - top 7 
        * RRF - K - 60; Top-K: 7
        * MMR - 0.7 to adjust for scoring for diversity 
        * Top N final: 5 (ordered by final score from greatest to lowest)
        * All of these settings should be configurable in a new settings tab under "Summarize" 
    * In a new table save the following in a new table:
        * parent_id
        * chunk_id (FK)
        * word_count
        * dense_score
        * lexical_score
        * final_score (after RRF and MMR)

3. Generate LLM prompts for summarization
    * Using the remaining "work-headings" and "content-chunks" we want to generate LLM calls to summarize the whole work within the budget of a maximum of 5 LLM calls with each being under 15K tokens (configurable in settings)
    * We should maximize the call by trying to summarize as much as possible for each call from the top down based on the following strategy:
        * Before generating the LLM prompts we should figure out how much information to pass in--
            * For each heading we have top 5 chunks, we can remove how many chunks we pass in for each heading: focus on reducing chunks from lower level headings first--keep on removing until we hit our budget until we get to 1. 
            * Now we can keep on removing chunks from the next level up headings until we hit 1 and so on
            * For H1 and H2 leave at least the top 2, and leave at least top 1 for H3; if we are still over budget remove the lowest levels chunks completely
            * If we are still over budget start removing the lowest level chunks without consideration for keeping at least 2 for H1 and H2. This would be a really small edge case.
    * Once we have our list of "work-headings" and "content-chunks" pruned to a point where all the content is below 70K total, we need to generate a 5 LLM calls (or less) to summarize the whole work:
        * Pass in the headings above and below the current section beeing summarized 
        * Pass in the line numbers of the headings and the line numbers of each chunk
        * Expect a return that section while preserving the headings so if we pass in:
        ```
        # Title 1 
        -- id: [title_1_id]
        [chunks for this title]
        ## Title 2
        -- id: [title_2_id]
        [chunks for this title]
        ...
        ```
        * We should get back
        ```
        {
            [
                {
                    id: [title_1_id]
                    summary: [markdown LLM summary of section for title]
                },
                {
                    id: [title_2_id]
                    summary: [markdown LLM summary of section for title]
                }
            ]
        }
        ```
    * The prompt should have instructions for what to do and we should have a prompt template we can edit in the DB and in the UI based o our existing patterns. 
    * After all the LLM calls are returned, we should save the results into a new table `summary_results` into the DB so we link back to the heading-chunk id `summary_results.chunk_id` (FK)

## UI
* From the corpus page you can click summarize on a work
* Starts manual flow (automatic flow for the future) where it shows the first LLM call to copy and paste and then paste the result
* When all the LLM calls are copied and pasted and pasted back into the flow we have completed our summary for the work
* In the left nav show a "Summaries" link that shows all the works that have been summarize
* Clicking on an item in the table shows a generated summary in markdown:
    * For all the the heading-chunks ordered by `start_line` where we have a result in `summary_results` do the following:
        * show the first line of the heading-chunk `content`
        * show the `summary_results.summary_content` (the results from the LLM)
    * This way we should have a complete summary of the document
