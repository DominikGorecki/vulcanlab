
import os
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append(os.path.abspath("src"))

from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.data.models.research_section import ResearchSection
from vulcanlab.data.models.research_report import ResearchReport
from vulcanlab.data.models.enums import SessionStatus

# Use the same DB URL as in the app
DATABASE_URL = "postgresql://vulcanlab:vulcanlab@localhost:5432/vulcanlab"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def check_session(session_id):
    print(f"--- Checking Session {session_id} ---")
    res_session = session.get(ResearchSession, session_id)
    if not res_session:
        print("Session not found")
        return

    print(f"Status: {res_session.status}")
    print(f"Current Phase: {res_session.current_phase}")
    print(f"Thread ID: {res_session.thread_id}")
    
    # Check sections
    sections = session.execute(select(ResearchSection).where(ResearchSection.session_id == session_id)).scalars().all()
    print(f"Number of sections: {len(sections)}")
    for s in sections:
        print(f"  - Section {s.question_id}: {s.question_text[:50]}... (Content length: {len(s.section_content) if s.section_content else 0})")

    # Check reports
    reports = session.execute(select(ResearchReport).where(ResearchReport.session_id == session_id)).scalars().all()
    print(f"Number of reports: {len(reports)}")
    for r in reports:
        print(f"  - Report ID {r.id}, Created at: {r.created_at}")

if __name__ == "__main__":
    session_id = 82
    if len(sys.argv) > 1:
        session_id = int(sys.argv[1])
    check_session(session_id)
