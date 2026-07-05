# Reproducible Demo Project

This directory is the v0.3 reproducible demo project for Buddhist Text
Collation. It packages a small public-domain text fixture with deterministic
expected outputs so documentation, screenshots, and tests can refer to the same
inputs.

The sample comes from the opening of the *Analects*, a public-domain classical
Chinese text. It is used only to demonstrate the text-agnostic collation
pipeline; Buddhist canonical samples can be added later as separate manifests
once attribution and copyright checks are complete.

## Layout

```
examples/demo-project/
├── manifest.json
├── texts/
│   ├── base-punctuated.txt
│   ├── witness-variant.txt
│   └── target-unpunctuated.txt
├── expected/
│   ├── text-compare.json
│   └── punctuation-transfer.txt
└── screenshots/
    └── README.md
```

## Workflows

### Text Comparison

Use:

- Base: `texts/base-punctuated.txt`
- Witness: `texts/witness-variant.txt`

Expected result:

- one replacement difference: `说` -> `悦`
- stable service output in `expected/text-compare.json`

### Punctuation Transfer

Use:

- Source: `texts/base-punctuated.txt`
- Target: `texts/target-unpunctuated.txt`

Expected result:

- the original punctuation is restored exactly
- stable transferred text in `expected/punctuation-transfer.txt`

## Verification

From the repository root:

```bash
cd backend
.venv/bin/python -m pytest tests/services/test_demo_project_expected_outputs.py -q
```

That test confirms the committed expected outputs still match the backend
services.
