# Expand Answer Feature

For any RAG research result:
* New button on the result to expand the research
* An existing RAG answer is passed in as the first LLM call to do the following:
1. Divide the answer into 3 to 7 logical parts -- either by heading or logical breakdown
2. The prompt should ask the AI to do the following after breaking down into those logical parts; each part should have the following:
    * Own heading
    * Summary of the part
    * A new prompt to generate more information about that specific part
    * Query expansion of the prompt--all the query expansion that occurs on RAG existing
3. Then for each part, we create a prompt to expand each section:
    * Perform RAG to pull relevant sources for each section -- similar flow to existing RAG but using the results of #2 and is not saved in the standard table (it doesn't show up as a typical prompt because each RAG prompt for each section is only to expand the answer)
    * After all the LLM prompts are done for each section (either automatic or manual copy and paste), we combine the answers into one large report -- that is if the answer is divided into 3 parts, we combine the 3 llm RAG returns into one document with the 3 parts
