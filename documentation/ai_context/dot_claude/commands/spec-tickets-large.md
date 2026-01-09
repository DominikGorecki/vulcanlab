---

description: Generate implementation tickets from a spec file and write them as separate markdown files (<spec-slug>.T##.md), optimized for large projects with phased delivery (migrations -> modules -> APIs -> frontend) and unit tests.
argument-hint: [path/to/<spec-slug>.spec.md]
--------------------------------------------

You generate a complete set of implementation tickets from a spec markdown file, designed for larger multi-module efforts.

* $1 = path to a spec file, typically `documentation/work/<spec-slug>.spec.md`.

## Hard requirements

* You MUST read the spec file ($1) fully before doing anything else.
* You MUST read `documentation/patterns.md` fully before creating any tickets. If it does not exist or is empty, STOP and ask.
* You MUST require unit tests for each ticket. Do NOT plan or require integration tests in any ticket.
* You MUST write each ticket to its own markdown file named: `<spec-slug>.T##.md`.
* Ticket files MUST be written in the same directory as the spec file by default (e.g., `documentation/work/`).
* If any target ticket file already exists, STOP and ask what to do (overwrite all, overwrite missing, renumber, or cancel).
* Use plain Markdown. Do NOT use emojis or icon-like characters. Prefer ASCII punctuation.
* Tickets must be concrete and implementable: clear deliverables, acceptance criteria, unit test plan.
* Compared to the regular command, place LESS emphasis on vertical slices. Prefer building correct foundations first (migrations, modules, contracts), then connecting APIs, then frontend.

## Step 1: Validate input

* If $1 is empty, ask for the spec file path and STOP.
* If $1 does not exist or is not a Markdown file, ask for a valid spec file path and STOP.

## Step 2: Load sources

1. Read the spec file ($1) fully.

2. Read `documentation/patterns.md` fully.

3. Infer repo context (lightweight, do not over-read):

* Identify likely languages/frameworks by scanning for manifests and entrypoints near repo root:

  * package.json, tsconfig.json, pnpm-workspace.yaml
  * pyproject.toml, requirements.txt
  * go.mod
  * *.csproj, *.sln
  * Dockerfile, compose, CI configs
* Note findings as assumptions (do not over-read).

## Step 3: Determine spec slug and output folder

* Let `spec_slug` = the base filename of the spec without `.spec.md`.

  * Example: `documentation/work/payments-refactor.spec.md` -> `payments-refactor`
* Let `out_dir` = the directory containing the spec file.
* Ticket filenames are: `${out_dir}/${spec_slug}.T01.md`, `${spec_slug}.T02.md`, ...

## Step 4: Preflight questions (only if needed)

If any of the following are true, ask the user a short set of questions and WAIT before writing tickets:

* The spec has unresolved "Open Questions" that materially affect scope.
* The spec lacks enough detail to decompose into implementable tickets (missing requirements, unclear target system).
* The spec conflicts with patterns.md in a way that would change ticket structure.
* The spec introduces breaking data/contract changes without a stated migration or rollout strategy.

Ask at most 7 questions, multiple-choice plus freeform. Otherwise proceed without questions.

Formatting requirement for questions:

* Output preflight questions inside a single fenced code block using ```text so line breaks are preserved.
* Use this format, including blank lines:

Q1) <question text>

A. <option>
B. <option>
C. <option>
Freeform: <what you need if none of the options fit>

---

Q2) ...

After asking questions, STOP. Do not write any tickets yet.

## Step 5: Decompose the spec into tickets using the "Foundation-First Phasing" strategy

### 5A) Ticket count budget (hard constraint)

* Target 12 to 24 tickets total.
* You MAY go up to 30 if the spec spans multiple independent domains/modules or requires careful rollout/migration sequencing.
* If you produce more than 24 tickets, you MUST add a short justification in the report back in chat titled: "Why >24 tickets" (2 to 6 bullets).
* Do NOT create micro-tickets. Each ticket should still be a meaningful chunk of work.

### 5B) Primary decomposition unit: components and phases (not vertical slices by default)

Decompose primarily by:

1. Data and migrations (schema, backfills, dual-writes, compatibility)
2. Core domain modules (business logic, services, libraries, internal packages)
3. Public contracts (API shapes, DTOs, events, persistence interfaces)
4. API implementation (handlers/controllers, authz, validation, orchestration)
5. Frontend integration (UI, state, client SDK usage, UX polish)
6. Rollout and hardening (feature flags, observability, performance, reliability) only when substantial

Vertical slices are allowed, but they are NOT the default. Prefer correct foundations first, then wire up.

Each ticket MUST include a line in Notes: "Requirements covered: R1, R2, ..." (or "Not explicitly enumerated in spec" if the spec does not label them).

### 5C) Ticket-worthiness gate (prevents micro-tickets)

You may create a new ticket ONLY if at least one is true:

* It delivers a significant building block needed by multiple downstream tickets (e.g., migration framework, core module, shared library).
* It introduces or changes a public contract (API, CLI, event schema, persisted data shape) in a meaningful way.
* It implements a cohesive subsystem/module that can be unit-tested in isolation.
* It delivers a user-visible/admin-visible behavior (optional, but not required early in large projects).
* It is a substantial migration/rollout step that must be tracked independently (e.g., backfill job, dual-write enablement, cutover, cleanup).

If a proposed ticket is mostly wiring/plumbing, it MUST be merged into the nearest substantive ticket unless it is large enough to warrant standalone tracking.

### 5D) Explicit merge rules (default bundling)

Do NOT create standalone tickets for the following; bundle them into the nearest relevant ticket by default:

* Small config wiring, basic DI registration, trivial scaffolding
* Small feature-flag wiring (unless the rollout itself is complex)
* Minor logging/metrics additions
* Minor refactors and small cleanup
* Documentation updates
* Small non-functional tweaks (minor performance or reliability adjustments)

Standalone tickets for the above are allowed ONLY when the work is substantial and primary, for example:

* It requires significant design decisions or multiple components.
* It materially changes architecture, security posture, or operational behavior.
* The spec explicitly requires it as a distinct deliverable.

### 5E) Default ordering: migrations -> modules -> contracts -> APIs -> frontend

Use this ordering unless the spec strongly implies otherwise:

1. Migration planning + scaffolding (only if needed): schemas, compatibility strategy, feature flags/rollout approach
2. Data migrations/backfills (as discrete tickets when large)
3. Core modules and domain services (internal correctness first)
4. Contract definition and validation rules (DTOs, schemas, events)
5. API endpoints/handlers and service orchestration
6. Frontend integration and UI behavior
7. Rollout hardening + operationalization (only if substantial)
8. Migration cleanup/cutover and removal of legacy paths (when applicable)

If the spec is purely internal (library/refactor), prefer:

1. Harness + unit test scaffolding + minimal consumer
2. Core module changes + unit tests
3. Coverage expansion for key edge cases (optional)
4. Cleanup/docs (optional)

### 5F) Ticket sizing rules (avoid both micro and mega)

* Each ticket should be implementable in roughly 0.5 to 2 engineer-days.
* Each ticket should have 4 to 10 concrete steps in "Implementation plan".

  * If fewer than 4 steps, it is probably too granular: merge it.
  * If more than 12 steps, it is probably too large: split by module/contract boundary (not by layer alone).

### 5G) Unit tests rule (enforced without creating test-only tickets)

* Every ticket MUST include unit tests that ship with the functionality in that ticket.
* Do NOT create standalone "tests-only" tickets unless the ticket is a refactor whose primary output is improved testability and coverage.
* Do NOT include integration tests anywhere.

### 5H) Mandatory pass: dependency graph + merge pass

After drafting an initial ticket list:

1. Build a dependency graph mentally (or explicitly in Notes) so ticket order is coherent and unblocks flow.
2. Perform a merge pass until:

* You are within the ticket budget, AND
* No ticket is mostly plumbing, AND
* No ticket is so large that it becomes a vague mega-ticket, AND
* Dependencies are minimal and sensible (avoid long serial chains where possible).

## Step 6: Ticket template (must follow)

Each ticket file MUST follow this structure:

# Ticket: <spec_slug>.T## - <Short Title>

## Source

* Spec: <path to spec file>
* Patterns: documentation/patterns.md

## Goal

* <1 to 3 bullets describing the outcome>

## Phase

* <one of: Migrations | Core Modules | Contracts | APIs | Frontend | Rollout/Hardening | Cleanup>

## Scope

### In scope

* <bullets>

### Out of scope

* <bullets>

## Dependencies

* Depends on: <none | T## | external>
* Unblocks: <T## list>

## Implementation plan

* <ordered bullets; concrete steps>
* Patterns to apply:

  * <pattern name> - <how it applies>
* Deviations (if any):

  * <deviation> - <reason> - <closest compliant option>

## Unit tests (required)

* Add tests for:

  * <test case bullet>
  * <test case bullet>
* Suggested locations:

  * <path bullets>
* Mocking/fakes needed:

  * <bullets or "none">

## Acceptance criteria (checklist)

* [ ] <criterion>
* [ ] <criterion>
* [ ] <criterion>

## Manual verification

* Steps:

  * <step 1>
  * <step 2>
* Expected results:

  * <bullets>

## Notes

* Requirements covered: <R# list or "Not explicitly enumerated in spec">
* <edge cases, gotchas, links to code areas, assumptions>
* <migration/rollout notes if relevant: compatibility, backfill, cutover, cleanup>

## Step 7: Write the ticket files

1. Generate the full ordered ticket list (after the dependency/merge passes).
2. Before writing, check if any `${out_dir}/${spec_slug}.T##.md` files already exist.

* If any exist, STOP and ask the user what to do:

  * A) Overwrite all
  * B) Overwrite only missing
  * C) Renumber starting after the highest existing
  * D) Cancel

3. Write each ticket to its own file using the template above.
4. Ensure ticket numbering is sequential and stable.

## Step 8: Report back in chat

After writing files, output:

* The number of tickets created.
* The list of ticket file paths in order.
* A concise 1 to 2 sentence description per ticket (no giant summaries).
* Identify:

  * The first migration ticket (if any) and what it changes in data shape/compatibility.
  * The first core module ticket and what capability it enables downstream.
  * The first API ticket and what contract it implements.
  * The first frontend ticket and what user-visible behavior it enables (if applicable).
* Any remaining ambiguities that could block implementation.
* If more than 24 tickets were created, include "Why >24 tickets" with 2 to 6 bullets explaining why it was unavoidable.
