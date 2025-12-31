#!/usr/bin/env python3
"""
Test script to verify template seeding from YAML config works correctly.

This script tests the new file-based template seeding mechanism without
requiring a full database initialization.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml


def test_templates_config():
    """Test that templates.yaml is valid and all referenced files exist."""
    print("Testing template configuration...")

    # Get paths
    seed_data_dir = Path(__file__).parent.parent / "src" / "vulcanlab" / "data" / "seed_data"
    templates_config_path = seed_data_dir / "templates.yaml"
    templates_dir = seed_data_dir / "templates"

    # Check templates.yaml exists
    if not templates_config_path.exists():
        print(f"❌ FAIL: templates.yaml not found at {templates_config_path}")
        return False

    print(f"✓ Found templates.yaml at {templates_config_path}")

    # Load and parse YAML
    try:
        with open(templates_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ FAIL: Could not parse templates.yaml: {e}")
        return False

    print(f"✓ Successfully parsed templates.yaml")

    # Check structure
    if 'templates' not in config:
        print("❌ FAIL: No 'templates' key in config")
        return False

    templates = config['templates']
    print(f"✓ Found {len(templates)} templates in config")

    # Verify each template
    all_valid = True
    for i, template in enumerate(templates, 1):
        print(f"\nTemplate {i}:")
        print(f"  Function tag: {template.get('function_tag', 'MISSING')}")
        print(f"  Version: {template.get('version', 'MISSING')}")
        print(f"  Title: {template.get('title', 'MISSING')}")
        print(f"  Template type: {template.get('template_type', 'null')}")
        print(f"  Is active: {template.get('is_active', 'MISSING')}")

        # Check required fields
        required = ['function_tag', 'version', 'title', 'is_active', 'content_file']
        for field in required:
            if field not in template:
                print(f"  ❌ Missing required field: {field}")
                all_valid = False

        # Check content file exists
        if 'content_file' in template:
            content_file = template['content_file']
            content_path = templates_dir / content_file

            if content_path.exists():
                # Check file is readable and has content
                try:
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if len(content.strip()) == 0:
                        print(f"  ❌ Template file is empty: {content_file}")
                        all_valid = False
                    else:
                        print(f"  ✓ Content file exists and has {len(content)} characters: {content_file}")
                except Exception as e:
                    print(f"  ❌ Could not read template file {content_file}: {e}")
                    all_valid = False
            else:
                print(f"  ❌ Content file not found: {content_path}")
                all_valid = False

    return all_valid


def test_variables_config():
    """Test that variables.yaml is valid (optional but recommended)."""
    print("\nTesting variable definitions configuration...")

    # Get paths
    seed_data_dir = Path(__file__).parent.parent / "src" / "vulcanlab" / "data" / "seed_data"
    variables_config_path = seed_data_dir / "variables.yaml"

    # Check if variables.yaml exists (optional)
    if not variables_config_path.exists():
        print(f"⚠ variables.yaml not found at {variables_config_path} (optional)")
        return True

    print(f"✓ Found variables.yaml at {variables_config_path}")

    # Load and parse YAML
    try:
        with open(variables_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ FAIL: Could not parse variables.yaml: {e}")
        return False

    print(f"✓ Successfully parsed variables.yaml")

    # Check structure
    if 'variables' not in config:
        print("❌ FAIL: No 'variables' key in config")
        return False

    variables = config['variables']
    print(f"✓ Found {len(variables)} variable definitions in config")

    # Verify each definition
    all_valid = True
    for i, var_entry in enumerate(variables, 1):
        print(f"\nVariable definition {i}:")
        function_tag = var_entry.get('function_tag', 'MISSING')
        print(f"  Function tag: {function_tag}")

        # Check required fields
        if 'function_tag' not in var_entry:
            print(f"  ❌ Missing required field: function_tag")
            all_valid = False

        if 'variables' not in var_entry:
            print(f"  ❌ Missing required field: variables")
            all_valid = False
        else:
            variables_list = var_entry['variables']
            print(f"  ✓ {len(variables_list)} variables defined")

            # Check each variable
            for var in variables_list:
                if 'variable_name' not in var or 'variable_description' not in var:
                    print(f"    ❌ Variable missing name or description: {var}")
                    all_valid = False

    return all_valid


def main():
    """Main entry point."""
    print("=" * 80)
    print("Template Seeding Configuration Test")
    print("=" * 80)
    print()

    templates_ok = test_templates_config()
    variables_ok = test_variables_config()

    print()
    print("=" * 80)
    if templates_ok and variables_ok:
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
