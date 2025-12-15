
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from vulcanlab.data.models.prompt_template import PromptTemplate

def check_template():
    # Setup session
    from vulcanlab.data.database import get_session as db_session
    
    with db_session() as session:
        t = session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == 'simple_sanitize_small'
        ).first()

        if not t:
            print("No template found")
            return

        print(f"Template ID: {t.id}, Active: {t.is_active}")
        print("--- Template Content Start ---")
        print(t.template_content)
        print("--- Template Content End ---")

        if "{markdown}" in t.template_content:
            print("SUCCESS: {markdown} placeholder found")
        else:
            print("FAILURE: {markdown} placeholder NOT found")

if __name__ == "__main__":
    check_template()
