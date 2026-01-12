import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from vulcanlab.research.checkpointer import PostgresSaver, serialize_state, deserialize_state
from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.research.state import ResearchState

class TestPostgresSaver(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock(spec=Session)
        self.mock_session_factory = MagicMock(return_value=self.mock_session)
        # We need the mock session to work as a context manager
        self.mock_session.__enter__.return_value = self.mock_session
        self.saver = PostgresSaver(self.mock_session_factory)
        
        self.test_state: ResearchState = {
            'collection_id': 1,
            'collection_description': "Test collection",
            'item_notes': [{'item_id': 1, 'note': 'test', 'type': 'excerpt'}],
            'research_plan': {'outline': 'test'},
            'current_phase': 'planning',
            'sections': {},
            'context_per_question': {},
            'reused_sections': {},
            'available_results': [],
            'synthesis': "Final synthesis",
            'quality_metrics': {'score': 0.9},
            'refinement_needed': [],
            'thread_id': "test_123"
        }

    def test_serialize_deserialize(self):
        """Test state serialization and deserialization."""
        serialized = serialize_state(self.test_state)
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized['collection_id'], 1)
        
        deserialized = deserialize_state(serialized)
        self.assertEqual(deserialized['collection_id'], 1)
        self.assertEqual(deserialized['synthesis'], "Final synthesis")

    @patch('vulcanlab.research.checkpointer.func')
    @patch('vulcanlab.research.checkpointer.select')
    def test_put_existing_session(self, mock_select, mock_func):
        """Test put updates an existing session."""
        mock_session_obj = MagicMock(spec=ResearchSession)
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = mock_session_obj
        
        self.saver.put("test_123", self.test_state)
        
        self.assertEqual(mock_session_obj.state_data, self.test_state)
        self.mock_session.commit.assert_called_once()
        self.assertIsNotNone(mock_session_obj.updated_at)

    @patch('vulcanlab.research.checkpointer.select')
    def test_put_non_existent_session(self, mock_select):
        """Test put handles non-existent session gracefully."""
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Should not raise exception
        self.saver.put("non_existent", self.test_state)
        self.mock_session.commit.assert_not_called()

    @patch('vulcanlab.research.checkpointer.select')
    def test_get_session(self, mock_select):
        """Test get retrieves session state."""
        mock_session_obj = MagicMock(spec=ResearchSession)
        mock_session_obj.state_data = self.test_state
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = mock_session_obj
        
        state = self.saver.get("test_123")
        
        self.assertEqual(state, self.test_state)
        self.assertEqual(state['thread_id'], "test_123")

    @patch('vulcanlab.research.checkpointer.select')
    def test_get_non_existent(self, mock_select):
        """Test get returns None for non-existent session."""
        self.mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        state = self.saver.get("non_existent")
        self.assertIsNone(state)

    @patch('vulcanlab.research.checkpointer.select')
    def test_list_sessions(self, mock_select):
        """Test list returns matching sessions."""
        mock_rs1 = MagicMock(spec=ResearchSession)
        mock_rs1.thread_id = "test_1"
        mock_rs1.state_data = {'thread_id': "test_1"}
        
        mock_rs2 = MagicMock(spec=ResearchSession)
        mock_rs2.thread_id = "test_2"
        mock_rs2.state_data = {'thread_id': "test_2"}
        
        self.mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_rs1, mock_rs2]
        
        results = self.saver.list("test")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], "test_1")
        self.assertEqual(results[1][0], "test_2")
