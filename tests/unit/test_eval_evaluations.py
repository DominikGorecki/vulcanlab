"""
Unit tests for evaluation core logic.

Tests the evaluation management functions including generation, submission, and deletion.
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import (
    ExperimentAnswer,
    ExperimentPrompt,
    ExperimentEvaluation,
    ExperimentDimensionResult,
)
from vulcanlab.eval.evaluations import (
    generate_eval_prompt,
    submit_evaluation,
    delete_evaluation,
)


class TestGenerateEvalPrompt:
    """Test evaluation prompt generation."""

    def test_generate_eval_prompt_success(self):
        """Test successful evaluation prompt generation."""
        # Mock session with query for template (T06 update)
        session = Mock()

        # Mock experiment without eval_template_id (will use default)
        mock_experiment = Mock()
        mock_experiment.id = 1
        mock_experiment.eval_template_id = None

        # Mock answer with prompt relationship
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.prompt_id = 10
        mock_answer.evaluation = None  # Not yet evaluated
        mock_answer.answer_a = "Answer A content"
        mock_answer.answer_b = "Answer B content"

        mock_prompt = Mock(spec=ExperimentPrompt)
        mock_prompt.prompt_text = "Test prompt"
        mock_prompt.experiment = mock_experiment
        mock_answer.prompt = mock_prompt

        # Mock query for get_default_template() - no template in DB, will use fallback
        mock_query = Mock()
        session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None  # No default template in DB

        # Mock get_answer_by_id to return the answer
        def mock_get_answer(sess, ans_id):
            if ans_id == 1:
                return mock_answer
            raise ValueError(f"Answer with id {ans_id} not found")

        # Patch the function
        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = mock_get_answer

        try:
            prompt = generate_eval_prompt(session, 1)

            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Test prompt" in prompt
            assert "Answer A content" in prompt
            assert "Answer B content" in prompt
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_generate_eval_prompt_already_evaluated(self):
        """Test that generating prompt for already evaluated answer raises ValueError."""
        session = Mock()

        # Mock answer that already has an evaluation
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = Mock(spec=ExperimentEvaluation)  # Already evaluated

        # Mock get_answer_by_id
        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            with pytest.raises(ValueError) as exc_info:
                generate_eval_prompt(session, 1)

            assert "already been evaluated" in str(exc_info.value).lower()
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_generate_eval_prompt_answer_not_found(self):
        """Test that generating prompt for non-existent answer raises ValueError."""
        session = Mock()

        # Mock get_answer_by_id to raise ValueError
        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id

        def mock_get_answer_not_found(sess, ans_id):
            raise ValueError(f"Answer with id {ans_id} not found")

        eval_module.get_answer_by_id = mock_get_answer_not_found

        try:
            with pytest.raises(ValueError) as exc_info:
                generate_eval_prompt(session, 999)

            assert "not found" in str(exc_info.value).lower()
        finally:
            eval_module.get_answer_by_id = original_get_answer


class TestSubmitEvaluation:
    """Test evaluation submission."""

    def test_submit_evaluation_success(self):
        """Test successful evaluation submission."""
        session = MagicMock()

        # Mock answer
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None  # Not yet evaluated

        # Mock evaluation with auto-assigned ID after flush
        mock_evaluation = Mock(spec=ExperimentEvaluation)
        mock_evaluation.id = 100

        # Setup session.add and flush behavior
        def mock_add(obj):
            if isinstance(obj, ExperimentEvaluation):
                obj.id = 100
            elif isinstance(obj, ExperimentDimensionResult):
                pass  # Dimension results

        session.add.side_effect = mock_add
        session.flush.return_value = None

        # Mock get_answer_by_id
        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            dimension_scores = {
                "clarity": 5,
                "accuracy": 8,
                "completeness": 3
            }

            result = submit_evaluation(
                session=session,
                answer_id=1,
                overall_score=6,
                justification="Test justification",
                dimension_scores=dimension_scores
            )

            # Verify evaluation was created
            assert isinstance(result, ExperimentEvaluation)
            assert session.add.called
            assert session.flush.called

            # Verify dimension results were created (1 evaluation + 3 dimensions = 4 adds)
            assert session.add.call_count >= 4
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_submit_evaluation_already_evaluated(self):
        """Test that submitting evaluation for already evaluated answer raises ValueError."""
        session = Mock()

        # Mock answer that already has evaluation
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = Mock(spec=ExperimentEvaluation)

        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            with pytest.raises(ValueError) as exc_info:
                submit_evaluation(
                    session=session,
                    answer_id=1,
                    overall_score=5,
                    justification="Test",
                    dimension_scores={"clarity": 5}
                )

            assert "already been evaluated" in str(exc_info.value).lower()
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_submit_evaluation_invalid_overall_score_too_low(self):
        """Test that overall score < -10 raises ValueError."""
        session = Mock()

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None

        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            with pytest.raises(ValueError) as exc_info:
                submit_evaluation(
                    session=session,
                    answer_id=1,
                    overall_score=-11,
                    justification="Test",
                    dimension_scores={"clarity": 5}
                )

            assert "overall score" in str(exc_info.value).lower()
            assert "-10 and 10" in str(exc_info.value)
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_submit_evaluation_invalid_overall_score_too_high(self):
        """Test that overall score > 10 raises ValueError."""
        session = Mock()

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None

        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            with pytest.raises(ValueError) as exc_info:
                submit_evaluation(
                    session=session,
                    answer_id=1,
                    overall_score=11,
                    justification="Test",
                    dimension_scores={"clarity": 5}
                )

            assert "overall score" in str(exc_info.value).lower()
            assert "-10 and 10" in str(exc_info.value)
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_submit_evaluation_invalid_dimension_score(self):
        """Test that dimension score out of range raises ValueError."""
        session = Mock()

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None

        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            with pytest.raises(ValueError) as exc_info:
                submit_evaluation(
                    session=session,
                    answer_id=1,
                    overall_score=5,
                    justification="Test",
                    dimension_scores={"clarity": 15}
                )

            assert "dimension score" in str(exc_info.value).lower()
            assert "clarity" in str(exc_info.value)
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_submit_evaluation_empty_dimension_scores(self):
        """Test that empty dimension_scores dict is allowed."""
        session = MagicMock()

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None

        def mock_add(obj):
            if isinstance(obj, ExperimentEvaluation):
                obj.id = 100

        session.add.side_effect = mock_add
        session.flush.return_value = None

        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            result = submit_evaluation(
                session=session,
                answer_id=1,
                overall_score=0,
                justification="No dimensions",
                dimension_scores={}
            )

            # Should succeed with no dimension results
            assert isinstance(result, ExperimentEvaluation)
        finally:
            eval_module.get_answer_by_id = original_get_answer

    def test_submit_evaluation_empty_dimension_name(self):
        """Test that empty dimension name raises ValueError."""
        session = Mock()

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None

        import vulcanlab.eval.evaluations as eval_module
        original_get_answer = eval_module.get_answer_by_id
        eval_module.get_answer_by_id = lambda sess, ans_id: mock_answer

        try:
            with pytest.raises(ValueError) as exc_info:
                submit_evaluation(
                    session=session,
                    answer_id=1,
                    overall_score=5,
                    justification="Test",
                    dimension_scores={"": 5}
                )

            assert "dimension name" in str(exc_info.value).lower()
        finally:
            eval_module.get_answer_by_id = original_get_answer


class TestDeleteEvaluation:
    """Test evaluation deletion."""

    def test_delete_evaluation_success(self):
        """Test successful evaluation deletion."""
        session = MagicMock()

        # Mock evaluation
        mock_evaluation = Mock(spec=ExperimentEvaluation)
        mock_evaluation.id = 100
        mock_evaluation.answer_id = 1
        mock_evaluation.overall_score = 5

        # Mock query
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_evaluation
        mock_query.filter.return_value = mock_filter
        session.query.return_value = mock_query

        delete_evaluation(session, 100)

        # Verify evaluation was deleted
        assert session.delete.called
        assert session.flush.called
        session.delete.assert_called_once_with(mock_evaluation)

    def test_delete_evaluation_not_found(self):
        """Test that deleting non-existent evaluation raises ValueError."""
        session = MagicMock()

        # Mock query returning None
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        session.query.return_value = mock_query

        with pytest.raises(ValueError) as exc_info:
            delete_evaluation(session, 999)

        assert "not found" in str(exc_info.value).lower()
        assert "999" in str(exc_info.value)
