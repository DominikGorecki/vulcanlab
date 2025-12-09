## Adding new Work (Asset) To DB

## 1. CONVERSION -- Convert to Markdown - From PDF

* Conversion can take time depending on your setup--
* For the output filename:
    * Keep the file simple--you'll need to reference it multiple times
    * Don't use spaces: `this file.md` should be `this_file.md`
    * Don't use special chars, etc. -- I didn't test this, plus keep it simple.
    * Don't worry about keeping meta information in the title -- the bibliography of the work will be pulled into the DB. As long as you just know the filename during the ingestion process--after it won't matter. 
    * **Don't delete any files from the `output` folder manually**


OSS Examples to try:
* https://en.wikibooks.org/wiki/Cognitive_Psychology_and_Cognitive_Neuroscience (pdf link)


### Option 1: Convert with single option

* Run `python -m vulcanlab.conversions.conv_pdf2md raw\input.pdf -o output\<file>.md`
* This generates `<file>.md`


### Option 2: Convert with style and hierarchy (recommended)
Run:
```bash
python -m vulcanlab.conversions.conv_pdf2md raw\input.pdf -o output\<file>.md --compare -v`
```
* This generates `<file>.style.md` and `<file>.hier.md`

**Choose the better result**
Automated Run runs heuristic to pick the better candidate
```bash
python -m vulcanlab.conversions.style_v_hier__cli output\<file>.style.md output\<file>.hier.md -v
``` 

* Manual: Scroll through both markdown files and manually choose the best one. Rename the `style` or `hier` to just `<file>.md`. Choose the file that better

### Output of Option 1 or 2
* At this point you should have:
    * `<file>.md`
    * `<file>.toc_titles.md` 

* Check to see if the `<file>.toc_titles.md` looks like it corresponds to `<file>.md` -- sometimes it might be empty if or completely off depending on the pdf bookmarks. Remove the file if it doesn't look right. 
* **Note**: The `toc_titles` that gets fed into the `toc` column in th `works` table is currently only used to help improve the hierarchy of the markdown if the conversion doesn't do a good job. Both aren't necessary for any other purpose. 

### 2. Create new Work in DB
This will add ask the user to input the bibliographic information and pull in the `<file>.toc_titles.md` into the `toc` in the DB:

```bash
python -m vulcanlab.conversions.new_work__cli <markdown_file>
```

### 3. Extract ToC from MD **(optional)**
| TODO: Update this section
** Skip step if `<file>.toc_titles.md` looks good, then we can skip this ste

--------------------------------------------

## 3. Sanitization

Now that we have the new work saved in the DB--going forward well be working with the work id of the row to continue the conversion. The file locations associated with this work saved in the DB. 

### Extract Titles (required)

This step is not optional--the `<file>.titles.md` is used in many different areas including the necessary vectorization suggestion steps. It will also be used as a sanity test in the UI. Run:

```bash
python -m vulcanlab.sanitization.extract_titles_cli <work-id-number> -v
```

### Replace Text
**TODO:** Write this and update the method--should be set so that it handles multiple pass-through cycles and the csv should record what has been completed and the pass-through completed. Handle case of ` /uniF____ ` and then ` /uniF___` (note the white spacing)

### Suggest Heading Changes (optional but recommended)

**Suggest heading changes:** This step will use an LLM to try to determine the best possible hierarchy for our markdown document. The hierarchy is important because it will improve chunking and context. 

**Run LIGHT Model**
```bash
python -m vulcanlab.sanitization.suggest_heading_changes_cli <work id>
```

**Run FULL model**
```bash
python -m vulcanlab.sanitization.suggest_heading_changes_cli <work id> --full-llm -v
```

**Output:** `<file>.title_changes.md` -- a list of title changes


    Notes: A few things here--if thee ToC is not present in the DB, this will not run properly. Need to think of a better approach when the ToC is not present as well how to improve this process:
    
    * Pass in some content under each heading until next heading -- perhaps the first 100 words and the last 100 words
    * Update prompt to specifically look for ToC based on the work title.


### Apply Heading Changes

Compare `<file>.titles.md` to the newly generated `<file>.title_changes.md` and do a spot check to ensure that the changes are welcome and appropriate.

If the suggestions seem reasonable and appropriate, you can apply them:
```bash
python -m vulcanlab.sanitization.apply_title_changes_cli <work id> -v
```
## 4. Chunking

Chunking divides out the sanitized document into chunks that are searchable. It does this in multiple steps -- higher level chunks (i.e. chapters) and then into semantic searchable chunks to be vectorized. 

### Suggest Headings to Vectorize (required)

This runs an LLM to call that tries to determine what headings to vectorize. Run:
```bash
python -m vulcanlab.chunking.suggested_chunks_cli <work_id> --full-llm -v
```

If `--full-llm` is not present, it will run the light model. It's recommended to run full. This is an important step. 

### Chunk Headings into DB (required)
This pulls in the the top headings into the DB so that it can be used for the augmentation piece. These won't be vectorized for semantic search but are needed for grouping, etc. 

Run:

```bash
python -m vulcanlab.chunking.chunk_headings_cli <work id> -v
```

### Chunk Content for Vectorization

Run:
```bash
python -m vulcanlab.chunking.content_chunking_cli <work id> -v
```

## 5. Vectorizing

Run:
```bash
 python -m vulcanlab.vectorization.vect_chunks_cli <work_id> -v 
```
________________________________________________________


# Running RAG

## Retrieval

### 1. Query Expansion
Expand query with multi-query expansion (MQE) and hypothetical document embeddings (HyDE). This will add an entry into the the DB with these new queries along with the original. 

**Note**: Full LLM is used

Run:
```bash
python -m vulcanlab.retrieval.query_expansion_cli "What is working memory?" -v
```

### 2. Vectorize Query (query embeddings)

this will be saved to the DB

Run:
```bash
python -m vulcanlab.retrieval.query_embeddings_cli <query id> -v
```

### 3. Retrieval

Pulls out the relevant chunks based on vector embeddings and dense retrieval--saves the output to the DB for augmentation.

Run:
```bash
python -m vulcanlab.retrieval.retrieve_cli <query id> -v
```
## Augmentation and Generation

Some can categorize this under retrieval, but this step includes:
1. consolidation 
2. augmentation and generation

### 1. Consolidation - Grouping retrieved chunks

Consolidates retrieved chunks stored in the DB by grouping under parents and merging adjacent chunks. It makes the context much cleaner and keeps relevant items together. 

Run:
```bash
python -m vulcanlab.augmentation.consolidate_context_cli <query id> -v
```
________________________________________________________

### 2. Augmentation and Generation

Run: 
```bash
python -m vulcanlab.augmentation.augment_cli --query-id <query_id>
```
________________________________________________________
________________________________________________________

