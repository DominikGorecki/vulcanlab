"""
Prompt template seeding from YAML configuration files.

Seeds prompt templates and their variable definitions from
file-based configuration in the seed_data directory.
"""

import json
from pathlib import Path

import yaml
from sqlalchemy import text

from ..database import engine


def seed_prompt_templates(verbose: bool = False) -> None:
    """
    Seed all prompt templates from YAML config and individual template files.

    Reads templates.yaml configuration and loads template content from
    individual .txt files in the seed_data/templates/ directory.

    Also seeds prompt_meta (variable definitions) from variables.yaml.

    This replaces the old hardcoded SQL approach and allows easy modification
    of templates by editing the .txt files.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Seeding prompt templates from configuration files...")

    # Get path to templates directory
    seed_data_dir = Path(__file__).parent.parent / "seed_data"
    templates_config_path = seed_data_dir / "templates.yaml"
    variables_config_path = seed_data_dir / "variables.yaml"
    templates_dir = seed_data_dir / "templates"

    # Load templates configuration
    if not templates_config_path.exists():
        if verbose:
            print(f"Warning: templates.yaml not found at {templates_config_path}")
        return

    with open(templates_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    templates = config.get('templates', [])
    if not templates:
        if verbose:
            print("Warning: No templates found in templates.yaml")
        return

    # Load variables configuration
    variables_map = {}
    if variables_config_path.exists():
        with open(variables_config_path, 'r', encoding='utf-8') as f:
            variables_config = yaml.safe_load(f)
            for var_entry in variables_config.get('variables', []):
                variables_map[var_entry['function_tag']] = var_entry['variables']

    with engine.connect() as conn:
        seeded_count = 0
        skipped_count = 0
        meta_seeded_count = 0
        meta_skipped_count = 0

        for template_config in templates:
            function_tag = template_config['function_tag']
            version = template_config['version']
            title = template_config['title']
            template_type = template_config.get('template_type')
            is_active = template_config.get('is_active', True)
            content_file = template_config['content_file']

            # Check if template already exists
            result = conn.execute(
                text("""
                    SELECT COUNT(*) FROM prompt_templates
                    WHERE function_tag = :tag AND version = :ver
                """),
                {"tag": function_tag, "ver": version}
            )
            exists = result.scalar() > 0

            if exists:
                if verbose:
                    print(f"  Template {function_tag} v{version} already exists, skipping")
                skipped_count += 1
                continue

            # Load template content from file
            content_path = templates_dir / content_file
            if not content_path.exists():
                if verbose:
                    print(f"  Warning: Template file not found: {content_path}")
                continue

            with open(content_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Insert template
            conn.execute(
                text("""
                    INSERT INTO prompt_templates
                    (function_tag, version, title, template_content, template_type, is_active, created_at, updated_at)
                    VALUES (:tag, :ver, :title, :content, :type, :active, NOW(), NOW())
                """),
                {
                    "tag": function_tag,
                    "ver": version,
                    "title": title,
                    "content": template_content,
                    "type": template_type,
                    "active": is_active
                }
            )
            seeded_count += 1

            if verbose:
                print(f"  Seeded: {function_tag} v{version} - {title}")

        # Seed prompt_meta (variable definitions)
        if variables_map:
            if verbose:
                print("\n  Seeding variable definitions (prompt_meta)...")

            for function_tag, variables in variables_map.items():
                # Check if meta already exists
                result = conn.execute(
                    text("SELECT COUNT(*) FROM prompt_meta WHERE function_tag = :tag"),
                    {"tag": function_tag}
                )
                meta_exists = result.scalar() > 0

                if meta_exists:
                    if verbose:
                        print(f"    Variables for {function_tag} already exist, skipping")
                    meta_skipped_count += 1
                    continue

                # Insert prompt_meta
                conn.execute(
                    text("""
                        INSERT INTO prompt_meta (function_tag, variables, created_at, updated_at)
                        VALUES (:tag, CAST(:vars AS jsonb), NOW(), NOW())
                    """),
                    {
                        "tag": function_tag,
                        "vars": json.dumps(variables)
                    }
                )
                meta_seeded_count += 1

                if verbose:
                    print(f"    Seeded variables for: {function_tag} ({len(variables)} variables)")

        conn.commit()

        if verbose:
            print(f"\nTemplate seeding complete: {seeded_count} seeded, {skipped_count} skipped")
            if variables_map:
                print(f"Variable definitions: {meta_seeded_count} seeded, {meta_skipped_count} skipped")


def seed_simple_conversion_templates(verbose: bool = False) -> None:
    """
    DEPRECATED: Use seed_prompt_templates() instead.

    This function is kept for backwards compatibility but now just calls
    the new file-based seeding function.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Note: seed_simple_conversion_templates() is deprecated, using seed_prompt_templates()")
    seed_prompt_templates(verbose=verbose)
