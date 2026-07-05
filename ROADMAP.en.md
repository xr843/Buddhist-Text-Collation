# Roadmap

[中文 ROADMAP](ROADMAP.md) · **English**

> A living roadmap. Items link to issues where possible.
> Ordering reflects "researcher value × feasibility", not a fixed schedule.

---

## Current

**v0.2.0 is published** — engineering baseline, CI gates, Docker/Alembic,
bilingual entry points, OCR integration, public-facing assets, and dependency
security cleanup are in place.

Full notes live in [`CHANGELOG.md`](CHANGELOG.md).

---

## v0.2 — Open-source Credibility

**Goal**: help external researchers and contributors understand the project
state, run samples quickly, and see deployment boundaries.

### Completed

| Item | Issue | Notes |
|---|---|---|
| `examples/` public sample + README "3-minute Try" | [#24](../../issues/24) | Merged; supports quick evaluation |
| API docs for collab / auth / admin modules | [#31](../../issues/31) | Module docs are in place |
| Backend ruff warnings to zero | [#27](../../issues/27) | Ruff is now a gating CI check |
| TypeScript strict-mode regression | [#28](../../issues/28) | `tsc --noEmit` runs in CI |
| Frontend Vitest baseline | [#29](../../issues/29) | Frontend tests are gated |
| Frontend i18n scaffold + English skeleton | [#34](../../issues/34) | react-i18next and zh/en resource skeleton are in place |
| GitHub Actions Node compatibility | [#33](../../issues/33) | CI actions updated |
| python-jose / multipart CVE bumps | [#32](../../issues/32) | Security dependencies upgraded |
| Frontend first-paint chunk diet | [#30](../../issues/30) | Route-level lazy loading and manual chunks are in place |
| Docker Compose provisions PostgreSQL | [#55](../../pull/55) | `docker-compose up -d --build` can start the stack |
| Alembic migrations + migration smoke CI | [#56](../../pull/56) | Covers upgrade/downgrade smoke |
| `CITATION.cff` and citation entry | [#58](../../pull/58) | GitHub can show repository citation |
| Algorithm-layer unit test baseline | [#60](../../pull/60) | Covers core collation algorithms |
| Ancient OCR integration | [#88](../../pull/88) | Requires user-supplied gj.cool credentials |
| GitHub Social Preview Image | [#25](../../issues/25) | Social preview assets are in place |
| Full-state feature screenshots with real data | [#26](../../issues/26) | README now uses filled-state screenshots |
| Freeze `CHANGELOG.md` as v0.2.0 release notes | [#96](../../pull/96) | Finalized with the release date |

### Release Status

| Item | Issue | Size |
|---|---|---|
| v0.2.0 tag / GitHub Release | TBD | Done |

**Outcome**: a credible v0.2 open-source release with clear docs, examples,
CI, deployment path, and security boundaries.

---

## v0.3 — Demo, i18n & Collaboration

**Goal**: let overseas scholars try the platform directly and move
collaboration from implemented features to usable research workflows.

| Item | Issue | Size |
|---|---|---|
| Reproducible demo project: public samples, expected outputs, screenshot source data | TBD | M |
| Per-page frontend translation, one PR per page | TBD | L |
| Collaboration module: invitation flow, annotation notifications | TBD | M |
| Mobile / tablet responsive layout | TBD | M |
| Public read-only demo site | TBD | M |
| Expanded English docs (`README.en.md` to `docs/en/`) | TBD | M |

---

## v0.4 — Research-grade Exports

**Goal**: make platform outputs suitable for papers, courses, digital
humanities projects, and long-term archival workflows.

| Item | Issue | Size |
|---|---|---|
| TEI P5 apparatus export: `app` / `lem` / `rdg` / `wit` / `sourceDesc` | TBD | L |
| Stable DOCX academic report template | TBD | M |
| Collation-note golden tests with fixed inputs and outputs | TBD | M |
| Punctuation-transfer golden tests | TBD | S |
| Multi-edition collation golden tests | TBD | M |
| Citation metadata and export provenance | TBD | M |

---

## Future — Open Directions

**Goal**: research directions; priority driven by user feedback and community demand.

- **Batch collation CLI**: turn multi-edition PDFs/TXTs into a draft collation note in one command.
- **CBETA offline snapshot**: bundle a CBETA subset and reduce external-API dependency.
- **Deeper visualization**: lineage 3D, timelines, geographic overlays.
- **AI assist (optional plugin, not core)**: punctuation hints and variant-adjudication suggestions as plugins, never as a hard dependency.
- **Teaching kit**: starter templates for Buddhology / classical-philology courses.
- **Zenodo / DOI integration**: formal academic publication paired with `CITATION.cff`.

---

## Size Legend

- **XS**: < 30 min, 1 PR
- **S**: < 2 hours, 1 PR
- **M**: half-day to a day, 1-3 PR
- **L**: multiple days, multiple PRs

---

## Want to help?

1. Pick an issue-linked item above, or start from [`good first issue`](../../issues?q=is%3Aissue+label%3A%22good+first+issue%22).
2. Comment "I'll take this" to avoid duplication.
3. Follow [`CONTRIBUTING.md`](CONTRIBUTING.md) to open the PR.

If the roadmap is missing something you'd want, please open a [Discussion](../../discussions).

---

*Last updated: 2026-07-05*
