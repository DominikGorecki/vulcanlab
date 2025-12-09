"""Suggest which document sections should be chunked and vectorized.

This module analyzes markdown document headings and uses an LLM to determine
which sections contain valuable content worth vectorizing versus sections
like table of contents, indexes, and references that should be skipped.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Usage:
    from vulcanlab.chunking.suggested_chunks import suggest_chunks_from_work
    output_path = suggest_chunks_from_work(work_id=1)

Examples:
    # Basic usage - creates document.vec_sugg.md
    from vulcanlab.chunking.suggested_chunks import suggest_chunks_from_work
    result = suggest_chunks_from_work(work_id=1)

    # Use full LLM model for better results
    result = suggest_chunks_from_work(work_id=1, use_full_model=True)

Functions:
    suggest_chunks_from_work(work_id, use_full_model, force, verbose) - Analyze from Work by ID
    suggest_chunks(input_path, bib_info, verbose) - Analyze from file path (legacy)

Exceptions:
    HashMismatchError - Raised when file hashes don't match database
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vulcanlab.chunking.bib_extractor import BibliographicInfo
from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.template_loader import load_template
from vulcanlab.sanitization.extract_titles import extract_titles_to_file, extract_titles_from_work, HashMismatchError
from vulcanlab.utils.file_utils import compute_file_hash, set_file_readonly, set_file_writable, is_file_readonly


def _build_prompt(titles_content: str, bib_info: BibliographicInfo | None) -> str:
    """Build the LLM prompt for analyzing titles.

    This function creates the prompt for the LLM to analyze document headings
    and suggest which sections to vectorize.

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        titles_content: The titles codeblock content.
        bib_info: Optional bibliographic information about the work.

    Returns:
        Formatted prompt string.
    """
    # Build bibliographic section if available
    bib_section = ""
    if bib_info:
        bib_parts = []
        if bib_info.title:
            bib_parts.append(f"Title: {bib_info.title}")
        if bib_info.authors:
            bib_parts.append(f"Authors: {', '.join(bib_info.authors)}")
        if hasattr(bib_info, 'publication_date') and bib_info.publication_date:
            bib_parts.append(f"Publication Date: {bib_info.publication_date}")
        if hasattr(bib_info, 'year') and bib_info.year:
            bib_parts.append(f"Year: {bib_info.year}")
        if bib_info.publisher:
            bib_parts.append(f"Publisher: {bib_info.publisher}")
        if bib_parts:
            bib_section = "## Bibliographic Information\n" + "\n".join(bib_parts) + "\n\n"

    # Define fallback template builder
    def get_fallback_template():
        return """You are analyzing a document's heading structure to determine which sections contain valuable content worth vectorizing for a RAG (Retrieval Augmented Generation) system. Your goal is to include headings whose underlying sections contain explanatory, conceptual, or narrative content, and to exclude purely structural, navigational, or index-like sections.

{bib_section}## Document Headings

{titles_content}

## Task

For each heading line number, determine whether it should be:

* **VECTORIZE**: The section under this heading likely contains meaningful prose or explanatory content that would help answer questions about the document's subject matter.
* **SKIP**: The section is primarily structural, navigational, index-like, or otherwise not useful as semantic knowledge for RAG.

## Decision Strategy

First, classify each heading based on its title. Then, enforce hierarchy rules so that parent headings are consistent with their children.

### A. Hierarchy rules

* Infer heading levels from markdown markers ("#", "##", "###", etc.) and/or numbering (e.g., "1.", "1.1.", "2.3.4").
* If any sub-heading is **VECTORIZE**, all of its ancestor headings (its parent, the parent's parent, etc.) MUST also be **VECTORIZE**.
* If a high-level heading looks structural (e.g., "Appendices", "Back Matter") but has child headings that clearly describe substantive content (e.g., "Appendix A: Experimental Stimuli"), treat those child headings and their ancestors as **VECTORIZE**.
* Do NOT force children to SKIP just because a parent is SKIP; children can still be **VECTORIZE** if they look like substantive content sections.

### B. Content to SKIP (structural / non-semantic)

Mark a heading as **SKIP** when it clearly indicates one of the following:

* Table of contents and navigation:

  * "Contents", "Table of Contents", "Detailed Contents", "List of Chapters"
  * "List of Figures", "List of Tables", "List of Boxes", "List of Abbreviations", "List of Acronyms"
* Indexes:

  * "Index", "Subject Index", "Author Index", "Name Index"
* References and bibliographic material:

  * "References", "Reference List", "Bibliography", "Works Cited", "Notes" / "Endnotes" sections that are primarily citation notes
* Pure front matter:

  * "Title Page", "Copyright", "Imprint", "Publication Data", "Dedication"
  * "Acknowledgments" / "Acknowledgements", "About the Author", "Foreword" (unless clearly domain-explanatory)
* Pure back matter or raw reference material:

  * Headings that obviously denote only raw data, item lists, or mechanical material such as:

    * "Data Tables", "Codebook", "Questionnaire Items", "Survey Items", "Answer Key"
    * "Appendix: Tables", "Appendix: Data", "Appendix: Raw Scores"
* Any heading that is clearly just a navigation/structure label with no real prose under it (e.g., "Part I", "Section I" by itself), **unless** its children are VECTORIZE (in which case the parent must also be VECTORIZE).

Only mark a heading as **SKIP** if it is very likely to be structurally / mechanically focused rather than explanatory content.

### C. Content to VECTORIZE (semantic / explanatory)

Mark a heading as **VECTORIZE** when the section under it is likely to contain any of the following:

* Core chapters and numbered sections that present the main subject matter.

  * e.g., "Chapter 1: Introduction to Cognitive Psychology", "2.3 Working Memory Capacity"
* Sections that define, explain, or discuss concepts, theories, models, mechanisms, or arguments.

  * e.g., "Theories of Intelligence", "Reinforcement Learning", "Social Identity Theory"
* Sections that describe methods, procedures, or empirical findings in a way that could answer user questions.

  * e.g., "Method", "Participants", "Procedure", "Results", "Discussion", "Implications", "Limitations"
* Sections that summarize, synthesize, or generalize information.

  * e.g., "Summary", "Conclusion", "General Discussion", "Practical Applications", "Future Directions"
* Worked examples, case studies, and explanatory exercises that teach or illustrate concepts.

  * e.g., "Case Study: Phineas Gage", "Example Problems", "Worked Example"
* Appendices that look conceptual or explanatory rather than purely tabular / raw data.

  * e.g., "Appendix A: Mathematical Derivation", "Appendix B: Scale Construction and Interpretation"

When in doubt, if a heading sounds like it could contain substantive explanatory text that would help answer questions about the topic, prefer **VECTORIZE** over **SKIP**.

## Output Format

Return ONLY a list in this exact format, one line per heading, preserving the original order of headings:

```
[line_number]: [SKIP|VECTORIZE]
```

Example:

```
10: SKIP
13: SKIP
18: VECTORIZE
19: VECTORIZE
20: VECTORIZE
```

Do NOT include any other commentary, explanations, or text. Analyze the headings and provide only your final SKIP/VECTORIZE labels:"""

    # Load template from database with fallback
    template = load_template("vectorization_suggestions", get_fallback_template)

    # Format template with variables
    return template.format(
        bib_section=bib_section,
        titles_content=titles_content
    )


def _parse_heading_level(line: str) -> int:
    """Extract heading level from a title line.

    Args:
        line: A line like "10: # Title" or "10: ### Subsection"

    Returns:
        Heading level (1-6) or 0 if not a heading.
    """
    # Match the heading after the line number
    match = re.search(r':\s*(#+)', line)
    if match:
        return len(match.group(1))
    return 0


def _parse_llm_response(response: str) -> dict[int, str]:
    """Parse LLM response into line number to decision mapping.

    Args:
        response: LLM response text.

    Returns:
        Dictionary mapping line numbers to SKIP/VECTORIZE decisions.
    """
    decisions = {}

    # Extract content from code blocks if present
    if "```" in response:
        blocks = re.findall(r'```(?:\w*\n)?(.*?)```', response, re.DOTALL)
        if blocks:
            response = blocks[-1]  # Use last code block

    # Parse each line
    for line in response.strip().split('\n'):
        match = re.match(r'(\d+):\s*(SKIP|VECTORIZE)', line.strip(), re.IGNORECASE)
        if match:
            line_num = int(match.group(1))
            decision = match.group(2).upper()
            decisions[line_num] = decision

    return decisions


def _apply_hierarchy_rules(
    decisions: dict[int, str],
    titles: list[str]
) -> dict[int, str]:
    """Apply hierarchy rules to decisions.

    Rules:
    - If a parent (H1/H2) is SKIP, all children should be SKIP
    - If any child is VECTORIZE, the parent should be VECTORIZE

    Args:
        decisions: Initial decisions from LLM.
        titles: List of title lines with line numbers.

    Returns:
        Updated decisions with hierarchy rules applied.
    """
    # Parse titles into structured format
    parsed = []
    for title in titles:
        match = re.match(r'(\d+):\s*(#+)', title)
        if match:
            line_num = int(match.group(1))
            level = len(match.group(2))
            parsed.append((line_num, level))

    if not parsed:
        return decisions

    result = decisions.copy()

    # First pass: propagate SKIP down
    for i, (line_num, level) in enumerate(parsed):
        if result.get(line_num) == 'SKIP':
            # Mark all children as SKIP
            for j in range(i + 1, len(parsed)):
                child_num, child_level = parsed[j]
                if child_level > level:
                    result[child_num] = 'SKIP'
                else:
                    break  # No longer a child

    # Second pass: propagate VECTORIZE up
    for i in range(len(parsed) - 1, -1, -1):
        line_num, level = parsed[i]
        if result.get(line_num) == 'VECTORIZE':
            # Find parent and mark as VECTORIZE
            for j in range(i - 1, -1, -1):
                parent_num, parent_level = parsed[j]
                if parent_level < level:
                    result[parent_num] = 'VECTORIZE'
                    level = parent_level  # Continue up the hierarchy

    return result


def suggest_chunks(
    input_path: str | Path,
    bib_info: "BibliographicInfo | None" = None,
    verbose: bool = False
) -> Path:
    """Analyze document headings and suggest which sections to vectorize.

    Args:
        input_path: Path to the sanitized markdown file.
        bib_info: Optional bibliographic information for context.
        verbose: Whether to print progress information.

    Returns:
        Path to the created suggestions file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() not in ('.md', '.markdown'):
        raise ValueError(f"Input file must be a markdown file: {input_path}")

    # Step 1: Extract titles
    if verbose:
        print(f"Extracting titles from {input_path.name}...")

    titles_path = extract_titles_to_file(input_path)

    if verbose:
        print(f"Titles saved to {titles_path.name}")

    # Step 2: Read titles content
    titles_content = titles_path.read_text(encoding='utf-8')

    # Extract the titles list from the file
    titles_match = re.search(r'```\n(.*?)```', titles_content, re.DOTALL)
    if not titles_match:
        raise ValueError("Could not find titles codeblock in titles file")

    titles_block = titles_match.group(1).strip()
    titles_list = titles_block.split('\n')

    # Step 3: Build and send prompt to LLM
    if verbose:
        print("Analyzing headings with LLM...")

    prompt = _build_prompt(titles_block, bib_info)

    # Lazy import - only load AI module when LLM is needed
    from vulcanlab.ai import create_langchain_chat, ModelTier

    langchain_stack = create_langchain_chat(
        settings=None,
        tier=ModelTier.LIGHT,
        search=True,
        temperature=0.2
    )

    response = langchain_stack.chat.invoke(prompt)
    response_text = response.content

    # Handle case where content might be a list
    if isinstance(response_text, list):
        response_text = '\n'.join(str(item) for item in response_text)

    # Step 4: Parse response and apply hierarchy rules
    decisions = _parse_llm_response(response_text)
    decisions = _apply_hierarchy_rules(decisions, titles_list)

    # Step 5: Build output content
    output_lines = ["# CHANGES TO HEADINGS", "```"]

    for title in titles_list:
        match = re.match(r'(\d+):', title)
        if match:
            line_num = int(match.group(1))
            decision = decisions.get(line_num, 'VECTORIZE')  # Default to VECTORIZE
            output_lines.append(f"{line_num}: {decision}")

    output_lines.append("```")
    output_content = "\n".join(output_lines)

    # Step 6: Save output
    output_path = input_path.with_suffix('.vectorize_suggestions.md')
    output_path.write_text(output_content, encoding='utf-8')

    if verbose:
        print(f"Suggestions saved to {output_path.name}")

    return output_path


def build_prompt_for_vec_suggestions(
    work_id: int,
    force: bool = False,
    verbose: bool = False
) -> dict:
    """Build the LLM prompt for vec suggestions for a work.

    Args:
        work_id: Database ID of the work.
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.

    Returns:
        Dictionary with prompt, work info, and titles list.

    Raises:
        ValueError: If work_id not found or sanitized file not in database.
        HashMismatchError: If file hash doesn't match stored hash (unless force=True).
        FileNotFoundError: If files referenced in database don't exist on disk.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")

        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")

        # Only use sanitized markdown
        if "sanitized" not in work.files:
            raise ValueError(
                f"Work {work_id} does not have 'sanitized' in files metadata. "
                f"Run apply_title_changes_from_work first to create sanitized markdown."
            )

        # Get sanitized file info
        sanitized_info = work.files["sanitized"]
        sanitized_path = Path(sanitized_info["path"])
        sanitized_stored_hash = sanitized_info["hash"]

        if verbose:
            print(f"Analyzing sanitized markdown: {sanitized_path}")

        # Validate sanitized file exists
        if not sanitized_path.exists():
            raise FileNotFoundError(
                f"Sanitized file not found on disk: {sanitized_path}\n"
                f"Referenced in work {work_id}, key 'sanitized'"
            )

        # Compute current hash and validate
        sanitized_current_hash = compute_file_hash(sanitized_path)

        if sanitized_current_hash != sanitized_stored_hash and not force:
            raise HashMismatchError(sanitized_stored_hash, sanitized_current_hash)

        if sanitized_current_hash != sanitized_stored_hash and verbose:
            print(f"Warning: Sanitized file hash mismatch, proceeding with --force")

        # Check if sanitized_titles exists, if not generate it
        titles_path = None
        if "sanitized_titles" in work.files:
            # Titles exist in database, use them
            titles_info = work.files["sanitized_titles"]
            titles_path = Path(titles_info["path"])
            titles_stored_hash = titles_info["hash"]

            if verbose:
                print(f"Using existing titles file: {titles_path}")

            # Validate titles file exists
            if not titles_path.exists():
                raise FileNotFoundError(
                    f"Titles file not found on disk: {titles_path}\n"
                    f"Referenced in work {work_id}, key 'sanitized_titles'"
                )

            # Validate titles hash
            titles_current_hash = compute_file_hash(titles_path)
            if titles_current_hash != titles_stored_hash and not force:
                raise HashMismatchError(titles_stored_hash, titles_current_hash)

            if titles_current_hash != titles_stored_hash and verbose:
                print(f"Warning: Titles file hash mismatch, proceeding with --force")

        else:
            # Generate titles file
            if verbose:
                print(f"Generating titles from sanitized markdown...")

            titles_path = extract_titles_from_work(
                work_id=work_id,
                source_key="sanitized",
                force=force,
                verbose=verbose
            )

            if verbose:
                print(f"Titles generated: {titles_path}")

            # Refresh work to get updated files metadata
            session.refresh(work)

        # Read titles content
        titles_content = titles_path.read_text(encoding='utf-8')

        # Extract the titles list from the file
        titles_match = re.search(r'```\n(.*?)```', titles_content, re.DOTALL)
        if not titles_match:
            raise ValueError("Could not find titles codeblock in titles file")

        titles_block = titles_match.group(1).strip()
        titles_list = titles_block.split('\n')

        # Build bibliographic info from work record
        bib_info = None
        if work.title or work.authors:
            # Lazy import - only load BibliographicInfo when needed
            from vulcanlab.chunking.bib_extractor import BibliographicInfo

            bib_parts = {}
            if work.title:
                bib_parts['title'] = work.title
            if work.authors:
                # Authors might be a string or list
                if isinstance(work.authors, str):
                    bib_parts['authors'] = [work.authors]
                else:
                    bib_parts['authors'] = work.authors
            if work.publisher:
                bib_parts['publisher'] = work.publisher
            if work.year:
                bib_parts['year'] = work.year

            bib_info = BibliographicInfo(**bib_parts)

            if verbose:
                print(f"Document: {work.title}")
                print(f"Authors: {work.authors}")

        # Build prompt
        prompt = _build_prompt(titles_block, bib_info)

        return {
            "prompt": prompt,
            "work_title": work.title,
            "work_authors": work.authors,
            "titles_list": titles_list
        }


def parse_vec_suggestions_response(response_text: str) -> dict[int, str]:
    """Parse LLM response into line number to decision mapping.

    Args:
        response_text: LLM response text.

    Returns:
        Dictionary mapping line numbers to SKIP/VECTORIZE decisions.
    """
    return _parse_llm_response(response_text)


def save_vec_suggestions_from_response(
    work_id: int,
    response_text: str,
    force: bool = False,
    verbose: bool = False
) -> Path:
    """Save vec suggestions from manual LLM response.

    Args:
        work_id: Database ID of the work.
        response_text: The LLM response text to parse.
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.

    Returns:
        Path to the created vectorization suggestions file.

    Raises:
        ValueError: If work_id not found or sanitized file not in database.
        HashMismatchError: If file hash doesn't match stored hash (unless force=True).
        FileNotFoundError: If files referenced in database don't exist on disk.
    """
    # Get prompt data (which validates everything and gets titles_list)
    prompt_data = build_prompt_for_vec_suggestions(work_id, force, verbose)
    titles_list = prompt_data["titles_list"]

    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")

        # Get sanitized path for output file naming
        sanitized_info = work.files["sanitized"]
        sanitized_path = Path(sanitized_info["path"])

        # Parse response and apply hierarchy rules
        decisions = _parse_llm_response(response_text)
        decisions = _apply_hierarchy_rules(decisions, titles_list)

        # Build output content
        output_lines = ["# CHANGES TO HEADINGS", "```"]

        for title in titles_list:
            match = re.match(r'(\d+):', title)
            if match:
                line_num = int(match.group(1))
                decision = decisions.get(line_num, 'VECTORIZE')  # Default to VECTORIZE
                output_lines.append(f"{line_num}: {decision}")

        output_lines.append("```")
        output_content = "\n".join(output_lines)

        # Determine output path: <file>.sanitized.md -> <file>.sanitized.vec_sugg.md
        output_path = sanitized_path.parent / f"{sanitized_path.stem}.vec_sugg.md"

        # Check if output file exists and is read-only
        if output_path.exists():
            if verbose:
                print(f"Output file already exists: {output_path}")

            # If it's read-only, we need to make it writable to overwrite
            if is_file_readonly(output_path):
                if verbose:
                    print(f"File is read-only, making it writable for overwrite")
                set_file_writable(output_path)

        # Write output file
        output_path.write_text(output_content, encoding='utf-8')

        if verbose:
            print(f"Suggestions written: {output_path}")

        # Set file to read-only
        set_file_readonly(output_path)

        if verbose:
            print(f"File set to read-only")

        # Compute hash of suggestions file
        suggestions_hash = compute_file_hash(output_path)

        # Update work's files metadata
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files["vec_suggestions"] = {
            "path": str(output_path.resolve()),
            "hash": suggestions_hash
        }
        work.files = updated_files

        session.commit()
        session.refresh(work)

        if verbose:
            print(f"Updated work {work_id} with 'vec_suggestions' file metadata")

    return output_path


def suggest_chunks_from_work(
    work_id: int,
    use_full_model: bool = False,
    force: bool = False,
    verbose: bool = False
) -> Path:
    """Analyze document headings from a work and suggest which sections to vectorize.

    Args:
        work_id: Database ID of the work.
        use_full_model: If True, use ModelTier.FULL instead of ModelTier.LIGHT.
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.

    Returns:
        Path to the created vectorization suggestions file.

    Raises:
        ValueError: If work_id not found or sanitized file not in database.
        HashMismatchError: If file hash doesn't match stored hash (unless force=True).
        FileNotFoundError: If files referenced in database don't exist on disk.
    """
    # Load work from database
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")

        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")

        # Only use sanitized markdown
        if "sanitized" not in work.files:
            raise ValueError(
                f"Work {work_id} does not have 'sanitized' in files metadata. "
                f"Run apply_title_changes_from_work first to create sanitized markdown."
            )

        # Get sanitized file info
        sanitized_info = work.files["sanitized"]
        sanitized_path = Path(sanitized_info["path"])
        sanitized_stored_hash = sanitized_info["hash"]

        if verbose:
            print(f"Analyzing sanitized markdown: {sanitized_path}")

        # Validate sanitized file exists
        if not sanitized_path.exists():
            raise FileNotFoundError(
                f"Sanitized file not found on disk: {sanitized_path}\n"
                f"Referenced in work {work_id}, key 'sanitized'"
            )

        # Compute current hash and validate
        sanitized_current_hash = compute_file_hash(sanitized_path)

        if sanitized_current_hash != sanitized_stored_hash and not force:
            raise HashMismatchError(sanitized_stored_hash, sanitized_current_hash)

        if sanitized_current_hash != sanitized_stored_hash and verbose:
            print(f"Warning: Sanitized file hash mismatch, proceeding with --force")

        # Check if sanitized_titles exists, if not generate it
        titles_path = None
        if "sanitized_titles" in work.files:
            # Titles exist in database, use them
            titles_info = work.files["sanitized_titles"]
            titles_path = Path(titles_info["path"])
            titles_stored_hash = titles_info["hash"]

            if verbose:
                print(f"Using existing titles file: {titles_path}")

            # Validate titles file exists
            if not titles_path.exists():
                raise FileNotFoundError(
                    f"Titles file not found on disk: {titles_path}\n"
                    f"Referenced in work {work_id}, key 'sanitized_titles'"
                )

            # Validate titles hash
            titles_current_hash = compute_file_hash(titles_path)
            if titles_current_hash != titles_stored_hash and not force:
                raise HashMismatchError(titles_stored_hash, titles_current_hash)

            if titles_current_hash != titles_stored_hash and verbose:
                print(f"Warning: Titles file hash mismatch, proceeding with --force")

        else:
            # Generate titles file
            if verbose:
                print(f"Generating titles from sanitized markdown...")

            titles_path = extract_titles_from_work(
                work_id=work_id,
                source_key="sanitized",
                force=force,
                verbose=verbose
            )

            if verbose:
                print(f"Titles generated: {titles_path}")

            # Refresh work to get updated files metadata
            session.refresh(work)

        # Read titles content
        titles_content = titles_path.read_text(encoding='utf-8')

        # Extract the titles list from the file
        titles_match = re.search(r'```\n(.*?)```', titles_content, re.DOTALL)
        if not titles_match:
            raise ValueError("Could not find titles codeblock in titles file")

        titles_block = titles_match.group(1).strip()
        titles_list = titles_block.split('\n')

        # Build bibliographic info from work record
        bib_info = None
        if work.title or work.authors:
            # Lazy import - only load BibliographicInfo when needed
            from vulcanlab.chunking.bib_extractor import BibliographicInfo

            bib_parts = {}
            if work.title:
                bib_parts['title'] = work.title
            if work.authors:
                # Authors might be a string or list
                if isinstance(work.authors, str):
                    bib_parts['authors'] = [work.authors]
                else:
                    bib_parts['authors'] = work.authors
            if work.publisher:
                bib_parts['publisher'] = work.publisher
            if work.year:
                bib_parts['year'] = work.year

            bib_info = BibliographicInfo(**bib_parts)

            if verbose:
                print(f"Document: {work.title}")
                print(f"Authors: {work.authors}")

        # Build and send prompt to LLM
        if verbose:
            print("Analyzing headings with LLM...")

        prompt = _build_prompt(titles_block, bib_info)

        # Lazy import - only load AI module when LLM is needed
        from vulcanlab.ai import create_langchain_chat, ModelTier

        tier = ModelTier.FULL if use_full_model else ModelTier.LIGHT

        if verbose:
            print(f"Calling LLM (tier: {'FULL' if use_full_model else 'LIGHT'})...")

        langchain_stack = create_langchain_chat(
            settings=None,
            tier=tier,
            search=True,
            temperature=0.2
        )

        response = langchain_stack.chat.invoke(prompt)
        response_text = response.content

        # Handle case where content might be a list
        if isinstance(response_text, list):
            response_text = '\n'.join(str(item) for item in response_text)

        if verbose:
            print("LLM response received")

        # Parse response and apply hierarchy rules
        decisions = _parse_llm_response(response_text)
        decisions = _apply_hierarchy_rules(decisions, titles_list)

        # Build output content
        output_lines = ["# CHANGES TO HEADINGS", "```"]

        for title in titles_list:
            match = re.match(r'(\d+):', title)
            if match:
                line_num = int(match.group(1))
                decision = decisions.get(line_num, 'VECTORIZE')  # Default to VECTORIZE
                output_lines.append(f"{line_num}: {decision}")

        output_lines.append("```")
        output_content = "\n".join(output_lines)

        # Determine output path: <file>.sanitized.md -> <file>.sanitized.vec_sugg.md
        output_path = sanitized_path.parent / f"{sanitized_path.stem}.vec_sugg.md"

        # Check if output file exists and is read-only
        if output_path.exists():
            if verbose:
                print(f"Output file already exists: {output_path}")

            # If it's read-only, we need to make it writable to overwrite
            if is_file_readonly(output_path):
                if verbose:
                    print(f"File is read-only, making it writable for overwrite")
                set_file_writable(output_path)

        # Write output file
        output_path.write_text(output_content, encoding='utf-8')

        if verbose:
            print(f"Suggestions written: {output_path}")

        # Set file to read-only
        set_file_readonly(output_path)

        if verbose:
            print(f"File set to read-only")

        # Compute hash of suggestions file
        suggestions_hash = compute_file_hash(output_path)

        # Update work's files metadata
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files["vec_suggestions"] = {
            "path": str(output_path.resolve()),
            "hash": suggestions_hash
        }
        work.files = updated_files

        session.commit()
        session.refresh(work)

        if verbose:
            print(f"Updated work {work_id} with 'vec_suggestions' file metadata")

    return output_path
