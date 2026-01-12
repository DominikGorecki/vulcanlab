# Collection Deep Research

## Feature Overview
Collection Deep Research is a powerful feature in VulcanLab that allows you to perform comprehensive, academic-quality research across a curated set of items (excerpts, previous research results, and queries). 

Unlike a simple search, Deep Research:
1.  **Analyzes your collection** to understand the research goal and themes.
2.  **Creates a research plan** with multiple targeted sub-questions.
3.  **Assembles context** by deduplicating and consolidating information from your items.
4.  **Synthesizes answers** for each sub-question with full inline citations.
5.  **Evaluates quality** automatically and refines sections if coverage or coherence is low.
6.  **Produces a final report** that integrates all findings into a unified narrative.

## Manual Research Guide (Wizard)
The Manual Research workflow gives you full control over every step of the research process.

### Step 1: Planning
*   **Trigger**: Click "Start Research" on any Collection page.
*   **Action**: The LLM analyzes your collection and suggests a research goal, key themes, and sub-questions.
*   **Customization**: You can edit the goal, add/remove themes, and modify the sub-questions or their token budgets.

### Step 2: Result Matching
*   **Action**: The system checks if any existing research results in your database already answer your sub-questions.
*   **Strategy**: You can choose to reuse a result exactly, use it as a starting point (partial reuse), or generate a new answer from scratch.

### Step 3: Context Assembly
*   **Action**: Review the items selected for each sub-question.
*   **Customization**: You can manually add or remove collection items to ensure the LLM has the exact context it needs.

### Step 4: Section Generation
*   **Action**: The LLM generates a drafted response for each sub-question using the assembled context.
*   **Review**: You can read the drafts and see the inline citations mapped to your sources.

### Step 5: Synthesis
*   **Action**: All sections are synthesized into a final, cohesive report.
*   **Review**: Verify the transitions and overall narrative flow.

### Step 6: Quality Evaluation
*   **Action**: The system provides a quality dashboard showing citation density, source diversity, and coherence scores.
*   **Finish**: Once satisfied, click "Complete" to save the report to your collection.

## Automated Research Guide
Automated research is perfect for quick insights or when you have well-curated collections.

1.  **Trigger**: From the Collection page, select "Automated Research".
2.  **Monitor**: A progress bar will show the current phase (Planning, Researching, Synthesizing, etc.).
3.  **Completion**: Once finished, the report will automatically appear in your collection's "Reports" tab.
4.  **Refinement**: If the system detects low quality in a section, it will automatically perform up to 2 refinement cycles (increasing token budgets or seeking more diverse sources) before finishing.

## Result Reuse
Deep Research is designed to save you time and LLM costs by reusing work you've already done.
*   **Exact Reuse**: If a sub-question is highly similar (>90%) to a previous result of high quality, it is used directly.
*   **Partial Reuse**: Previous results are provided as context to the generator to ensure consistency.
*   **Benefits**: Reduces redundant LLM calls and ensures that improved sections from previous sessions carry forward into new reports.

## Session Resume
Research sessions are long-running and stateful.
*   **Auto-Save**: Every step you complete in the manual wizard is saved to the database.
*   **Pausing**: You can close your browser at any time during Step 1-5.
*   **Resuming**: When you return to the collection page, you will see a "Resume Session" button that takes you exactly back to where you left off.

## Troubleshooting
*   **"No items in collection"**: Ensure you have added at least 3 items (excerpts or results) to your collection before starting.
*   **Low Citation Coverage**: If a report has few citations, try adding more specific notes to your collection items to guide the LLM.
*   **Session Stuck**: If an automated session stays in "Researching" for more than 10 minutes, try refreshing the page. If it persists, the session may have failed; check the error logs.
*   **Recursion Limit**: If you see a recursion error, it means the refinement loop triggered too many times. Try simplifying your sub-questions in Step 1.
