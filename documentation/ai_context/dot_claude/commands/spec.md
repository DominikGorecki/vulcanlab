---

description: Create a new spec markdown file in documentation/work from a prompt or a markdown file, using documentation/patterns.md as guidance.
argument-hint: [prompt text OR path/to/input.md]
------------------------------------------------

You generate a new spec markdown file for spec-driven development.

* $1 = either raw prompt text OR a path to a markdown file. If $1 is a valid file path, treat it as a file. Otherwise treat it as prompt text.

## Hard requirements

* You MUST read `documentation/patterns.md` first. If it does not exist or is empty, STOP and ask.
* You MUST ask clarifying questions first, but ONLY ask the minimum number needed. Maximum is 10 questions total.
* You MUST wait for the user answers before writing the spec file.
* You MUST write the spec to `documentation/work/<slug>.spec.md`.
* `<slug>` is derived from the spec title: lowercase, ASCII letters and digits, replace spaces with hyphens, collapse multiple hyphens, trim hyphens.
* If the output spec file already exists, STOP and ask what to do.
* Markdown output may use Unicode, but DO NOT use emojis or icon-like characters.
* Separate stable requirements from implementation notes. Requirements should be testable.
* The spec MUST include an implementation-oriented work breakdown that maps cleanly to tickets (logical decomposition), without prioritizing “vertical slices”.

## Step 1: Load inputs

1. Resolve $1:

* If $1 is a readable file path:

  * Read the entire file.
  * If it contains frontmatter, ignore it:

    * YAML frontmatter between `---` and `---` at the start of the file
    * JSON frontmatter between `{` and `}` at the start of the file

* Otherwise:

  * Treat $1 as the raw prompt text.

2. Read `documentation/patterns.md` fully.

3. Infer repo context (lightweight, do not over-read):

* Identify likely languages/frameworks by scanning for common manifests and entrypoints near repo root and relevant directories:

  * package.json, tsconfig.json, pnpm-workspace.yaml, yarn.lock
  * pyproject.toml, requirements.txt, poetry.lock
  * go.mod
  * *.csproj, *.sln
  * Dockerfile, docker-compose.yml

* Note what you found; if ambiguous, include it as an assumption to confirm in questions.

## Step 2: Ask clarifying questions (must ask, then wait)

### Question count rule (critical)

Ask ONLY questions that are necessary to produce a correct, ticketable spec.

* Do NOT ask questions for choices that are obvious or already specified in the prompt/input file.
* Do NOT ask preference questions unless the answer materially changes scope, contracts, or acceptance criteria.
* If the input is detailed and unambiguous, you may ask as few as 0 to 3 questions.
* Maximum is 10 questions total.

Your questions MUST cover the following topics ONLY if they are unclear or missing and relevant:

* Problem and user impact
* Goals vs non-goals (strict non-goals required if there is meaningful scope)
* Scope boundaries (what is explicitly out)
* Interfaces/APIs/contracts (if any)
* Data model/storage (if any)
* Security and privacy considerations (high level)
* Non-functional requirements (perf, reliability, observability)
* Acceptance criteria (bullet checklist)
* Risks and alternatives
* How patterns.md applies, and where you might deviate (ask for approval if deviating)
* Implementation breakdown needs (modules/components/migrations) ONLY if missing and necessary to make a sane work breakdown

### Output formatting rule for questions

* Do NOT put questions inside fenced code blocks.
* Use normal markdown with a simple numbered list: `Q1. ...`, `Q2. ...`
* If options help, include them as bullets under the question.
* After asking questions, STOP. Do not create or write the spec file yet.

## Step 3: Write the spec file after answers

After the user answers:

1. Determine the spec Title.
2. Generate `<slug>` from Title using the slug rules above.
3. Set output path: `documentation/work/<slug>.spec.md`.
4. If that file exists, STOP and ask whether to overwrite, rename, or cancel.

## Step 4: Spec quality bar

* Treat `documentation/patterns.md` as guidance. If you deviate, you MUST justify why and propose the closest compliant alternative.
* Use repo context inference to tailor the spec (languages, frameworks, toolchain), but prefer patterns.md where possible.
* Keep total length around 1 to 2 pages equivalent. Be concise, but do not omit critical constraints or acceptance criteria.
* Use precise, testable language.
* Do not invent endpoints, tables, or components that are not implied by the prompt; mark unknowns as TBD and add them to Open Questions.
* Work breakdown should be implementation-friendly and logical (layers/modules), not “vertical slices”. Prefer sequencing like: foundations/migrations → core domain/modules → APIs/contracts → UI/clients → integration/observability → rollout.

## Step 5: Spec markdown template (must follow)

Write the spec using this structure. If a section is not applicable, include it with "Not applicable" and one sentence explaining why.

# Title: <Spec Title>

## Summary

* <3 to 6 bullets describing what is being built and why>

## Problem / Context

* <what exists today, what is broken or missing, who is affected>
* <user impact and business impact>

## Goals

* <bullets>

## Non-goals (Strict)

* <bullets; be explicit>

## Scope

### In scope

* <bullets>

### Out of scope

* <bullets>

## Requirements (Functional)

* R1: <requirement>
* R2: <requirement>
  (Each requirement should be testable.)

## Requirements (Non-functional)

* Performance:

  * <bullets>
* Reliability:

  * <bullets>
* Security / Privacy:

  * <bullets>
* Observability:

  * <bullets>

## Proposed Solution (High-level)

* <architecture bullets>
* <main components and responsibilities>
* <data flow in bullets>

## Interfaces / APIs / Contracts

* <bullets describing endpoints, commands, events, interfaces>
* <include request/response shapes only if known; otherwise list TBDs>

## Data Model / Storage

* <bullets; entities, relationships, migrations; or Not applicable>

## UX / Workflows

* <bullets describing key user flows; or Not applicable>

## Work Breakdown (Ticket Seed)

Provide a logical implementation breakdown that can be turned into tickets. Keep it concrete and ordered. Prefer grouping by dependency and cohesion.

### Phase 0: Foundations (if applicable)

* <repo setup, feature flags, scaffolding, permissions, shared libs>

### Phase 1: Data / Migrations (if applicable)

* <schema changes, migrations, backfills, data validation, rollback notes>

### Phase 2: Core Domain / Modules

* <services/modules with clear responsibilities>
* <key internal APIs or interfaces between modules>

### Phase 3: External APIs / Integrations (if applicable)

* <endpoint work, auth, rate limiting, third-party integrations>

### Phase 4: UI / Client (if applicable)

* <screens/components, state, validation, error handling>

### Phase 5: Testing + Observability + Hardening

* <integration tests, logging/metrics/tracing, alerts, perf checks>

### Phase 6: Rollout

* <deploy steps, migrations sequencing, feature flag plan, monitoring, rollback>

## Testing Plan

* Unit tests:

  * <bullets>
* Integration tests:

  * <bullets>
* Manual test plan:

  * <bullets>

## Acceptance Criteria (Checklist)

* [ ] <criterion>
* [ ] <criterion>
* [ ] <criterion>

## Rollout / Migration Plan

* <bullets; or Not applicable>

## Risks and Alternatives

* Risks:

  * <bullets>
* Alternatives considered:

  * <bullets>

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:

  * <pattern name> - <where it applies in this spec>
* Deviations (if any):

  * <deviation> - <reason> - <closest compliant option>

## Implementation Notes (Non-binding)

* <bullets that help implementers, but are not requirements>
* <call out inferred repo conventions and why>

## Open Questions

* Q1: <question>
* Q2: <question>

## Step 6: Write and report

* Write the completed spec markdown to `documentation/work/<slug>.spec.md`.
* Then, in chat, provide:

  * The output file path you wrote
  * A 5 to 10 bullet summary of what is in the spec
  * Any remaining open questions that block ticket generation
