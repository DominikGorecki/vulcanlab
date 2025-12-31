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

### Database Seeding (Prompt Templates)
> **Standard**: Use file-based YAML configuration for seeding prompt templates.

**Pattern**: Prompt templates are seeded from individual `.txt` files managed by a YAML configuration file during database initialization.

-   **Configuration**: `src/vulcanlab/data/seed_data/templates.yaml` defines template metadata (function_tag, version, title, etc.)
-   **Content**: Individual template content stored in `src/vulcanlab/data/seed_data/templates/*.txt`
-   **Seeding Function**: `seed_prompt_templates()` in `src/vulcanlab/data/init_db.py` reads YAML config and loads content from files
-   **Benefits**:
    -   Easy to modify templates without touching Python code
    -   Version control friendly (diff-able text files)
    -   Clear separation of metadata and content
    -   Idempotent seeding (only inserts new templates)

**How to Add/Modify Templates**:
1. Create or edit `.txt` file in `templates/` directory
2. Update `templates.yaml` with metadata
3. Run `python -m vulcanlab.data.init_db -v` to seed

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
    -   **Migration**: SQL-based migrations or `alembic` (check specific project setup).

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
