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
- Use **PostgreSQL-based checkpointer** (custom implementation using research_sessions table)
- Store full state in `state_data` JSONB column
- Enable resume from any node via thread_id
- Support branching for A/B testing approaches
- Time-travel debugging for quality issues
- **Shared storage**: Manual and automated sessions use same tables
- **Thread ID format**:
  - Manual: `manual_{timestamp}_{random}` (e.g., `manual_20260108_143022_a1b2c3`)
  - Automated: `auto_{collection_id}_{timestamp}` (e.g., `auto_5_20260108_143500`)
  - Both formats compatible with LangGraph checkpointer interface

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

### Workflow State Tracking (Database-Backed)

**All state persisted to database** (same as automated flow):

#### Database Schema for Research Sessions

**New Table: `research_sessions`**
```sql
CREATE TABLE research_sessions (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL,  -- 'manual' or 'automated'
    thread_id VARCHAR(255) UNIQUE,       -- For LangGraph compatibility
    current_phase VARCHAR(50),           -- 'planning', 'research', 'synthesis', etc.
    research_plan JSONB,                 -- Step 1 output
    state_data JSONB,                    -- Full ResearchState object
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'in_progress'  -- 'in_progress', 'completed', 'failed'
);

CREATE INDEX idx_research_sessions_collection ON research_sessions(collection_id);
CREATE INDEX idx_research_sessions_thread ON research_sessions(thread_id);
CREATE INDEX idx_research_sessions_status ON research_sessions(status);
```

**New Table: `research_sections`**
```sql
CREATE TABLE research_sections (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES research_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,    -- 'Q1', 'Q2', etc.
    question_text TEXT NOT NULL,
    section_content TEXT,                 -- Generated markdown
    context_data JSONB,                   -- Step 3 output (assembled context)
    matching_results JSONB,               -- Step 2 output (result matching decisions)
    metadata JSONB,                       -- {word_count, citation_count, quality_scores}
    reuse_info JSONB,                     -- {source_result_ids, reuse_type, similarity_scores}
    quality_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'needs_refinement'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_research_sections_session ON research_sections(session_id);
CREATE INDEX idx_research_sections_question ON research_sections(question_id);
```

**New Table: `research_reports`**
```sql
CREATE TABLE research_reports (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES research_sessions(id) ON DELETE CASCADE,
    report_content TEXT NOT NULL,         -- Final markdown report
    executive_summary TEXT,
    quality_evaluation JSONB,             -- Step 6 output
    metadata JSONB,                       -- {total_words, total_citations, sources_used}
    version INTEGER DEFAULT 1,            -- For iterative refinements
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_research_reports_session ON research_reports(session_id);
```

#### Helper Scripts Using Database

**Script 1: Start Manual Research Session**
```bash
# Creates session record and copies collection data
python scripts/start_manual_research.py --collection-id 5
# Output: Session ID: 42, Thread ID: manual_abc123
# Collection data copied to clipboard
```

**Script 2: Save Research Plan**
```bash
# After Step 1, paste JSON into file or stdin
python scripts/save_research_plan.py --session-id 42 --plan plan.json
# Or pipe directly:
pbpaste | python scripts/save_research_plan.py --session-id 42 --stdin
```

**Script 3: Save Section**
```bash
# After Step 4, save section to DB
python scripts/save_section.py --session-id 42 --question-id Q1 \
    --content section_Q1.md \
    --metadata '{"word_count": 1200, "citation_count": 15}'
```

**Script 4: Fetch Context for Sub-Question**
```bash
# Step 3 helper: retrieves excerpts/results based on relevant_items
python scripts/fetch_context.py --session-id 42 --question-id Q1 --copy
# Queries DB, assembles context, copies to clipboard
```

**Script 5: Save Final Report**
```bash
# After Step 5
python scripts/save_report.py --session-id 42 --content final_report.md
```

**Script 6: View Session Progress**
```bash
# Check current state
python scripts/view_research_session.py --session-id 42
# Shows: current phase, completed sections, pending sections
```

#### Workflow Integration

**Step 0: Initialize Session**
```bash
$ python scripts/start_manual_research.py --collection-id 5

Created research session:
  Session ID: 42
  Thread ID: manual_20260108_143022
  Collection: "Schema Therapy Foundations"

Collection data copied to clipboard - paste into LLM chat.
```

**Step 1: Save Plan to Database**
```bash
# User copies LLM response (JSON), then:
$ pbpaste | python scripts/save_research_plan.py --session-id 42 --stdin

Saved research plan to session 42:
  - 5 sub-questions identified
  - Token budgets allocated
  - Status: ready_for_research
```

**Step 2-4: Per Sub-Question (Loop)**
```bash
# For each question Q1, Q2, etc:

# Fetch context (automated)
$ python scripts/fetch_context.py --session-id 42 --question-id Q1 --copy
Context assembled (25,430 tokens) - copied to clipboard.

# User pastes into LLM, gets section back, then:
$ python scripts/save_section.py --session-id 42 --question-id Q1 \
    --content section_Q1.md \
    --auto-metadata  # Extracts word count, citations automatically

Section Q1 saved. Progress: 1/5 sections complete.
```

**Step 5: Generate & Save Final Report**
```bash
# Fetch all sections for synthesis
$ python scripts/fetch_all_sections.py --session-id 42 --copy
All sections copied to clipboard for synthesis prompt.

# After LLM generates final report:
$ python scripts/save_report.py --session-id 42 --content final_report.md --complete-session

Report saved. Session 42 marked as completed.
```

**Step 6: Save Quality Evaluation**
```bash
$ pbpaste | python scripts/save_quality_eval.py --session-id 42 --stdin
Quality evaluation saved to session 42.
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

**Unified Persistence Benefits:**
- **Seamless transition**: Manual sessions stored identically to automated ones
- **Resume capability**: Can resume manual session with automation or vice versa
- **Shared history**: All research sessions (manual/auto) queryable in one place
- **Consistency**: Same data model, same API, same UI for viewing
- **Auditability**: Full provenance tracking regardless of execution mode
- **Collaboration**: Multiple team members can view/continue sessions
- **Learning data**: Manual sessions become training data for automation improvements

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

### Cross-Mode Session Compatibility

**Resume Manual Session with Automation**
```bash
# Start manually, switch to automation midway
$ python scripts/start_manual_research.py --collection-id 5
# Session ID: 42, complete Step 1 manually, then:

$ python scripts/resume_with_automation.py --session-id 42
# LangGraph picks up from current phase, continues automatically
```

**Resume Automated Session Manually**
```bash
# Automated session failed or needs human intervention
$ python scripts/list_sessions.py --status in_progress
# Session 45: auto_5_20260108, Phase: research, 2/5 sections complete

$ python scripts/resume_manual.py --session-id 45 --question-id Q3
# Fetch Q3 context, user completes manually, saves back to same session
```

**View Any Session (Unified Interface)**
```bash
# Same viewing tool for both modes
$ python scripts/view_research_session.py --session-id 42
# Shows: mode (manual/auto), progress, sections, reports

# Query all sessions for a collection
$ python scripts/list_sessions.py --collection-id 5
# Returns both manual and automated sessions
```

**API Endpoints Support Both Modes**
```python
# GET /api/research-sessions/{session_id}
# Returns session data regardless of type

# POST /api/research-sessions/{session_id}/resume
# Can resume with mode="manual" or mode="auto"

# GET /api/collections/{collection_id}/research-sessions
# Lists all sessions (manual + automated)
```

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

### Export Formats
- Markdown (primary)
- PDF (with citations)
- JSON (structured data + metadata)
- Interactive HTML (with source links)

## Implementation Priorities

### Phase 1: Database Schema & Core Infrastructure (Week 1-2)
1. **Create database tables**
   - `research_sessions` table
   - `research_sections` table
   - `research_reports` table
   - Migration scripts for schema deployment

2. **SQLAlchemy models**
   - ResearchSession model
   - ResearchSection model
   - ResearchReport model
   - Relationships and enums

3. **Basic CRUD operations**
   - Create/read/update research sessions
   - Store and retrieve sections
   - Save reports with versioning

### Phase 2: Manual Workflow Scripts (Week 2-3)
1. **Helper script suite**
   - `start_manual_research.py` - Initialize session
   - `save_research_plan.py` - Store planning output
   - `fetch_context.py` - Assemble context for sub-questions
   - `save_section.py` - Store generated sections
   - `fetch_all_sections.py` - Retrieve for synthesis
   - `save_report.py` - Store final report
   - `view_research_session.py` - View session status
   - `list_sessions.py` - Query sessions

2. **Prompt template library**
   - Create reusable `.txt` templates for each step
   - Document variable substitution patterns
   - Include examples in README

3. **Validation & Testing**
   - Test full manual workflow end-to-end
   - Validate data persistence
   - Ensure clipboard integration works

### Phase 3: Result Matching & Reuse Logic (Week 3-4)
1. **Implement result matching**
   - Embedding similarity computation
   - Quality scoring algorithm
   - Decision tree for reuse strategy

2. **Ensemble synthesis support**
   - Multi-result retrieval
   - Consensus extraction logic
   - Contradiction detection

3. **Manual workflow integration**
   - Update `fetch_context.py` to check for existing results
   - Display matching recommendations
   - Support ensemble mode in context assembly

### Phase 4: API Endpoints (Week 4-5)
1. **RESTful API for research sessions**
   - `POST /api/research-sessions` - Create new session
   - `GET /api/research-sessions/{id}` - Get session details
   - `PUT /api/research-sessions/{id}` - Update session
   - `GET /api/collections/{id}/research-sessions` - List sessions
   - `POST /api/research-sessions/{id}/sections` - Save section
   - `GET /api/research-sessions/{id}/report` - Get final report

2. **Web UI components**
   - Session list/detail views
   - Progress tracking display
   - Section editor with preview
   - Report viewer with citations

### Phase 5: LangGraph Automation (Week 6-8)
1. **State graph implementation**
   - Define ResearchState TypedDict
   - Implement 6 workflow nodes
   - Configure conditional edges
   - Set up PostgreSQL checkpointer

2. **Node implementations**
   - Research Planner node
   - Query Executor node (with result reuse)
   - Context Assembler node
   - Synthesizer node
   - Quality Evaluator node
   - Refinement Coordinator node

3. **Checkpointer integration**
   - PostgreSQL-based persistence
   - Thread ID management
   - Resume capability from any node

### Phase 6: Quality & Evaluation (Week 8-9)
1. **Automated quality checks**
   - Citation coverage analyzer
   - Source diversity calculator
   - Coherence scoring
   - Hallucination detection

2. **Quality thresholds**
   - Empirical testing on sample collections
   - Tune thresholds for refinement triggers
   - Document quality patterns

3. **Evaluation harness**
   - Test collections with ground truth
   - Compare with ChatGPT Deep Research
   - Measure quality metrics

### Phase 7: Cross-Mode Compatibility (Week 9-10)
1. **Session resume logic**
   - Resume manual session with automation
   - Resume automated session manually
   - Handle state synchronization

2. **Unified interfaces**
   - Same API for both modes
   - Same viewing tools
   - Same data model

3. **Mode switching scripts**
   - `resume_with_automation.py`
   - `resume_manual.py`

### Phase 8: Production Hardening (Week 10-12)
1. **Error handling**
   - Graceful degradation
   - Retry logic for API failures
   - State recovery on crashes

2. **Performance optimization**
   - Query optimization
   - Caching strategies
   - Parallel processing where applicable

3. **Monitoring & Logging**
   - Progress tracking
   - Performance metrics
   - Error reporting

## Key Risks and Mitigations

### Risk: Token budget explosion
- **Mitigation**: Hard limits per node, pre-filtering sources, adaptive chunking

### Risk: Quality degradation with long context
- **Mitigation**: Test empirically, stay in 20K-40K range, use quality metrics

### Risk: Citation hallucination
- **Mitigation**: Strict source validation, quote extraction verification, automated checks

### Risk: Incoherent synthesis across sections
- **Mitigation**: Pass section summaries in state, coherence scoring, synthesis prompt engineering

### Risk: Over-reliance on low-quality items
- **Mitigation**: Item note weighting, quality scoring of sources, human curation signals

### Risk: Stale result reuse (outdated or incomplete)
- **Mitigation**: Freshness checks, similarity thresholds, source validation, partial match supplementation

### Risk: Missing opportunities for result reuse
- **Mitigation**: Comprehensive embedding-based matching, maintain result index, log reuse decisions

### Risk: Database schema evolution breaking compatibility
- **Mitigation**: Version state_data JSONB, backward-compatible migrations, schema validation

## Success Metrics

### Quantitative
- Research completion time < X minutes
- Citation accuracy > 95%
- Source coverage > 80% of collection items
- Quality score > threshold on all sections
- Token efficiency (insights per 1K tokens)
- Result reuse rate (% sections using existing results)
- Cost savings from reuse (API calls avoided)

### Qualitative
- Human expert rating (compared to manual research)
- Coherence and readability scores
- Novel insights generated (vs. simple summarization)
- User satisfaction with depth and breadth
- Trust in citations and sources

## Next Steps

1. **Design and implement database schema** (research_sessions, research_sections, research_reports)
2. **Build manual workflow helper scripts** with database persistence
3. **Implement result matching and reuse logic**
   - Embedding similarity computation for sub-questions vs. existing results
   - Quality assessment heuristics
   - Reuse decision tree (exact/partial/contextual/ensemble)
4. **Create prompt template library** for all workflow steps
5. **Test end-to-end manual workflow** on sample collection
6. **Benchmark token usage patterns** with sample questions
7. **Develop quality metrics and thresholds** empirically
8. **Build API endpoints** for research sessions
9. **Implement LangGraph automation** with PostgreSQL checkpointer
10. **Enable cross-mode compatibility** (resume manual with auto, vice versa)
11. **Create evaluation harness** with test collections
12. **Measure reuse effectiveness** (time/cost savings vs. quality impact)
13. **Refine based on quality comparisons** with ChatGPT Deep Research