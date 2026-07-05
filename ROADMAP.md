# 路线图 / Roadmap

**中文** · [English](ROADMAP.en.md)

> 这是一份**生长中的路线图**。每条都尽量挂到具体 issue 上，方便认领。
> 排序原则：按"对研究者价值 × 实施可行性"判断；不是死板时间表。
>
> A living roadmap. Items link to issues where possible.
> Ordering reflects "researcher value × feasibility", not a fixed schedule.

---

## 当前状态 / Current

**v0.2.0 release candidate** — 工程基础设施、测试门禁、Docker/Alembic、
双语入口、OCR 集成与文档基线已经完成。正式发布前仍需要补齐公开展示素材：
GitHub Social Preview 与主要功能"满状态"截图。

完整变更见 [`CHANGELOG.md`](CHANGELOG.md)。

---

## v0.2 — 开源可信版 / Open-source Credibility

**目标**：让外部研究者和贡献者能判断项目状态、快速跑通样例、理解部署边界。

### 已完成 / Completed

| Item | Issue | Notes |
|---|---|---|
| 添加 `examples/` 公开文本样本 + README "3 分钟试用" 章节 | [#24](../../issues/24) | 已合入，支撑快速体验 |
| 协作 / auth / admin 模块 API 文档 | [#31](../../issues/31) | 已补齐模块文档 |
| 后端 ruff 警告清零 | [#27](../../issues/27) | CI 中 ruff 已改为 gating |
| TypeScript 严格模式回归 | [#28](../../issues/28) | `tsc --noEmit` 已进入 CI |
| 前端 Vitest 基础设置 | [#29](../../issues/29) | 已加入前端测试门禁 |
| 前端 i18n 脚手架 + 英文骨架 | [#34](../../issues/34) | 已接入 react-i18next 与中英资源骨架 |
| GitHub Actions Node 兼容升级 | [#33](../../issues/33) | CI actions 已更新 |
| python-jose / multipart CVE 升级 | [#32](../../issues/32) | 安全依赖已升级 |
| 前端首屏 chunk 体积优化 | [#30](../../issues/30) | 已有路由级 lazy 与 manualChunks |
| Docker Compose 内置 PostgreSQL 主库 | [#55](../../pull/55) | `docker-compose up -d --build` 可直接起栈 |
| Alembic 迁移与 migration smoke CI | [#56](../../pull/56) | 覆盖 upgrade/downgrade smoke |
| `CITATION.cff` 与引用入口 | [#58](../../pull/58) | GitHub 侧栏可显示引用 |
| 算法层单元测试基线 | [#60](../../pull/60) | 已覆盖 collation 基础算法 |
| 古籍 OCR 集成 | [#88](../../pull/88) | 需自配 gj.cool 凭据 |

### 发布前剩余 / Release Polish

| Item | Issue | Size |
|---|---|---|
| GitHub Social Preview Image | [#25](../../issues/25) | XS |
| 主要功能"满状态"截图（带真实数据） | [#26](../../issues/26) | M |
| `CHANGELOG.md` 固化为 v0.2.0 release notes | TBD | XS |
| 发布 tag / GitHub Release | TBD | XS |

**预期产出**：一个可信的 v0.2 开源版本，文档、示例、CI、部署路径与安全边界都足够清楚。

---

## v0.3 — 演示、国际化与协作 / Demo, i18n & Collaboration

**目标**：让海外学者能直接试用，让协作机制从"已实现"走向"可用于真实项目"。

| Item | Issue | Size |
|---|---|---|
| 可复现 demo project：公开样本、预期输出、截图数据源 | TBD | M |
| 前端逐 page 翻译（每 page 一个 PR） | TBD | L |
| 协作模块完善：成员邀请流程、批注通知 | TBD | M |
| 移动端 / 平板适配（响应式布局） | TBD | M |
| 公开只读 Demo Site | TBD | M |
| 文档英文版扩展（`README.en.md` → `docs/en/`） | TBD | M |

---

## v0.4 — 研究级导出 / Research-grade Exports

**目标**：让平台输出能进入论文、课程、数字人文项目和长期归档流程。

| Item | Issue | Size |
|---|---|---|
| TEI P5 apparatus 导出增强：`app` / `lem` / `rdg` / `wit` / `sourceDesc` | TBD | L |
| DOCX 学术报告模板稳定化 | TBD | M |
| 校勘记 golden tests：固定输入、固定输出 | TBD | M |
| 标点迁移 golden tests | TBD | S |
| 多版本对勘 golden tests | TBD | M |
| 引用元数据与导出 provenance | TBD | M |

---

## Future — 探索方向 / Open Directions

**目标**：研究方向探索；优先级看用户反馈与社区需求决定。

- **批量校勘流水线**：CLI 工具把多版本 PDF/TXT 一键跑成校勘记草稿。
- **CBETA 离线快照**：内置一份 CBETA 子集，去除外部 API 依赖。
- **可视化深化**：版本谱系 3D / 时间轴 / 地理分布联动。
- **AI 辅助（可选插件，非核心）**：标点建议、异文判取建议；以插件形态接入，不进核心依赖。
- **教学场景包**：面向佛学/古文献课程的示例项目模板。
- **Zenodo / DOI 集成**：配合 `CITATION.cff` 做正式学术发布。

---

## 大小标记 / Size Legend

- **XS**: < 30 分钟，1 个 PR
- **S**: < 2 小时，1 个 PR
- **M**: 半天到一天，1-3 个 PR
- **L**: 多天，多个 PR

---

## 想贡献？ / Want to help?

1. 选一个上面带 issue 链接的条目，或从 [`good first issue`](../../issues?q=is%3Aissue+label%3A%22good+first+issue%22) 开始。
2. 在 issue 下回复 "I'll take this" 防撞。
3. 按 [`CONTRIBUTING.md`](CONTRIBUTING.md) 流程开 PR。

如果发现路线图缺了你想要的能力，欢迎开 [Discussion](../../discussions) 提议。

---

*最后更新 / Last updated: 2026-07-05*
