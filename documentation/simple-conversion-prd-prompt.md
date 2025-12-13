# Simple Conversion Prompt for new PRD

Instead of all the manual steps described in the existing conversion process here: [conversion process reference](./conversion-process-reference.md), I want to build a simple approach that does everything in three steps

## Step 1
### 1.1 Parsing 
Parsing is part of step 1, and everything is kept in memory so we can just move along the flow.

#### PDF
Parse pdf into **markdown** including `hier` and `style`data -- do not write in the DB, just keep everything in memory in a single one step module:
    * Can use module `src/vulcanlab/conversions/conv_pdf2md.py` as library    
    * Use `src/vulcanlab/conversions/style_v_hier.py` to choose the best markdown version -- can ignore the not chosen version
#### Epub
Parse pdf into markdown:
    * Can use `src/vulcanlab/conversions/conv_epub2md.py` as a library

### 1.2 Small vs. Large Processing 
This step determines if the parsed markdown should be entirely sanitized via LLM (Small Conversion) or through heuristics + LLM (Large Conversion):
    * Based on token estimate (words * 1.33) -- if it's less than 15,000 tokens, take the **SMALL PROCESSING** approach otherwise take the **LARGE PROCESSING** approach
    * Ensure that we can set how many tokens is considered for small vs. large conversion (the 15,000 default) in `vulcanlab.config.json` and exposed in the UI in the settings page

## Step 2A - SMALL PROCESSING
This step processes the entire markdown document in an LLM call. It will generate the LLM prompt to do the following:
    * Proper document hierarchy: Process the provided markdown document so that titles and their heading level is adjusted.
        * Anything identified by the LLM that is not a title, the heading level of that title is removed (No "#...")
        * Anything that should be nested under a different title is adjusted (For example: H1 to H2, H4 to H3, etc.)
        * The resulting markdown document should have APPROPRIATE hierarchy with nesting headings based on context
    * Sanatization of content so that only data that is relevant for chunking and vectorization is left:
        * Sometimes pdf conversion has issues converting based on glyphs or weird font, the LLM will attempt to replace these poorly processed symbols into text representations. Sometimes it could be a number or letter, using the context around it. 
        * Anything that is meta information such as where the document is downloaded, etc. is removed
        * Other non topic related information (References, Aknowledgments, ToC, Giberish, page numbers) is removed
        * Only relevant and useful information for the purpose of RAG should be left
    * At this point, we should have the perfect markdown document to chunk into our database
    * That is, all headings should be vectorized

## Step 2B - LARGE Processing
This is about processing documents we can't or it's too costly to pass into the LLM context as a whole. This requires some heuristic work beforehand:
    * Create a markdown document to pass into the LLM that will give us information of the changes we need to make 
    * The document should parse out titles from the markdown like it's done in `src/vulcanlab/sanitization/extract_titles.py`, but it should also parse out out the first two and last two sentences of that title block (until the next title is encountered)
    * The document should have information about the line number where the title is just like we do existingly 
    * We will pass in this smaller document as markdown to focus ensuring a proper hierarchy in the document:
        * Any heading changes or removal
        * Any cleanup to the title (white space, et)
        * Indication of whether this title block should be vectorized
    * We will use this response to update the markdown document that's parsed out as well as for step 3

## Step 3 - Chunking
Chunk all the headings and content like we do right now -- if 2A, all headings are suggested for chunking if 2B then only the ones that are suggested from the LLM return will be be chunked. Chunk content as well. Follow existing procedure outlined in "./conversion-process-reference.md"


For now build out this PRD and later we'll add onto it to include the FE flow. 

At the end of the process, we should have chunks in the database (heading and content) for a given pdf. The work it should relate to should be passed into step 1. For Step 2, it should give us an option to either generate the full prompt that we can copy and paste (include the markdown or summarized markdown) to the LLM or running the prompt just like we do in other cases. 
