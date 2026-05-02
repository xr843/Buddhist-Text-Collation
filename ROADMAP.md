# 路线图 / Roadmap

> 这是一份**生长中的路线图**。每条都尽量挂到具体 issue 上，方便认领。
> 排序原则：按"对研究者价值 × 实施可行性"判断；不是死板时间表。
>
> A living roadmap. Items link to issues where possible.
> Ordering reflects "researcher value × feasibility", not a fixed schedule.

---

## 🎯 当前版本 / Current

**v0.1.0** — 首个公开开源版本（2026-05-02）。
完整功能见 [`CHANGELOG.md`](CHANGELOG.md)。

---

## 🟢 v0.2 — 完善阶段（近期 / Soon）

**目标**：补全开源项目应有的工程基础设施 + 第一波质量改进。

| Item | Issue | Size |
|---|---|---|
| 添加 `examples/` 公开文本样本 + README "3 分钟试用" 章节 | [#24](../../issues/24) | S |
| GitHub Social Preview Image | [#25](../../issues/25) | XS |
| 主要功能"满状态"截图（带真实数据） | [#26](../../issues/26) | M (4 PR) |
| 协作 / auth / admin 模块 API 文档 | [#31](../../issues/31) | M (3 PR) |
| 后端 ruff 警告清零 | [#27](../../issues/27) | XS |
| TypeScript 严格模式回归 | [#28](../../issues/28) | L (~10 PR) |
| 前端 Vitest 基础设置 | [#29](../../issues/29) | S |
| GitHub Actions Node 24 兼容 | [#33](../../issues/33) | XS |
| python-jose / multipart CVE 升级 | [#32](../../issues/32) | XS |
| 前端首屏 chunk 体积优化 | [#30](../../issues/30) | M |

**预期产出**：CI 全部 strict 模式、文档完备、海外贡献者能上手。

---

## 🟡 v0.3 — 国际化与可达性（中期 / Mid）

**目标**：让海外学者也能直接用，让协作机制真正跑起来。

| Item | Issue | Size |
|---|---|---|
| 前端 i18n 脚手架 + 英文骨架 | [#34](../../issues/34) | M |
| 前端逐 page 翻译（每 page 一个 PR） | TBD | L (~15 PR) |
| 协作模块完善：成员邀请流程、批注通知 | TBD | M |
| 移动端 / 平板适配（响应式布局） | TBD | M |
| 校勘记智能生成：基于异文类型自动生成草稿（**纯规则**，不引入 LLM 依赖） | TBD | L |
| 文档英文版（README.en.md → docs/en/）| TBD | M |

---

## 🔵 Future — 探索方向 / Open

**目标**：研究方向探索；优先级看用户反馈与社区需求决定。

- **批量校勘流水线**：CLI 工具把多版本 PDF/TXT 一键跑成校勘记草稿
- **TEI XML 全套导出**：完全符合 TEI P5 / EpiDoc 规范的输出
- **CBETA 离线快照**：内置一份 CBETA 子集，去除外部 API 依赖
- **可视化深化**：版本谱系 3D / 时间轴 / 地理分布联动
- **AI 辅助（可选插件，非核心）**：标点建议、异文判取建议——以**插件**形态接入，不进核心依赖
- **公开实例 / Demo Site**：在 fly.io / Render 部署一个只读演示
- **学术引用规范**：DOI 申请、CITATION.cff、Zenodo 集成
- **教学场景包**：面向佛学/古文献课程的示例项目模板

---

## 📐 大小标记 / Size legend

- **XS**: < 30 分钟，1 个 PR
- **S**: < 2 小时，1 个 PR
- **M**: 半天到一天，1-3 个 PR
- **L**: 多天，多个 PR

---

## 💡 想贡献？ / Want to help?

1. 选一个上面带 issue 链接的条目（推荐 [`good first issue`](../../issues?q=is%3Aissue+label%3A%22good+first+issue%22) 标签）
2. 在 issue 下回复 "I'll take this" 防撞
3. 按 [`CONTRIBUTING.md`](CONTRIBUTING.md) 流程开 PR

如果发现路线图缺了你想要的能力，欢迎开 [Discussion](../../discussions) 提议。

---

*最后更新 / Last updated: 2026-05-02*
