# 参与贡献 / Contributing

感谢你对本项目感兴趣！本项目是面向佛典数字人文研究的开放平台，欢迎研究者、开发者和爱好者一同完善。

> *English version below.*

## 中文

### 提问 / 报告问题
- 在 [Issues](../../issues) 提交 bug 或功能建议前，请先搜索是否已有相关讨论。
- bug 报告请尽量包含：复现步骤、期望行为、实际行为、运行环境、相关日志/截图。

### 提交 Pull Request
1. Fork 本仓库并基于 `main` 创建特性分支：`git checkout -b feat/your-topic`
2. 保持改动聚焦于单一主题；大功能建议先开 Issue 讨论方案。
3. 遵循现有代码风格（后端 Ruff/Black、前端 ESLint/Prettier）。
4. commit message 建议使用 [Conventional Commits](https://www.conventionalcommits.org/)：
   `feat: ...` / `fix: ...` / `docs: ...` / `refactor: ...`
5. 推送后开 PR，描述清楚改动动机、影响范围、自测情况。
6. CI 通过且至少一位 maintainer review 后合并。

> 💡 **快捷脚本**：仓库根目录运行 `./scripts/dev/newpr.sh <branch-name> "PR title"`
> 自动完成"建分支 → commit → push → 开 PR"全流程，避免直推 main。

### 开发环境
见 [docs/WSL_SETUP.md](docs/WSL_SETUP.md) 与 [README.md](README.md#快速开始)。

### 数据 / 版权
- 本项目**不分发**带版权的现代点校本（如佛光版、中华版等）。
- CBETA、DILA 等公开资料请按其原协议使用并保留致谢。
- 提交 PR 时，请确认你引入的样本数据可在本项目协议（AGPL-3.0）下分发。

### 行为准则
请阅读 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

---

## English

### Reporting Issues
Search existing [issues](../../issues) first. Bug reports should include reproduction steps,
expected vs. actual behavior, environment details, and logs/screenshots if relevant.

### Pull Requests
1. Fork and branch from `main`: `git checkout -b feat/your-topic`
2. Keep PRs focused; discuss large changes in an issue first.
3. Match existing style (Ruff/Black for backend, ESLint/Prettier for frontend).
4. Use [Conventional Commits](https://www.conventionalcommits.org/).
5. Open a PR with motivation, scope, and self-test notes.
6. CI must pass and at least one maintainer must review before merge.

> 💡 **Helper**: From the repo root run `./scripts/dev/newpr.sh <branch-name> "PR title"`
> to do the whole "branch → commit → push → open PR" dance in one command.

### Data & Copyright
This repo does **not** redistribute copyrighted modern punctuated editions
(e.g. Foguang, Zhonghua). Use CBETA / DILA assets under their respective licenses.
Sample data added via PR must be redistributable under AGPL-3.0.

### Code of Conduct
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
