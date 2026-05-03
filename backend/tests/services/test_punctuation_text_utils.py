"""Unit tests for app.services.punctuation_analysis.text_utils."""
from __future__ import annotations

from app.services.punctuation_analysis.text_utils import (
    build_punctuation_map,
    normalize_for_comparison,
    split_into_sentences,
)


class TestNormalizeForComparison:
    def test_collapses_newlines_to_spaces(self):
        assert normalize_for_comparison("a\nb\nc") == "a b c"

    def test_collapses_multiple_spaces(self):
        assert normalize_for_comparison("a    b   c") == "a b c"

    def test_strips_outer_whitespace(self):
        assert normalize_for_comparison("  hello  ") == "hello"

    def test_empty_input(self):
        assert normalize_for_comparison("") == ""


class TestBuildPunctuationMap:
    def test_no_punctuation_yields_empty_map(self):
        # All non-punct chars; nothing to map.
        assert build_punctuation_map("学而时习之") == {}

    def test_trailing_punctuation_after_each_char(self):
        # 子，曰：学：
        # char 0 (子) followed by ，
        # char 1 (曰) followed by ：
        # char 2 (学) followed by ：
        result = build_punctuation_map("子，曰：学：")
        assert result == {0: "，", 1: "：", 2: "："}

    def test_leading_punctuation_keyed_at_minus_one(self):
        # The function explicitly uses key -1 for sentence-leading
        # punctuation (per docstring).
        result = build_punctuation_map("「学而")
        assert result.get(-1) == "「"

    def test_consecutive_punct_concatenated(self):
        # When several punct marks follow the same char, they're collected
        # into one string at that index.
        result = build_punctuation_map("学。」")
        assert result.get(0) == "。」"


class TestSplitIntoSentences:
    def test_period_terminator_kept_with_sentence(self):
        result = split_into_sentences("学而时习之。有朋自远方来。")
        assert result == ["学而时习之。", "有朋自远方来。"]

    def test_question_and_exclam_terminators(self):
        result = split_into_sentences("不亦说乎？不亦乐乎！")
        assert result == ["不亦说乎？", "不亦乐乎！"]

    def test_trailing_text_without_terminator_preserved(self):
        # The remainder after the last terminator must NOT be dropped.
        result = split_into_sentences("学而时习之。不亦说乎")
        assert result == ["学而时习之。", "不亦说乎"]

    def test_empty_input_yields_empty_list(self):
        assert split_into_sentences("") == []
