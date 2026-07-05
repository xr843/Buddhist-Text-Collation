# Examples / 示例数据

公开样本，让你在不接入 CBETA / DILA 的情况下，
3 分钟内跑通"标点对比"和"两版本对勘"两条主路径。

Public-domain samples to let you exercise the **punctuation diff** and
**two-edition collation** flows in ~3 minutes without first wiring up
CBETA / DILA. The pipeline is text-agnostic — any classical Chinese text
works the same way as a Buddhist canonical text.

## 目录 / Layout

```
examples/
├── classical-chinese-sample/
│   ├── punctuated.txt    # 通行标点版（《论语·学而》开篇三句）
│   ├── unpunctuated.txt  # 同一文本，去标点版（用于"标点迁移"演示）
│   └── variant.txt       # 引入一处异体字差异（"说" → "悦"，用于"对勘"演示）
└── demo-project/
    ├── manifest.json
    ├── texts/            # v0.3 可复现 demo 的输入数据
    ├── expected/         # 后端服务生成的固定期望输出
    └── screenshots/      # 后续截图刷新应使用的数据源说明
```

样本取自《论语·学而》开篇——公元前 5 世纪典籍，**公有领域**，
仅作平台演示用途，与佛典无关；选它纯粹为了把"差异在哪、怎么呈现"
这件事讲清楚。真正接入 CBETA / DILA 的佛典走的是同一条管线。

Sample is from the opening of *Analects*, **public domain** (5th c. BCE),
chosen purely to demonstrate diff/collation behavior. CBETA/DILA Buddhist
texts go through the exact same pipeline.

## 怎么用 / How to use

### 推荐：v0.3 可复现 demo project

`demo-project/` 是后续公开 Demo Site、截图刷新、英文文档扩展和回归测试
共同使用的基线数据集。它包含 manifest、输入文本和已提交的 expected outputs。

从仓库根目录运行：

```bash
cd backend
.venv/bin/python -m pytest tests/services/test_demo_project_expected_outputs.py -q
```

该测试会验证 committed expected outputs 与当前后端服务行为一致。

### A. 不装环境 — 用文件直接看 / No setup — just inspect

`diff punctuated.txt variant.txt` 即可看到一处单字异文（"说" / "悦"），
这正是平台要在 UI 中高亮、自动写进校勘记的对象。

```
$ diff classical-chinese-sample/punctuated.txt classical-chinese-sample/variant.txt
1c1
< 子曰：「学而时习之，不亦说乎？...
---
> 子曰：「学而时习之，不亦悦乎？...
```

### B. 跑起平台 — 上传两个文件试 / Run the platform — upload both

按 [README.md → 快速开始](../README.md#快速开始--quick-start) 起好后端 + 前端，
打开 `http://localhost:5173`，进入"两版本对勘"，分别上传：

- 底本 / Base: `punctuated.txt`
- 校本 / Witness: `variant.txt`

应能看到 1 处差异高亮 + 自动生成的校勘记（"说"↔"悦"）。

### C. 标点迁移 / Punctuation transfer

进入"标点迁移"，分别上传：

- 已标点 / Source: `punctuated.txt`
- 待标点 / Target: `unpunctuated.txt`

应能看到标点被映射回去的预览。

## 想贡献佛典样本 / Want to contribute a Buddhist sample?

欢迎 PR。请确保：
1. 选用 **公有领域** 底本（早期汉译/藏译/巴利原文皆可），不复制任何在版权保护期内的现代点校本；
2. 单文件控制在 ~500 字以内，避免仓库膨胀；
3. 在本目录加一个子文件夹 + `README.md` 说明出处与引文规范。

PRs welcome — public-domain sources only, ≤500 chars per file, one
subfolder per sample with attribution.
