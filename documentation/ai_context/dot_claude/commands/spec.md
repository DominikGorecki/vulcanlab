---
description: Create a new spec markdown file in documentation/work from a prompt or a markdown file, using documentation/patterns.md as guidance.
argument-hint: [prompt text OR path/to/input.md]
---

You generate a new spec markdown file for spec-driven development.

- $1 = either raw prompt text OR a path to a markdown file. If $1 is a valid file path, treat it as a file. Otherwise treat it as prompt text.

## Hard requirements
- You MUST read `documentation/patterns.md` first. If it does not exist or is empty, stop and ask.
- You MUST ask clarifying questions first, but ONLY ask the minimum number needed. Maximum is 10, not a target.
- You MUST wait for the user's answers before writing the spec file.
- You MUST write the spec to `documentation/work/<slug>.spec.md`.
- `<slug>` is derived from the spec title: lowercase, ASCII letters and digits, replace spaces with hyphens, collapse multiple hyphens, trim hyphens.
- If the output spec file already exists, stop and ask what to do.
- Markdown output may use Unicode, but DO NOT use emojis or icon-like characters.
- Separate stable requirements from implementation notes. Requirements should be testable.

## Step 1: Load inputs
1) Resolve $1:
- If $1 is a readable file path:
  - Read the entire file.
  - If it contains frontmatter, ignore it:
    - YAML frontmatter between `---` and `---` at the start of the file
    - JSON frontmatter between `{` and `}` at the start of the file
- Otherwise:
  - Treat $1 as the raw prompt text.

2) Read `documentation/patterns.md` fully.

3) Infer repo context (lightweight, do not over-read):
- Identify likely languages/frameworks by scanning for common manifests and entrypoints near repo root and relevant directories:
  - package.json, tsconfig.json, pnpm-workspace.yaml, yarn.lock
  - pyproject.toml, requirements.txt, poetry.lock
  - go.mod
  - *.csproj, *.sln
  - Dockerfile, docker-compose.yml
- Note what you found; if ambiguous, include it as an assumption to confirm in questions.

## Step 2: Ask clarifying questions (must ask, then wait)
### Question count rule (critical)
Ask ONLY questions that are necessary to produce a correct, ticketable spec.
- Do NOT ask questions for choices that are obvious or already specified in the prompt/input file.
- Do NOT ask "preference" questions unless the answer materially changes scope, contracts, or acceptance criteria.
- If the input is detailed and unambiguous, you may ask as few as 0 to 3 questions.
- Maximum is 10 questions total.

Your questions MUST cover the following topics ONLY if they are unclear or missing and relevant:
- Problem and user impact
- Goals vs non-goals (strict non-goals required if there is meaningful scope)
- Scope boundaries (what is explicitly out)
- Interfaces/APIs/contracts (if any)
- Data model/storage (if any)
- Security and privacy considerations (high level)
- Non-functional requirements (perf, reliability, observability)
- Acceptance criteria (bullet checklist)
- Risks and alternatives
- How patterns.md applies, and where you might deviate (ask for approval if deviating)

### Formatting rule (critical)
Questions MUST be easy to read in Markdown:
- Put the question text on its own line.
- Put each option on its own line.
- Put the freeform line on its own line.
- Insert a separator between questions using a Markdown horizontal rule: `---`
- Do not collapse content into a single paragraph line.

Use exactly this format:

Q1) <question text>
A. <option>
B. <option>
C. <option>
Freeform: <what you need if none of the options fit>

---

Q2) <question text>
A. <option>
B. <option>
C. <option>
Freeform: <what you need if none of the options fit>

After asking questions, STOP. Do not create or write the spec file yet.

## Step 3: Write the spec file after answers
After the user answers:
1) Determine the spec Title.
2) Generate `<slug>` from Title using the slug rules above.
3) Set output path: `documentation/work/<slug>.spec.md`.
4) If that file exists, STOP and ask whether to overwrite, rename, or cancel.

## Step 4: Spec quality bar
- Treat `documentation/patterns.md` as guidance. If you deviate, you MUST justify why and propose the closest compliant alternative.
- Use repo context inference to tailor the spec (languages, frameworks, toolchain), but prefer patterns.md where possible.
- Keep total length around 1 to 2 pages equivalent. Be concise, but do not omit critical constraints or acceptance criteria.
- Use precise, testable language.
- Do not invent endpoints, tables, or components that are not implied by the prompt; mark unknowns as TBD and add them to Open Questions.

## Step 5: Spec markdown template (must follow)
Write the spec using this structure. If a section is not applicable, include it with "Not applicable" and one sentence explaining why.

# Title: <Spec Title>

## Summary
- <3 to 6 bullets describing what is being built and why>

## Problem / Context
- <what exists today, what is broken or missing, who is affected>
- <user impact and business impact>

## Goals
- <bullets>

## Non-goals (Strict)
- <bullets; be explicit>

## Scope
### In scope
- <bullets>
### Out of scope
- <bullets>

## Requirements (Functional)
- R1: <requirement>
- R2: <requirement>
(Each requirement should be testable.)

## Requirements (Non-functional)
- Performance:
  - <bullets>
- Reliability:
  - <bullets>
- Security / Privacy:
  - <bullets>
- Observability:
  - <bullets>

## Proposed Solution (High-level)
- <architecture bullets>
- <main components and responsibilities>
- <data flow in bullets>

## Interfaces / APIs / Contracts
- <bullets describing endpoints, commands, events, interfaces>
- <include request/response shapes only if known; otherwise list TBDs>

## Data Model / Storage
- <bullets; entities, relationships, migrations; or Not applicable>

## UX / Workflows
- <bullets describing key user flows; or Not applicable>

## Testing Plan
- Unit tests:
  - <bullets>
- Integration tests:
  - <bullets>
- Manual test plan:
  - <bullets>

## Acceptance Criteria (Checklist)
- [ ] <criterion>
- [ ] <criterion>
- [ ] <criterion>

## Rollout / Migration Plan
- <bullets; or Not applicable>

## Risks and Alternatives
- Risks:
  - <bullets>
- Alternatives considered:
  - <bullets>

## Patterns and Standards Alignment (from documentation/patterns.md)
- Patterns applied:
  - <pattern name> - <where it applies in this spec>
- Deviations (if any):
  - <deviation> - <reason> - <closest compliant option>

## Implementation Notes (Non-binding)
- <bullets that help implementers, but are not requirements>
- <call out inferred repo conventions and why>

## Open Questions
- Q1: <question>
- Q2: <question>

## Step 6: Write and report
- Write the completed spec markdown to `documentation/work/<slug>.spec.md`.
- Then, in chat, provide:
  - The output file path you wrote
  - A 5 to 10 bullet summary of what is in the spec
  - Any remaining open questions that block ticket generation