import unittest
from typing import get_type_hints
from vulcanlab.research.state import ResearchState

class TestResearchState(unittest.TestCase):
    def test_research_state_fields(self):
        """Verify that ResearchState has all required fields with correct types."""
        hints = get_type_hints(ResearchState)
        
        expected_fields = {
            'collection_id': int,
            'collection_description': str,
            'item_notes': list,
            'research_plan': dict,
            'current_phase': str,
            'sections': dict,
            'context_per_question': dict,
            'reused_sections': dict,
            'available_results': list,
            'synthesis': str,
            'quality_metrics': dict,
            'refinement_needed': list,
            'thread_id': str
        }
        
        # Check that all expected fields are present
        for field, expected_type in expected_fields.items():
            self.assertIn(field, hints, f"Field '{field}' missing from ResearchState")
            
            # For generics like List[Dict], get_type_hints returns the origin type
            # but we can check if it's compatible
            field_type = hints[field]
            origin = getattr(field_type, '__origin__', field_type)
            
            # Simple check for origin types
            self.assertTrue(issubclass(origin, expected_type) or origin is expected_type, 
                            f"Field '{field}' has type {field_type}, expected {expected_type}")

    def test_research_state_instantiation(self):
        """Verify that ResearchState can be instantiated with all fields."""
        state: ResearchState = {
            'collection_id': 1,
            'collection_description': "Test collection",
            'item_notes': [],
            'research_plan': {},
            'current_phase': 'planning',
            'sections': {},
            'context_per_question': {},
            'reused_sections': {},
            'available_results': [],
            'synthesis': "",
            'quality_metrics': {},
            'refinement_needed': [],
            'thread_id': "test_thread"
        }
        self.assertEqual(state['collection_id'], 1)
        self.assertEqual(state['thread_id'], "test_thread")
