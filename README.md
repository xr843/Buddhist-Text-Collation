# 佛典标点与校勘研究平台 / Buddhist Text Collation Platform

[![CI](https://github.com/xr843/buddhist-text-collation/actions/workflows/ci.yml/badge.svg)](https://github.com/xr843/buddhist-text-collation/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![CBETA](https://img.shields.io/badge/CBETA-integrated-green.svg)](#致谢--acknowledgements)
[![DILA](https://img.shields.io/badge/DILA-integrated-green.svg)](#致谢--acknowledgements)

> **一句话** · 把佛经古籍的"标点对比、多版本对勘、注疏对读、版本谱系"统一进同一个研究工作台。
>
> **One line** · A unified research workbench for punctuation diff, multi-edition collation, commentary cross-reading, and version-lineage analysis of Buddhist canonical texts.

📖 详细中文文档 / Full Chinese docs: **[docs/README.zh-CN.md](docs/README.zh-CN.md)** · 🛡️ 安全 / Security: **[SECURITY.md](SECURITY.md)** · 🤝 参与 / Contribute: **[CONTRIBUTING.md](CONTRIBUTING.md)** · 📝 更新日志 / Changelog: **[CHANGELOG.md](CHANGELOG.md)**

---

> 💡 **当前版本说明** / Note on v0.1.0
>
> 本开源版**未集成第三方付费 OCR**（如 gj.cool）。如需图片→文字流程，请用任意外部 OCR 工具识别后，再把文本导入本平台校勘流程。
>
> The OCR digitization workbench from the internal version is **not** bundled.
> Use any external OCR tool and import recognized text into the collation flow.

---

## 这是什么 / What is this?

中文：本平台帮助研究者在同一个工作台中完成佛经古籍的 **标点对比、多版本对勘、注疏对读、版本谱系分析**。底层集成 CBETA、DILA 等公开学术资源，前端提供"禅意/学术 UI"以适配长时间校勘工作。

English: A research workbench that unifies **punctuation diff,
multi-edition collation, commentary cross-reading, and version-lineage
analysis** for Buddhist canonical texts. It integrates open scholarly resources
(CBETA, DILA) and ships with a focused reading UI suited to long collation
sessions.

## 核心能力 / Key Features

| 模块 / Module | 功能 / Capability |
| --- | --- |
| 标点对比 | 单文件多版本对照、差异高亮、可逐句判取 |
| 两版本对勘 | 行级 / 字级差异、异体字识别、判定流转 |
| 多版本对勘 | 31 个版本同屏对勘，自动生成校勘记 |
| 注疏对读 | 经论与注疏并排、跨文本引证 |
| 版本谱系 | 异文聚类、谱系图（Lineage Graph）生成 |
| 协作 | 项目/成员/角色、批注、协作锁 |
| 导出 | TXT / DOCX / 校勘记 CSV / 全量对照表 |

详细模块说明见 [docs/README.zh-CN.md](docs/README.zh-CN.md)。

## 技术栈 / Tech Stack

- **Backend**: Python 3.11 · FastAPI · SQLAlchemy (async) · PostgreSQL · Redis · Celery
- **Frontend**: React 18 · TypeScript · Vite · Zustand · Tailwind
- **Infra**: Docker Compose · nginx · Umami（可选 / optional）

架构详情 / Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 快速开始 / Quick Start

### 1. 准备环境 / Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ 与 Redis 7+（开发期可用 Docker 起）

### 2. 克隆 & 配置 / Clone & configure

```bash
git clone https://github.com/<your-org>/buddhist-text-platform.git
cd buddhist-text-platform

# 复制环境变量模板
cp .env.example .env
cp backend/.env.example backend/.env

# 生成 SECRET_KEY 等强随机值
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# 把输出填入 backend/.env 的 SECRET_KEY
```

### 3. 安装依赖 / Install

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. 启动 / Run

```bash
# 仓库根目录
./start_backend.sh    # http://localhost:8001 (默认 8001 避开 Docker 8000)
./start_frontend.sh   # http://localhost:5173
```

### Docker 部署 / Docker deployment

```bash
docker-compose up -d --build
```

详见 [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) 与
[docs/WSL_SETUP.md](docs/WSL_SETUP.md)。

## 数据资源 / Data Resources

本仓库**不分发**带版权的现代点校本（佛光版、中华版等）。
This repo does **not** redistribute copyrighted modern punctuated editions.

可使用的公开资源：

- [CBETA 中華電子佛典](https://www.cbeta.org/) — 按其使用条款引用并致谢
- [DILA 法鼓文理學院](https://www.dila.edu.tw/) — 按 CC-BY-NC-SA 等协议
- 用户自有的校勘成果

异体字、对勘等大型派生数据通过 GitHub Releases 下发（不入仓）。

## 文档 / Documentation

- 中文完整文档 / Full Chinese docs · [docs/README.zh-CN.md](docs/README.zh-CN.md)
- 架构设计 / Architecture · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 部署清单 / Deployment · [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)
- WSL 环境 · [docs/WSL_SETUP.md](docs/WSL_SETUP.md)
- 安全策略 / Security · [SECURITY.md](SECURITY.md)
- 参与贡献 / Contributing · [CONTRIBUTING.md](CONTRIBUTING.md)

## 安全 / Security

部署到公网前请阅读 [SECURITY.md](SECURITY.md) 中的"部署侧硬性要求"。
Before public deployment, read the **Deployment Requirements** in
[SECURITY.md](SECURITY.md).

漏洞披露请通过 GitHub Security Advisories 私下提交，**不要**开 public issue。
Please report vulnerabilities privately via GitHub Security Advisories.

## 致谢 / Acknowledgements

本平台站在以下学术开源项目的肩膀上 / This project stands on the shoulders of:

- [CBETA 中華電子佛典協會](https://www.cbeta.org/)
- [DILA 法鼓文理學院 數位典藏](https://www.dila.edu.tw/)
- [異體字字典 / Unihan / IDS](https://www.unicode.org/charts/unihan.html)
- 以及所有为佛典数字化默默付出的研究者与志愿者。

## License

[GNU Affero General Public License v3.0](LICENSE) — 详见 LICENSE 文件。

> 选择 AGPL 是为了确保平台的衍生改动也能回馈给社区，符合佛典数字资源
> "公益、共享、不闭源"的精神。
> AGPL was chosen so that derivative works — including network-deployed
> services — remain open, in keeping with the open-knowledge ethos of
> Buddhist textual scholarship.
