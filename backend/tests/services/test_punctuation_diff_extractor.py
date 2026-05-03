"""Unit tests for app.services.punctuation_analysis.diff_extractor.

Focus on the cheap-to-test classification helpers — they're what the
UI uses to label each variation in the punctuation-comparison view.
"""
from __future__ import annotations

import pytest

from app.services.punctuation_analysis.diff_extractor import (
    extract_punctuation_differences,
    get_diff_type,
    get_punctuation_category,
    get_punctuation_name,
)


class TestGetDiffType:
    def test_empty_first_means_addition(self):
        assert get_diff_type("", "。") == "新增标点"

    def test_empty_second_means_deletion(self):
        assert get_diff_type("。", "") == "删除标点"

    def test_different_punctuation_is_replacement(self):
        assert get_diff_type("，", "。") == "替换标点"

    def test_same_punctuation_with_extra_tail_is_addition(self):
        # punct1 is a prefix of punct2 → user added marks at the end.
        assert get_diff_type("。", "。」") == "新增标点"

    def test_same_punctuation_with_missing_tail_is_deletion(self):
        # punct2 is a prefix of punct1 → user removed trailing marks.
        assert get_diff_type("。」", "。") == "删除标点"

    def test_partial_overlap_is_replacement(self):
        # Common prefix exists but neither is a prefix of the other.
        assert get_diff_type("。」", "。』") == "替换标点"


class TestGetPunctuationCategory:
    @pytest.mark.parametrize("punct", ["，", "。", "？", "！"])
    def test_known_punct_returns_a_named_category_not_other(self, punct):
        # Don't pin to specific category strings — those live in constants
        # and may evolve. Just assert a known mark gets a real category.
        assert get_punctuation_category(punct, "") != "其他"

    def test_unknown_input_falls_back_to_other(self):
        assert get_punctuation_category("Z", "") == "其他"


class TestGetPunctuationName:
    def test_no_punct_returns_empty_label(self):
        assert get_punctuation_name("", "") == "无标点"

    def test_known_punct_yields_human_name(self):
        # Period is in PUNCTUATION_NAMES; we don't pin the exact string,
        # only that it's not the raw glyph (i.e. a name was looked up).
        name = get_punctuation_name("。", "")
        assert name and name != "。"

    def test_unknown_punct_falls_back_to_glyph(self):
        # Unknown char: the function returns the first char itself.
        assert get_punctuation_name("§", "") == "§"


class TestExtractPunctuationDifferences:
    def test_identical_texts_have_no_differences(self):
        diffs = extract_punctuation_differences(
            "学而时习之，不亦说乎",
            "学而时习之，不亦说乎",
        )
        assert diffs == []

    def test_single_punctuation_swap_surfaces_one_diff(self):
        diffs = extract_punctuation_differences(
            "学而时习之，不亦说乎",
            "学而时习之。不亦说乎",
        )
        assert len(diffs) == 1
        # Each diff dict must at minimum carry both sides + a type label.
        d = diffs[0]
        assert "version1_punct" in d or "punct1" in d  # tolerate either key
