# Augmentation

This step does the following:
* Takes the raw results in the `Query` object that is saved in `retrieval_context` and consolidates them into a cleaner object to send to the LLM as context. We'll call this the `clean_retrieval_context`.
* It converts the `clean_retrieval_context` JSON into md format that will be easy for the LLM to use. 
* It provides the instructions how to use the clean retrieval context markdown
* It then provides the original query

# Consolidation -- Generating a Clean Retrieval Context

1. Group all items by `work id` and `parent_id`
2. Based on `start_line` and `end_line` of the chunks and the `start_line` and `end_line` of the parent:
    * If the chunks of the parent cover 50% or more of the parent, replace all the chunks with the parent. Use the highest `final_score` of the group as the as the `score`. This will be the entry for this group.
    * If the chunks of the parent cover less than 50% of the parent, then try to combine the chunks if they are within each other based on the `start_line` and `end_line`:
        1. Order by `start_line`
        2. If any chunk i `end_line` of one chunk is within 7 lines of the `start_line` of the next chunk, then group them together based on the line:

            * `start_line`: based on the first chunk in the group
            * `end_line`: based on the last chunk in the group
            * `content`: read from the original `<work>.sanitized.md` file found in `works` (matched on `work_id`) in the `markdown_path` column. Use the `start_line` and `end-line` determined in the two points above
            * `score`: highest `final_score` of the group
            * Append the title of the first chunk in the group -- the first line of the first chunk should be copied over to the top of the `content` with a line space in between
            * `parent_id`: stays the same--should be the same for the whole group

    * When there are nested parents, follow the above steps but from lowest level to the top. That is, first determine the grouping based on the lower level parents and then work up to higher level parents. 
    * The final `clean_retrieval_context` should have the following properties:
        * `chunk_ids: [chunk_id]`: array of the chunk ids in the group (could be just 1)
        * `parent_id`: Since we're grouping by parent, the parent id of the group
        * `work_id`: all need to be in the same work
        * `content`: Content generated as explained above
        * `start_line` and `end_line`: as explained above
        * `score`: highest `final_score` of the group

# LLM Query Generation - Final Augmentation

In the `src\vulcanLab\augmentation` folder generate: the module called `augment.py` and the cli `augment_cli.py` that does what is described below:

The CLI by default should only output the prompt to screen and not send it to the LLM. After the showing the prompt the use can type in "send" which will send to the LLM with the FULL settings and search turned on. The user can instead choose to `copy` the output into clipboard (ensure it works on both windows, mac, and linux if possible). If you're using any new libraries ensure you add them to @pyproject.toml . 

Here is what it should do

Finally we need to adjust our query to take into account the new context and instructions on how to use it:
1. Instruction block – defines behavior and how to use context. 
2. Context block – your retrieved passages `[S1]..[Sn]`.
3. Question block – original user question, possibly with a small reminder to use the context.

For this, we need:
* The query from `queries` table in the DB
    * `original_query` will be used in #3 -- the question block
    * Top `N` items from the `clean_retrieval_context` -- default will be 5 (`N = 5`) based on `score` -- order from biggest to lowest.
    * For each item generate markdown as follows:
        * Look up the work in the `works` table based on the `work_id`
        * Generate the source: `[S#] Source: {work_title} -- {first_line_of_content} | start-line: {start_line} | end-line: {end_line}`
        * Add the text: `Text:\n {content_without_first_line}`
    * Combine all these together into `context_blocks`. The final output should be like the following:
    ```md
    Context documents:
    [S1] Source: {Title of highest ranked section} -- {First line of content} | (work_id={work-id}, start-line={start-line}, end-line={end-line})
    Text:
    {content starting at line 2 -- trim empty lines at the top and bottom or whitespace}
    ...
    [S5] Source: {Title of lowest of our top N results} -- {First line of content} | (work_id={work-id}, start-line={start-line}, end-line={end-line})
    Text:
    {content starting at line 2 -- trim empty lines at the top and bottom or whitespace}
    ```

Generate the prompt to send to the LLM based on this:

```
prompt = f"""You are an academic assistant that answers questions using a set of retrieved source passages
plus your own general knowledge when appropriate.

Your job is to:
1. Read and understand the source passages in the CONTEXT section below.
2. Answer the user's question as accurately and clearly as possible.
3. Clearly distinguish between:
   - Information that is directly supported by the provided sources.
   - Information that comes from your broader academic knowledge but is NOT explicitly in the sources.
4. Explicitly reference which source passages you are using, with the keys [S1], [S2], etc.

HYBRID EVIDENCE POLICY (VERY IMPORTANT)
- PRIMARY: Treat the provided sources as the main evidence base.
- SECONDARY: You MAY use general academic knowledge, but:
  - Only if it is standard and non-controversial in the relevant field.
  - You MUST clearly separate it from what is supported by the sources.
- If the sources do not contain enough information to fully answer the question:
  - Say what can be concluded from the sources.
  - Then optionally add a clearly marked section with general knowledge and search.

CITATION RULES
- Each context block below is tagged with a label like [S1], [S2], etc.
- Each block may also include metadata such as work_id, start_line and end_line in parentheses.
  Example header:
    [S1] Source: Some Book Title -- section title | (work_id=123, start_line=23, end_line=32)
- When you make a claim that is supported by one or more sources:
  - Add the relevant source labels at the end of the sentence or paragraph, e.g. [S1], [S1][S3].
  - Do NOT invent new source labels beyond those given.
  - Do NOT cite work_id or start_line or end_line directly in the prose; just use [S#].
- Our system will later map [S#] back to work_id, start_line, and end_line for linking to the original content.

STRUCTURE YOUR ANSWER AS FOLLOWS
1. **Answer**
   - Provide a direct, well-organized answer to the question.
   - Use citations [S#] whenever you rely on information from the sources.
   - If multiple sources contribute to a point, cite each of them.
2. **Explanation and Details**
   - Expand on key concepts, mechanisms, comparisons, or study details.
   - Group related ideas logically (e.g., definitions, mechanisms, evidence, limitations).
   - Continue to use [S#] citations where appropriate.
3. **From General Knowledge or Search (Outside Provided Sources)** (optional)
   - Only include this section if you add material that is NOT clearly supported by the sources.
   - Clearly mark that this section is based on your broader academic knowledge or search.
   - Do NOT attach [S#] citations to statements in this section.
4. **Sources Used**
   - List the source labels you actually relied on in your answer, e.g.:
     - Sources used: [S1], [S3], [S5]

INTENT AND ENTITIES (GUIDANCE ONLY)
- The question intent type is: {intent}
  Possible values include: DEFINITION, MECHANISM, COMPARISON, APPLICATION, STUDY_DETAIL, CRITIQUE.
- Key entities and concepts for this question are:
  {entities_str}
Use this information to shape your answer style:
- DEFINITION: Start with a clear definition, then elaborate.
- MECHANISM: Focus on explaining processes, causes, and “how/why”.
- COMPARISON: Explicitly compare similarities and differences between entities.
- APPLICATION: Emphasize examples and real-world implications.
- STUDY_DETAIL: Highlight study design, samples, methods, and key findings.
- CRITIQUE: Emphasize limitations, criticisms, and alternative interpretations.

TONE AND STYLE
- Write in a clear, academic style suitable for an advanced student or researcher.
- Define technical terms when they first appear, if the context does not already define them.
- Do not simply repeat large chunks of the sources; synthesize and explain them.
- If the sources disagree or present multiple perspectives, acknowledge this explicitly.

============================================================
CONTEXT (RETRIEVED SOURCE PASSAGES)
Each block is labeled [S#] and may include work_id and parent_id metadata
that our system uses to link back to the original document.

{context_blocks}
============================================================

USER QUESTION
{user_question}
"""
```
Please ask any questions if anything is not clear. 