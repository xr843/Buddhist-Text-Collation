# v0.3 Reproducible Demo Project Implementation Plan

## Goal

Create a small, versioned demo project that can serve as the shared fixture for
v0.3 docs, screenshots, automated checks, and later hosted demo work.

## Tasks

1. Add a failing backend regression test for the future demo project.
2. Add the demo project directory, manifest, source texts, and documentation.
3. Generate expected outputs from the existing text comparison and punctuation
   transfer services.
4. Update `examples/README.md` to distinguish quick samples from the
   reproducible demo project.
5. Run targeted and broader verification.

## Verification

- `cd backend && .venv/bin/python -m pytest tests/services/test_demo_project_expected_outputs.py -q`
- `cd backend && .venv/bin/python -m pytest tests/ -q`
- `git diff --check`
