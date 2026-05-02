# 更新日志 / Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式与
[Semantic Versioning](https://semver.org/lang/zh-CN/) 规范。

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### 待办 / Planned
- 后端测试覆盖（pytest）
- 前端类型债清理（移除 `tsc --noEmit` advisory 模式）
- 后端依赖升级（`python-jose`、`python-multipart` CVE 修复）

---

## [0.1.0] — 2026-05-02

首个开源版本，从内部研究仓库整理而来，适配公开发布。

First open-source release, polished from an internal research repo for
public distribution.

### 包含的核心模块 / Modules included

- **标点版本对比 / Punctuation diff** —— 单文件多版本逐字对照、差异高亮、判取流转
- **两版本对勘 / Two-edition collation** —— 行/字级差异、异体字识别
- **多版本对勘 / Multi-edition collation** —— 31 个版本同屏对勘、自动校勘记
- **注疏对读 / Commentary parallel reading** —— 经论注疏并排、跨文本引证
- **版本谱系 / Version lineage** —— 异文聚类、Lineage Graph
- **标点迁移 / Punctuation transfer** —— 在不同文本之间迁移标点
- **CBETA 集成 / CBETA integration** —— 直接从 CBETA 数据库导入文本
- **协作 / Collaboration** —— 项目、成员、角色、批注、协作锁
- **导出 / Export** —— TXT / DOCX / 校勘记 CSV / 全量对照表

### 不含 / Removed prior to release

- **OCR 数字化工作台** —— 原内部版本集成了第三方付费 OCR（gj.cool）。开源版**不**集成；
  用户可使用任意外部 OCR 工具，把识别后的文本导入本平台校勘流程。
- **数字佛典平台数据迁移** —— 内网定向工具，已下线，仅保留模块壳供自部署者扩展。
- **The OCR digitization workbench** that integrated a paid third-party OCR
  service (gj.cool) is **not** included in the open-source release.
  Use any external OCR tool and import the recognized text into the
  collation workflow.

### 工程化 / Engineering

- 添加 `LICENSE` (AGPL-3.0)
- 添加 `CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`
- 添加 GitHub Issue / PR 模板
- 添加 `.github/workflows/ci.yml`：ruff (advisory) + tsc (advisory) + vite build (gating) + gitleaks
- 添加 `.github/dependabot.yml`：每周自动检查 pip / npm 依赖更新
- 重建 git 历史，确保无凭据/版权敏感数据残留
- 内网 IP / 默认密码全部改为环境变量
- 双语 README + 详细中文文档

### 安全 / Security

- 部署前请阅读 [SECURITY.md](SECURITY.md) 中的硬性要求
- 默认 `BACKEND_CORS_ORIGINS` 仅本地；公网部署须显式配置
- `SECRET_KEY` / `UMAMI_APP_SECRET` / `UMAMI_DB_PASSWORD` 必须从环境变量注入
- `gitleaks` CI 步骤会扫描每次 push 的密钥泄露

[Unreleased]: https://github.com/xr843/buddhist-text-collation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xr843/buddhist-text-collation/releases/tag/v0.1.0
