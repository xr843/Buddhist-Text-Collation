"""Golden-sample tests for punctuation transfer."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.punctuation_transfer_service import punctuation_transfer_service
from app.utils.punctuation import strip_punctuation_and_whitespace


REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DIR = REPO_ROOT / "examples" / "classical-chinese-sample"


def read_sample(filename: str) -> str:
    return (SAMPLE_DIR / filename).read_text(encoding="utf-8").strip()


def test_transfers_punctuation_to_unpunctuated_sample_exactly():
    punctuated = read_sample("punctuated.txt")
    unpunctuated = read_sample("unpunctuated.txt")

    result = punctuation_transfer_service.transfer(punctuated, unpunctuated)

    assert result.result_text == punctuated
    assert result.transferred_count == 7
    assert result.total_punctuation_count == 7
    assert result.alignment_score == 1.0
    assert result.warnings == []


def test_transfers_punctuation_to_variant_sample_stably():
    punctuated = read_sample("punctuated.txt")
    variant = read_sample("variant.txt")
    stripped_variant = strip_punctuation_and_whitespace(variant)

    result = punctuation_transfer_service.transfer(punctuated, stripped_variant)

    assert result.result_text == variant
    assert result.transferred_count == 7
    assert result.total_punctuation_count == 7
    assert result.alignment_score == pytest.approx(0.96875)
    assert result.warnings == []
