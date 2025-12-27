"""
Unit tests for evaluation template resolution.

Tests the template utilities for resolving evaluation prompts with placeholder substitution.
"""

import pytest

from vulcanlab.eval.template_utils import resolve_eval_template, get_default_template


class TestResolveEvalTemplate:
    """Test template resolution functionality."""

    def test_resolve_template_basic(self):
        """Test basic placeholder substitution."""
        template = "Prompt: {prompt}\nAnswer A: {answer_a}\nAnswer B: {answer_b}"
        prompt = "What is 2+2?"
        answer_a = "Four"
        answer_b = "4"

        resolved = resolve_eval_template(template, prompt, answer_a, answer_b)

        assert "Prompt: What is 2+2?" in resolved
        assert "Answer A: Four" in resolved
        assert "Answer B: 4" in resolved
        assert "{prompt}" not in resolved
        assert "{answer_a}" not in resolved
        assert "{answer_b}" not in resolved

    def test_resolve_template_missing_prompt_placeholder(self):
        """Test that missing {prompt} placeholder raises ValueError."""
        template = "Answer A: {answer_a}\nAnswer B: {answer_b}"

        with pytest.raises(ValueError) as exc_info:
            resolve_eval_template(template, "test", "a", "b")

        assert "prompt" in str(exc_info.value).lower()
        assert "placeholder" in str(exc_info.value).lower()

    def test_resolve_template_missing_answer_a_placeholder(self):
        """Test that missing {answer_a} placeholder raises ValueError."""
        template = "Prompt: {prompt}\nAnswer B: {answer_b}"

        with pytest.raises(ValueError) as exc_info:
            resolve_eval_template(template, "test", "a", "b")

        assert "answer_a" in str(exc_info.value).lower()
        assert "placeholder" in str(exc_info.value).lower()

    def test_resolve_template_missing_answer_b_placeholder(self):
        """Test that missing {answer_b} placeholder raises ValueError."""
        template = "Prompt: {prompt}\nAnswer A: {answer_a}"

        with pytest.raises(ValueError) as exc_info:
            resolve_eval_template(template, "test", "a", "b")

        assert "answer_b" in str(exc_info.value).lower()
        assert "placeholder" in str(exc_info.value).lower()

    def test_resolve_template_with_empty_values(self):
        """Test that empty string values are allowed."""
        template = "Prompt: {prompt}\nAnswer A: {answer_a}\nAnswer B: {answer_b}"

        resolved = resolve_eval_template(template, "", "", "")

        assert "Prompt: \n" in resolved
        assert "Answer A: \n" in resolved
        assert "Answer B: " in resolved

    def test_resolve_template_with_long_content(self):
        """Test template resolution with long content."""
        template = "Prompt: {prompt}\nAnswer A: {answer_a}\nAnswer B: {answer_b}"
        prompt = "x" * 1000
        answer_a = "y" * 2000
        answer_b = "z" * 1500

        resolved = resolve_eval_template(template, prompt, answer_a, answer_b)

        assert prompt in resolved
        assert answer_a in resolved
        assert answer_b in resolved
        assert len(resolved) > 4500

    def test_resolve_template_with_special_characters(self):
        """Test template resolution with special characters in content."""
        template = "Prompt: {prompt}\nAnswer A: {answer_a}\nAnswer B: {answer_b}"
        prompt = "What is 'quoted' and \"double-quoted\"?"
        answer_a = "Text with\nnewlines\nand\ttabs"
        answer_b = "Special chars: @#$%^&*()"

        resolved = resolve_eval_template(template, prompt, answer_a, answer_b)

        assert prompt in resolved
        assert answer_a in resolved
        assert answer_b in resolved

    def test_get_default_template(self):
        """Test that default template contains required placeholders."""
        template = get_default_template()

        assert isinstance(template, str)
        assert len(template) > 0
        assert "{prompt}" in template
        assert "{answer_a}" in template
        assert "{answer_b}" in template

    def test_default_template_can_be_resolved(self):
        """Test that the default template can be successfully resolved."""
        template = get_default_template()
        prompt = "Test prompt"
        answer_a = "Test answer A"
        answer_b = "Test answer B"

        resolved = resolve_eval_template(template, prompt, answer_a, answer_b)

        assert prompt in resolved
        assert answer_a in resolved
        assert answer_b in resolved
        assert "{prompt}" not in resolved
        assert "{answer_a}" not in resolved
        assert "{answer_b}" not in resolved

    def test_resolve_template_with_multiple_occurrences(self):
        """Test template resolution when placeholders appear multiple times."""
        template = "Prompt: {prompt}\nRepeated: {prompt}\nAnswer A: {answer_a}\nAnswer B: {answer_b}"
        prompt = "What is AI?"
        answer_a = "Artificial Intelligence"
        answer_b = "AI is machine learning"

        resolved = resolve_eval_template(template, prompt, answer_a, answer_b)

        # Both occurrences of {prompt} should be replaced
        assert resolved.count(prompt) == 2
        assert "{prompt}" not in resolved
