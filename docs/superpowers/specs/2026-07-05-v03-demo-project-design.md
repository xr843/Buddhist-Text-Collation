# v0.3 Reproducible Demo Project Design

## Decision

Start v0.3 with a reproducible demo project instead of beginning with the
larger frontend translation, collaboration, responsive layout, or public demo
site work.

## Why This Comes First

- It gives every later v0.3 task the same stable source data.
- It can be verified in CI without deploying the full stack.
- It reduces ambiguity for screenshots, public demo content, and English docs.
- It keeps the first v0.3 change small enough to review and merge quickly.

## Scope

This change adds:

- `examples/demo-project/manifest.json`
- source texts under `examples/demo-project/texts/`
- deterministic expected outputs under `examples/demo-project/expected/`
- screenshot-source notes under `examples/demo-project/screenshots/`
- backend regression tests proving the expected outputs match current services
- updated examples documentation

This change does not add a hosted demo, new UI routes, auth flow changes, or
new collation algorithms.

## Data Choice

Use the existing public-domain classical Chinese sample from the opening of
the *Analects*. It is not a Buddhist canonical text, but it is suitable for a
repository demo because it is short, public domain, and already demonstrates
the same text-agnostic collation pipeline.

Future Buddhist samples can be added as separate demo manifests once
attribution and copyright boundaries are settled.

## Acceptance Criteria

- A reader can inspect `examples/demo-project/README.md` and understand which
  files drive each workflow.
- `manifest.json` lists all source and expected-output files.
- Expected text-comparison and punctuation-transfer outputs are committed.
- A backend test fails if the committed expected outputs drift from service
  behavior.
- `examples/README.md` points contributors to the richer demo project.
