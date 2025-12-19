"""
Unit tests for init_db default RAG config (T05 - Parent Chunk Enrichment).

Tests that the default RAG config created by init_db.py:
- Includes max_word_count: 750 in retrieval section
- Does NOT include deprecated retrieval keys
- Does NOT include deprecated consolidation keys
- Includes coverage_threshold in consolidation section
- Matches the spec schema structure
"""

from unittest.mock import patch, MagicMock
import json

import pytest


class TestDefaultRagConfigStructure:
    """Tests for default RAG config structure (T05)."""

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_config_includes_max_word_count(self, mock_load_config):
        """Test that default config includes max_word_count: 750 in retrieval section."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON
        insert_call = insert_calls[0]
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify max_word_count is present with correct value
        assert 'retrieval' in config
        assert 'max_word_count' in config['retrieval']
        assert config['retrieval']['max_word_count'] == 750

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_config_excludes_deprecated_retrieval_keys(self, mock_load_config):
        """Test that default config does NOT include deprecated retrieval keys."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON
        insert_call = insert_calls[0]
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify deprecated keys are NOT present
        assert 'retrieval' in config
        assert 'min_char_count' not in config['retrieval']
        assert 'min_content_length' not in config['retrieval']
        assert 'enrich_lines_above' not in config['retrieval']
        assert 'enrich_lines_below' not in config['retrieval']

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_config_excludes_deprecated_consolidation_keys(self, mock_load_config):
        """Test that default config does NOT include deprecated consolidation keys."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON
        insert_call = insert_calls[0]
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify deprecated consolidation key is NOT present
        assert 'consolidation' in config
        assert 'enrich_from_md' not in config['consolidation']

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_config_includes_coverage_threshold(self, mock_load_config):
        """Test that default config includes coverage_threshold in consolidation section."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON
        insert_call = insert_calls[0]
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify coverage_threshold is present with correct value
        assert 'consolidation' in config
        assert 'coverage_threshold' in config['consolidation']
        assert config['consolidation']['coverage_threshold'] == 0.5

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_config_includes_all_required_keys(self, mock_load_config):
        """Test that default config includes all required non-deprecated keys."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON
        insert_call = insert_calls[0]
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify all required retrieval keys are present
        required_retrieval_keys = [
            'dense_limit',
            'lexical_limit',
            'rrf_k',
            'top_k_rrf',
            'top_n_final',
            'entity_boost',
            'min_word_count',
            'max_word_count',
            'mmr_lambda',
            'reranker_batch_size',
            'reranker_max_length',
            'min_sentence_filter_enabled',
            'min_sentence_count'
        ]
        for key in required_retrieval_keys:
            assert key in config['retrieval'], f"Missing required retrieval key: {key}"

        # Verify all required consolidation keys are present
        required_consolidation_keys = [
            'coverage_threshold',
            'line_gap',
            'min_content_length'
        ]
        for key in required_consolidation_keys:
            assert key in config['consolidation'], f"Missing required consolidation key: {key}"

        # Verify all required augmentation keys are present
        required_augmentation_keys = ['top_n_contexts']
        for key in required_augmentation_keys:
            assert key in config['augmentation'], f"Missing required augmentation key: {key}"

    @patch('vulcanlab.data.init_db.load_config')
    def test_default_config_matches_spec_schema(self, mock_load_config):
        """Test that default config structure matches spec schema."""
        from vulcanlab.data.init_db import create_default_rag_config

        # Mock config
        mock_config = MagicMock()
        mock_config.database.app_user = "test_user"
        mock_load_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        # Mock empty config table
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'SELECT COUNT(*)' in query_str:
                return mock_count_result
            return MagicMock()

        mock_conn.execute.side_effect = execute_side_effect

        with patch('vulcanlab.data.init_db.engine', mock_engine):
            try:
                create_default_rag_config(verbose=False)
            except Exception:
                # Ignore ownership transfer errors in test
                pass

        # Find the INSERT call
        insert_calls = [call for call in mock_conn.execute.call_args_list
                       if 'INSERT INTO rag_config' in str(call[0][0])]
        assert len(insert_calls) == 1

        # Extract the config JSON
        insert_call = insert_calls[0]
        if len(insert_call[0]) > 1:
            config_json = insert_call[0][1]['config']
        else:
            config_json = insert_call.kwargs['config'] if 'config' in insert_call.kwargs else insert_call[1]['config']
        config = json.loads(config_json)

        # Verify structure has three top-level sections
        assert set(config.keys()) == {'retrieval', 'consolidation', 'augmentation'}

        # Verify no _deprecated objects exist
        assert '_deprecated' not in config.get('retrieval', {})
        assert '_deprecated' not in config.get('consolidation', {})
        assert '_deprecated' not in config.get('augmentation', {})

        # Verify specific values match spec example
        assert config['retrieval']['min_word_count'] == 150
        assert config['retrieval']['max_word_count'] == 750
        assert config['consolidation']['coverage_threshold'] == 0.5
        assert config['consolidation']['min_content_length'] == 350
        assert config['augmentation']['top_n_contexts'] == 5
