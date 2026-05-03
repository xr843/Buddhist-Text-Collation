# Roadmap

[中文 ROADMAP](ROADMAP.md) · **English**

> A living roadmap. Items link to issues where possible.
> Ordering reflects "researcher value × feasibility", not a fixed schedule.

---

## 🎯 Current

**v0.1.0** — first public open-source release (2026-05-02).
Full notes in [`CHANGELOG.md`](CHANGELOG.md).

---

## 🟢 v0.2 — Polish (Soon)

**Goal**: complete the open-source baseline + first wave of quality fixes.

| Item | Issue | Size |
|---|---|---|
| `examples/` public sample + README "3-minute Try" | [#24](../../issues/24) | S |
| GitHub Social Preview Image | [#25](../../issues/25) | XS |
| "Full-state" feature screenshots (real data) | [#26](../../issues/26) | M (4 PR) |
| API docs for collab / auth / admin modules | [#31](../../issues/31) | M (3 PR) |
| Backend ruff warnings → 0 | [#27](../../issues/27) | XS |
| TypeScript strict-mode regression | [#28](../../issues/28) | L (~10 PR) |
| Frontend Vitest baseline | [#29](../../issues/29) | S |
| GitHub Actions Node 24 compat | [#33](../../issues/33) | XS |
| python-jose / multipart CVE bumps | [#32](../../issues/32) | XS |
| Frontend first-paint chunk diet | [#30](../../issues/30) | M |

**Outcome**: CI strict everywhere, docs complete, overseas contributors can ramp up.

---

## 🟡 v0.3 — Internationalization & Accessibility (Mid)

**Goal**: enable non-Chinese-reading scholars to use the platform directly;
make the collaboration features work in practice.

| Item | Issue | Size |
|---|---|---|
| Frontend i18n scaffold + English skeleton | [#34](../../issues/34) | M |
| Per-page translation (one PR per page) | TBD | L (~15 PR) |
| Collaboration module: invitation flow, annotation notifications | TBD | M |
| Mobile / tablet responsive layout | TBD | M |
| Smart collation-note generation (**pure rules**, no LLM dependency) | TBD | L |
| English docs (README.en.md → docs/en/) | TBD | M |

---

## 🔵 Future — Open Directions

**Goal**: research directions; priority driven by user feedback and community demand.

- **Batch collation CLI**: turn multi-edition PDFs/TXTs into a draft
  collation note in one command
- **Full TEI XML export**: TEI P5 / EpiDoc-compliant output
- **CBETA offline snapshot**: bundle a CBETA subset, remove external-API dependency
- **Deeper visualization**: lineage 3D, timelines, geographic overlays
- **AI assist (optional plugin, not core)**: punctuation hints,
  variant-adjudication suggestions — surfaced as **plugins**, never as
  a hard dependency
- **Public demo site**: read-only demo on fly.io / Render
- **Academic citation**: DOI, CITATION.cff, Zenodo integration
- **Teaching kit**: starter templates for Buddhology / classical-philology courses

---

## 📐 Size Legend

- **XS**: < 30 min, 1 PR
- **S**: < 2 hours, 1 PR
- **M**: half-day to a day, 1–3 PR
- **L**: multiple days, multiple PRs

---

## 💡 Want to help?

1. Pick an item above linked to an issue (the
   [`good first issue`](../../issues?q=is%3Aissue+label%3A%22good+first+issue%22)
   label is the easiest entry point)
2. Comment "I'll take this" to avoid duplication
3. Follow [`CONTRIBUTING.md`](CONTRIBUTING.md) to open the PR

If the roadmap is missing something you'd want, please open a
[Discussion](../../discussions).

---

*Last updated: 2026-05-03*
