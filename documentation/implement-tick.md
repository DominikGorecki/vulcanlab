---
description: Implement a ticket markdown file and mark it COMPLETE when done.
argument-hint: [path/to/Ticket.T001.md]
---

You implement a ticket described in a markdown file.

- `$1` = path to a ticket file, e.g. `docs/FeatureX.T001.md`.

## Behavior

1. **Load ticket**
   - Read `$1`. If it doesn’t exist or isn’t markdown, ask for a valid ticket path and stop.

2. **Check COMPLETE marker**
   - Find the first non-empty line of the ticket.
   - If it is exactly `COMPLETE` **and** the user’s latest message does **not** contain the exact phrase `FORCE REIMPLEMENTATION`:
     - Do not change any code.
     - Tell the user the ticket is already COMPLETE and to rerun with `FORCE REIMPLEMENTATION` if they really want to redo it.
     - Stop.
   - If it is `COMPLETE` **and** the user’s latest message does contain `FORCE REIMPLEMENTATION`, continue as normal but keep a single `COMPLETE` line at the top when finished.

3. **Understand and clarify**
   - Use the ticket’s content (context, outcome, implementation plan, tests, etc.) as the source of truth.
   - If anything important is unclear (APIs, data shapes, flows, constraints), ask targeted clarification questions before editing code.

4. **Implement**
   - Locate and modify relevant files according to the ticket:
     - Backend (models, migrations, services, APIs, jobs, etc.).
     - Frontend (components/pages, state, API calls, UX states), if applicable.
   - Add/update **unit tests** and any other tests explicitly requested.
   - Keep changes scoped to the ticket; avoid unrelated refactors.

5. **Mark ticket COMPLETE**
   - After implementation:
     - Re-read `$1`.
     - If the first non-empty line is **not** `COMPLETE`, rewrite the file so it becomes:

       ```md
       COMPLETE

       <existing ticket content...>
       ```

     - If it already starts with `COMPLETE`, do not add another.

6. **Close out**
   - In chat, briefly summarize what changed and remind the user to run the ticket’s manual/acceptance tests to verify behavior.
