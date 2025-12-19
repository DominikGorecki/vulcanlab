---
description: Generate or update an AI-oriented README.ai.md for a folder by summarizing code, structure, and key details.
argument-hint: [path/to/folder]
---

You generate AI-oriented README files named README.ai.md. You MUST write files to disk (not just paste contents in chat).

* $1 = folder path, relative to repo root or absolute.

## Hard requirements

* You MUST create or overwrite `$1/README.ai.md` (unless you are blocked by a stop-and-ask choice).
* In recursive mode (if enabled), you MUST also create or overwrite `README.ai.md` in eligible subfolders within the selected recursion depth, bottom-up (deepest folders first).
* After writing files, you MAY paste a short excerpt, but do not replace writing with pasting.
* Use plain ASCII only. Do NOT use emojis or unicode icon-like characters.
* Headings and bullets must render well in standard Markdown.

## Step 0: Clarify first (must ask, then wait)

Before reading or writing files, ask the user these questions in one message, with lettered options and defaults preselected. Tell the user they can reply with a compact answer like "1:A 2:C 3:DEFAULT" or just "DEFAULTS" to accept all defaults.

Output the questions inside a single fenced code block using ```text so line breaks are preserved.

1. Output file
   A. Create or overwrite README.ai.md in the target folder (default)
   B. Update README.md instead

2. Rewrite strategy
   A. Full rewrite every time
   B. Incremental update
   C. Full rewrite but preserve a "Manual Notes" block if present (default)

3. Scope depth (used for recursion boundary and top-level file tree depth)
   A. Depth 1
   B. Depth 2
   C. Depth 3 (default)
   D. Custom depth

4. Target size (per folder README.ai.md)
   A. Aim for about 600 words
   B. Aim for about 1000 words, can be bigger if needed (default)
   C. Aim for about 1500 words
   D. No target, maximize completeness

5. What to include (default is all)
   A. Purpose and quick start
   B. Architecture overview
   C. Entry points and main flows
   D. Key conventions
   E. Dependency overview
   F. API contracts and interfaces
   G. LLM handoff section
   H. Gotchas (cap at 5 bullets)

6. Ignore rules
   A. Respect .gitignore (default)
   B. Ignore nothing
   C. Respect .gitignore plus common ignores even if not listed (node_modules, dist, bin, obj)

7. Symlinks
   A. Follow symlinks (default)
   B. Do not follow symlinks

8. Very large folders safeguard (only if needed)
   A. If listing all files would be extremely long, ask whether to still list all (default)
   B. Auto collapse large directories into counts

9. Recursive generation order and coverage
   A. Single folder only: write only `$1/README.ai.md` (no subfolder writes)
   B. Recursive bottom-up: write README.ai.md in all subfolders within depth, then write `$1/README.ai.md` last (default)

10. Per-folder file tree depth in recursive mode
    A. Depth 1 for subfolders, chosen depth for the target folder (default)
    B. Use the chosen depth for every folder
    C. Custom per-folder depth rule

After the user answers (or says DEFAULTS), proceed.

## Step 1: Validate inputs

* If $1 is empty, ask for the folder path and STOP.
* Resolve the folder path. If it does not exist or is not a directory, ask for a valid folder path and STOP.

## Step 2: Gather context (respect ignore rules)

Inspect folders while respecting the selected ignore rules.

* Determine repo root if possible. If unclear, treat the provided folder as the root for ignore lookup.
* Read ignore files as needed (.gitignore in repo root and relevant subfolders). If repo root is unclear, at minimum respect the closest .gitignore you can find when walking upward.
* Build the folder list to process:

  * If recursive mode is enabled:

    * Enumerate all descendant subfolders up to the selected depth (depth counted from $1, where $1 is depth 0).
    * Exclude ignored folders and symlinked folders if symlinks are disabled.
  * If single-folder mode:

    * Only process $1.

## Step 3: Processing order (bottom-up required in recursive mode)

If recursive mode is enabled, you MUST process folders in strict bottom-up order:

* Sort folders by descending depth (deepest first).
* For folders at the same depth, sort lexicographically by path for stable output.
* Process each folder once.
* Write parent folders only after all eligible children have been written.

If single-folder mode, process only $1.

## Step 4: What to read per folder (heuristic, keep it high leverage)

For each folder being processed:

* Read `<folder>/README.ai.md` if it exists (for context). You will still follow the selected rewrite strategy.
* Read `<folder>/README.md` if present (for human intent), but do not edit it.

Use an importance heuristic. Do not read every file.
High priority signals:

* Entry points: main, index, app, server, cli, Program.cs, **main**.py, cmd/*, src/main*, routes, controllers
* Public API surfaces: exported modules, interfaces, endpoints, schema files
* Config that defines behavior: package.json, tsconfig, pyproject, requirements, go.mod, Cargo.toml, csproj, solution files, docker files, CI workflows, lint and format configs
* Build and run scripts: Makefile, task runners, scripts directories

Read enough of the important files to accurately describe purpose, architecture, entry points, APIs, and conventions.
For non-important files, rely on names and folder structure unless a detail is unclear.

## Step 5: Secrets and safety

* Never paste secrets, tokens, private keys, passwords, or full connection strings into README.ai.md.
* If you detect likely secrets in a file, do not reproduce them. Mention "Potential secret material detected and omitted" and point to the file path only.

## Step 6: Subfolder summaries (bottom-up aggregation)

This section defines how parent folders summarize children.

If recursive mode is enabled:

* For each folder, identify its direct child subfolders that are within the recursion boundary.
* Because you are processing bottom-up, each direct child folder should already have a fresh `README.ai.md`.
* For the parent folder's "Subfolders" section:

  * Prefer summarizing each direct child using the child's `README.ai.md` (freshly generated).
  * If a child README.ai.md could not be generated (blocked or error), fall back to child's README.md if present, else summarize using folder structure and key files only.
* Each subfolder summary MUST be 2 to 4 sentences and include:

  * What the subfolder is for
  * The primary entry point(s) if any
  * Any key conventions or responsibilities that matter to an LLM

If single-folder mode:

* Summarize direct child subfolders using:

  * README.md if present, else structure-based summary
* Do NOT write subfolder README.ai.md files.

## Step 7: Determine per-folder file tree depth

* In single-folder mode: use the chosen depth for the file tree in `$1/README.ai.md`.
* In recursive mode:

  * For the target folder ($1): use the chosen depth.
  * For subfolders: use the selected per-folder tree depth rule (default: depth 1).
* Always respect the very large folders safeguard option for each folder independently.

## Step 8: Write README.ai.md (full rewrite unless strategy says otherwise)

For each folder in the processing order, write `<folder>/README.ai.md` using the required template below.

* Prefer headings with bullet-first summaries.
* Keep Gotchas to max 5 bullets.
* Avoid huge code blocks. If a code snippet is needed, keep it under 10 lines.
* Use plain ASCII for bullets and punctuation.

If the user selected "Full rewrite but preserve Manual Notes":

* Preserve everything between these markers exactly as-is from the previous README.ai.md (if present):

  * BEGIN MANUAL NOTES
  * END MANUAL NOTES

### Required README.ai.md template (use exactly this structure)

# {FolderName} (AI README)

## Purpose

* {1 to 3 bullets}
* {1 short paragraph if needed}

## Quick start

* {How to run, build, test, lint if discoverable}
* {If unknown, say what is missing and where to look}

## Architecture overview

* {3 to 8 bullets that describe major components and data flow}
* Key folders:

  * {folder} - {meaning}

## Entry points and main flows

* Entry points:

  * {path} - {what it starts}
* Typical flows:

  * {flow name}: {steps in 3 to 6 bullets}

## Key conventions

* {naming, layering, error handling, logging, configuration, tests, style}
* {include only what you can justify from the repo, do not guess}

## Dependencies overview

* Runtime dependencies: {bullets}
* Dev dependencies and tooling: {bullets}
* External services: {bullets, only if evidenced}

## APIs and contracts

* Endpoints, handlers, or RPC surfaces: {bullets with file pointers}
* Data models and schemas: {bullets with file pointers}
* Events, queues, background jobs: {bullets if present}

## Subfolders

* {direct subfolder path}: {2 to 4 sentence summary}
* {repeat}
* If no direct subfolders are included by the recursion boundary: "None."

## File tree (depth {N})

{Include the full tree to the selected depth, respecting ignore rules and safeguards.}

## LLM handoff

* When asking an LLM to work in this folder, include:

  * {top 5 to 12 highest leverage files or folders to add to context}
* Good first questions to ask:

  * {3 to 6 bullets}
* Guardrails:

  * {what must not be broken, tests to run, style expectations}

## Gotchas

* {max 5 bullets}

### Manual Notes (preserve if present and user selected preservation)

BEGIN MANUAL NOTES
{verbatim}
END MANUAL NOTES

## Step 9: Report back (after all writes)

After writing files:

* Confirm explicitly which files were written:

  * Always include `$1/README.ai.md`
  * If recursive mode: include the count of subfolder README.ai.md files written and the recursion depth used
* Provide a 5 to 10 bullet summary of what you generated for the target folder ($1).
* Mention any uncertainty and exactly which files you would read next if the user wants higher accuracy.
* If any folders were skipped due to ignore rules, symlinks, or safeguards, list them briefly with the reason.