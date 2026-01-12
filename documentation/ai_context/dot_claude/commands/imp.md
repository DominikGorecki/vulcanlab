---
description: Implement a single ticket by reading the ticket markdown file, then making the required code changes and verifying via tests using the repo’s Python venv.
argument-hint: [path/to/<spec-slug>.T##.md]
-------------------------------------------

You implement exactly one ticket.

* $1 = path to a ticket markdown file (e.g., `documentation/work/<spec-slug>.T03.md`).

## Hard requirements

* You MUST read the entire ticket file ($1) before doing anything else.
* You MUST implement only what the ticket asks for (no extra features, no refactors unless required to complete the ticket).
* You MUST aim to complete the ENTIRE ticket (all acceptance criteria / checklist items) before stopping.
* If you cannot complete the ticket (time/complexity/unknowns), you MUST:

  1. clearly state what is unfinished and why, and
  2. write a follow-up ticket for the remaining work.

## Unfinished-work ticket rule (critical)

* If any part of the ticket remains unfinished, you MUST write a new ticket file alongside the original with:

  * the same base filename, but insert `.unf##` before `.md`
  * start numbering at `unf01` and increment if more are needed
  * example: `collection-deep-research.T03.md` → `collection-deep-research.T03.unf01.md`
* The unfinished ticket MUST include:

  * remaining acceptance criteria / tasks (only what’s left)
  * current state (what’s already done)
  * concrete next steps
  * any blocking questions or missing info
  * validation commands to run

## Environment rule (critical)

* When running ANY Python command (tests, linting, scripts, tooling), you MUST use the virtual environment in:
  `/home/dardawk/python/vulcanlab/venv`
* Prefer invoking tools via the venv explicitly (e.g., `/home/dardawk/python/vulcanlab/venv/bin/python -m ...`) to avoid accidentally using system Python.

## Workflow

1. Read the ticket and extract:

   * goals / acceptance criteria
   * files likely involved
   * required commands to validate
2. Implement the changes in small, atomic steps.
3. Run the validation commands using the venv path above.
4. Summarize:

   * what changed (files + high-level)
   * commands run + results
   * whether the ticket is fully complete
   * if not complete: link to the `.unf##` follow-up ticket created
