"""
Unit tests for LangGraph workflow and orchestration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from vulcanlab.research.workflow import (
    final_synthesis_node,
    should_refine,
    create_research_graph,
    start_automated_research,
    LLMClientWrapper
)
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase
from vulcanlab.research.state import ResearchState


class TestWorkflow(unittest.TestCase):
    """Test suite for research workflow orchestration."""

    def setUp(self):
        self.mock_session = MagicMock()
        self.initial_state: ResearchState = {
            "collection_id": 1,
            "collection_description": "Test Research",
            "item_notes": [],
            "research_plan": {},
            "current_phase": "planning",
            "sections": {"Q1": {"content": "Section 1 content"}},
            "context_per_question": {},
            "reused_sections": {},
            "available_results": [],
            "synthesis": "",
            "quality_metrics": {},
            "refinement_needed": [],
            "refinement_iteration_count": 0,
            "thread_id": "test_thread"
        }

    def test_should_refine_true(self):
        """Test should_refine returns True when refinement is needed."""
        state = self.initial_state.copy()
        state["refinement_needed"] = ["Q1"]
        self.assertTrue(should_refine(state))

    def test_should_refine_false(self):
        """Test should_refine returns False when no refinement is needed."""
        state = self.initial_state.copy()
        state["refinement_needed"] = []
        self.assertFalse(should_refine(state))

    @patch("vulcanlab.research.workflow.create_langchain_chat")
    @patch("vulcanlab.research.workflow.load_template")
    @patch("vulcanlab.research.workflow.create_research_report")
    @patch("vulcanlab.research.workflow.get_research_session_by_thread_id")
    def test_final_synthesis_node(self, mock_get_session, mock_create_report, mock_load_template, mock_create_chat):
        """Test final_synthesis_node generates report and updates state."""
        # 1. Setup mocks
        # Mock LangChain PromptTemplate
        mock_template = Mock()
        mock_template.format.return_value = "Formatted synthesis prompt"
        mock_load_template.return_value = mock_template

        mock_chat = Mock()
        mock_chat.invoke.return_value.content = "Synthesized Report"
        mock_create_chat.return_value.chat = mock_chat

        mock_res_session = Mock()
        mock_res_session.id = 123
        mock_get_session.return_value = mock_res_session

        # 2. Call node
        final_state = final_synthesis_node(self.initial_state, self.mock_session)

        # 3. Assertions
        self.assertEqual(final_state["synthesis"], "Synthesized Report")
        self.assertEqual(final_state["current_phase"], ResearchPhase.COMPLETED.value)

        mock_load_template.assert_called_once_with("synthesis", fallback_builder=None)
        mock_template.format.assert_called_once()
        mock_create_report.assert_called_once()
        args, kwargs = mock_create_report.call_args
        self.assertEqual(kwargs["session_id"], 123)
        self.assertEqual(kwargs["report_content"], "Synthesized Report")

    def test_create_research_graph_structure(self):
        """Test that the graph is created with correct nodes and edges."""
        workflow = create_research_graph(self.mock_session)
        
        # Check nodes
        nodes = workflow.nodes
        expected_nodes = [
            "planner", "executor", "assembler", "synthesizer", 
            "evaluator", "refiner", "final_synthesis"
        ]
        for node in expected_nodes:
            self.assertIn(node, nodes)
            
        # Entry point is internal in LangGraph 1.0+
        # We'll just verify the graph compiles
        compiled = workflow.compile()
        self.assertIsNotNone(compiled)

    @patch("vulcanlab.research.workflow.get_research_session_by_thread_id")
    @patch("vulcanlab.research.workflow.StateGraph")
    @patch("vulcanlab.research.workflow.create_research_session")
    @patch("vulcanlab.research.workflow.update_research_session")
    def test_start_automated_research(self, mock_update_session, mock_create_session, mock_state_graph, mock_get_session):
        """Test start_automated_research orchestration flow."""
        # 1. Setup mocks
        mock_res_session = Mock()
        mock_res_session.id = 456
        mock_res_session.status = SessionStatus.IN_PROGRESS
        mock_res_session.current_phase = ResearchPhase.COMPLETED
        mock_create_session.return_value = mock_res_session
        mock_get_session.return_value = mock_res_session

        mock_graph_instance = mock_state_graph.return_value
        mock_compiled_graph = mock_graph_instance.compile.return_value

        # 2. Call function
        session_id, thread_id = start_automated_research(1, self.mock_session)

        # 3. Assertions
        self.assertEqual(session_id, 456)
        self.assertTrue(thread_id.startswith("auto_1_"))

        mock_create_session.assert_called_once()
        mock_graph_instance.compile.assert_called_once()
        mock_compiled_graph.invoke.assert_called_once()

        # Check initial state passed to invoke
        args, kwargs = mock_compiled_graph.invoke.call_args
        initial_state = args[0]
        self.assertEqual(initial_state["collection_id"], 1)
        self.assertEqual(initial_state["thread_id"], thread_id)
        self.assertEqual(initial_state["current_phase"], ResearchPhase.PLANNING.value)

    @patch("vulcanlab.research.workflow.get_research_session_by_thread_id")
    @patch("vulcanlab.research.workflow.create_research_graph")
    @patch("vulcanlab.research.workflow.create_research_session")
    @patch("vulcanlab.research.workflow.update_research_session")
    def test_start_automated_research_error_handling(self, mock_update_session, mock_create_session, mock_create_graph, mock_get_session):
        """Test that session status is updated to failed on exception."""
        # 1. Setup mocks
        mock_res_session = Mock()
        mock_res_session.id = 789
        mock_create_session.return_value = mock_res_session
        mock_get_session.return_value = mock_res_session

        mock_graph = mock_create_graph.return_value.compile.return_value
        mock_graph.invoke.side_effect = Exception("Graph failed")

        # 2. Call and expect exception
        with self.assertRaises(Exception):
            start_automated_research(1, self.mock_session)

        # 3. Verify session was updated to failed
        mock_update_session.assert_called_once()
        args, kwargs = mock_update_session.call_args
        self.assertEqual(args[1], 789)
        self.assertEqual(args[2]["status"], SessionStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
