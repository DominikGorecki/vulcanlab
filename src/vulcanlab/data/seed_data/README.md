# Template Seeding System

This directory contains the file-based template seeding system for VulcanLab prompt templates.

## Overview

The template seeding system uses a declarative YAML configuration file and individual template content files to seed the database with prompt templates during initialization. This approach makes it easy to:

- View and edit templates without touching Python code
- Version control template changes
- Add new templates by creating files
- Maintain template metadata in a structured format

## Directory Structure

```
seed_data/
├── templates.yaml          # Configuration file with template metadata
├── variables.yaml          # Variable definitions for templates (prompt_meta)
├── templates/              # Directory containing individual template files
│   ├── query_expansion.txt
│   ├── rag_augmentation.txt
│   ├── vectorization_suggestions.txt
│   ├── toc_extraction.txt
│   ├── heading_hierarchy.txt
│   ├── simple_sanitize_small.txt
│   ├── simple_sanitize_large.txt
│   ├── eval_default.txt
│   └── _metadata.txt       # Reference file with full template information
└── README.md               # This file
```

## How It Works

### 1. Configuration File (templates.yaml)

The `templates.yaml` file contains metadata for all templates to be seeded:

```yaml
templates:
  - function_tag: query_expansion
    version: 1
    title: "Query Expansion - Multi-Query Expansion (MQE) and HyDE"
    template_type: null
    is_active: true
    content_file: query_expansion.txt
```

**Required fields:**
- `function_tag`: Unique identifier for the template's function
- `version`: Version number (integer)
- `title`: Human-readable title
- `is_active`: Whether the template is active (boolean)
- `content_file`: Filename in the `templates/` directory

**Optional fields:**
- `template_type`: Type categorization (e.g., "eval", null for general)

### 2. Template Content Files (templates/*.txt)

Each template's actual content is stored in a separate `.txt` file in the `templates/` directory. These files contain the full prompt template text with variable placeholders (e.g., `{markdown}`, `{query}`).

**Example:** `simple_sanitize_small.txt`
```
You are an expert document processor preparing academic and research documents...

## Document to Process

{markdown}

---

## Sanitized Output
```

### 3. Variable Definitions (variables.yaml)

The `variables.yaml` file defines the placeholders available in each template and their descriptions. This populates the `prompt_meta` table and appears in the UI on the template settings page.

**Example:** `variables.yaml`
```yaml
variables:
  - function_tag: query_expansion
    variables:
      - variable_name: n
        variable_description: The number of alternative query reformulations
      - variable_name: query
        variable_description: The original user query
```

### 4. Seeding Process

During database initialization, the `seed_prompt_templates()` function:

1. Reads `templates.yaml` to get template metadata
2. For each template configuration:
   - Checks if the template already exists in the database
   - If not, loads the content from the corresponding `.txt` file
   - Inserts the template into the `prompt_templates` table
3. Reads `variables.yaml` (if present) to get variable definitions
4. For each variable definition:
   - Checks if variables for that function_tag already exist
   - If not, inserts into the `prompt_meta` table

## How to Modify Templates

### Edit an Existing Template

1. Locate the template file in `templates/` directory (e.g., `simple_sanitize_small.txt`)
2. Edit the content as needed
3. If changing the version, update `templates.yaml` to increment the version number
4. Reinitialize the database or manually update the template in the database

**Note:** Existing templates are not automatically updated. The seeding only inserts new templates (new function_tag/version combinations).

### Add a New Template

1. Create a new `.txt` file in the `templates/` directory with your template content
2. Add a new entry to `templates.yaml`:
   ```yaml
   - function_tag: my_new_template
     version: 1
     title: "My New Template"
     template_type: null
     is_active: true
     content_file: my_new_template.txt
   ```
3. Reinitialize the database to seed the new template

### Deactivate a Template

Set `is_active: false` in `templates.yaml`:

```yaml
- function_tag: old_template
  version: 1
  title: "Old Template"
  template_type: null
  is_active: false  # This template won't be seeded
  content_file: old_template.txt
```

### Add or Edit Variable Definitions

To define variables for a template (these appear in the UI settings page):

1. Edit `variables.yaml` to add or update variable definitions:
   ```yaml
   variables:
     - function_tag: my_template
       variables:
         - variable_name: my_var
           variable_description: Description of what this variable is used for
         - variable_name: another_var
           variable_description: Another variable description
   ```
2. Reinitialize the database to seed the new variables

**Note:** Variable definitions are optional. If a template doesn't have variables defined, it will still work, but the UI won't show available placeholders.

## Testing

Use the test script to verify your configuration:

```bash
python scripts/test_template_seeding.py
```

This script checks:
- `templates.yaml` is valid YAML
- All required fields are present in template configurations
- All referenced content files exist
- All content files are readable and non-empty
- `variables.yaml` (if present) is valid YAML
- All variable definitions have required fields (function_tag, variables)

## Database Initialization

The template seeding happens during database initialization:

```bash
python -m vulcanlab.data.init_db -v
```

The `-v` flag enables verbose output showing which templates are seeded.

## Implementation Details

### Code Location

- Templates configuration: `src/vulcanlab/data/seed_data/templates.yaml`
- Variables configuration: `src/vulcanlab/data/seed_data/variables.yaml`
- Template content files: `src/vulcanlab/data/seed_data/templates/*.txt`
- Seeding function: `src/vulcanlab/data/init_db.py::seed_prompt_templates()`

### Database Schema

Templates are stored in the `prompt_templates` table:

```sql
CREATE TABLE prompt_templates (
    id SERIAL PRIMARY KEY,
    function_tag VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    title TEXT NOT NULL,
    template_content TEXT NOT NULL,
    template_type VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_function_tag_version UNIQUE (function_tag, version)
);
```

Variable definitions are stored in the `prompt_meta` table:

```sql
CREATE TABLE prompt_meta (
    id SERIAL PRIMARY KEY,
    function_tag VARCHAR(100) UNIQUE NOT NULL,
    variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

The `variables` column stores a JSON array of objects with `variable_name` and `variable_description` fields.

### Idempotency

The seeding process is idempotent:
- Templates are only inserted if they don't already exist (by function_tag + version)
- Variable definitions are only inserted if they don't already exist (by function_tag)
- Running the seeding multiple times is safe
- Existing templates and variables are not modified or deleted

## Migration from Old System

The old system used hardcoded SQL INSERT statements in `seed_simple_conversion_templates()`. This has been replaced with the file-based system.

The old function is kept for backwards compatibility but now just calls `seed_prompt_templates()`:

```python
def seed_simple_conversion_templates(verbose: bool = False) -> None:
    """DEPRECATED: Use seed_prompt_templates() instead."""
    seed_prompt_templates(verbose=verbose)
```

## Extracting Templates from Database

If you need to extract templates from an existing database, use:

```bash
python scripts/dump_templates.py
```

This will:
- Connect to the database specified in the script
- Extract all active templates from `prompt_templates` table
- Extract all variable definitions from `prompt_meta` table
- Create/update `templates.yaml` with template metadata
- Create/update `variables.yaml` with variable definitions
- Create individual `.txt` files for each template content
- Create `_metadata.txt` with full template information for reference

## Best Practices

1. **Version Control:** Always increment the version number when making changes to a template
2. **Testing:** Test template changes in a development environment before deploying
3. **Documentation:** Update template titles to reflect their purpose
4. **Variable Naming:** Use clear, consistent variable names in templates (e.g., `{markdown}`, `{query}`)
5. **Formatting:** Use proper markdown formatting in template files for readability
6. **Backup:** Keep backups of templates before making significant changes

## Troubleshooting

### "templates.yaml not found"

Ensure the file exists at: `src/vulcanlab/data/seed_data/templates.yaml`

### "Template file not found"

Check that:
1. The filename in `templates.yaml` matches the actual file in `templates/`
2. The file has the correct extension (`.txt`)
3. The file path is relative to the `templates/` directory

### "No templates seeded"

This is normal if templates already exist in the database. The seeding process skips existing templates.

To force re-seeding:
1. Drop and recreate the database, or
2. Delete specific templates from the `prompt_templates` table

### PyYAML ImportError

If you get an import error for `yaml`, install the dependency:

```bash
pip install pyyaml
```

Or reinstall from `pyproject.toml`:

```bash
pip install -e .
```
