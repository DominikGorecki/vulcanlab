#!/usr/bin/env python3
"""
Dump all active prompt templates from the working database.

This script extracts all active templates and saves them as individual files
in the seed_data/templates/ directory.

Usage:
    python scripts/dump_templates.py
"""

import sys
import yaml
from pathlib import Path
from sqlalchemy import create_engine, text

# Database connection info
DB_CONFIG = {
    "admin_user": "postgres",
    "admin_password": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "db_name": "psych_rag_test"
}

def get_engine():
    """Create database engine."""
    db_url = (
        f"postgresql+psycopg://{DB_CONFIG['admin_user']}:"
        f"{DB_CONFIG['admin_password']}"
        f"@{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/{DB_CONFIG['db_name']}"
    )
    return create_engine(db_url)


def dump_prompt_meta(conn):
    """Extract prompt_meta variable definitions."""
    result = conn.execute(text("""
        SELECT
            function_tag,
            variables
        FROM prompt_meta
        ORDER BY function_tag
    """))

    meta_dict = {}
    for row in result:
        meta_dict[row.function_tag] = row.variables

    return meta_dict


def dump_templates():
    """Dump all active templates and their variable definitions to individual files."""
    engine = get_engine()

    # Create output directory
    output_dir = Path("src/vulcanlab/data/seed_data/templates")
    seed_data_dir = Path("src/vulcanlab/data/seed_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dumping templates to {output_dir}/")

    with engine.connect() as conn:
        # Get all active templates
        result = conn.execute(text("""
            SELECT
                id,
                function_tag,
                version,
                title,
                template_content,
                template_type,
                is_active,
                created_at,
                updated_at
            FROM prompt_templates
            WHERE is_active = TRUE
            ORDER BY function_tag, version
        """))

        templates = list(result)

        if not templates:
            print("No active templates found!")
            return

        print(f"Found {len(templates)} active templates\n")

        for template in templates:
            # Create filename from function_tag
            filename = f"{template.function_tag}.txt"
            filepath = output_dir / filename

            # Write template content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template.template_content)

            print(f"✓ {template.function_tag} (v{template.version})")
            print(f"  Title: {template.title}")
            print(f"  Type: {template.template_type or 'N/A'}")
            print(f"  File: {filepath}")
            print()

        # Also create a metadata file with all template info
        metadata_file = output_dir / "_metadata.txt"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write("# Prompt Template Metadata\n")
            f.write("# Generated from working database\n\n")

            for template in templates:
                f.write(f"Function Tag: {template.function_tag}\n")
                f.write(f"Version: {template.version}\n")
                f.write(f"Title: {template.title}\n")
                f.write(f"Type: {template.template_type or 'N/A'}\n")
                f.write(f"Is Active: {template.is_active}\n")
                f.write(f"Created: {template.created_at}\n")
                f.write(f"Updated: {template.updated_at}\n")
                f.write(f"Content File: {template.function_tag}.txt\n")
                f.write("-" * 80 + "\n\n")

        print(f"✓ Metadata written to {metadata_file}")
        print(f"\nTotal: {len(templates)} templates extracted")

        # Dump prompt_meta variable definitions
        print("\n" + "=" * 80)
        print("Extracting variable definitions (prompt_meta)...")
        print("=" * 80)

        prompt_meta = dump_prompt_meta(conn)

        if prompt_meta:
            # Create variables.yaml file
            variables_file = seed_data_dir / "variables.yaml"

            variables_data = {
                "variables": []
            }

            for function_tag, variables in prompt_meta.items():
                variables_data["variables"].append({
                    "function_tag": function_tag,
                    "variables": variables
                })

            with open(variables_file, 'w', encoding='utf-8') as f:
                yaml.dump(variables_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            print(f"\n✓ Variable definitions written to {variables_file}")
            print(f"  Found variable definitions for {len(prompt_meta)} templates:")
            for function_tag in prompt_meta.keys():
                print(f"    - {function_tag}")
        else:
            print("\n⚠ No prompt_meta records found")

        print("\n" + "=" * 80)
        print("COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    try:
        dump_templates()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
