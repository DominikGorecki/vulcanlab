import os
import yaml
from pathlib import Path

def test_summarize_sections_template_exists():
    """Verify that the summarize_sections template file exists and is non-empty."""
    template_path = Path("src/vulcanlab/data/seed_data/templates/summarize_sections.txt")
    assert template_path.exists(), f"Template file not found at {template_path}"
    content = template_path.read_text()
    assert len(content) > 0, "Template file is empty"
    
    # Check for required placeholders
    assert "{sections_content}" in content
    assert "{context_headings}" in content
    
    # Check for JSON format instructions
    assert 'JSON array of objects' in content
    assert '"id"' in content
    assert '"summary"' in content

def test_summarize_sections_registration():
    """Verify that the template is registered correctly in templates.yaml."""
    config_path = Path("src/vulcanlab/data/seed_data/templates.yaml")
    assert config_path.exists()
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    templates = config.get("templates", [])
    summarize_entry = next((t for t in templates if t["function_tag"] == "summarize_sections"), None)
    
    assert summarize_entry is not None, "summarize_sections not found in templates.yaml"
    assert summarize_entry["version"] == 1
    assert summarize_entry["template_type"] == "summarize"
    assert summarize_entry["content_file"] == "summarize_sections.txt"
    assert summarize_entry["is_active"] is True

def test_summarize_sections_variables():
    """Verify that the template variables are documented in variables.yaml."""
    config_path = Path("src/vulcanlab/data/seed_data/variables.yaml")
    assert config_path.exists()
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    variables_list = config.get("variables", [])
    summarize_vars = next((v for v in variables_list if v["function_tag"] == "summarize_sections"), None)
    
    assert summarize_vars is not None, "summarize_sections not found in variables.yaml"
    
    vars_dict = {v["variable_name"]: v["variable_description"] for v in summarize_vars["variables"]}
    assert "sections_content" in vars_dict
    assert "context_headings" in vars_dict
