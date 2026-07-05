"""Regression tests for the reproducible v0.3 demo project."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.punctuation_transfer_service import punctuation_transfer_service
from app.services.text_compare import TextComparisonService


REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_DIR = REPO_ROOT / "examples" / "demo-project"


def read_text(relative_path: str) -> str:
    return (DEMO_DIR / relative_path).read_text(encoding="utf-8").strip()


def test_demo_project_manifest_describes_reproducible_assets():
    assert DEMO_DIR.exists(), "examples/demo-project must exist"

    manifest = json.loads((DEMO_DIR / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["project_slug"] == "classical-chinese-collation-demo"
    assert manifest["texts"] == [
        "texts/base-punctuated.txt",
        "texts/witness-variant.txt",
        "texts/target-unpunctuated.txt",
    ]
    assert manifest["expected_outputs"] == [
        "expected/text-compare.json",
        "expected/punctuation-transfer.txt",
    ]


def test_text_compare_expected_output_matches_demo_texts():
    expected = json.loads(read_text("expected/text-compare.json"))
    base = read_text("texts/base-punctuated.txt")
    witness = read_text("texts/witness-variant.txt")

    actual = TextComparisonService().compare_texts(
        base,
        witness,
        "Demo base punctuated",
        "Demo witness variant",
    )

    assert actual == expected


def test_punctuation_transfer_expected_output_matches_demo_texts():
    source = read_text("texts/base-punctuated.txt")
    target = read_text("texts/target-unpunctuated.txt")
    expected_text = read_text("expected/punctuation-transfer.txt")

    actual = punctuation_transfer_service.transfer(source, target)

    assert actual.result_text == expected_text
    assert actual.transferred_count == 7
    assert actual.total_punctuation_count == 7
    assert actual.alignment_score == pytest.approx(1.0)
    assert actual.warnings == []
