# Deep Research Strategy: LangGraph-Based Collection Analysis

## Overview
Strategy for implementing ChatGPT Deep Research-equivalent capability using LangGraph orchestration with collection items (excerpts, research results, research queries) as source material.

## Core Architecture

### LangGraph State Machine Components
- **StateGraph with MemorySaver checkpointer** for persistence and resumability
- **Thread ID-based sessions** for multi-turn research refinement
- **State object** tracking:
  - Collection metadata (description, tags, item notes)
  - Current research phase
  - Generated sub-questions
  - Retrieved context per sub-question
  - Synthesis progress
  - Quality metrics

### Multi-Agent Workflow Nodes
1. **Research Planner**
   - Analyzes collection description and item notes
   - Generates research outline and key questions
   - Breaks down into focused sub-queries (vertical slices)
   - Estimates token budgets per section

2. **Query Executor**
   - For each sub-query, checks for matching research_results first
   - If multiple results match: applies quality scoring and selection strategy
   - Decides: exact reuse, partial reuse, ensemble synthesis, or new generation
   - If new generation needed: retrieves relevant excerpts and queries
   - Prioritizes by item type: research_result > excerpt > research_query
   - Uses item notes as relevance signals
   - Fetches actual content (excerpts from chunks, results from DB)

3. **Context Assembler**
   - Consolidates retrieved items per sub-question
   - Applies token limits (20K-40K optimal window)
   - Deduplicates overlapping content
   - Maintains source attribution

4. **Synthesizer**
   - Generates report sections from context
   - Maintains coherence across sections
   - Integrates citations properly
   - Produces structured markdown output

5. **Quality Evaluator**
   - Checks citation accuracy
   - Validates claims against sources
   - Identifies gaps or weak sections
   - Triggers refinement loops if needed

6. **Refinement Coordinator**
   - Re-plans problematic sections
   - Generates follow-up queries
   - Re-retrieves with adjusted parameters
   - Iterates until quality threshold met

## Token Budget Strategy

### Adaptive Chunking Based on Research Depth
- **High-level overview sections**: 15K-25K tokens
  - Broader context, multiple sources
  - Synthesis-heavy, less detail per source

- **Deep-dive analysis sections**: 30K-40K tokens
  - Focused on specific aspects
  - More direct quotes and detailed analysis
  - Maximum quality threshold

- **Synthesis/conclusion sections**: 10K-20K tokens
  - References previous sections (from state)
  - Integration across findings

### Dynamic Token Allocation
- Monitor LLM performance per section
- Track hallucination indicators
- Adjust token budgets based on section complexity
- Reserve tokens for citations and formatting

## Collection Item Utilization

### Item Type Hierarchy
1. **Research Results** (highest priority)
   - Pre-analyzed content with LLM insights
   - Use as authoritative interpretations
   - Extract claims and sources

2. **Excerpts** (primary sources)
   - Direct chunks from works
   - Use for direct quotes and evidence
   - Leverage heading_breadcrumbs for context
   - Apply enriched_content for better understanding

3. **Research Queries** (context signals)
   - Use to understand research intent
   - Guide sub-question generation
   - Identify focus areas

### Note-Driven Retrieval
- Parse collection.description for overall goals
- Use collection_item.note as retrieval hints
- Weight items with detailed notes higher
- Use notes to generate contextual prompts

### Result Reuse Strategy (Critical Optimization)

**Semantic Matching of Sub-Questions to Existing Results**
- Before generating new research for sub-question, check collection for research_result items
- Use embedding similarity between sub-question and original queries that produced results
- Match threshold: cosine similarity > 0.85 (configurable)
- Consider both query similarity AND source overlap

**Quality Assessment of Existing Results**
- Check result age/freshness (recent = more relevant)
- Validate sources still present in collection
- Evaluate completeness relative to current sub-question
- Check citation density and quality metrics

**Reuse Strategies by Match Quality**

1. **High-quality exact match (similarity > 0.90, complete sources)**
   - Use result as-is for that section
   - Extract and validate citations
   - Include in final report with metadata note
   - Skip generation entirely (major time/cost savings)

2. **Partial match (similarity 0.85-0.90, some sources missing)**
   - Use as base/starting point
   - Supplement with additional retrieval for gaps
   - Regenerate with combined context (old result + new sources)
   - Preserve valid portions, enhance weak areas

3. **Low match or outdated (similarity < 0.85 or quality issues)**
   - Treat as regular collection item (informative context)
   - Use to guide new research direction
   - Don't directly reuse content
   - Generate fresh analysis

**Incremental Research Pattern**
- Collections evolve: new excerpts, queries, results added over time
- Reuse stable sections, regenerate only what needs updating
- Track provenance: which results used which collection state
- Enable "research versioning" with checkpointer thread branches

**Benefits of Result Reuse**
- **Speed**: Skip redundant generation (potentially 50%+ time savings)
- **Consistency**: Maintain coherent analysis across related questions
- **Cost**: Reduce LLM API calls significantly
- **Quality**: Build on previously validated research
- **Iterative refinement**: Collection grows → research quality improves

**State Tracking for Reuse**
```python
state["reused_sections"] = {
    "question_id": {
        "source_result_ids": list[int],  # Can be multiple results
        "reuse_type": "exact" | "partial" | "contextual" | "ensemble",
        "similarity_scores": list[float],
        "original_queries": list[str],
        "timestamp": datetime
    }
}
```

### Handling Multiple Results for Same Query

**Why Multiple Results Exist**
- Different models/prompts used over time
- Iterative refinement attempts
- Different context sets (collection evolved)
- A/B testing of approaches
- Temporal progression of understanding

**Multiple Result Strategies**

1. **Quality-Based Selection (Simple)**
   - Rank all matching results by quality metrics
   - Select highest-quality single result
   - Use quality scoring: citation_density × freshness × completeness
   - **When to use**: Results are significantly different in quality

2. **Ensemble Synthesis (Advanced)**
   - Use multiple high-quality results together
   - LLM synthesizes consistent elements across versions
   - Highlights consensus points (mentioned in multiple results)
   - Flags divergent interpretations for deeper analysis
   - **When to use**: Multiple high-quality results (>0.90 quality each)

3. **Temporal Evolution View (Meta-analysis)**
   - Order results chronologically
   - Show how understanding evolved over time
   - Latest result = current state, earlier = historical context
   - Useful for "what changed" or "progression" questions
   - **When to use**: Collection has evolved significantly, research history matters

4. **Diversity Sampling (Comprehensive)**
   - Select most diverse subset of results (using embedding distance)
   - Ensures different perspectives/angles covered
   - Avoid redundant near-duplicates
   - **When to use**: Many results with overlapping content

**Decision Tree for Multiple Results**

```
Multiple results found for sub-question
  ↓
Calculate quality scores for each
  ↓
Count high-quality results (score > threshold)
  ↓
  0-1 high-quality → Use quality-based selection (or generate new)
  2-3 high-quality → Ensemble synthesis (combine strengths)
  4+ high-quality → Diversity sampling → Ensemble of diverse subset
  ↓
Check temporal spread
  ↓
  >30 days span AND collection evolved → Consider temporal view
  <30 days span → Treat as refinement iterations, use latest
```

**Ensemble Synthesis Prompt Strategy**
```
You have {N} previous research results for this question:

Result 1 (Quality: {score}, Date: {date}):
{content}

Result 2 (Quality: {score}, Date: {date}):
{content}

Synthesize a coherent answer that:
1. Preserves consensus points (agreed across results)
2. Integrates unique insights from each
3. Resolves contradictions (with source verification)
4. Maintains all valid citations
5. Flags any unresolved ambiguities
```

**Quality Scoring for Result Ranking**
- **Citation density**: % of claims with sources (40% weight)
- **Freshness**: Recency penalty: `1.0 - (days_old / 180)` (20% weight)
- **Completeness**: Content length relative to median (15% weight)
- **Source diversity**: Number of unique works cited (15% weight)
- **Model quality**: If model_id tracked, penalize weaker models (10% weight)

**Metadata Tracking for Multiple Results**
```python
{
    "matched_results": [
        {
            "result_id": 123,
            "similarity": 0.94,
            "quality_score": 0.87,
            "created_at": "2025-01-01",
            "citations_count": 12,
            "word_count": 850,
            "model_used": "gpt-4"
        },
        # ... more results
    ],
    "selection_strategy": "ensemble",
    "results_used": [123, 127],  # Which ones were actually used
    "synthesis_type": "consensus_with_unique_insights"
}
```

**Benefits of Ensemble Approach**
- **Robustness**: Less dependent on single generation quality
- **Comprehensiveness**: Captures more aspects of the question
- **Confidence**: Consensus across results = higher reliability
- **Quality improvement**: Best parts of each result combined

**Risks and Mitigations**
- **Risk**: Increased complexity and token usage
  - *Mitigation*: Limit ensemble to 2-3 best results, summarize before synthesis
- **Risk**: Contradictory claims between results
  - *Mitigation*: Source verification, flag contradictions explicitly, re-retrieve if needed
- **Risk**: Redundancy bloat (saying same thing multiple ways)
  - *Mitigation*: Deduplicate consensus points, focus on unique contributions

## Research Orchestration Flow

### Phase 1: Planning (Conditional Edge)
```
Start → Analyze Collection → Generate Research Plan
  ↓
Check if plan approved (human-in-loop option)
  ↓ (approved)
Extract Sub-Questions → Set token budgets
```

### Phase 2: Iterative Research (Loop with Caching)
```
For each sub-question:
  Check for existing research_result match
  ↓
  Match found? → Yes: Evaluate existing result quality
              → No: Proceed to retrieval
  ↓
  Existing quality OK? → Yes: Reuse result, Next question
                     → No: Supplement or regenerate
  ↓
  Retrieve Relevant Items → Assemble Context (with token limit)
  ↓
  Generate Section → Evaluate Quality
  ↓
  Quality OK? → Yes: Save section (as new result), Next question
           → No: Refine query, Re-retrieve
```

### Phase 3: Synthesis
```
All sections complete → Cross-section synthesis
  ↓
Generate introduction/conclusion
  ↓
Integrate citations and references
  ↓
Final quality check
```

### Phase 4: Refinement (Optional Loop)
```
Human review → Identify weak sections
  ↓
Re-plan specific sections → Re-execute with adjusted parameters
  ↓
Merge updates → Final output
```

## Quality Evaluation Criteria

### Automated Quality Checks
- **Citation coverage**: % of claims with sources
- **Source diversity**: Number of unique works referenced
- **Coherence score**: Semantic similarity between sections
- **Completeness**: All sub-questions addressed
- **Token efficiency**: Information density per token used

### Quality Thresholds (Trigger Refinement)
- Citation coverage < 70%
- Source diversity < 3 works for synthesis sections
- Coherence drop > 0.3 between adjacent sections
- Missing sub-questions
- Hallucination detection (claim not in sources)

### Human-in-Loop Checkpoints
- After initial research plan generation
- Before final synthesis (optional review of sections)
- After quality evaluation if scores borderline
- For domain-specific accuracy validation

## LangGraph Implementation Details

### State Schema
```python
class ResearchState(TypedDict):
    collection_id: int
    collection_description: str
    item_notes: list[dict]  # {item_id, note, type}
    research_plan: dict  # {outline, sub_questions, token_budgets}
    current_phase: str
    sections: dict[str, dict]  # {question: {content, sources, quality}}
    context_per_question: dict[str, list]
    reused_sections: dict[str, dict]  # {question_id: {source_result_id, reuse_type, similarity}}
    available_results: list[dict]  # Cache of research_result items from collection
    synthesis: str
    quality_metrics: dict
    refinement_needed: list[str]
    thread_id: str
```

### Checkpointer Configuration
- Use **MemorySaver** or **SqliteSaver** for persistence
- Enable resume from any node
- Support branching for A/B testing approaches
- Time-travel debugging for quality issues

### Conditional Edges
- Quality threshold → Refinement or Continue
- Token budget exceeded → Prioritize sources or Split section
- All sections complete → Synthesis
- Human approval → Continue or Re-plan

## Manual Copy-Paste Workflow (Human-in-the-Loop Alternative)

### Overview
Instead of full automation, conduct research through iterative copy-paste with a single LLM chat session. The chat maintains conversational context while you control each step explicitly.

**Benefits of Manual Flow**
- **Transparency**: See exactly what happens at each stage
- **Control**: Intervene, adjust, or skip steps as needed
- **Debugging**: Identify prompt issues or quality problems immediately
- **Flexibility**: Use any LLM interface (ChatGPT, Claude, etc.)
- **Prototyping**: Test the workflow before building automation
- **Learning**: Understand the research process deeply

### Workflow Structure

Each step produces:
1. **Structured output** (JSON or markdown)
2. **Next prompt template** with placeholders for previous output
3. **Quality checkpoint** (human reviews before continuing)

### Step-by-Step Manual Process

#### **Step 0: Collection Preparation**
```
System prepares and copies to clipboard:

COLLECTION OVERVIEW
===================
Collection ID: {id}
Name: {name}
Description: {description}
Tags: {tags}

ITEMS SUMMARY
=============
Total items: {count}
- Research Results: {count} items
- Excerpts: {count} items
- Research Queries: {count} items

ITEM DETAILS
============
[For each item:]
- ID: {item_id}
- Type: {item_type}
- Note: {note or "No note"}
- Link: {link}
- Date Added: {date_added}

[For research_result items, include preview:]
  Preview: {first 200 chars of result content}

[For excerpt items, include preview:]
  Preview: {first 200 chars of chunk content}
  Work: {work_title} ({authors}, {year})
```

**User action**: Paste into new chat session

---

#### **Step 1: Research Planning**
```
PROMPT TEMPLATE (User pastes this after Step 0):

You are a research synthesist. Based on the collection above, create a comprehensive research plan.

OUTPUT FORMAT (JSON):
{
  "research_goal": "One sentence summary of what this research aims to answer",
  "key_themes": ["theme1", "theme2", ...],
  "sub_questions": [
    {
      "id": "Q1",
      "question": "Specific research question",
      "rationale": "Why this question matters",
      "estimated_tokens": 25000,
      "relevant_items": [item_id, item_id, ...]
    },
    ...
  ],
  "synthesis_approach": "How to integrate findings across questions"
}

REQUIREMENTS:
- Generate 3-7 focused sub-questions
- Each sub-question should be answerable in 20K-40K tokens
- Identify which collection items are relevant to each question
- Consider collection description and item notes as guidance
```

**User action**: Copy LLM response (JSON), save locally

---

#### **Step 2: Result Matching (Per Sub-Question)**
```
PROMPT TEMPLATE (User customizes with Q1 details):

Check if existing research results match this sub-question:

SUB-QUESTION: {question from Q1}

AVAILABLE RESEARCH RESULTS IN COLLECTION:
[Paste research_result items with previews from Step 0]

TASK:
1. Calculate semantic similarity between sub-question and each result's original query
2. Assess quality of matching results (citation density, freshness, completeness)
3. Recommend reuse strategy

OUTPUT FORMAT (JSON):
{
  "sub_question_id": "Q1",
  "matching_results": [
    {
      "result_id": 123,
      "similarity_estimate": "high|medium|low",
      "quality_assessment": "Explain quality (citations, date, completeness)",
      "recommendation": "exact_reuse|partial_reuse|supplement|generate_new"
    },
    ...
  ],
  "recommended_strategy": "exact|partial|ensemble|new_generation",
  "results_to_use": [result_ids if reusing],
  "rationale": "Explain recommendation"
}
```

**User action**:
- Copy LLM response
- If "exact_reuse": Skip to Step 5 (section already done)
- If "ensemble": Copy full content of results_to_use for Step 3
- If "new_generation": Proceed to Step 3 with context assembly

---

#### **Step 3: Context Assembly**
```
PROMPT TEMPLATE:

Assemble context for answering this sub-question:

SUB-QUESTION: {question from Q1}

STRATEGY: {from Step 2: new_generation or ensemble}

[If new_generation:]
RELEVANT EXCERPTS:
[User queries DB/API for excerpts matching relevant_items from Q1]
[Pastes enriched_content, work metadata, citations]

[If ensemble:]
EXISTING RESULTS TO SYNTHESIZE:
Result 1 (Quality: X, Date: Y):
{full content}

Result 2 (Quality: X, Date: Y):
{full content}

TASK:
Prepare final context for synthesis, staying within 35K token budget.

OUTPUT:
Return the assembled context with:
- Source attribution for each piece
- Organization by theme/topic
- Total estimated tokens
- Quality notes (gaps, overlaps, strengths)

[If ensemble: Also extract consensus points and unique insights]
```

**User action**: Copy context assembly output

---

#### **Step 4: Section Generation**
```
PROMPT TEMPLATE:

Generate a comprehensive research section answering this question.

SUB-QUESTION: {question from Q1}

CONTEXT:
{Pasted from Step 3}

REQUIREMENTS:
- Synthesize insights from all sources
- Maintain precise citations [Author Year, pp. line_start-line_end]
- Identify consensus vs. divergent views
- Note any gaps or limitations
- Use clear markdown structure with headings
- Target: 800-1500 words

[If ensemble mode:]
- Preserve consensus points (mentioned in multiple results)
- Integrate unique insights from each result
- Resolve contradictions with source verification
- Flag unresolved ambiguities

OUTPUT FORMAT (Markdown with embedded metadata):
---
question_id: Q1
sources_cited: [list of work IDs or result IDs]
word_count: X
citation_count: Y
---

# {Section Title}

{Content with inline citations}

## Sources Used
- [Author Year] - {work_title}
- ...

## Quality Notes
- Confidence: high|medium|low
- Gaps: {any unanswered aspects}
- Limitations: {source or coverage limitations}
```

**User action**:
- Copy section markdown
- Save to file (e.g., `section_Q1.md`)
- Review quality
- If quality issues: Regenerate with adjusted prompt
- If acceptable: Proceed to next sub-question (back to Step 2)

---

#### **Step 5: Cross-Section Synthesis**
```
PROMPT TEMPLATE (After all sections complete):

Synthesize findings across all research sections.

SECTIONS:
{Paste all section markdown files concatenated}

ORIGINAL RESEARCH GOAL:
{From Step 1 research_goal}

TASK:
Create final research report with:
1. Executive Summary (200-300 words)
2. Introduction (context and research questions)
3. {Integrate sections Q1-QN}
4. Cross-Cutting Insights (themes across sections)
5. Limitations and Gaps
6. Conclusions and Implications
7. Complete References

OUTPUT: Full markdown report
```

**User action**:
- Copy final report
- Save as `final_report.md`
- Review for coherence

---

#### **Step 6: Quality Evaluation (Optional)**
```
PROMPT TEMPLATE:

Evaluate the quality of this research report.

REPORT:
{Paste final_report.md}

EVALUATION CRITERIA:
1. Citation accuracy (all claims sourced?)
2. Source diversity (multiple works cited?)
3. Coherence (sections flow logically?)
4. Completeness (all sub-questions addressed?)
5. Depth (beyond surface-level synthesis?)
6. Limitations acknowledged?

OUTPUT FORMAT (JSON):
{
  "citation_coverage": 0.0-1.0,
  "source_diversity": X unique works,
  "coherence_score": "high|medium|low",
  "completeness_score": "high|medium|low",
  "depth_assessment": "Evaluation...",
  "identified_gaps": ["gap1", "gap2"],
  "recommended_improvements": ["improvement1", ...]
}
```

**User action**: Review evaluation, decide if refinement needed

---

### Workflow State Tracking

**User maintains local files:**
```
research_session_001/
├── 0_collection_data.txt          # Step 0 output
├── 1_research_plan.json           # Step 1 output
├── 2_Q1_matching.json             # Step 2 per question
├── 2_Q2_matching.json
├── 3_Q1_context.md                # Step 3 per question
├── 3_Q2_context.md
├── 4_section_Q1.md                # Step 4 per question
├── 4_section_Q2.md
├── 5_final_report.md              # Step 5 output
├── 6_quality_eval.json            # Step 6 output (optional)
└── chat_session_url.txt           # Link to LLM chat for reference
```

### Prompt Templates Library

**Store reusable templates:**
```
prompts/
├── 01_planning.txt
├── 02_result_matching.txt
├── 03_context_assembly_new.txt
├── 03_context_assembly_ensemble.txt
├── 04_section_generation.txt
├── 04_section_generation_ensemble.txt
├── 05_synthesis.txt
├── 06_quality_eval.txt
└── README.md  # Usage instructions
```

### Helper Scripts for Manual Workflow

**Script 1: Prepare Collection Data (Step 0)**
```bash
# Fetches collection data and formats for clipboard
python scripts/prepare_collection_context.py --collection-id 5 --copy
```

**Script 2: Extract Sub-Question Context (Step 3)**
```bash
# Fetches excerpts/results for specific items
python scripts/fetch_items.py --items 12,15,18 --format markdown --copy
```

**Script 3: Validate Citations (Post-generation)**
```bash
# Checks that all citations in report match collection sources
python scripts/validate_citations.py --report final_report.md --collection-id 5
```

### Advantages of Manual Workflow

**Development Phase:**
- Test prompt effectiveness quickly
- Iterate on prompt wording
- Discover edge cases
- Build intuition for automation

**Production Use Cases:**
- High-stakes research (need human oversight)
- Exploratory research (requirements unclear)
- Small collections (automation overhead not worth it)
- Teaching/learning the research process

**Quality Control:**
- Catch errors before they propagate
- Adjust strategy mid-stream
- Add domain expertise at each step
- Verify source accuracy manually

### Hybrid Approach: Semi-Automated

**Automated:** Steps 0, 2, 3 (data fetching, matching, context assembly)
**Manual:** Steps 1, 4, 5 (planning, generation, synthesis)

This combines speed with control—automation handles tedious data work, human handles creative synthesis.

### Transition to Full Automation

Once manual workflow is validated:
1. Capture successful prompt patterns
2. Identify quality thresholds empirically
3. Automate decision logic (result matching, token budgets)
4. Implement as LangGraph nodes
5. Keep manual override capability for exceptions

**Progressive automation stages:**
- **Stage 1**: Manual with helper scripts (current)
- **Stage 2**: Semi-automated (data fetch + context assembly automated)
- **Stage 3**: Supervised automation (runs automatically, human approves at checkpoints)
- **Stage 4**: Full automation (LangGraph with human monitoring)

## Advanced Features

### Multi-Prompt Strategy
1. **Planning prompts**: Broad, strategic thinking
2. **Retrieval prompts**: Specific, targeted extraction
3. **Synthesis prompts**: Integration, coherence focus
4. **Evaluation prompts**: Critical analysis, gap detection

### Source Attribution System
- Track provenance: collection_item → excerpt/result → chunk_id
- Generate citations: [Author Year, pp. start_line-end_line]
- Build bibliography from work metadata
- Link back to original items for verification

### Comparison with ChatGPT Deep Research

#### Advantages of Collection-Based Approach
- **Pre-curated sources**: Higher signal-to-noise ratio
- **Domain expertise**: Item notes encode expert guidance
- **Reproducibility**: Same collection → consistent results
- **Transparency**: Full source lineage
- **Iterative refinement**: Build on previous research results

#### Achieving Parity/Superiority
- **Depth**: Use 30K-40K token windows strategically
- **Breadth**: Leverage diverse item types in collection
- **Quality**: Multi-phase evaluation and refinement
- **Citations**: Precise source attribution vs. generic web links
- **Customization**: Collection structure guides research direction

## Token Window Optimization

### Why 20K-40K is Optimal
- Sufficient context for nuanced analysis
- Below degradation threshold for most frontier models
- Allows multiple sources per question
- Room for examples and quotes
- Maintains response quality and coherence

### Strategies to Stay in Range
- Prioritize enriched_content over raw chunks
- Use excerpt excerpts (most relevant portions)
- Summarize lengthy research results
- Deduplicate redundant sources
- Focus on high-relevance items per sub-question

### When to Split
- Complex multi-part questions → 2-3 sub-questions
- Token budget would exceed 45K
- Source diversity too low (need more retrieval)
- Quality metrics indicate information overload

## Deliverables and Outputs

### Report Structure
1. **Executive Summary** (generated last, from state)
2. **Research Questions** (from plan)
3. **Methodology** (collection description, item types used)
4. **Findings** (per sub-question sections)
5. **Synthesis** (cross-cutting insights)
6. **Limitations** (identified during quality eval)
7. **References** (from source attribution)

### Metadata Tracking
- Time per phase
- Token usage per section
- Quality scores progression
- Refinement iterations
- Sources utilized vs. available