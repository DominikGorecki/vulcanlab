---

description: Generate implementation tickets from a spec file and write them as separate markdown files (<spec-slug>.T##.md), optimized for vertical slices and unit tests.
argument-hint: [path/to/<spec-slug>.spec.md]
--------------------------------------------

You generate a complete set of implementation tickets from a spec markdown file.

* $1 = path to a spec file, typically `documentation/work/<spec-slug>.spec.md`.

## Hard requirements

* You MUST read the spec file ($1) fully before doing anything else.
* You MUST read `documentation/patterns.md` fully before creating any tickets. If it does not exist or is empty, STOP and ask.
* You MUST generate vertical slices when possible (end-to-end user-visible or manually testable paths early).
* You MUST require unit tests for each ticket. Do NOT plan or require integration tests in any ticket.
* You MUST write each ticket to its own markdown file named: `<spec-slug>.T##.md`.
* Ticket files MUST be written in the same directory as the spec file by default (e.g., `documentation/work/`).
* If any target ticket file already exists, STOP and ask what to do (overwrite all, overwrite missing, renumber, or cancel).
* Use plain Markdown. Do NOT use emojis or icon-like characters. Prefer ASCII punctuation.
* Tickets must be concrete and implementable: clear deliverables, acceptance criteria, unit test plan.

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

Ask at most 5 questions, multiple-choice plus freeform. Otherwise proceed without questions.

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

## Step 5: Decompose the spec into tickets using the "Slice-First + Merge Thresholds" strategy

### 5A) Ticket count budget (hard constraint)

* Target 4 to 8 tickets total.
* You MAY exceed 8 only if the spec clearly contains more than 8 independently shippable slices or major subsystems that cannot be bundled without creating non-implementable work.
* If you produce more than 8 tickets, you MUST add a short justification in the report back in chat titled: "Why >8 tickets".

### 5B) Primary decomposition unit: vertical slices (not individual requirements)

* The primary unit of planning is a "slice": a cohesive capability that results in at least one new manually verifiable behavior.
* Each ticket SHOULD cover multiple functional requirements when they belong to the same slice.
* Each ticket MUST include a line in Notes: "Requirements covered: R1, R2, ..." (or "Not explicitly enumerated in spec" if the spec does not label them).

### 5C) Ticket-worthiness gate (prevents micro-tickets)

You may create a new ticket ONLY if at least one is true:

* It delivers a new user-visible or operator-visible behavior that can be manually verified.
* It introduces or changes a public contract (API, CLI, event schema, persisted data shape) and the change is large enough that bundling would create a risky mega-change.
* It represents a genuinely independent major boundary (new service/module/package) that is too large or risky to bundle into a slice ticket.

If a proposed ticket does NOT enable manual verification by itself, it MUST be merged into the nearest slice ticket, unless it is the only way to unblock the first slice and is substantial.

### 5D) Explicit merge rules (default bundling)

Do NOT create standalone tickets for the following; bundle them into the nearest slice ticket by default:

* Config wiring, dependency injection, basic scaffolding
* Feature flags
* Logging, metrics, tracing, basic observability wiring
* Minor refactors and small cleanup
* Documentation updates
* Small non-functional tweaks (minor performance or reliability adjustments)

Standalone tickets for the above are allowed ONLY when the work is substantial and primary, for example:

* It requires significant design decisions or multiple files/components (not a few lines).
* It materially changes architecture, security posture, or operational behavior.
* The spec explicitly requires it as a distinct deliverable.

### 5E) Slice ordering (keep it shippable)

When the feature is user-facing or has a runnable flow, prefer this capped ordering:

1. Walking skeleton (at most 1 ticket): minimal runnable path, minimal wiring, safe no-op / feature-flagged behavior if needed.
2. Happy path slice (at most 1 ticket): end-to-end behavior with unit tests.
3. Edge/validation slice (at most 1 ticket): key error cases and validation with unit tests.
4. Hardening slice (at most 1 ticket, only if required): bundle required security/observability/performance/reliability improvements.
5. Cleanup/docs slice (at most 1 ticket, only if substantial): otherwise bundle into prior tickets.

If the spec is purely internal (library/refactor), prefer:

1. Harness + unit test scaffolding + minimal consumer (1 ticket if possible)
2. Core change + unit tests (1 ticket)
3. Coverage expansion + key edge cases (optional)
4. Cleanup/docs (optional)

### 5F) Ticket sizing rules (avoid both micro and mega)

* Each ticket should be implementable in roughly 0.5 to 2 engineer-days.
* Each ticket should have 3 to 8 concrete steps in "Implementation plan".

  * If fewer than 3 steps, it is probably too granular: merge it.
  * If more than 10 steps, it is probably too large: split by slice boundary (not by layer).

### 5G) Unit tests rule (enforced without creating test-only tickets)

* Every ticket MUST include unit tests that ship with the functionality in that ticket.
* Do NOT create standalone "tests-only" tickets unless the ticket is a refactor whose primary output is improved testability and coverage.
* Do NOT include integration tests anywhere.

### 5H) Required merge pass (mandatory)

After drafting an initial ticket list, perform a merge pass until you are within the ticket budget and the list passes the ticket-worthiness gate:

* Merge tickets that are only plumbing/scaffolding into the nearest slice.
* Merge tickets that do not produce a new manually verifiable behavior by themselves into the nearest slice.
* Merge tickets that share the same primary component and are sequentially dependent, unless merging would create an oversized ticket.

## Step 6: Ticket template (must follow)

Each ticket file MUST follow this structure:

# Ticket: <spec_slug>.T## - <Short Title>

## Source

* Spec: <path to spec file>
* Patterns: documentation/patterns.md

## Goal

* <1 to 3 bullets describing the outcome>

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

## Step 7: Write the ticket files

1. Generate the full ordered ticket list (after the mandatory merge pass).
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
* Which ticket is the first vertical slice and what manual end-to-end behavior it enables.
* Any remaining ambiguities that could block implementation.
* If more than 8 tickets were created, include "Why >8 tickets" with 2 to 5 bullets explaining why it was unavoidable.
