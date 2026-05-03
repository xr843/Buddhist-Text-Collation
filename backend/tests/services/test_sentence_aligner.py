"""Unit tests for app.services.collation.sentence_aligner."""
from __future__ import annotations

from app.services.collation.sentence_aligner import (
    compute_similarity,
    split_sentences,
)


class TestSplitSentences:
    def test_period_splits(self):
        result = split_sentences("学而时习之。有朋自远方来。")
        # Should produce two non-empty sentences; trailing whitespace tolerated.
        assert [s.strip() for s in result if s.strip()] == [
            "学而时习之。",
            "有朋自远方来。",
        ]

    def test_question_mark_also_splits(self):
        result = [s.strip() for s in split_sentences("不亦说乎？不亦乐乎？") if s.strip()]
        assert result == ["不亦说乎？", "不亦乐乎？"]

    def test_single_sentence_returns_single_element(self):
        result = [s for s in split_sentences("学而时习之。") if s.strip()]
        assert result == ["学而时习之。"]

    def test_falls_back_to_comma_for_long_unpunctuated_text(self):
        # 350+ chars with no terminal punctuation should trigger the
        # comma/semicolon fallback documented in the function's strategy.
        long_text = "甲乙丙丁戊己庚辛壬癸，" * 30 + "。"
        result = split_sentences(long_text)
        # Many segments expected (≥10) — exact count depends on heuristic.
        assert len(result) >= 10


class TestComputeSimilarity:
    def test_identical_texts_score_1(self):
        assert compute_similarity("学而时习之", "学而时习之") == 1.0

    def test_completely_different_texts_score_0(self):
        # No shared chars after punctuation/whitespace stripping.
        assert compute_similarity("ABCDE", "xyzwq") == 0.0

    def test_punctuation_only_diff_still_scores_1(self):
        # The whole point of the function: ignore punctuation when scoring
        # similarity (so "学而，时习之" and "学而时习之" are "the same").
        assert compute_similarity("学而，时习之。", "学而时习之") == 1.0

    def test_empty_pair_is_handled(self):
        # Documented behavior: don't crash on empty inputs.
        score = compute_similarity("", "")
        assert 0.0 <= score <= 1.0
