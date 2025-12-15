
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from vulcanlab_api.dependencies import get_db_session
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.work import Work

def check_latest_parsed():
    # Setup session
    from vulcanlab.data.database import get_session as db_session
    
    with db_session() as session:
        # Get latest work
        work = session.query(Work).order_by(Work.id.desc()).first()
        if not work:
            print("No work found")
            return

        print(f"Latest Work ID: {work.id}, Title: {work.title}")

        # Get parsed record
        parsed = session.query(ParsedMarkdown).filter(ParsedMarkdown.work_id == work.id).first()
        
        if not parsed:
            print("No ParsedMarkdown record found for this work")
            return

        print(f"Parsed ID: {parsed.id}")
        print(f"Classification: {parsed.classification.value}")
        print(f"Content Length (compressed): {len(parsed._content)} bytes")
        
        content = parsed.content
        print(f"Content Length (decompressed): {len(content)} chars")
        print("--- Start Content Preview ---")
        print(content[:500])
        print("--- End Content Preview ---")

if __name__ == "__main__":
    check_latest_parsed()
