"""Unit tests for app.services.collation.text_normalizer.

Covers the three exported functions used by both collation pipelines:
- normalize_text_for_comparison: strips whitespace + zero-width chars
- extract_clean_text_with_mapping: returns clean text + position map back to original
- parse_text_to_chars_and_gaps: splits text into chars list and surrounding-punctuation gaps

Test data uses generic Classical Chinese (Analects) to avoid coupling the
test suite to any specific corpus.
"""
from __future__ import annotations

import pytest

from app.services.collation.text_normalizer import (
    extract_clean_text_with_mapping,
    normalize_text_for_comparison,
    parse_text_to_chars_and_gaps,
)


class TestNormalizeTextForComparison:
    def test_strips_ascii_whitespace(self):
        assert normalize_text_for_comparison("a b\tc\nd\re") == "abcde"

    def test_strips_full_width_space(self):
        # U+3000 is the CJK ideographic space — common in OCR'd Buddhist texts.
        assert normalize_text_for_comparison("子　曰") == "子曰"

    def test_strips_nbsp(self):
        assert normalize_text_for_comparison("a b") == "ab"

    def test_strips_zero_width_chars(self):
        # ZWSP, ZWNJ, ZWJ, BOM, word joiner — all should disappear.
        for invisible in ("​", "‌", "‍", "﻿", "⁠"):
            assert normalize_text_for_comparison(f"a{invisible}b") == "ab"

    def test_preserves_punctuation(self):
        # Normalization removes whitespace, NOT punctuation — punctuation is
        # what the diff layer reasons about.
        s = "学而时习之，不亦说乎？"
        assert normalize_text_for_comparison(s) == s

    def test_empty_string_is_idempotent(self):
        assert normalize_text_for_comparison("") == ""


class TestExtractCleanTextWithMapping:
    def test_no_punctuation_is_identity_mapping(self):
        clean, pos_map = extract_clean_text_with_mapping("学而时习之")
        assert clean == "学而时习之"
        assert pos_map == {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}

    def test_strips_punctuation_and_keeps_round_trip_pointers(self):
        clean, pos_map = extract_clean_text_with_mapping("学而，时习之。")
        assert clean == "学而时习之"
        # Each clean position must point back to a real original-text index
        # whose character is the matching clean char.
        original = "学而，时习之。"
        for clean_idx, char in enumerate(clean):
            assert original[pos_map[clean_idx]] == char

    def test_empty_input(self):
        clean, pos_map = extract_clean_text_with_mapping("")
        assert clean == ""
        assert pos_map == {}


class TestParseTextToCharsAndGaps:
    def test_gaps_envelope_chars(self):
        # Invariant declared in the function's docstring:
        #   len(gaps) == len(chars) + 1
        # gaps[i] is whatever sits *before* chars[i]; gaps[-1] is the trailing run.
        chars, gaps = parse_text_to_chars_and_gaps("子曰：学而")
        assert chars == ["子", "曰", "学", "而"]
        assert len(gaps) == len(chars) + 1

    def test_pure_text_yields_empty_gaps(self):
        chars, gaps = parse_text_to_chars_and_gaps("学而时习之")
        assert chars == ["学", "而", "时", "习", "之"]
        # All gaps are empty when there's no punctuation/whitespace.
        assert all(g == "" for g in gaps)

    def test_empty_input(self):
        chars, gaps = parse_text_to_chars_and_gaps("")
        assert chars == []
        # The "len(gaps) == len(chars) + 1" invariant means one empty gap.
        assert gaps == [""]


# Sanity check: the three functions agree on what counts as a "char".
def test_clean_extract_and_chars_agree():
    text = "子曰：学而时习之，不亦说乎？"
    clean, _ = extract_clean_text_with_mapping(text)
    chars, _ = parse_text_to_chars_and_gaps(text)
    assert clean == "".join(chars)
