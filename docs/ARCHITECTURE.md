# 项目架构设计

## 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **语言**: Python 3.10+
- **数据库**: PostgreSQL 15+ with JSONB
- **ORM**: SQLAlchemy 2.0+
- **异步任务**: Celery + Redis
- **文本处理**: difflib, python-Levenshtein（规则 + 编辑距离；不依赖 LLM）
- **文件处理**: python-docx, chardet

### 前端
- **框架**: React 18+ with TypeScript
- **状态管理**: Zustand / Redux Toolkit
- **UI组件**: Ant Design / Material-UI
- **富文本编辑器**: Slate.js / Quill.js
- **HTTP客户端**: Axios
- **构建工具**: Vite

### 基础设施
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **缓存**: Redis
- **文件存储**: MinIO / 本地文件系统

## 项目结构

```
buddhist-text-platform/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── v1/
│   │   │   │   ├── punctuation.py    # 标点处理 API（规则 + 编辑距离）
│   │   │   │   ├── comparison.py     # 版本对比API
│   │   │   │   ├── collation.py      # 校勘API
│   │   │   │   └── export.py         # 导出API
│   │   │   └── deps.py        # 依赖注入
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   └── security.py    # 安全配置
│   │   ├── models/            # 数据模型
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── text.py
│   │   │   └── collation.py
│   │   ├── schemas/           # Pydantic模式
│   │   ├── services/          # 业务逻辑
│   │   │   ├── ai_punctuation.py    # AI标点服务
│   │   │   ├── text_compare.py      # 文本对比服务
│   │   │   ├── collation.py         # 校勘服务
│   │   │   └── export.py            # 导出服务
│   │   ├── utils/             # 工具函数
│   │   │   ├── text_processing.py
│   │   │   ├── diff_algorithm.py
│   │   │   └── file_handler.py
│   │   └── main.py            # 应用入口
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # 测试
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # 组件
│   │   │   ├── PunctuationEditor/    # 标点编辑器
│   │   │   ├── ComparisonView/       # 对比视图
│   │   │   ├── CollationWorkbench/   # 校勘工作台
│   │   │   └── RichTextEditor/       # 富文本编辑器
│   │   ├── pages/             # 页面
│   │   │   ├── Punctuation.tsx
│   │   │   ├── Comparison.tsx
│   │   │   ├── Collation.tsx
│   │   │   └── Projects.tsx
│   │   ├── services/          # API服务
│   │   ├── hooks/             # 自定义钩子
│   │   ├── store/             # 状态管理
│   │   ├── types/             # TypeScript类型
│   │   ├── utils/             # 工具函数
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── database/                   # 数据库
│   ├── init.sql               # 初始化脚本
│   └── schemas/               # 数据库模式
│
├── docs/                       # 文档
│   ├── api/                   # API文档
│   └── deployment/            # 部署文档
│
├── docker-compose.yml          # Docker编排
├── .env.example               # 环境变量模板
└── README.md                  # 项目说明
```

## 核心模块设计

### 1. 标点处理模块
- **输入处理**: 文本预处理、编码转换、繁简归一
- **核心算法**: 规则 + 编辑距离（python-Levenshtein）
  > 注：本平台**不调用** LLM / OpenAI / Claude 等外部 AI 服务；
  > 标点比对、迁移、对勘均为本地确定性算法。
- **异步处理**: >5000 字文本走异步处理
- **结果导出**: TXT、DOCX 格式

### 2. 多版本对比模块
- **差异算法**: 基于 difflib + LCS 的标点级 / 字符级差异检测
- **可视化**: 并排视图、内联视图
- **同步滚动**: 双栏同步滚动
- **差异高亮**: 颜色编码差异

### 3. 校勘模块
- **项目管理**: 项目制工作流（底本 + 1-30 个校本）
- **差异分析**: LCS 算法字符级差异
- **异文分类**: 基于异体字词典自动归类（同 / 异 / 脱 / 衍）
- **校勘记**: 富文本编辑器、判取流转
- **报告生成**: DOCX、CSV、TEI XML、Markdown 导出

## 数据库设计

### 核心表
- `users`: 用户表
- `projects`: 校勘项目表
- `texts`: 文本版本表
- `differences`: 差异记录表（JSONB）
- `collation_notes`: 校勘记表（JSONB）
- `tasks`: 异步任务表

## API设计

### RESTful API结构
```
POST   /api/v1/punctuation/process      # 提交标点任务
GET    /api/v1/punctuation/status/{id}  # 查询任务状态
POST   /api/v1/comparison/compare       # 版本对比
POST   /api/v1/collation/projects       # 创建校勘项目
GET    /api/v1/collation/projects/{id}  # 获取项目详情
POST   /api/v1/collation/differences    # 分析差异
POST   /api/v1/export/document          # 导出文档
```

## 部署架构

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (反向代理)  │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
         ┌────▼─────┐            ┌─────▼────┐
         │ Frontend │            │ Backend  │
         │  (React) │            │(FastAPI) │
         └──────────┘            └────┬─────┘
                                      │
                           ┌──────────┼──────────┐
                           │          │          │
                      ┌────▼───┐ ┌───▼────┐ ┌──▼────┐
                      │PostGres│ │ Redis  │ │ MinIO │
                      │   QL   │ │(Cache) │ │(File) │
                      └────────┘ └────────┘ └───────┘
```

## 开发阶段

### Phase 1: 基础框架（V3.1）
1. 项目初始化和环境配置
2. 数据库设计和ORM配置
3. 基础API框架搭建
4. 前端框架搭建

### Phase 2: 核心功能（V3.1）
1. 标点处理模块（规则 + 编辑距离）
2. 文本上传和预处理
3. 结果展示和导出
4. 基础 UI 界面

### Phase 3: 对比和校勘（V3.1-V3.2）
1. 文本差异算法实现
2. 对比可视化界面
3. 校勘项目管理
4. 富文本编辑器集成

### Phase 4: 高级功能（V3.2）
1. AI辅助标注
2. 版本用字分析
3. 校勘报告生成
4. 性能优化

### Phase 5: 平台化（V4.0）
1. 多人协作
2. 知识图谱
3. 命名实体识别
4. 高级数据可视化

## 安全考虑

- JWT身份认证
- CORS配置
- SQL注入防护
- XSS防护
- 文件上传验证
- 速率限制

## 性能优化

- 数据库索引优化
- Redis缓存策略
- 异步任务处理
- 文件分片上传
- CDN静态资源加速
- WebAssembly文本处理
