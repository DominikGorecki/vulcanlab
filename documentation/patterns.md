# VulcanLab Architecture & Patterns

This document defines the architectural standards, design patterns, and implementation guidelines for the VulcanLab project. It serves as the source of truth for both human developers and AI assistants to ensure consistency, maintainability, and scalability.

> [!NOTE]
> **Living Document**: This is a living document. The codebase currently contains legacy patterns that may deviate from these standards (particularly in routing and error handling).
>
> **Actionable Rule**: **New implementations MUST follow the standards defined below.**
> Refactoring existing code to match these standards should be done opportunistically but carefully to avoid breaking changes.

## 1. High-Level Architecture

VulcanLab follows a decoupled, three-tier architecture designed for modularity and scalability:

1.  **Frontend**: Next.js (React/TypeScript) application located in `vulcanlab_ui`.
2.  **API Layer**: FastAPI application located in `src/vulcanlab_api`.
3.  **Core Module**: Pure Python library located in `src/vulcanlab`.

### Data Flow
`Frontend (Next.js)` <--> `API Layer (FastAPI)` <--> `Core Module (Logic)` <--> `Database (PostgreSQL)`

---

## 2. Core Module (`src/vulcanlab`)

**Purpose**: Encapsulate all business logic, data models, and complex processing (RAG, Chunking, etc.).
**Critical Constraint**: This module **MUST** remain independent of framework-specific code (e.g., no FastAPI imports, no HTTP request objects). This ensures the core logic can be used in CLI tools or other interfaces without the web server overhead.

### Structure
-   `config/`: JSON-based application configuration.
-   `data/`: Database models (SQLAlchemy) and access patterns.
-   `utils/`: Shared utilities (file I/O, compression, hashing).
-   `[domain]/`: Feature-specific logic (e.g., `simple_conversion`, `rag`, `chunking`).

### Database Patterns
-   **ORM**: Use SQLAlchemy declarative models defined in `src/vulcanlab/data/models`.
-   **Session Management**: Database sessions should be passed explicitly to functions as arguments.
    -   *Anti-Pattern*: Creating a new session inside a core logic function.
    -   *Standard*: `def process_data(work_id: int, session: Session): ...`

#### Enum Value Capitalization (CRITICAL)
> **CRITICAL RULE**: Python enum values MUST exactly match database CHECK constraint values (typically lowercase).

**Context**: SQLAlchemy enums map Python Enum classes to database VARCHAR columns. The database enforces values through CHECK constraints, not PostgreSQL enum types.

**Pattern**:
```python
# Python Enum Definition (src/vulcanlab/data/models/enums.py)
class SessionType(str, enum.Enum):
    """
    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (session_type IN ('manual', 'automated'))
    """
    MANUAL = 'manual'      # Python constant is UPPERCASE
    AUTOMATED = 'automated'  # But value is lowercase to match DB

# Database Schema (migrations/*.sql or schema/specialized_tables.py)
CREATE TABLE research_sessions (
    session_type VARCHAR(20) NOT NULL,
    CONSTRAINT chk_session_type CHECK (session_type IN ('manual', 'automated'))
);
```

**Why This Matters**:
- Database CHECK constraints enforce exact value matches (case-sensitive)
- Python enum constant names (e.g., `MANUAL`) can be any case, but values (e.g., `'manual'`) must match DB
- Mismatches cause runtime failures when inserting/updating records

**Verification Checklist** (when adding new enums):
1. ✅ Check migration file for CHECK constraint values
2. ✅ Verify `schema/specialized_tables.py` matches migration
3. ✅ Document expected values in Python enum docstring
4. ✅ Use lowercase values unless DB explicitly uses uppercase
5. ✅ Import new models in `src/vulcanlab/data/init_db.py`

**Example Enum Documentation**:
```python
class SessionStatus(str, enum.Enum):
    """
    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (status IN ('in_progress', 'completed', 'failed', 'paused'))
    See: migrations/028_add_research_tables.sql and schema/specialized_tables.py
    """
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PAUSED = 'paused'
```

### Prompt Templates (CRITICAL)
> **CRITICAL RULE**: Prompt templates are stored in the database and MUST be editable via the Settings > Templates UI. Templates are NEVER read from the filesystem at runtime.
#### Architecture Overview

```
Seeding (one-time):     .txt files + templates.yaml  -->  prompt_templates table
Runtime (always):       Core module  -->  prompt_templates table (via get_active_template)
User editing:           Settings UI  -->  prompt_templates table (via API)
```

#### The Two-Phase Pattern

**Phase 1: Seeding (Database Initialization)**
- Templates are seeded from `.txt` files + `templates.yaml` during `init_db`
- This is a ONE-TIME operation to populate initial template content
- Files: `src/vulcanlab/data/seed_data/templates/*.txt`
- Config: `src/vulcanlab/data/seed_data/templates.yaml`

**Phase 2: Runtime (Application Usage)**
- Templates are ALWAYS read from the `prompt_templates` database table
- Use `get_active_template(function_tag, session)` to query the active version
- Users can edit templates via Settings > Templates UI
- Core module code NEVER reads from filesystem for templates

#### Adding New Prompt Templates (Checklist)

1. **Create the template file**: `src/vulcanlab/data/seed_data/templates/{function_tag}.txt`
2. **Add metadata to templates.yaml**:
   ```yaml
   - function_tag: my_new_template
     version: 1
     title: "Human-Readable Title"
     template_type: feature_area  # e.g., summarize, research, eval
     is_active: true
     content_file: my_new_template.txt
   ```
3. **Add variable documentation to variables.yaml** (for prompt_meta table):
   ```yaml
   - function_tag: my_new_template
     variables:
       - variable_name: input_text
         variable_description: "The text to process"
   ```
4. **Update FUNCTION_LABELS in UI** (both files):
   - `vulcanlab_ui/src/components/settings/templates-tab.tsx`
   - `vulcanlab_ui/src/app/settings/templates/[function_tag]/page.tsx`
5. **In core module code, load from database**:
   ```python
   def get_active_template(function_tag: str, session: Session) -> str:
       template = session.query(PromptTemplate).filter(
           PromptTemplate.function_tag == function_tag,
           PromptTemplate.is_active == True
       ).first()
       if not template:
           raise ValueError(f"No active template for {function_tag}")
       return template.template_content
   ```
6. **Run seeding**: `python -m vulcanlab.data.init_db -v`
7. **Verify in UI**: Navigate to Settings > Templates and confirm template appears

#### Common Mistakes to Avoid

- **WRONG**: Reading template from filesystem at runtime
  ```python
  # NEVER DO THIS
  with open("templates/my_template.txt") as f:
      template = f.read()
  ```
- **RIGHT**: Reading template from database
  ```python
  # ALWAYS DO THIS
  template = get_active_template("my_template", session)
  ```

- **WRONG**: Hardcoding template content in Python code
- **RIGHT**: Storing in database, editable via UI

- **WRONG**: Forgetting to add FUNCTION_LABELS (template shows as raw function_tag in UI)
- **RIGHT**: Adding human-readable labels to both UI files

#### Template Type Categories

Use `template_type` to group templates in the UI:
- `null` - General/legacy templates
- `eval` - Evaluation templates
- `research` - Research session templates
- `summarize` - Summarization templates

**Testing**: Use `python scripts/test_template_seeding.py` to validate configuration before initialization.

For complete documentation, see: [`src/vulcanlab/data/seed_data/README.md`](../src/vulcanlab/data/seed_data/README.md)

---

## 3. API Layer (`src/vulcanlab_api`)

**Purpose**: Provide the HTTP interface, request validation, authentication, and response formatting.
**Constraint**: This layer should be "thin". It should orchestrate calls to the Core Module rather than implementing business logic directly.

### Standards

#### 3.1 Routing (API Versioning)
> **Status**: Inconsistent in legacy code.
> **Standard**: All NEW API routes must be prefixed with `/api/v1`.

-   **Implementation**: Define the prefix in `main.py` when including the router, not hardcoded in the individual router file.
    ```python
    # correct in main.py
    app.include_router(new_router, prefix="/api/v1/resource")
    ```
-   **Structure**: Group routers by domain in `src/vulcanlab_api/routers/`.

#### 3.2 Error Handling
> **Status**: Inconsistent (some explicit try/except, some global).
> **Standard**: Use Global Exception Handlers / Middleware.

-   **Guideline**: Avoid wrapping every endpoint function in a generic `try/except Exception` block.
-   **Practice**:
    -   Raise specific, meaningful exceptions (e.g., `ValueError`, `FileNotFoundError`) or `HTTPException` directly when a logical error occurs.
    -   Allow the global exception handler to catch unhandled 500 errors and log them appropriately.
    -   *Exception*: Use `try/except` only when you can specifically recover from the error or need to rollback a transaction explicitly before re-raising.

#### 3.3 Configuration (Dual System)
> **Status**: Intentional Design.
> **Standard**: Maintain strict separation between App Config and API Config.

1.  **App Config** (`vulcanlab.config`):
    -   **Source**: `vulcanlab.config.json`.
    -   **Scope**: Controls behavior of the core logic (file paths, LLM model selection, prompting strategies).
    -   **Access**: via `vulcanlab.config.load_config()`.

2.  **API Config** (`vulcanlab_api.config`):
    -   **Source**: Environment variables (`.env`).
    -   **Scope**: Controls infrastructure and server settings (Host, Port, CORS, API Key injection).
    -   **Access**: via `vulcanlab_api.config.get_settings()`.
    -   *Reasoning*: Keeps the Core module dependency-free from `pydantic-settings` and environment contexts, making it portable.

---

## 4. Frontend (`vulcanlab_ui`)

**Stack**: Next.js 15+, TypeScript, TailwindCSS v4, Radix UI.

### 4.1 Development Standards
-   **Router**: Use the **App Router** (`src/app`).
-   **Styling**: Use **TailwindCSS** for utility classes. Avoid CSS Modules.
-   **Components**: Use **Shadcn/Radix** patterns for interactive UI elements.
    - Base primitives (Button, Card, Input) are in `vulcanlab_ui/src/components/ui/`.
    - Business-logic-aware or pattern-standardized components are in `vulcanlab_ui/src/components/`.
-   **Forms**: Use **react-hook-form** with the `FormField` wrapper for all user input.
-   **State Management**:
    -   Prefer **React Server Components (RSC)** for initial data fetching where interactivity is not required.
    -   Use **Client Components** (`"use client"`) for pages requiring state (forms, tables, real-time updates).
-   **Critical Rule: Avoid Infinite Rendering Loops**:
    -   **ALWAYS** wrap fetch functions or complex objects in `useCallback` or `useMemo` when passed as dependencies to hooks (like `usePageData` or `useEffect`).
    -   *Reason*: Inline functions are recreated on every render. If a hook uses that function as a dependency to trigger an update, it will cause an infinite rendering loop.

### 4.2 UI Building Patterns
For detailed component documentation and code examples, refer to: `documentation/work/ui-component-library-guide.md`.

#### 1. Page Lifecycle Pattern
All data-driven pages MUST follow the standardized fetching lifecycle using the `usePageData` hook and layout components. **Ensure fetch functions are memoized with `useCallback` to avoid infinite loops.**

```tsx
function MyPage() {
  const fetchFn = useCallback(async () => {
    const response = await fetch('/api/data');
    return response.json();
  }, []); // Add dependencies if needed

  const { data, loading, error, refetch } = usePageData(fetchFn);

  // 1. Loading State
  if (loading) return <PageLoadingState title="Loading data..." />;

  // 2. Error State
  if (error) return <PageErrorState error={error} onRetry={refetch} />;

  // 3. Empty State (optional but recommended)
  if (!data || data.length === 0) return <EmptyState title="No items found" />;

  // 4. Data State
  return <DataTable data={data} columns={columns} />;
}
```

#### 2. Component Composition Rules
- **Props-In, Events-Out**: Components should be "pure" UI implementations that receive data via props and communicate via callbacks.
- **Composition over Inheritance**: Build complex views by composing smaller, standardized components.
- **Theme Awareness**: All UI code MUST be theme-aware (dark/light mode) by using Tailwind's semantic classes (e.g., `text-foreground`, `bg-card`).

#### 3. Standard Layout Hierarchy
- **List/Dashboard Pages**: Start with `PageHeader` + `StatsCardGrid` (if metrics available) + `DataTable`.
- **Detail Pages**: Start with `StickyDetailHeader` + Content Cards.
- **Modals/Dialogs**: Avoid inline `useState` for dialogs; use the `useModal` hook and `ConfirmDialog` for destructive actions.

### 4.3 Component Library Reference
| Pattern | Shared Component | Hook |
| :--- | :--- | :--- |
| **Data Fetching** | `PageLoadingState`, `PageErrorState` | `usePageData` |
| **Tabular Data** | `DataTable`, `StatusBadge` | `useTable` (internal) |
| **Navigation** | `PageHeader`, `StickyDetailHeader` | — |
| **User Input** | `FormField`, `ConfirmDialog` | `useModal`, `react-hook-form` |
| **Metrics** | `StatsCard`, `StatsCardGrid` | — |
| **Misc** | `EmptyState` | — |

---

## 5. Infrastructure

-   **Docker**: Implementation in `docker/`.
    -   **Multi-stage Builds**:
        1.  `base`: System dependencies (AGE, simple necessities).
        2.  `python-deps`: Virtualenv creation.
        3.  `frontend-build`: Next.js standalone build.
        4.  `final`: Slim runtime image copying artifacts from previous stages.
-   **Database**: PostgreSQL 16+.
    -   **Required Extensions**:
        -   `pgvector`: For vector similarity search.
        -   `age`: For Apache AGE graph database functionality.
    -   **Migration**: SQL-based migrations in `migrations/` directory (see Migration Patterns below).

### 5.1 Database Initialization Module Structure
> **Standard**: Database initialization logic must be organized into focused modules.

The `src/vulcanlab/data/` directory follows a modular structure to keep initialization logic maintainable:

```
src/vulcanlab/data/
├── init_db.py                          # Orchestration only (~100 lines max)
├── database_setup.py                   # Database/user creation, extensions
├── schema/
│   ├── __init__.py
│   ├── enums.py                        # PostgreSQL enum types
│   ├── tables.py                       # SQLAlchemy ORM table creation
│   ├── indexes.py                      # Vector, fulltext, history indexes
│   ├── triggers.py                     # Timestamp triggers and helpers
│   └── specialized_tables.py           # Feature-specific tables (research, collections)
├── seeding/
│   ├── __init__.py
│   ├── prompt_templates.py             # Template seeding from YAML/files
│   └── defaults.py                     # Default data (result models, RAG config)
└── seed_data/
    ├── templates.yaml
    ├── variables.yaml
    └── templates/*.txt
```

**Rules for new database initialization functions:**
1. **Keep init_db.py thin**: Only orchestration logic (`init_database()`) and CLI (`main()`)
2. **Group by responsibility**: Enums, tables, indexes, triggers, and seeding go in their respective modules
3. **Use shared helpers**: Extract common patterns (ownership transfer, trigger creation) into reusable functions
4. **Document dependencies**: Each function should document which tables/objects it depends on

**Shared Helper Patterns** (in `schema/triggers.py`):
```python
def transfer_function_ownership(conn, function_names: list[str], app_user: str, verbose: bool = False):
    """Transfer ownership of PostgreSQL functions to app user."""
    for func_name in function_names:
        conn.execute(text(f'ALTER FUNCTION {func_name}() OWNER TO "{app_user}"'))

def create_timestamp_trigger(conn, table_name: str, column_name: str = "updated_at"):
    """Create standard updated_at trigger for a table."""
    func_name = f"update_{table_name}_{column_name}"
    trigger_name = f"trigger_{func_name}"
    # ... implementation
```

### 5.2 Schema Changes & Migration Patterns
> **Standard**: All schema changes are made in `init_db.py` modules. The init script is idempotent and safe to run on existing databases.

#### Single-Source-of-Truth Approach

**The `init_db.py` script is the ONLY place where schema is defined.** It handles both fresh installs AND existing database updates through idempotent SQL patterns.

**Key Principle**: `init_db.py` must NEVER be destructive. All statements must use idempotent patterns:
-   `CREATE TABLE IF NOT EXISTS`
-   `CREATE INDEX IF NOT EXISTS`
-   `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
-   `CREATE OR REPLACE FUNCTION`
-   `DROP TRIGGER IF EXISTS` followed by `CREATE TRIGGER`

#### When Schema Changes Are Needed

When adding new tables, columns, indexes, or other schema elements:

1. **Update the appropriate module** in `src/vulcanlab/data/schema/` or `src/vulcanlab/data/seeding/`
2. **Update the SQLAlchemy model** in `src/vulcanlab/data/models/` if applicable
3. **Notify the user**: After making schema changes, inform the user to run:
   ```bash
   python -m vulcanlab.data.init_db -v
   ```

> **AI Assistant Rule**: When implementing features that require database schema changes, ALWAYS notify the user at the end of implementation that they need to run `python -m vulcanlab.data.init_db -v` to apply the changes.

#### Adding New Columns to Existing Tables

Use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` pattern in the schema module:

```python
# In specialized_tables.py or appropriate schema module
conn.execute(text("""
    ALTER TABLE my_table ADD COLUMN IF NOT EXISTS new_column INTEGER
"""))
conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_my_table_new_column ON my_table(new_column)
"""))
```

#### When Migration Scripts ARE Needed

Migration scripts (`migrations/*.sql` or `migrations/*.py`) are **only required for data backfills** - operations that need to transform or populate existing data based on business logic.

**Examples requiring migration scripts:**
-   Populating a new column with computed values from existing data
-   Transforming data formats (e.g., splitting a column into multiple columns)
-   One-time data cleanup or corrections

**Migration File Naming**: `NNN_backfill_description.sql` or `NNN_backfill_description.py`

**Example backfill migration:**
```sql
-- migrations/033_backfill_word_counts.sql
-- Backfill word_count for existing chunks that have NULL values
UPDATE chunks
SET word_count = array_length(regexp_split_to_array(content, '\s+'), 1)
WHERE word_count IS NULL;
```

#### Summary: Schema Change Checklist

1. ✅ Update schema module (`schema/*.py`) with idempotent SQL
2. ✅ Update SQLAlchemy model (`models/*.py`) if applicable
3. ✅ If data backfill needed, create `migrations/NNN_backfill_*.sql` or `.py`
4. ✅ Notify user to run: `python -m vulcanlab.data.init_db -v`
5. ✅ If backfill exists, notify user to also run the backfill script

---

## 6. Testing Strategy

-   **Location**: `tests/`
-   **Unit Tests (`tests/unit`)**:
    -   **Strict Isolation**: Unit tests must NOT connect to a real database.
    -   **Mocking**: Use `unittest.mock` or `pytest-mock` to mock DB sessions and external API calls (LLMs).
-   **Integration Tests**:
    -   Allowed to spin up Docker containers or connect to a test database--not from the `vulcanlab.config.json` configuration file.
    -   Don't implement in ticket unless explicitly requested.

## 7. Development Workflow

1.  **New Features**:
    -   Define the Core logic first in `src/vulcanlab`.
    -   Write unit tests for the Core logic.
    -   Expose via API Router in `src/vulcanlab_api`.
    -   Build UI in `vulcanlab_ui`.
2.  **Naming Conventions**:
    -   Python: `snake_case` for functions/variables, `PascalCase` for classes.
    -   TypeScript/React: `camelCase` for variables, `PascalCase` for Components.
    -   Files: `snake_case` in Python, `kebab-case` or `PascalCase` (components) in JS/TS.
    -   NextJS routes: `kebab-case` for pages, `PascalCase` for API routes.
