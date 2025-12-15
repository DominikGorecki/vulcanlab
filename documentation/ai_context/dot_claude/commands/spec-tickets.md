---
description: Generate implementation tickets from a spec file and write them as separate markdown files (<spec-slug>.T##.md), optimized for vertical slices and unit tests.
argument-hint: [path/to/<spec-slug>.spec.md]
---

You generate a complete set of implementation tickets from a spec markdown file.

- $1 = path to a spec file, typically `documentation/work/<spec-slug>.spec.md`.

## Hard requirements
- You MUST read the spec file ($1) first.
- You MUST read `documentation/patterns.md` fully before creating tickets. If it does not exist or is empty, stop and ask.
- You MUST generate vertical slices when possible (end-to-end user-visible or manually testable paths early).
- You MUST require unit tests for each ticket. Do NOT plan or require integration tests in any ticket.
- You MUST write each ticket to its own markdown file named: `<spec-slug>.T##.md`.
- Ticket files MUST be written in the same directory as the spec file by default (e.g., `documentation/work/`).
- If any target ticket file already exists, stop and ask what to do (overwrite all, overwrite specific ones, renumber, or cancel).
- Use plain Markdown. Do NOT use emojis or icon-like characters. Prefer ASCII punctuation.
- Tickets must be concrete and "implementable": clear deliverables, acceptance criteria, unit test plan.

## Step 1: Validate input
- If $1 is empty, ask for the spec file path and stop.
- If $1 does not exist or is not markdown, ask for a valid spec file path and stop.

## Step 2: Load sources
1) Read the spec file ($1) fully.
2) Read `documentation/patterns.md` fully.
3) Infer repo context (lightweight):
- Identify likely languages/frameworks by scanning for manifests and entrypoints near repo root:
  - package.json, tsconfig.json, pnpm-workspace.yaml
  - pyproject.toml, requirements.txt
  - go.mod
  - *.csproj, *.sln
  - Dockerfile, compose, CI configs
- Note findings as assumptions (do not over-read).

## Step 3: Determine spec slug and output folder
- Let `spec_slug` = the base filename of the spec without `.spec.md`.
  - Example: `documentation/work/payments-refactor.spec.md` -> `payments-refactor`
- Let `out_dir` = the directory containing the spec file.
- Ticket filenames are: `${out_dir}/${spec_slug}.T01.md`, `${spec_slug}.T02.md`, ...

## Step 4: Preflight questions (only if needed)
If any of the following are true, ask the user a short set of questions and WAIT before writing tickets:
- The spec has unresolved "Open Questions" that materially affect scope.
- The spec lacks enough detail to decompose into implementable tickets (missing requirements, unclear target system).
- The spec conflicts with patterns.md in a way that would change ticket structure.

Ask at most 5 questions, multiple-choice plus freeform. Otherwise proceed without questions.

## Step 5: Decompose the spec into tickets
Goal: produce a set of tickets that:
- Delivers a vertical slice early when possible (manual end-to-end path that can be tested).
- Keeps tickets small and sequentially shippable.
- Covers all Functional + Non-functional requirements, plus any necessary refactors, wiring, docs, and unit tests.
- Applies patterns.md guidance; if you deviate, justify in the ticket.

### Vertical slice strategy (default)
When the feature is user-facing or has a runnable flow, prefer this ordering:
1) Thin walking skeleton (minimal runnable path, feature flag if needed).
2) Vertical slice 1 (happy path end-to-end) with unit tests.
3) Additional slices (edge cases, validation, error handling).
4) Non-functional hardening (security, observability, performance) as required.
5) Cleanup and docs updates if needed.

If the spec is purely internal (library/refactor), use:
1) Harness + unit test scaffolding
2) Core API + minimal consumer
3) Expand coverage + edge cases
4) Cleanup

### Ticket sizing
- Default to 6 to 15 tickets depending on scope.
- Prefer tickets that can be implemented and verified in isolation.
- Do not create "mega tickets". Split by slice, layer, or requirement cluster.

### Unit tests rule
Each ticket must include:
- The unit test cases to add (bullets).
- Where the tests should live (file path hints).
- Any test doubles/mocks needed.
Do NOT include integration tests.

## Step 6: Ticket template (must follow)
Each ticket file MUST follow this structure:

# Ticket: <spec_slug>.T## - <Short Title>

## Source
- Spec: <path to spec file>
- Patterns: documentation/patterns.md

## Goal
- <1 to 3 bullets describing the outcome>

## Scope
### In scope
- <bullets>
### Out of scope
- <bullets>

## Dependencies
- Depends on: <none | T## | external>
- Unblocks: <T## list>

## Implementation plan
- <ordered bullets; concrete steps>
- Patterns to apply:
  - <pattern name> - <how it applies>
- Deviations (if any):
  - <deviation> - <reason> - <closest compliant option>

## Unit tests (required)
- Add tests for:
  - <test case bullet>
  - <test case bullet>
- Suggested locations:
  - <path bullets>
- Mocking/fakes needed:
  - <bullets or "none">

## Acceptance criteria (checklist)
- [ ] <criterion>
- [ ] <criterion>
- [ ] <criterion>

## Manual verification
- Steps:
  - <step 1>
  - <step 2>
- Expected results:
  - <bullets>

## Notes
- <edge cases, gotchas, links to code areas, assumptions>

## Step 7: Write the ticket files
1) Generate the full ordered ticket list.
2) Before writing, check if any `${out_dir}/${spec_slug}.T##.md` files already exist.
- If any exist, STOP and ask the user what to do:
  - A) Overwrite all
  - B) Overwrite only missing
  - C) Renumber starting after the highest existing
  - D) Cancel
3) Write each ticket to its own file using the template above.
4) Ensure ticket numbering is sequential and stable.

## Step 8: Report back in chat
After writing files, output:
- The number of tickets created.
- The list of ticket file paths in order.
- A concise 1 to 2 sentence description per ticket (no giant summaries).
- Which ticket is the first vertical slice and what manual end-to-end behavior it enables.
- Any remaining ambiguities that could block implementation.
