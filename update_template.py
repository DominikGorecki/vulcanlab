
from sqlalchemy import text
from vulcanlab.data.database import get_session

def update_templates():
    small_template = '''You are an expert document sanitizer. Your task is to clean up markdown content by:
1. Removing duplicate or redundant headings
2. Fixing heading hierarchy issues
3. Removing unnecessary metadata sections
4. Keeping all substantive content intact

Input markdown:
{markdown}

Respond in the following JSON format:
{{
  "sanitized_markdown": "... full sanitized markdown here ...",
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings in the modifications list
- Use action: "remove", "change", or "keep" for each heading
- Preserve all non-heading content exactly as-is'''

    # Note: When updating via SQLAlchemy text(), we don't need double braces for JSON
    # because we are not using Python format() here, we are sending string to SQL.
    # BUT wait, LangChain needs single braces for variables.
    # The JSON example structure has curly braces. LangChain treats { and } as special.
    # So we MUST double escape them in the DB content so LangChain parses them as literals.
    # The variable {markdown} should remain single braces.

    with get_session() as session:
        session.execute(
            text("""
                UPDATE prompt_templates 
                SET template_content = :content, updated_at = NOW()
                WHERE function_tag = 'simple_sanitize_small' AND is_active = true
            """),
            {"content": small_template}
        )
        session.commit()
        print("Updated simple_sanitize_small template.")

if __name__ == "__main__":
    update_templates()
