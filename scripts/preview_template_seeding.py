#!/usr/bin/env python3
"""
Preview what templates would be seeded from the configuration.

This script shows what the seed_prompt_templates() function would do
without actually touching the database.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml


def preview_seeding():
    """Preview what templates would be seeded."""
    # Get paths
    seed_data_dir = Path(__file__).parent.parent / "src" / "vulcanlab" / "data" / "seed_data"
    templates_config_path = seed_data_dir / "templates.yaml"
    templates_dir = seed_data_dir / "templates"

    # Load configuration
    with open(templates_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    templates = config.get('templates', [])

    print("=" * 80)
    print("Template Seeding Preview")
    print("=" * 80)
    print(f"\nConfiguration: {templates_config_path}")
    print(f"Templates directory: {templates_dir}")
    print(f"\nTotal templates to seed: {len(templates)}")
    print()

    for i, template_config in enumerate(templates, 1):
        function_tag = template_config['function_tag']
        version = template_config['version']
        title = template_config['title']
        template_type = template_config.get('template_type')
        is_active = template_config.get('is_active', True)
        content_file = template_config['content_file']

        print(f"{'─' * 80}")
        print(f"Template {i}: {function_tag} (v{version})")
        print(f"{'─' * 80}")
        print(f"  Title: {title}")
        print(f"  Type: {template_type if template_type else '(none)'}")
        print(f"  Active: {is_active}")
        print(f"  Content file: {content_file}")

        # Load and show preview of content
        content_path = templates_dir / content_file
        if content_path.exists():
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Show first 200 characters
            preview = content[:200].replace('\n', ' ')
            if len(content) > 200:
                preview += "..."

            print(f"  Content preview: {preview}")
            print(f"  Content length: {len(content)} characters")
        else:
            print(f"  ❌ ERROR: Content file not found!")

        print()

    print("=" * 80)
    print("SQL that would be executed for each template:")
    print("=" * 80)
    print("""
    INSERT INTO prompt_templates
    (function_tag, version, title, template_content, template_type, is_active, created_at, updated_at)
    VALUES (:tag, :ver, :title, :content, :type, :active, NOW(), NOW())

    (Only if template with same function_tag and version doesn't already exist)
    """)


def main():
    """Main entry point."""
    try:
        preview_seeding()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
