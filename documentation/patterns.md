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

### Standards
-   **Router**: Use the **App Router** (`src/app`).
-   **Styling**: Use **TailwindCSS** for utility classes. Avoid CSS Modules unless strictly necessary for complex animations.
-   **Components**: Use **Shadcn/Radix** patterns for interactive UI elements.
    - Use existing components whenever possible for things like buttons, cards, etc. as they are available in `vulcanlab_ui/src/components/ui/`.
    - Create new components when necessary and add them to `vulcanlab_ui/src/components/ui/`.
    - Navigation and higher level components like navigation is in `vulcanlab_ui/src/components/`.
    - **Shared Component Library**: Use shared components from `vulcanlab_ui/src/components/` for common patterns:
        - **PageLoadingState** - Standardized loading displays
        - **PageErrorState** - Standardized error displays with retry
        - **DataTable** - Generic tables with configurable columns and sorting
        - **StatusBadge** - Universal status indicators
        - **EmptyState** - Standardized empty states
        - **PageHeader** / **StickyDetailHeader** - Consistent page headers
        - **FormField** - Form fields with react-hook-form integration
        - **ConfirmDialog** - Generic confirmation dialogs
        - See `documentation/work/ui-component-standardization.spec.md` for complete component reference
-   **Custom Hooks**: Use shared hooks from `vulcanlab_ui/src/hooks/` for common patterns:
    - **usePageData** - Data fetching with loading/error/retry states
    - **useTable** - Table state management (sorting, selection)
    - **useModal** - Modal open/close state management
-   **Forms**: Use **react-hook-form** for form validation following shadcn/ui patterns
    - Keep validation lightweight - basic required/pattern checks
    - Use FormField component wrapper for consistent styling and error display
    - Reference: https://ui.shadcn.com/docs/components/form
-   **State Management**:
    -   Prefer **React Server Components (RSC)** for initial data fetching.
    -   Use **Client Components** (`"use client"`) only for interactivity (forms, buttons, real-time updates).
-   **API Integration**: Use a typed client or `fetch` wrappers that respect the API schema.

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
