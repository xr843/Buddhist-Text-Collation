"""Unit tests for app.services.text_compare.TextComparisonService."""
from __future__ import annotations

from app.services.text_compare import DiffType, TextComparisonService


class TestCompareTexts:
    def test_identical_texts_have_similarity_1_and_only_equal_diffs(self):
        svc = TextComparisonService()
        result = svc.compare_texts("学而时习之", "学而时习之")
        assert result["similarity"] == 1.0
        assert all(d.get("type") == DiffType.EQUAL for d in result["differences"])

    def test_completely_different_texts_score_low(self):
        svc = TextComparisonService()
        # Disjoint Chinese chars; similarity should be low. Don't pin
        # to 0.0 — the implementation uses SequenceMatcher heuristics.
        result = svc.compare_texts("学而时习之", "甲乙丙丁戊")
        assert result["similarity"] <= 0.2

    def test_layout_differences_dont_count(self):
        # Per the docstring of compare_texts: line-break differences
        # between editions (高丽版 20-char lines vs. 福州版 40-char lines)
        # must NOT register as content differences. Same content, different
        # newlines → similarity 1.
        svc = TextComparisonService()
        with_breaks = "学而时习之\n不亦说乎"
        without_breaks = "学而时习之不亦说乎"
        result = svc.compare_texts(with_breaks, without_breaks)
        assert result["similarity"] == 1.0

    def test_response_shape_is_stable(self):
        svc = TextComparisonService()
        result = svc.compare_texts("a", "a", "ed1", "ed2")
        # Public callers (UI + export) rely on these keys being present.
        assert set(result.keys()) >= {
            "version1_name",
            "version2_name",
            "differences",
            "statistics",
            "similarity",
        }
        assert result["version1_name"] == "ed1"
        assert result["version2_name"] == "ed2"


class TestNormalizeTextForComparison:
    def test_strips_newlines(self):
        svc = TextComparisonService()
        # The function exists specifically to make line-break differences
        # invisible to the diff layer.
        assert "\n" not in svc.normalize_text_for_comparison("a\nb\nc")


class TestCheckPureTextConsistency:
    def test_same_pure_text_with_diff_punctuation_is_consistent(self):
        svc = TextComparisonService()
        consistent, _, _ = svc.check_pure_text_consistency(
            "学而时习之，不亦说乎",
            "学而时习之。不亦说乎",
        )
        # Pure text (sans punctuation) is identical → True.
        assert consistent is True

    def test_different_pure_text_is_not_consistent(self):
        svc = TextComparisonService()
        consistent, _, _ = svc.check_pure_text_consistency(
            "学而时习之",
            "学而时习也",  # 之 → 也
        )
        assert consistent is False
