# Title: RAG Query Manual Result & Model Tracking

## Summary

* Remove automatic modal opening after copying prompt on `/rag/[id]` page
* Add explicit "Paste Response" button next to "Copy Prompt" for manual result submission
* Implement model tracking for generated results via new `result_models` table
* Automatically capture model from settings for auto-generated results
* Allow manual model selection (with "Add New" option) when pasting results manually
* Display model information in results list and detail pages
* Create migration script `025_add_model_tracking.sql` and update `init_db.py` for fresh installs

## Problem / Context

* Current UX automatically opens the paste modal after copying the prompt, which is intrusive and doesn't allow users to simply copy without immediately pasting
* No tracking of which LLM model was used to generate each result, making it difficult to compare outputs, audit generations, or analyze model performance
* Users need flexibility to paste results at their convenience rather than being forced into the paste workflow immediately
* Business impact: Poor data tracking for model usage analytics and A/B testing between different models

## Goals

* Separate "copy prompt" and "paste response" actions into distinct, user-initiated steps
* Track which model generated each result for auditing, analytics, and comparison purposes
* Support both automatic model capture (from settings) and manual model selection
* Allow users to easily add new models on-the-fly when pasting manual results
* Maintain backward compatibility with existing results that have no model information

## Non-goals (Strict)

* Model configuration management (temperature, max tokens, etc.) - only track model name
* Model performance analytics or comparison dashboards
* Automatic model detection from pasted responses
* Provider-specific metadata (API keys, endpoints, pricing)
* Refactoring existing results pages beyond adding model display
* Migration of existing results to assign models retroactively

## Scope

### In scope

* Frontend: Modify `/rag/[id]/page.tsx` to change copy/paste button behavior
* Frontend: Add model selection dropdown to paste modal
* Frontend: Implement "Add New Model" inline input in dropdown
* Frontend: Display model name in results list (`/rag/[id]/results/page.tsx`) and detail view (`/rag/[id]/results/[resultId]/page.tsx`)
* Backend: Create `result_models` table to store model names
* Backend: Alter `results` table to add nullable `model_id` foreign key
* Backend: Update Result SQLAlchemy model (`src/vulcanlab/data/models/result.py`)
* Backend: Create ResultModel SQLAlchemy model
* Backend: Modify manual result endpoint to accept and store model selection
* Backend: Modify automatic result endpoint to capture model from app config
* Backend: Create API endpoints for fetching models list and creating new models
* Database: Migration script `025_add_model_tracking.sql`
* Database: Update `init_db.py` to create `result_models` table for fresh installs
* Seeding: Create default "Unspecified" model record during database initialization

### Out of scope

* Editing model information after result creation
* Deleting or archiving models
* Model selection for the automatic "Run" flow (always uses config)
* Historical result model assignment (existing results remain with NULL model_id)
* Provider tracking (OpenAI, Anthropic, etc.)
* Model metadata beyond name

## Requirements (Functional)

* R1: "Copy Prompt" button must copy prompt to clipboard without opening any modal
* R2: "Paste Response" button must be visible at all times next to "Copy Prompt"
* R3: "Paste Response" button must open the paste modal when clicked
* R4: Paste modal must include a model selection dropdown (optional field)
* R5: Model dropdown must include an "Add New..." option that reveals an inline text input
* R6: Adding a new model via inline input must create a new `result_models` record and select it
* R7: Automatic result generation (via "Run") must capture model name from `vulcanlab.config.json`
* R8: Manual result submission must save the selected model_id (or NULL if unspecified)
* R9: Results list page must display model name for each result (show "Unspecified" for NULL)
* R10: Results detail page must display model name
* R11: `result_models` table must store unique model names with auto-incrementing ID
* R12: `results.model_id` must be a nullable foreign key to `result_models.id`
* R13: Migration script must create `result_models` table, alter `results` table, and seed "Unspecified" model
* R14: Fresh database installs via `init_db.py` must create `result_models` table without requiring migrations
* R15: Database must seed a default "Unspecified" model record during initialization

## Requirements (Non-functional)

* Performance:
  * Model dropdown population must load in <200ms
  * Adding a new model inline must complete in <500ms
  * No impact on existing result generation performance

* Reliability:
  * Foreign key constraint must maintain referential integrity
  * Unique constraint on model name must prevent duplicates
  * NULL model_id must be handled gracefully in all UI components

* Security / Privacy:
  * Model names are non-sensitive metadata, no special access controls required
  * Standard SQL injection prevention via parameterized queries

* Observability:
  * Log model selection events for manual result submissions
  * Log model capture from config for automatic results

## Proposed Solution (High-level)

* Frontend changes to `/rag/[id]/page.tsx`:
  * Remove `setCopyDialogOpen(true)` call from `handleCopyPrompt` function
  * Add new "Paste Response" button next to "Copy Prompt" that calls `setCopyDialogOpen(true)`
  * Add model selection dropdown to paste dialog
  * Add "Add New..." option in dropdown with conditional inline input field
  * Implement API calls to fetch models list and create new models

* Backend API additions:
  * `GET /api/v1/rag/result-models` - List all models
  * `POST /api/v1/rag/result-models` - Create new model (accepts `{name: string}`)
  * Modify `POST /api/v1/rag/queries/{id}/augment/manual` to accept optional `model_id` or `new_model_name`
  * Modify `POST /api/v1/rag/queries/{id}/augment/run` to auto-capture model from config and create/fetch model_id

* Database schema:
  * New `result_models` table with columns: `id`, `name` (unique), `created_at`, `updated_at`
  * Alter `results` table to add `model_id INTEGER NULL REFERENCES result_models(id) ON DELETE SET NULL`

* Data flow for automatic generation:
  1. User clicks "Run" → API reads model from `vulcanlab.config.json`
  2. API checks if model exists in `result_models`, creates if not
  3. API generates result and saves with `model_id`

* Data flow for manual paste:
  1. User clicks "Paste Response" → Modal opens with dropdown
  2. Dropdown populated from `GET /api/v1/rag/result-models`
  3. User selects existing model OR selects "Add New..." and types name
  4. On save, API creates model if new, then saves result with `model_id`

## Interfaces / APIs / Contracts

### Frontend → Backend API Endpoints

**1. List Result Models**
```
GET /api/v1/rag/result-models
Response: {
  "models": [
    {"id": 1, "name": "gpt-4", "created_at": "..."},
    {"id": 2, "name": "claude-sonnet-3.5", "created_at": "..."}
  ]
}
```

**2. Create Result Model**
```
POST /api/v1/rag/result-models
Request: {"name": "gpt-4-turbo"}
Response: {
  "id": 3,
  "name": "gpt-4-turbo",
  "created_at": "...",
  "message": "Model created successfully"
}
```

**3. Modified Manual Result Endpoint**
```
POST /api/v1/rag/queries/{id}/augment/manual
Request: {
  "response_text": "The answer is...",
  "model_id": 2,           // optional: existing model ID
  "new_model_name": "gpt-4-turbo"  // optional: create new model
}
Response: {
  "result_id": 123,
  "message": "Response saved successfully",
  "model_name": "gpt-4-turbo"
}
```

**4. Results List Response (Modified)**
```
GET /api/v1/rag/queries/{id}/results
Response: {
  "results": [
    {
      "id": 1,
      "response_text": "...",
      "model_name": "gpt-4",  // NEW: denormalized for display
      "created_at": "..."
    }
  ]
}
```

**5. Result Detail Response (Modified)**
```
GET /api/v1/rag/results/{id}
Response: {
  "id": 1,
  "response_text": "...",
  "model_name": "claude-sonnet-3.5",  // NEW
  "created_at": "...",
  "updated_at": "..."
}
```

## Data Model / Storage

### New Table: `result_models`
```sql
CREATE TABLE result_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

* Index on `name` for unique constraint and lookups
* Trigger for auto-updating `updated_at` timestamp

### Modified Table: `results`
```sql
ALTER TABLE results
ADD COLUMN model_id INTEGER NULL
REFERENCES result_models(id) ON DELETE SET NULL;
```

* Index on `model_id` for join performance: `CREATE INDEX ix_results_model_id ON results(model_id)`

### Seed Data
```sql
INSERT INTO result_models (name, created_at, updated_at)
VALUES ('Unspecified', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;
```

### SQLAlchemy Models

**New Model: `ResultModel`**
```python
class ResultModel(Base):
    __tablename__ = "result_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Modified Model: `Result`**
```python
class Result(Base):
    __tablename__ = "results"

    # ... existing fields ...
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("result_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    # Relationship (optional, for ORM convenience)
    model: Mapped[Optional["ResultModel"]] = relationship("ResultModel")
```

## UX / Workflows

### Workflow 1: Copy Prompt Only
1. User navigates to `/rag/{id}`
2. User clicks "Copy Prompt" button
3. Prompt is copied to clipboard, visual feedback shows "Copied!"
4. No modal opens, user can now paste in external LLM interface

### Workflow 2: Manual Paste with Existing Model
1. User returns to `/rag/{id}` after generating response externally
2. User clicks "Paste Response" button
3. Modal opens with textarea and model dropdown
4. User selects existing model from dropdown (e.g., "gpt-4")
5. User pastes response text into textarea
6. User clicks "Save"
7. API saves result with selected model_id
8. User redirected to result detail page showing model name

### Workflow 3: Manual Paste with New Model
1. User clicks "Paste Response" button
2. Modal opens, user selects "Add New..." from model dropdown
3. Inline text input appears below dropdown
4. User types new model name (e.g., "claude-opus-4")
5. User pastes response text into textarea
6. User clicks "Save"
7. API creates new model record, then saves result
8. User redirected to result detail page

### Workflow 4: Automatic Generation
1. User clicks "Run" button
2. API reads model from `vulcanlab.config.json` (e.g., `llm.model_name`)
3. API checks if model exists in `result_models`, creates if not
4. API generates result and saves with model_id
5. User redirected to result detail page showing model name

### Workflow 5: Viewing Results with Model Info
1. User navigates to `/rag/{id}/results`
2. Results table displays columns: Response Preview, Model, Created At
3. User sees model names (or "Unspecified" for NULL model_id)
4. User clicks on result to view detail page
5. Detail page shows "Model: gpt-4" in metadata section

## Testing Plan

### Unit tests

* `tests/unit/test_result_model_crud.py`:
  * Test creating result model via SQLAlchemy
  * Test unique constraint on model name
  * Test updating result with model_id
  * Test querying results with joined model data

* `tests/unit/test_rag_augment_api.py`:
  * Test manual result endpoint with model_id
  * Test manual result endpoint with new_model_name
  * Test automatic result endpoint captures model from config
  * Test default "Unspecified" model fallback

### Integration tests

* Not required for this ticket (per testing strategy in patterns.md)

### Manual test plan

* **MT1**: Navigate to `/rag/{id}`, click "Copy Prompt", verify clipboard has prompt text, verify no modal opens
* **MT2**: Click "Paste Response" button, verify modal opens with model dropdown
* **MT3**: In paste modal, select existing model from dropdown, paste text, save, verify result is created with correct model_id
* **MT4**: In paste modal, select "Add New...", type new model name, save, verify new model is created and result references it
* **MT5**: Click "Run" button, verify result is created with model from `vulcanlab.config.json`
* **MT6**: Navigate to `/rag/{id}/results`, verify model column shows correct model names
* **MT7**: Click on a result, verify detail page shows model name
* **MT8**: Verify legacy results (NULL model_id) display "Unspecified" in UI
* **MT9**: Run migration `025_add_model_tracking.sql` on existing database, verify no errors
* **MT10**: Run `init_db.py` fresh install, verify `result_models` table exists and "Unspecified" model is seeded

## Acceptance Criteria (Checklist)

* [ ] "Copy Prompt" button copies to clipboard without opening modal
* [ ] "Paste Response" button is visible next to "Copy Prompt" at all times
* [ ] "Paste Response" button opens paste modal with model dropdown
* [ ] Model dropdown lists all existing models from `result_models` table
* [ ] Model dropdown includes "Add New..." option
* [ ] Selecting "Add New..." shows inline text input for model name
* [ ] Saving with new model creates `result_models` record and links to result
* [ ] Automatic "Run" captures model from `vulcanlab.config.json`
* [ ] Results list page displays model name column
* [ ] Results detail page displays model name
* [ ] NULL model_id displays as "Unspecified" in UI
* [ ] Migration script `025_add_model_tracking.sql` creates tables and seeds default model
* [ ] `init_db.py` includes `result_models` table creation for fresh installs
* [ ] Foreign key constraint enforces referential integrity
* [ ] Unique constraint prevents duplicate model names
* [ ] All manual tests pass

## Rollout / Migration Plan

* **Phase 1: Database Migration**
  * Create migration script `025_add_model_tracking.sql`
  * Run migration on development database
  * Verify existing results have NULL model_id
  * Verify "Unspecified" model is seeded

* **Phase 2: Backend Implementation**
  * Create `ResultModel` SQLAlchemy model
  * Update `Result` model with `model_id` field
  * Implement `/api/v1/rag/result-models` endpoints (GET, POST)
  * Modify manual result endpoint to accept model selection
  * Modify automatic result endpoint to capture model from config
  * Update result list/detail endpoints to include model_name

* **Phase 3: Frontend Implementation**
  * Modify `handleCopyPrompt` to remove auto-modal behavior
  * Add "Paste Response" button to action bar
  * Add model dropdown to paste modal
  * Implement "Add New..." inline input logic
  * Update results list table to show model column
  * Update results detail page to show model name

* **Phase 4: Fresh Install Support**
  * Add `create_result_models_table()` function to `init_db.py`
  * Add `seed_default_result_model()` function to `init_db.py`
  * Call both functions in `init_database()` orchestration
  * Test fresh install creates all objects correctly

* **Backward Compatibility**
  * Existing results with NULL model_id remain unchanged
  * UI gracefully handles NULL by displaying "Unspecified"
  * No data migration required for existing results

## Risks and Alternatives

### Risks

* **Risk 1**: Users might forget to select a model when pasting manually
  * Mitigation: Make dropdown optional with clear default ("Unspecified"), low severity

* **Risk 2**: Model name typos when using "Add New..." feature
  * Mitigation: Consider future enhancement for model name validation/autocomplete, accept for MVP

* **Risk 3**: Model from config might not exist in database on first auto-run
  * Mitigation: Auto-create model record if not found (covered in design)

* **Risk 4**: Migration might fail on production due to existing foreign key constraints
  * Mitigation: Use `ADD COLUMN ... NULL` (safe operation), thoroughly test migration script

### Alternatives considered

* **Alternative 1**: Required model selection for all results
  * Rejected: Too strict for backward compatibility and user flexibility

* **Alternative 2**: Store model in `results` table as denormalized string
  * Rejected: Poor normalization, harder to query/filter, model name inconsistencies

* **Alternative 3**: Separate modal for adding new model
  * Rejected: More clicks, worse UX than inline input

* **Alternative 4**: Automatic model detection from response text
  * Rejected: Unreliable, complex, out of scope for MVP

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied

* **Three-tier architecture**: Frontend (Next.js) ↔ API (FastAPI) ↔ Core (SQLAlchemy models)
* **Database ORM**: SQLAlchemy declarative models for `ResultModel` and updated `Result`
* **API Routing**: New endpoints under `/api/v1/rag/` prefix (consistent with existing pattern)
* **Frontend Component Patterns**: Using existing `Dialog`, `Select`, `Button` from Shadcn/Radix
* **Migration Strategy**: SQL-based migration file following existing 001-024 numbering
* **Fresh Install Pattern**: Add table creation to `init_db.py` to mirror migration (consistent with `create_enums`, `create_tables`, `create_vector_indexes`, etc.)
* **Seeding Pattern**: Add seeding function for default model (consistent with `seed_prompt_templates`)

### Deviations (if any)

* None - this spec follows all established patterns for database changes, API additions, and frontend modifications

## Implementation Notes (Non-binding)

* Model name field should use `VARCHAR(200)` to accommodate long model names like "claude-3-opus-20240229"
* Consider adding client-side validation to prevent empty model names in "Add New..." flow
* The "Unspecified" default model should have ID=1 for predictability in tests
* Frontend should debounce model creation API call to prevent double-submissions
* Results list query should use LEFT JOIN to include results with NULL model_id
* Consider adding `updated_at` trigger for `result_models` table (consistent with other tables)
* API should return model_name denormalized in results list response to avoid N+1 queries
* Migration script should grant appropriate permissions to app user (follow pattern from 009_create_results_table.sql)

## Open Questions

* Q1: Should we limit the length of model names in the UI? (e.g., truncate long names with ellipsis)
* Q2: Should we add a "last used model" preference to auto-select in dropdown for faster manual entry?
* Q3: Should we add a counter to show how many results use each model? (for future analytics)
* Q4: What specific path in `vulcanlab.config.json` should be used for model name? (e.g., `llm.model_name` or `generation.model`?)
