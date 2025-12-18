
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from vulcanlab.retrieval.retrieve import enrich_chunk_from_parent, retrieve, RetrievalResult, RetrievedChunk
from vulcanlab.augmentation.consolidate_context import consolidate_context
from vulcanlab.data.models import Chunk, Query, Work

@pytest.fixture
def caplog_info(caplog):
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def caplog_debug(caplog):
    caplog.set_level(logging.DEBUG)
    return caplog

class TestEnrichmentLogging:
    """Tests for logging in enrichment operations."""

    def test_enrich_chunk_from_parent_logs_traversal(self, caplog_debug):
        """Should log each step of parent traversal at DEBUG level."""
        chunk = Mock(spec=Chunk)
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2
        
        parent = Mock(spec=Chunk)
        parent.id = 2
        parent.content = " ".join(["word"] * 200)
        parent.parent_id = None
        parent.heading_breadcrumbs = None
        
        session = Mock()
        # Use return_value instead of side_effect to avoid StopIteration if called multiple times
        session.query.return_value.filter_by.return_value.first.return_value = parent
        
        enrich_chunk_from_parent(chunk, session, min_word_count=150)
        
        assert "Enriching chunk 1" in caplog_debug.text
        assert "Traversing chunk 1 to parent 2" in caplog_debug.text
        assert "Enrichment completed for chunk 1" in caplog_debug.text

    def test_enrich_chunk_from_parent_logs_warning_on_root(self, caplog):
        """Should log warning when traversal reaches root without meeting minimum."""
        chunk = Mock(spec=Chunk)
        chunk.id = 1
        chunk.content = "Short"
        chunk.parent_id = 2
        
        parent = Mock(spec=Chunk)
        parent.id = 2
        parent.content = "Still short" # 2 words
        parent.parent_id = None
        parent.heading_breadcrumbs = None
        
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = parent
        
        enrich_chunk_from_parent(chunk, session, min_word_count=150)
        
        assert any(record.levelname == "WARNING" for record in caplog.records)
        assert "traversal reached root" in caplog.text
        assert "without meeting min_word_count" in caplog.text

    @patch('vulcanlab.retrieval.retrieve.enrich_chunk_from_parent')
    @patch('vulcanlab.retrieval.retrieve._rerank_chunks')
    @patch('vulcanlab.retrieval.retrieve._dense_search')
    @patch('vulcanlab.retrieval.retrieve._lexical_search')
    @patch('vulcanlab.retrieval.retrieve.get_session')
    @patch('vulcanlab.retrieval.retrieve.load_config')
    def test_retrieve_logs_summary_metrics(
        self, mock_load_config, mock_get_session, mock_lexical, mock_dense, mock_rerank, mock_enrich, caplog_info
    ):
        """Should log enrichment summary metrics per query at INFO level."""
        # Mock config
        mock_load_config.return_value.logging.enabled = True
        mock_load_config.return_value.logging.log_dir = "/tmp/logs"
        
        # Mock session and query
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        query = Mock(spec=Query)
        query.id = 1
        query.vector_status = 'vec'
        query.original_query = "test"
        query.embedding_original = [0.1] * 768
        query.intent = None
        query.entities = []
        query.embeddings_mqe = []
        query.expanded_queries = []
        query.embedding_hyde = None
        mock_session.query.return_value.filter.return_value.first.return_value = query
        
        # Mock search results
        mock_dense.return_value = [(10, 1), (11, 2)]
        mock_lexical.return_value = []
        
        # Mock chunks - long enough to pass filtration
        long_content = " ".join(["word"] * 200)
        c1 = Mock(spec=Chunk, id=10, work_id=1, content=long_content, start_line=1, end_line=10, level="chunk", heading_breadcrumbs=None, embedding=None)
        c2 = Mock(spec=Chunk, id=11, work_id=1, content=long_content, start_line=11, end_line=20, level="chunk", heading_breadcrumbs=None, embedding=None)
        # 1. chunks_data, 2. works (many times)
        mock_session.query.return_value.filter.return_value.all.side_effect = [[c1, c2], [Mock(spec=Work, id=1)], [Mock(spec=Work, id=1)], [Mock(spec=Work, id=1)]]
        
        # Mock enrichment result
        mock_enrich.side_effect = [
            {'content': 'enriched 1', 'parent_id': 100, 'enriched': True, 'depth': 2, 'reached_root': False},
            {'content': 'enriched 2', 'parent_id': 101, 'enriched': True, 'depth': 1, 'reached_root': True}
        ]
        
        # Mock rerank to return what it gets
        mock_rerank.side_effect = lambda q, chunks, **kwargs: chunks
        
        result = retrieve(query_id=1)
        
        assert "Enrichment summary: 2 chunks, 2 enriched (100.0%), avg depth 1.5, reached root 1 times" in caplog_info.text
        assert result.enrichment_percentage == 100.0
        assert result.average_traversal_depth == 1.5
        assert result.traversal_reached_root_count == 1

    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.load_config')
    def test_consolidate_context_logs_coverage(self, mock_load_config, mock_get_session, caplog_info):
        """Should log coverage calculations and replacement decisions at INFO level."""
        mock_load_config.return_value.logging.enabled = True
        mock_load_config.return_value.logging.log_dir = "/tmp/logs"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        query = Mock(spec=Query)
        query.id = 1
        query.retrieved_context = [
            {'id': 1, 'work_id': 1, 'parent_id': 10, 'content': 'part 1', 'start_line': 1, 'end_line': 5, 'final_score': 0.9}
        ]
        mock_session.query.return_value.filter.return_value.first.return_value = query
        
        parent = Mock(spec=Chunk, id=10, work_id=1, content='whole parent content', start_line=1, end_line=20, level='H2', parent_id=None)
        # 1. works, 2. parent_ids, 3. next_level (while loop), 4. all_parents
        mock_session.query.return_value.filter.return_value.all.side_effect = [[Mock(spec=Work, id=1)], [parent], [], [parent]]
        
        # Adjust coverage threshold to ensure replacement (coverage = 6/20 = 0.3 here roughly by char count)
        # 'part 1' is 6 chars, 'whole parent content' is 20 chars. coverage = 0.3
        consolidate_context(query_id=1, coverage_threshold=0.1)
        
        assert "Consolidation group parent_id=10" in caplog_info.text
        assert "coverage 0.30" in caplog_info.text
        assert "replacing with parent" in caplog_info.text

    @patch('vulcanlab.augmentation.consolidate_context.get_session')
    @patch('vulcanlab.augmentation.consolidate_context.load_config')
    def test_consolidate_context_logs_merging(self, mock_load_config, mock_get_session, caplog_debug):
        """Should log adjacency merging operations at DEBUG level."""
        mock_load_config.return_value.logging.enabled = True
        mock_load_config.return_value.logging.log_dir = "/tmp/logs"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        query = Mock(spec=Query)
        query.id = 1
        # Two chunks close to each other
        query.retrieved_context = [
            {'id': 1, 'work_id': 1, 'parent_id': 10, 'content': 'part 1', 'start_line': 1, 'end_line': 5, 'final_score': 0.9},
            {'id': 2, 'work_id': 1, 'parent_id': 10, 'content': 'part 2', 'start_line': 7, 'end_line': 10, 'final_score': 0.8}
        ]
        mock_session.query.return_value.filter.return_value.first.return_value = query
        
        parent = Mock(spec=Chunk, id=10, work_id=1, content='a' * 100, start_line=1, end_line=20, level='H2', parent_id=None)
        # 1. works, 2. parent_ids, 3. next_level (while loop), 4. all_parents
        mock_session.query.return_value.filter.return_value.all.side_effect = [[Mock(spec=Work, id=1)], [parent], [], [parent]]
        
        # High coverage threshold to avoid replacement but allow merging
        consolidate_context(query_id=1, coverage_threshold=0.9, line_gap=5)
        
        assert "Merged 2 adjacent items into 1 for parent 10" in caplog_debug.text
