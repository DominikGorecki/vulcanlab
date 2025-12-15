# Generate README.ai.md for a folder

You will generate an AI oriented README named README.ai.md inside the folder given by the user.

Folder path argument: $ARGUMENTS

## Step 0: Clarify first (must ask, then wait)
Before reading or writing files, ask the user these questions in one message, with lettered options and defaults preselected. Tell the user they can reply with a compact answer like "1:A 2:C 3:DEFAULT" or just "DEFAULTS" to accept all defaults.

1) Output file
A. Create or overwrite README.ai.md in the target folder (default)
B. Update README.md instead

2) Rewrite strategy
A. Full rewrite every time (default)
B. Incremental update
C. Full rewrite but preserve a "Manual Notes" block if present (recommended, default)

3) Scope depth
A. Folder tree depth 1
B. Folder tree depth 2
C. Folder tree depth 3 (default)
D. Custom depth

4) Target size
A. Aim for about 600 words
B. Aim for about 1000 words, can be bigger if needed (default)
C. Aim for about 1500 words
D. No target, maximize completeness

5) What to include (default is all)
A. Purpose and quick start
B. Architecture overview
C. Entry points and main flows
D. Key conventions
E. Dependency overview
F. API contracts and interfaces
G. LLM handoff section
H. Gotchas (cap at 5 bullets)

6) Ignore rules
A. Respect .gitignore (default)
B. Ignore nothing
C. Respect .gitignore plus common ignores even if not listed (node_modules, dist, bin, obj)

7) Subfolder README handling (for subfolders within the chosen depth)
A. If a subfolder lacks README.md, stop and ask whether to proceed (default)
B. If missing, proceed anyway
C. If missing, create a tiny README.ai.md in that subfolder too

8) Symlinks
A. Follow symlinks (default)
B. Do not follow symlinks

9) Very large folders safeguard (only if needed)
A. If listing all files would be extremely long, ask whether to still list all (default)
B. Auto collapse large directories into counts

10) Output style
A. Headings with bullet first summaries (default)
B. Narrative paragraphs
C. Table heavy

After the user answers (or says DEFAULTS), proceed.

## Step 1: Validate inputs
- If $ARGUMENTS is empty, ask for the folder path and stop.
- Resolve the folder path. If it does not exist or is not a directory, ask for a valid folder path and stop.

## Step 2: Gather context (respect ignore rules)
Use file tools to inspect the folder while respecting the selected ignore rules.
- Read README.ai.md if it exists (for context). You will still do a full rewrite per the selected strategy.
- Read README.md in the target folder if present (for human intent, but do not edit it).
- Read ignore files as needed (.gitignore in repo root and relevant subfolders). If repo root is unclear, at minimum respect the closest .gitignore you can find when walking upward.
- Build a file tree to the selected depth, sorted, with no max on files listed unless the user explicitly chooses collapsing.

## Step 3: Subfolder summaries
For each subfolder within the selected depth:
- If README.md exists in that subfolder, read it first and produce a 2 to 4 sentence summary for that subfolder.
- If README.md does not exist:
  - Follow the selected behavior. If "stop and ask", present a list of subfolders missing README.md and ask once whether to proceed, skip, or generate minimal README.ai.md stubs.

## Step 4: Identify what is important to read (heuristic)
Goal: keep README.ai.md concise but high leverage for LLM coding.
Do not try to fully read every file. Use an importance heuristic:
High priority signals:
- Entry points: main, index, app, server, cli, Program.cs, __main__.py, cmd/*, src/main*, routes, controllers
- Public API surfaces: exported modules, interfaces, endpoints, schema files
- Config that defines behavior: package.json, tsconfig, pyproject, requirements, go.mod, Cargo.toml, csproj, solution files, docker files, CI workflows, lint and format configs
- Build and run scripts: Makefile, task runners, scripts directories

Read enough of the important files to accurately describe purpose, architecture, entry points, and conventions.
For non important files, rely on names and folder structure unless a detail is unclear.

## Step 5: Secrets and safety
- Never paste secrets, tokens, private keys, passwords, or full connection strings into README.ai.md.
- If you detect likely secrets in a file, do not reproduce them. Mention "Potential secret material detected and omitted" and point to the file path only.

## Step 6: Write README.ai.md (full rewrite)
Write README.ai.md into the target folder (default behavior), using this exact structure and keeping it tight.
- Prefer headings with bullet first summaries.
- Keep gotchas to max 5 bullets.
- Avoid huge code blocks. If a code snippet is needed, keep it under 10 lines.

### Required README.ai.md template

# {FolderName} (AI README)

## Purpose
- {1 to 3 bullets}
- {1 short paragraph if needed}

## Quick start
- {How to run, build, test, lint if discoverable}
- {If unknown, say what is missing and where to look}

## Architecture overview
- {3 to 8 bullets that describe major components and data flow}
- Key folders:
  - {folder} - {meaning}

## Entry points and main flows
- Entry points:
  - {path} - {what it starts}
- Typical flows:
  - {flow name}: {steps in 3 to 6 bullets}

## Key conventions
- {naming, layering, error handling, logging, configuration, tests, style}
- {include only what you can justify from the repo, do not guess}

## Dependencies overview
- Runtime dependencies: {bullets}
- Dev dependencies and tooling: {bullets}
- External services: {bullets, only if evidenced}

## APIs and contracts
- Endpoints, handlers, or RPC surfaces: {bullets with file pointers}
- Data models and schemas: {bullets with file pointers}
- Events, queues, background jobs: {bullets if present}

## Subfolders
- {subfolder path}: {2 to 4 sentence summary from its README.md}
- {repeat}

## File tree (depth {N})
{Include the full tree to the selected depth, respecting ignore rules.}

## LLM handoff
- When asking an LLM to work in this folder, include:
  - {top 5 to 12 highest leverage files or folders to add to context}
- Good first questions to ask:
  - {3 to 6 bullets}
- Guardrails:
  - {what must not be broken, tests to run, style expectations}

## Gotchas
- {max 5 bullets}

### Manual Notes (preserve if present and user selected preservation)
If preserving, keep everything between these markers exactly as is from the previous README.ai.md:
BEGIN MANUAL NOTES
{verbatim}
END MANUAL NOTES

## Step 7: Report back in chat
After writing README.ai.md:
- Briefly summarize what you generated in 5 to 10 bullets.
- Mention any uncertainty and exactly which files you would read next if the user wants higher accuracy.
- If you had to ask about missing subfolder READMEs, do not write README.ai.md until the user answers.
