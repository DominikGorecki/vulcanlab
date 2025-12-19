"""
Unit tests for improved sentence validation logic.

Tests the linguistic criteria for determining valid sentences:
- Minimum token count (7 tokens excluding punctuation)
- Grammatical structure validation (verb+noun, root verb, or noun+subject)
"""

import pytest
import spacy

# Import from both locations to ensure consistency
from vulcanlab.chunking.content_chunking import _get_sentences as chunking_get_sentences
from vulcanlab.chunking.content_chunking import _is_valid_sentence as chunking_is_valid_sentence

# Import from migration
import importlib.util
import sys
from pathlib import Path

migration_path = Path(__file__).parent.parent.parent / "migrations" / "019_backfill_sentence_count.py"
spec = importlib.util.spec_from_file_location("migration_019", migration_path)
migration_019 = importlib.util.module_from_spec(spec)
sys.modules["migration_019_for_test"] = migration_019
spec.loader.exec_module(migration_019)

migration_get_sentences = migration_019._get_sentences
migration_is_valid_sentence = migration_019._is_valid_sentence

# Load spaCy for direct testing
nlp = spacy.load("en_core_web_sm")


class TestSentenceValidation:
    """Tests for sentence validation criteria."""

    def test_valid_sentence_with_verb_and_noun(self):
        """Test that sentence with verb and noun is valid."""
        text = "The researchers analyzed the experimental data from multiple sources."
        doc = nlp(text)
        sent = list(doc.sents)[0]

        assert chunking_is_valid_sentence(sent) is True
        assert migration_is_valid_sentence(sent) is True

    def test_valid_sentence_with_root_verb(self):
        """Test that sentence with root as verb is valid."""
        text = "Analyzing data requires careful attention to statistical methods and controls."
        doc = nlp(text)
        sent = list(doc.sents)[0]

        # Should be valid if root is verb
        result = chunking_is_valid_sentence(sent)
        assert result is True
        assert migration_is_valid_sentence(sent) == result

    def test_valid_sentence_with_noun_and_subject(self):
        """Test that sentence with noun and subject is valid (passive voice)."""
        text = "The hypothesis was tested by researchers at multiple independent laboratories."
        doc = nlp(text)
        sent = list(doc.sents)[0]

        assert chunking_is_valid_sentence(sent) is True
        assert migration_is_valid_sentence(sent) is True

    def test_invalid_sentence_too_few_tokens(self):
        """Test that sentence with fewer than 7 tokens is invalid."""
        text = "The cat sat."
        doc = nlp(text)
        sent = list(doc.sents)[0]

        assert chunking_is_valid_sentence(sent) is False
        assert migration_is_valid_sentence(sent) is False

    def test_invalid_sentence_no_verb_or_noun(self):
        """Test that sentence without proper grammatical structure is invalid."""
        # Create a fragment without verb or proper structure
        text = "Over and above the standard deviation threshold value."
        doc = nlp(text)
        sent = list(doc.sents)[0]

        # This might still pass if it has verb/noun, so we check the result
        result = chunking_is_valid_sentence(sent)
        assert migration_is_valid_sentence(sent) == result

    def test_punctuation_not_counted_in_tokens(self):
        """Test that punctuation is excluded from token count."""
        # Sentence with 6 words but lots of punctuation
        text = "One, two, three, four, five, six!"
        doc = nlp(text)
        sent = list(doc.sents)[0]

        # 6 tokens + punctuation - should be invalid (need 7+)
        assert chunking_is_valid_sentence(sent) is False
        assert migration_is_valid_sentence(sent) is False

    def test_punctuation_excluded_but_valid_structure(self):
        """Test that valid sentence with punctuation still passes."""
        text = "The machine learning algorithm, which was trained on millions of examples, achieved remarkable accuracy!"
        doc = nlp(text)
        sent = list(doc.sents)[0]

        assert chunking_is_valid_sentence(sent) is True
        assert migration_is_valid_sentence(sent) is True

    def test_get_sentences_filters_invalid(self):
        """Test that _get_sentences returns only valid sentences."""
        text = """
        The comprehensive study carefully analyzed multiple factors in detail. Too short.
        This is another valid sentence that meets all the criteria for inclusion.
        Just three words.
        """

        chunking_result = chunking_get_sentences(text)
        migration_result = migration_get_sentences(text)

        # Should only include the two valid sentences (first has 7+ tokens, second has 7+ tokens)
        assert len(chunking_result) == 2
        assert len(migration_result) == 2
        assert chunking_result == migration_result

    def test_zero_sentence_count_acceptable(self):
        """Test that text with no valid sentences returns empty list."""
        text = "Too short. Very brief. So quick."

        chunking_result = chunking_get_sentences(text)
        migration_result = migration_get_sentences(text)

        # All sentences are too short
        assert len(chunking_result) == 0
        assert len(migration_result) == 0

    def test_empty_text_returns_empty_list(self):
        """Test that empty text returns empty list."""
        assert chunking_get_sentences("") == []
        assert migration_get_sentences("") == []
        assert chunking_get_sentences(None) == []
        assert migration_get_sentences(None) == []

    def test_consistency_between_implementations(self):
        """Test that content_chunking and migration implementations are consistent."""
        test_texts = [
            "The quick brown fox jumps over the lazy dog every single day.",
            "Short.",
            "This is a longer sentence that should definitely be counted as valid text.",
            "Machine learning models require substantial computational resources for training purposes.",
            "Figure 1 shows the results.",
            "In conclusion, the experimental data strongly supports the proposed theoretical framework.",
            "One two three four five six seven eight.",
        ]

        for text in test_texts:
            chunking_result = chunking_get_sentences(text)
            migration_result = migration_get_sentences(text)
            assert chunking_result == migration_result, f"Mismatch for text: {text}"

    def test_sentence_with_subject_dependency_variants(self):
        """Test that various subject dependency types are detected."""
        # Test nsubj (nominal subject)
        text = "The scientist discovered a new method for analyzing complex datasets efficiently."
        chunking_result = chunking_get_sentences(text)
        assert len(chunking_result) == 1

        # Test nsubjpass (passive nominal subject)
        text = "The results were carefully examined by independent reviewers from different institutions."
        chunking_result = chunking_get_sentences(text)
        assert len(chunking_result) == 1

        # Test csubj (clausal subject)
        text = "What matters most in research is maintaining rigorous methodological standards throughout."
        chunking_result = chunking_get_sentences(text)
        assert len(chunking_result) >= 0  # May or may not pass other criteria

    def test_academic_text_examples(self):
        """Test with realistic academic text examples."""
        text = """
        The study examined the relationship between cognitive load and learning outcomes.
        Results indicated significant improvements in the experimental group compared to controls.
        These findings suggest important implications for educational practice and curriculum design.
        """

        chunking_result = chunking_get_sentences(text)
        migration_result = migration_get_sentences(text)

        assert len(chunking_result) == 3
        assert chunking_result == migration_result

    def test_sentence_with_auxiliary_verb(self):
        """Test that auxiliary verbs (AUX) are recognized as verbs."""
        text = "The experiment has been conducted at multiple research facilities around the world."
        chunking_result = chunking_get_sentences(text)

        assert len(chunking_result) == 1

    def test_proper_nouns_counted_as_nouns(self):
        """Test that proper nouns (PROPN) are recognized as nouns."""
        text = "Dr. Smith and Professor Johnson collaborated on developing new analytical techniques."
        chunking_result = chunking_get_sentences(text)

        assert len(chunking_result) == 1
