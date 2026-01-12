
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from vulcanlab.data.database import SessionLocal
from vulcanlab.data.models.collection import Collection
from vulcanlab.data.models.collection_item import CollectionItem
from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.data.models.research_section import ResearchSection
from vulcanlab.data.models.research_report import ResearchReport
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase, CollectionItemType
from vulcanlab.research.workflow import create_research_graph, start_automated_research
from vulcanlab.data.research_session import (
    create_research_session, 
    get_research_session_by_thread_id,
    update_research_session
)

class DeepResearchE2EVerification(unittest.TestCase):
    def setUp(self):
        self.db_session = SessionLocal()
        # Create a test collection
        self.collection = Collection(
            name=f"E2E Test Collection {int(time.time() * 1000)}",
            description="A collection for end-to-end testing of deep research."
        )
        self.db_session.add(self.collection)
        self.db_session.commit()
        self.db_session.refresh(self.collection)
        
        # Add some items
        self.item_ids = []
        for i in range(3):
            item = CollectionItem(
                collection_id=self.collection.id,
                item_type=CollectionItemType.RESEARCH_RESULT,
                link=f"/research/results/{i+6000}", 
                note=f"Test Item {i}"
            )
            self.db_session.add(item)
            self.db_session.flush()
            self.item_ids.append(item.id)
        self.db_session.commit()

    def tearDown(self):
        # Clean up
        try:
            self.db_session.query(ResearchReport).filter(
                ResearchReport.session_id.in_(
                    self.db_session.query(ResearchSession.id).filter_by(collection_id=self.collection.id)
                )
            ).delete(synchronize_session=False)
            self.db_session.query(ResearchSection).filter(
                ResearchSection.session_id.in_(
                    self.db_session.query(ResearchSession.id).filter_by(collection_id=self.collection.id)
                )
            ).delete(synchronize_session=False)
            self.db_session.query(ResearchSession).filter_by(collection_id=self.collection.id).delete()
            self.db_session.query(CollectionItem).filter_by(collection_id=self.collection.id).delete()
            self.db_session.query(Collection).filter_by(id=self.collection.id).delete()
            self.db_session.commit()
        except Exception as e:
            print(f"Error in tearDown: {e}")
            self.db_session.rollback()
        finally:
            self.db_session.close()

    def test_automated_workflow_e2e(self):
        """Test the automated workflow from start to finish."""
        
        # Prepare responses
        responses = [
            # 1. Planner response
            json.dumps({
                "research_goal": "Test goal",
                "key_themes": ["test"],
                "sub_questions": [
                    {
                        "id": "Q1", 
                        "question": "What is test?", 
                        "rationale": "need to know", 
                        "estimated_tokens": 30000,
                        "relevant_items": self.item_ids
                    }
                ],
                "synthesis_approach": "simple"
            }),
            # 2. Synthesizer Q1 - High quality to pass evaluation
            ("Word " * 1000) + " [Source 1]. " + ("Word " * 1000) + " [Source 2]. " + ("Word " * 1000) + " [Source 3].",
            # 3. Final Synthesis (Workflow)
            "Final synthesized report content."
        ]
        
        def side_effect(prompt):
            if not responses:
                print(f"OUT OF RESPONSES! Prompt: {prompt[:100]}...")
                return MagicMock(content="Default")
            res = responses.pop(0)
            print(f"CALL {3 - len(responses)}: Prompt starts with: {prompt[:100]}")
            m = MagicMock()
            m.content = res
            return m
            
        mock_chat = MagicMock()
        mock_chat.invoke.side_effect = side_effect

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 768

        from langgraph.checkpoint.memory import MemorySaver

        with patch("vulcanlab.research.nodes.research_planner_node.create_langchain_chat") as p1, \
             patch("vulcanlab.research.nodes.synthesizer_node.create_langchain_chat") as p2, \
             patch("vulcanlab.research.workflow.create_langchain_chat") as p3, \
             patch("vulcanlab.research.result_matcher.create_embeddings") as p4, \
             patch("vulcanlab.research.workflow.PostgresSaver") as p5, \
             patch("vulcanlab.research.context_assembler.fetch_collection_items") as p6, \
             patch("vulcanlab.research.nodes.quality_evaluator_node.evaluate_quality") as p7, \
             patch("vulcanlab.research.nodes.quality_evaluator_node.check_citation_coverage") as p8:
            
            p1.return_value.chat = mock_chat
            p2.return_value.chat = mock_chat
            p3.return_value.chat = mock_chat
            p4.return_value = mock_embeddings
            p5.return_value = MemorySaver()
            
            # Mock evaluate_quality to always pass
            p7.return_value = {
                "citation_coverage": 1.0,
                "source_diversity": 3,
                "coherence_score": "High",
                "completeness_score": "High"
            }
            # Mock check_citation_coverage to return no broken citations
            p8.return_value = []
            
            p6.return_value = [
                {"item_id": self.item_ids[0], "type": "research_result", "content": "C1", "work_id": 1, "work_title": "Source 1", "work_metadata": {"work_id": 1, "title": "Source 1", "authors": "A1", "year": 2020}},
                {"item_id": self.item_ids[1], "type": "research_result", "content": "C2", "work_id": 2, "work_title": "Source 2", "work_metadata": {"work_id": 2, "title": "Source 2", "authors": "A2", "year": 2021}},
                {"item_id": self.item_ids[2], "type": "research_result", "content": "C3", "work_id": 3, "work_title": "Source 3", "work_metadata": {"work_id": 3, "title": "Source 3", "authors": "A3", "year": 2022}},
            ]
            
            # Start automated research
            session_id, thread_id = start_automated_research(self.collection.id, self.db_session)
            
            # Verify session created and completed
            session = self.db_session.query(ResearchSession).get(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(session.status, SessionStatus.COMPLETED)
            
            # Verify report exists
            report = self.db_session.query(ResearchReport).filter_by(session_id=session_id).first()
            self.assertIsNotNone(report)
            print(f"ACTUAL REPORT CONTENT: {report.report_content}")
            self.assertIn("Final synthesized report content", report.report_content)

    def test_manual_workflow_resume_e2e(self):
        """Test creating a manual session, pausing, and resuming."""
        thread_id = f"manual_e2e_{int(time.time() * 1000)}"
        session_obj = create_research_session(self.db_session, self.collection.id, SessionType.MANUAL, thread_id)
        session_id = session_obj.id
        update_research_session(self.db_session, session_id, {"current_phase": ResearchPhase.RESEARCH})
        resumed_session = get_research_session_by_thread_id(self.db_session, thread_id)
        self.assertEqual(resumed_session.id, session_id)

    def test_authorization_simulated(self):
        """Verify that we can check session ownership (simplified)."""
        thread_id = f"auth_test_{int(time.time() * 1000)}"
        session_obj = create_research_session(self.db_session, self.collection.id, SessionType.MANUAL, thread_id)
        session = get_research_session_by_thread_id(self.db_session, thread_id)
        self.assertEqual(session.collection_id, self.collection.id)

if __name__ == "__main__":
    unittest.main()
