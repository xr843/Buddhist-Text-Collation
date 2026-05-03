"""Unit tests for app.services.collation.char_diff.

These exercise the core academic value of the platform — character-level
collation between two editions — so they're deliberately concrete:
identical inputs, single-char swaps, punctuation-only differences,
each with the diff_type the platform reports back to the UI.
"""
from __future__ import annotations

from app.services.collation.char_diff import compute_char_diff


def _all_equal(segments) -> bool:
    return all(seg.get("type") == "equal" for seg in segments)


class TestComputeCharDiff:
    def test_identical_texts_have_no_diff(self):
        result = compute_char_diff("学而时习之", "学而时习之")
        assert _all_equal(result["segments1"])
        assert _all_equal(result["segments2"])
        # No diff at all — diff_type should be falsy (None / "" / absent).
        assert not result.get("diff_type")

    def test_identical_with_same_punctuation(self):
        s = "学而时习之，不亦说乎？"
        result = compute_char_diff(s, s)
        assert _all_equal(result["segments1"])
        assert _all_equal(result["segments2"])

    def test_single_char_substitution_is_text_diff(self):
        # 说 → 悦: classic variant character (异体字) — exactly the case the
        # collation platform exists to surface. Should NOT be flagged as
        # punctuation-only.
        result = compute_char_diff("学而时习之，不亦说乎", "学而时习之，不亦悦乎")
        assert result.get("diff_type") in {"text_only", "mixed"}, result
        # Both sides must contain at least one non-equal segment.
        assert not _all_equal(result["segments1"])
        assert not _all_equal(result["segments2"])

    def test_punctuation_only_diff_is_classified_as_punct_only(self):
        # Same characters, different punctuation — must be flagged so the UI
        # can colour-code it differently from a real textual variant.
        result = compute_char_diff("学而时习之，不亦说乎", "学而时习之。不亦说乎")
        assert result.get("diff_type") == "punct_only", result

    def test_pure_addition_marks_one_side_equal(self):
        # text2 is a strict superset; segments1 should be all-equal.
        result = compute_char_diff("学而时习之", "学而时习之，不亦说乎")
        assert _all_equal(result["segments1"])
        # segments2 must contain something non-equal (the added tail).
        assert not _all_equal(result["segments2"])

    def test_returns_expected_top_level_keys(self):
        result = compute_char_diff("a", "a")
        assert set(result.keys()) >= {"segments1", "segments2", "diff_type"}
