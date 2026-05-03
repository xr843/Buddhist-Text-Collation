# 更新日志 / Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式与
[Semantic Versioning](https://semver.org/lang/zh-CN/) 规范。

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- `examples/classical-chinese-sample/` 公开样本 + README "3 分钟试用" 章节 (#52)
- 标准 English README + ROADMAP（`README.en.md` / `ROADMAP.en.md`）+ 顶部语言切换 (#53)
- `docker-compose.yml` 新增 `postgres:15-alpine` 主库服务，`docker-compose up -d --build` 真正可用 (#55)
- Alembic schema migrations + `0001_baseline` + CI `migration-smoke` job (#56)
- `CITATION.cff`，GitHub 侧栏出现 "Cite this repository" 按钮 (#58)
- 27 个 `services/collation/` 算法层单元测试（normalize / split_sentences / compute_char_diff 等）(#60)
- nginx CSP 与一组安全响应头（X-Frame-Options / Referrer-Policy / Permissions-Policy / COOP）(#62)

### Changed
- 前端依赖大版本升级 + `npm audit fix`：清掉 12 个 high-severity CVE（axios SSRF、react-router XSS、minimatch ReDoS、rollup 任意写入、follow-redirects header leak 等）；`@typescript-eslint` 6 → 8 (#50)
- 后端依赖升级：fastapi 0.104 → ≥0.117（含 starlette CVE）、lxml 6.1、markdown 3.8.1、python-dotenv 1.2.2、pytest 8.4；pydantic → 2.9 修 OpenAPI `$ref` 序列化 (#51)
- backend ruff 85 错全部清零并把 CI 改为 gating（之前 `|| true` advisory）；新增 `[tool.ruff]` 配置，pin `ruff==0.15.12` (#57)
- Dockerfiles 与 docker-compose 默认走上游镜像源；中国大陆镜像改为 `--build-arg` / 环境变量可选 (#61)
- 仓库 topics 配齐 12 个 + homepage URL 设置

### Fixed
- `services/punctuation_analysis/constants.py` curly-quote 字典：源码丢失 U+201C/201D/2018/2019 字符，被压成 ASCII 形成 dup keys，弯引号识别一直是死代码 — 恢复正确 codepoint (#57)
- `services/collation/text_normalizer.py` 把正则元字符 `\s` 字面塞进 `set()`，等于把 `\` 与 `s` 也算成标点 — 移除 (#57)
- `services/collation/sentence_aligner.py` 多段字符串里非 raw 段含 `\s`，正则失效 — 改为 raw (#57)
- `multi_collation/variant_table.py` bare `except:` 收紧到 `(IndexError, ValueError)` (#57)
- JWT `datetime.utcnow()` (naive) → `datetime.now(timezone.utc)` (aware)；非 UTC 服务器上 token 过期时间会偏差一个本地时区偏移 (#59)

### Security
- 见上面 #50 / #51 / #62。剩余 1 条 dev-only Vite/esbuild moderate alert（需 vite 5→8 大版本）已记入 follow-up。

### 待办 / Planned (未来 PR)
- vite 5 → 8 大版本（清最后一条 dev-only alert）
- pytest 9 升级（先验 pytest-asyncio matrix）
- `services/punctuation_analysis/` 与 `services/text_compare.py` 测试覆盖
- 前端 `: any` / `@ts-ignore` 类型债清理（约 76 处，按文件拆 PR）
- 拆分 3000-行 `MultiCollation.tsx` / 1146-行 `cbeta_service.py`
- 226KB 数据型 `variant_data/variant_groups_unified.py` 改 JSON 懒加载
- backend in-process state 迁出 Redis，解锁 uvicorn `--workers > 1`

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

[Unreleased]: https://github.com/xr843/Buddhist-Text-Collation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xr843/Buddhist-Text-Collation/releases/tag/v0.1.0
