"""
Unit tests for automatic evaluation workflow (T04).

Tests the execute_automatic_eval function with mocked LLM calls and database.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.exc import IntegrityError

from vulcanlab.ai.config import LLMProvider
from vulcanlab.data.models.experiment import (
    Experiment,
    ExperimentPrompt,
    ExperimentAnswer,
    ExperimentEvaluation,
)
from vulcanlab.eval.auto_eval import execute_automatic_eval, _parse_judge_response


class TestExecuteAutomaticEval:
    """Test automatic evaluation workflow orchestration."""

    @patch("vulcanlab.eval.auto_eval.submit_evaluation")
    @patch("vulcanlab.eval.auto_eval.generate_eval_prompt")
    @patch("vulcanlab.eval.auto_eval.create_answer_pair")
    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_creates_three_prompts_with_same_group_id(
        self,
        mock_settings_class,
        mock_create_llm,
        mock_create_answer,
        mock_generate_eval,
        mock_submit_eval,
    ):
        """Test that execute_automatic_eval creates three prompts with same prompt_group_id."""
        # Setup mocks
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment query
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "openai"
        mock_experiment.auto_judge_provider = "gemini"
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )

        # Mock prompt_group_id query (max + 1)
        mock_session.query.return_value.filter.return_value.scalar.return_value = 5

        # Mock LLM responses
        mock_answer_llm = MagicMock()
        mock_answer_response = MagicMock()
        mock_answer_response.content = "Generated answer text"
        mock_answer_llm.invoke.return_value = mock_answer_response

        mock_judge_llm = MagicMock()
        mock_judge_response = MagicMock()
        mock_judge_response.content = (
            "OVERALL_SCORE: 5\n"
            'DIMENSION_SCORES: {"factual_correctness": 6, "clarity": 4}\n'
            "JUSTIFICATION: Answer A is better because..."
        )
        mock_judge_llm.invoke.return_value = mock_judge_response

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),  # First call for answer provider
            MagicMock(chat=mock_judge_llm),  # Second call for judge provider
        ]

        # Mock answer creation
        mock_answer = MagicMock(spec=ExperimentAnswer)
        mock_answer.id = 10
        mock_create_answer.return_value = mock_answer

        # Mock eval prompt generation
        mock_generate_eval.return_value = "Evaluate these answers..."

        # Mock evaluation submission
        mock_evaluation = MagicMock(spec=ExperimentEvaluation)
        mock_evaluation.id = 20
        mock_submit_eval.return_value = mock_evaluation

        # Execute
        result = execute_automatic_eval(
            session=mock_session,
            experiment_id=1,
            main_prompt_text="What is 2+2?",
            answer_x_prompt_text="Answer briefly",
            answer_y_prompt_text="Answer in detail",
        )

        # Verify three prompts were created with prompt_group_id=6
        assert mock_session.add.call_count == 3
        added_prompts = [call[0][0] for call in mock_session.add.call_args_list]

        assert all(isinstance(p, ExperimentPrompt) for p in added_prompts)
        assert all(p.prompt_group_id == 6 for p in added_prompts)
        assert all(p.experiment_id == 1 for p in added_prompts)

        # Verify prompt texts
        prompt_texts = [p.prompt_text for p in added_prompts]
        assert "What is 2+2?" in prompt_texts
        assert "Answer briefly" in prompt_texts
        assert "Answer in detail" in prompt_texts

        # Verify result
        assert result["evaluation_id"] == 20
        assert result["answer_id"] == 10
        assert result["prompt_group_id"] == 6

    @patch("vulcanlab.eval.auto_eval.submit_evaluation")
    @patch("vulcanlab.eval.auto_eval.generate_eval_prompt")
    @patch("vulcanlab.eval.auto_eval.create_answer_pair")
    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_prompt_group_id_starts_at_1_when_none(
        self,
        mock_settings_class,
        mock_create_llm,
        mock_create_answer,
        mock_generate_eval,
        mock_submit_eval,
    ):
        """Test that prompt_group_id starts at 1 when no existing prompts."""
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "openai"
        mock_experiment.auto_judge_provider = "gemini"
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )

        # Mock prompt_group_id query - no existing prompts (None)
        mock_session.query.return_value.filter.return_value.scalar.return_value = None

        # Setup LLM mocks
        mock_answer_llm = MagicMock()
        mock_answer_llm.invoke.return_value = MagicMock(content="Answer")

        mock_judge_llm = MagicMock()
        mock_judge_llm.invoke.return_value = MagicMock(
            content='OVERALL_SCORE: 0\nDIMENSION_SCORES: {"clarity": 0}\nJUSTIFICATION: Tie'
        )

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),
            MagicMock(chat=mock_judge_llm),
        ]

        mock_answer = MagicMock(spec=ExperimentAnswer)
        mock_answer.id = 10
        mock_create_answer.return_value = mock_answer

        mock_generate_eval.return_value = "Evaluate..."
        mock_evaluation = MagicMock(spec=ExperimentEvaluation)
        mock_evaluation.id = 20
        mock_submit_eval.return_value = mock_evaluation

        # Execute
        result = execute_automatic_eval(
            session=mock_session,
            experiment_id=1,
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y",
        )

        # Verify prompt_group_id is 1
        added_prompts = [call[0][0] for call in mock_session.add.call_args_list]
        assert all(p.prompt_group_id == 1 for p in added_prompts)
        assert result["prompt_group_id"] == 1

    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_calls_answer_provider_twice(
        self, mock_settings_class, mock_create_llm
    ):
        """Test that answer provider is called twice (answer_x and answer_y)."""
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "openai"
        mock_experiment.auto_judge_provider = "gemini"
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock LLMs
        mock_answer_llm = MagicMock()
        mock_answer_llm.invoke.side_effect = [
            MagicMock(content="Answer X text"),
            MagicMock(content="Answer Y text"),
        ]

        mock_judge_llm = MagicMock()
        mock_judge_llm.invoke.return_value = MagicMock(
            content='OVERALL_SCORE: 3\nDIMENSION_SCORES: {"clarity": 3}\nJUSTIFICATION: Good'
        )

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),
            MagicMock(chat=mock_judge_llm),
        ]

        # Mock other functions
        with patch("vulcanlab.eval.auto_eval.create_answer_pair") as mock_create_answer:
            mock_answer = MagicMock(spec=ExperimentAnswer)
            mock_answer.id = 10
            mock_create_answer.return_value = mock_answer

            with patch("vulcanlab.eval.auto_eval.generate_eval_prompt") as mock_gen_eval:
                mock_gen_eval.return_value = "Eval prompt"

                with patch("vulcanlab.eval.auto_eval.submit_evaluation") as mock_submit:
                    mock_submit.return_value = MagicMock(id=20)

                    # Execute
                    execute_automatic_eval(
                        session=mock_session,
                        experiment_id=1,
                        main_prompt_text="Main",
                        answer_x_prompt_text="Answer briefly",
                        answer_y_prompt_text="Answer in detail",
                    )

        # Verify answer LLM was invoked twice
        assert mock_answer_llm.invoke.call_count == 2
        assert mock_answer_llm.invoke.call_args_list[0][0][0] == "Answer briefly"
        assert mock_answer_llm.invoke.call_args_list[1][0][0] == "Answer in detail"

    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_calls_judge_provider_once(
        self, mock_settings_class, mock_create_llm
    ):
        """Test that judge provider is called once for evaluation."""
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "openai"
        mock_experiment.auto_judge_provider = "gemini"
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock LLMs
        mock_answer_llm = MagicMock()
        mock_answer_llm.invoke.return_value = MagicMock(content="Answer text")

        mock_judge_llm = MagicMock()
        mock_judge_llm.invoke.return_value = MagicMock(
            content='OVERALL_SCORE: 7\nDIMENSION_SCORES: {"clarity": 8}\nJUSTIFICATION: Excellent'
        )

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),
            MagicMock(chat=mock_judge_llm),
        ]

        # Mock other functions
        with patch("vulcanlab.eval.auto_eval.create_answer_pair") as mock_create_answer:
            mock_answer = MagicMock(spec=ExperimentAnswer)
            mock_answer.id = 10
            mock_create_answer.return_value = mock_answer

            with patch("vulcanlab.eval.auto_eval.generate_eval_prompt") as mock_gen_eval:
                eval_prompt = "Evaluate these answers carefully..."
                mock_gen_eval.return_value = eval_prompt

                with patch("vulcanlab.eval.auto_eval.submit_evaluation") as mock_submit:
                    mock_submit.return_value = MagicMock(id=20)

                    # Execute
                    execute_automatic_eval(
                        session=mock_session,
                        experiment_id=1,
                        main_prompt_text="Main",
                        answer_x_prompt_text="X",
                        answer_y_prompt_text="Y",
                    )

        # Verify judge LLM was invoked once with the eval prompt
        assert mock_judge_llm.invoke.call_count == 1
        assert mock_judge_llm.invoke.call_args[0][0] == eval_prompt

    @patch("vulcanlab.eval.auto_eval.submit_evaluation")
    @patch("vulcanlab.eval.auto_eval.generate_eval_prompt")
    @patch("vulcanlab.eval.auto_eval.create_answer_pair")
    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_creates_experiment_answer(
        self,
        mock_settings_class,
        mock_create_llm,
        mock_create_answer,
        mock_generate_eval,
        mock_submit_eval,
    ):
        """Test that ExperimentAnswer is created with both answers."""
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "openai"
        mock_experiment.auto_judge_provider = "gemini"
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock LLMs
        mock_answer_llm = MagicMock()
        mock_answer_llm.invoke.side_effect = [
            MagicMock(content="Answer X content"),
            MagicMock(content="Answer Y content"),
        ]

        mock_judge_llm = MagicMock()
        mock_judge_llm.invoke.return_value = MagicMock(
            content='OVERALL_SCORE: 0\nDIMENSION_SCORES: {"clarity": 0}\nJUSTIFICATION: Tie'
        )

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),
            MagicMock(chat=mock_judge_llm),
        ]

        mock_answer = MagicMock(spec=ExperimentAnswer)
        mock_answer.id = 123
        mock_create_answer.return_value = mock_answer

        mock_generate_eval.return_value = "Eval"
        mock_submit_eval.return_value = MagicMock(id=20)

        # Execute
        execute_automatic_eval(
            session=mock_session,
            experiment_id=1,
            main_prompt_text="Main",
            answer_x_prompt_text="X prompt",
            answer_y_prompt_text="Y prompt",
        )

        # Verify create_answer_pair was called with the generated answers
        mock_create_answer.assert_called_once()
        call_kwargs = mock_create_answer.call_args[1]
        assert call_kwargs["session"] == mock_session
        assert call_kwargs["answer_x"] == "Answer X content"
        assert call_kwargs["answer_y"] == "Answer Y content"
        # prompt_id should be the main prompt (first one added)
        assert "prompt_id" in call_kwargs

    @patch("vulcanlab.eval.auto_eval.submit_evaluation")
    @patch("vulcanlab.eval.auto_eval.generate_eval_prompt")
    @patch("vulcanlab.eval.auto_eval.create_answer_pair")
    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_creates_experiment_evaluation(
        self,
        mock_settings_class,
        mock_create_llm,
        mock_create_answer,
        mock_generate_eval,
        mock_submit_eval,
    ):
        """Test that ExperimentEvaluation is created."""
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "openai"
        mock_experiment.auto_judge_provider = "gemini"
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock LLMs
        mock_answer_llm = MagicMock()
        mock_answer_llm.invoke.return_value = MagicMock(content="Answer")

        mock_judge_llm = MagicMock()
        mock_judge_llm.invoke.return_value = MagicMock(
            content=(
                "OVERALL_SCORE: 8\n"
                'DIMENSION_SCORES: {"factual_correctness": 9, "clarity": 7}\n'
                "JUSTIFICATION: Answer A is much better"
            )
        )

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),
            MagicMock(chat=mock_judge_llm),
        ]

        mock_answer = MagicMock(spec=ExperimentAnswer)
        mock_answer.id = 456
        mock_create_answer.return_value = mock_answer

        mock_generate_eval.return_value = "Eval prompt"

        mock_evaluation = MagicMock(spec=ExperimentEvaluation)
        mock_evaluation.id = 789
        mock_submit_eval.return_value = mock_evaluation

        # Execute
        result = execute_automatic_eval(
            session=mock_session,
            experiment_id=1,
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y",
        )

        # Verify submit_evaluation was called with parsed judge response
        mock_submit_eval.assert_called_once()
        call_kwargs = mock_submit_eval.call_args[1]
        assert call_kwargs["session"] == mock_session
        assert call_kwargs["answer_id"] == 456
        assert call_kwargs["overall_score"] == 8
        assert call_kwargs["dimension_scores"] == {
            "factual_correctness": 9,
            "clarity": 7,
        }
        assert call_kwargs["justification"] == "Answer A is much better"

        # Verify result contains evaluation_id
        assert result["evaluation_id"] == 789

    def test_execute_automatic_eval_raises_error_if_experiment_not_found(self):
        """Test that ValueError is raised if experiment doesn't exist."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Experiment with id 999 not found"):
            execute_automatic_eval(
                session=mock_session,
                experiment_id=999,
                main_prompt_text="Main",
                answer_x_prompt_text="X",
                answer_y_prompt_text="Y",
            )

    def test_execute_automatic_eval_raises_error_if_auto_mode_disabled(self):
        """Test that ValueError is raised if auto mode is not enabled."""
        mock_session = MagicMock()

        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = False
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )

        with pytest.raises(ValueError, match="not enabled"):
            execute_automatic_eval(
                session=mock_session,
                experiment_id=1,
                main_prompt_text="Main",
                answer_x_prompt_text="X",
                answer_y_prompt_text="Y",
            )

    @patch("vulcanlab.eval.auto_eval.create_langchain_chat_for_provider")
    @patch("vulcanlab.eval.auto_eval.LLMSettings")
    def test_execute_automatic_eval_uses_correct_providers(
        self, mock_settings_class, mock_create_llm
    ):
        """Test that correct providers are used for answer and judge."""
        mock_session = MagicMock()
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock experiment with specific providers
        mock_experiment = MagicMock(spec=Experiment)
        mock_experiment.id = 1
        mock_experiment.auto_mode_enabled = True
        mock_experiment.auto_answer_provider = "gemini"  # Answer with Gemini
        mock_experiment.auto_judge_provider = "openai"  # Judge with OpenAI
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_experiment
        )
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock LLMs
        mock_answer_llm = MagicMock()
        mock_answer_llm.invoke.return_value = MagicMock(content="Answer")

        mock_judge_llm = MagicMock()
        mock_judge_llm.invoke.return_value = MagicMock(
            content='OVERALL_SCORE: 0\nDIMENSION_SCORES: {"clarity": 0}\nJUSTIFICATION: Tie'
        )

        mock_create_llm.side_effect = [
            MagicMock(chat=mock_answer_llm),
            MagicMock(chat=mock_judge_llm),
        ]

        with patch("vulcanlab.eval.auto_eval.create_answer_pair") as mock_create_answer:
            mock_answer = MagicMock(id=10)
            mock_create_answer.return_value = mock_answer

            with patch("vulcanlab.eval.auto_eval.generate_eval_prompt") as mock_gen:
                mock_gen.return_value = "Eval"

                with patch("vulcanlab.eval.auto_eval.submit_evaluation") as mock_submit:
                    mock_submit.return_value = MagicMock(id=20)

                    # Execute
                    execute_automatic_eval(
                        session=mock_session,
                        experiment_id=1,
                        main_prompt_text="Main",
                        answer_x_prompt_text="X",
                        answer_y_prompt_text="Y",
                    )

        # Verify create_langchain_chat_for_provider was called with correct providers
        assert mock_create_llm.call_count == 2
        assert mock_create_llm.call_args_list[0][1]["provider"] == LLMProvider.GEMINI
        assert mock_create_llm.call_args_list[1][1]["provider"] == LLMProvider.OPENAI


class TestParseJudgeResponse:
    """Test parsing of judge LLM responses."""

    def test_parse_judge_response_valid(self):
        """Test parsing a valid judge response."""
        judge_text = (
            "OVERALL_SCORE: 5\n"
            'DIMENSION_SCORES: {"factual_correctness": 6, "clarity": 4}\n'
            "JUSTIFICATION: Answer A is better because it provides more detail."
        )

        overall, dimensions, justification = _parse_judge_response(judge_text)

        assert overall == 5
        assert dimensions == {"factual_correctness": 6, "clarity": 4}
        assert justification == "Answer A is better because it provides more detail."

    def test_parse_judge_response_multiline_justification(self):
        """Test parsing response with multiline justification."""
        judge_text = (
            "OVERALL_SCORE: 3\n"
            'DIMENSION_SCORES: {"clarity": 3}\n'
            "JUSTIFICATION: Answer A is better.\n"
            "It has more examples.\n"
            "And clearer structure."
        )

        overall, dimensions, justification = _parse_judge_response(judge_text)

        assert overall == 3
        assert justification == (
            "Answer A is better.\nIt has more examples.\nAnd clearer structure."
        )

    def test_parse_judge_response_negative_score(self):
        """Test parsing response with negative overall score."""
        judge_text = (
            "OVERALL_SCORE: -8\n"
            'DIMENSION_SCORES: {"clarity": -10}\n'
            "JUSTIFICATION: Answer B is much better."
        )

        overall, dimensions, justification = _parse_judge_response(judge_text)

        assert overall == -8
        assert dimensions == {"clarity": -10}

    def test_parse_judge_response_missing_overall_score(self):
        """Test that ValueError is raised if OVERALL_SCORE is missing."""
        judge_text = (
            'DIMENSION_SCORES: {"clarity": 5}\n' "JUSTIFICATION: Good answer."
        )

        with pytest.raises(ValueError, match="OVERALL_SCORE not found"):
            _parse_judge_response(judge_text)

    def test_parse_judge_response_missing_dimension_scores(self):
        """Test that ValueError is raised if DIMENSION_SCORES is missing."""
        judge_text = "OVERALL_SCORE: 5\n" "JUSTIFICATION: Good answer."

        with pytest.raises(ValueError, match="DIMENSION_SCORES not found"):
            _parse_judge_response(judge_text)

    def test_parse_judge_response_missing_justification(self):
        """Test that ValueError is raised if JUSTIFICATION is missing."""
        judge_text = 'OVERALL_SCORE: 5\nDIMENSION_SCORES: {"clarity": 5}'

        with pytest.raises(ValueError, match="JUSTIFICATION not found"):
            _parse_judge_response(judge_text)

    def test_parse_judge_response_invalid_overall_score_format(self):
        """Test that ValueError is raised for invalid OVERALL_SCORE format."""
        judge_text = (
            "OVERALL_SCORE: not_a_number\n"
            'DIMENSION_SCORES: {"clarity": 5}\n'
            "JUSTIFICATION: Good."
        )

        with pytest.raises(ValueError, match="Invalid OVERALL_SCORE format"):
            _parse_judge_response(judge_text)

    def test_parse_judge_response_invalid_dimension_scores_json(self):
        """Test that ValueError is raised for invalid DIMENSION_SCORES JSON."""
        judge_text = (
            "OVERALL_SCORE: 5\n"
            "DIMENSION_SCORES: {invalid json}\n"
            "JUSTIFICATION: Good."
        )

        with pytest.raises(ValueError, match="Invalid DIMENSION_SCORES format"):
            _parse_judge_response(judge_text)

    def test_parse_judge_response_dimension_scores_non_integer_values(self):
        """Test that ValueError is raised if dimension scores are not integers."""
        judge_text = (
            "OVERALL_SCORE: 5\n"
            'DIMENSION_SCORES: {"clarity": 5.5}\n'
            "JUSTIFICATION: Good."
        )

        with pytest.raises(ValueError, match="Invalid DIMENSION_SCORES format"):
            _parse_judge_response(judge_text)
