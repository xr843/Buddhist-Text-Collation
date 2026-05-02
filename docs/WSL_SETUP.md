# WSL本地开发环境配置指南

本指南专门针对在WSL (Ubuntu)环境中进行本地开发的配置。

## 📋 环境要求

- WSL 2 (Ubuntu 20.04/22.04)
- VSCode with Remote-WSL extension
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

## 🔧 第一步：安装系统依赖

### 1.1 更新系统包

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 安装Python 3.11

```bash
# 添加deadsnakes PPA
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装Python 3.11及相关包
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# 安装pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# 验证安装
python3.11 --version
```

### 1.3 安装PostgreSQL 15

```bash
# 添加PostgreSQL官方仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# 安装PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15 -y

# 启动PostgreSQL服务
sudo service postgresql start

# 设置开机自启（可选）
# sudo systemctl enable postgresql
```

### 1.4 安装Redis

```bash
sudo apt install redis-server -y

# 启动Redis服务
sudo service redis-server start

# 验证安装
redis-cli ping  # 应该返回 PONG
```

### 1.5 安装Node.js 20

```bash
# 安装nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# 重新加载shell配置
source ~/.bashrc

# 安装Node.js 20
nvm install 20
nvm use 20
nvm alias default 20

# 验证安装
node --version  # 应该显示 v20.x.x
npm --version
```

### 1.6 安装其他开发工具

```bash
# 安装构建工具
sudo apt install build-essential libpq-dev -y

# 安装git（如果还没有）
sudo apt install git -y
```

## 🗄️ 第二步：配置PostgreSQL

### 2.1 创建数据库用户和数据库

```bash
# 切换到postgres用户
sudo -u postgres psql

# 在PostgreSQL命令行中执行：
CREATE USER buddhist_user WITH PASSWORD 'your_password_here';
CREATE DATABASE buddhist_text OWNER buddhist_user;
GRANT ALL PRIVILEGES ON DATABASE buddhist_text TO buddhist_user;

# 退出PostgreSQL
\q
```

### 2.2 配置PostgreSQL允许本地连接（可选）

```bash
# 编辑pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# 找到以下行：
# local   all             all                                     peer

# 修改为：
# local   all             all                                     md5

# 保存并重启PostgreSQL
sudo service postgresql restart
```

### 2.3 测试连接

```bash
psql -U buddhist_user -d buddhist_text -h localhost -W
# 输入密码后应该能成功连接
```

## 🔴 第三步：配置Redis

Redis默认配置即可使用，如需修改：

```bash
# 编辑Redis配置
sudo nano /etc/redis/redis.conf

# 建议配置：
# bind 127.0.0.1
# protected-mode yes
# requirepass your_redis_password  # 可选：设置密码

# 重启Redis
sudo service redis-server restart
```

## 🚀 第四步：配置后端

### 4.1 进入项目目录

```bash
cd ~/projects/"AI-Powered Platform for Buddhist Text Punctuation and Collation Research"
```

### 4.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

修改以下配置：

```env
# 数据库配置（使用你刚才创建的用户和密码）
DATABASE_URL="postgresql+asyncpg://buddhist_user:your_password_here@localhost:5432/buddhist_text"

# Redis配置
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"

# AI配置（必须配置）
OPENAI_API_KEY="your-api-key-here"
OPENAI_API_BASE="https://api.openai.com/v1"

# 安全密钥（生成一个随机密钥）
SECRET_KEY="请运行：openssl rand -hex 32 生成"

# 开发模式
DEBUG=true
```

生成安全密钥：
```bash
openssl rand -hex 32
```

### 4.3 创建Python虚拟环境

```bash
cd backend

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 4.4 安装Python依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 如果遇到编译错误，可能需要安装额外的系统包：
# sudo apt install python3.11-dev libpq-dev build-essential
```

### 4.5 初始化数据库

```bash
# 确保在backend目录，且虚拟环境已激活

# 方法1：使用init.sql初始化
cd ..
psql -U buddhist_user -d buddhist_text -h localhost -W < database/init.sql

# 方法2：如果使用Alembic迁移（后续配置）
# cd backend
# alembic upgrade head
```

### 4.6 启动后端服务

```bash
cd backend
source venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 运行

访问 http://localhost:8000/docs 查看API文档

## 🎨 第五步：配置前端

打开新的终端（或VSCode新终端）：

### 5.1 进入前端目录

```bash
cd ~/projects/"AI-Powered Platform for Buddhist Text Punctuation and Collation Research"/frontend
```

### 5.2 安装依赖

```bash
npm install

# 如果npm速度慢，可以使用国内镜像：
# npm config set registry https://registry.npmmirror.com
# npm install
```

### 5.3 启动开发服务器

```bash
npm run dev
```

前端服务将在 http://localhost:3000 运行（或显示的其他端口）

## 💻 第六步：VSCode配置

### 6.1 安装必要的VSCode扩展

在WSL中的VSCode中安装以下扩展：

**必需扩展：**
- WSL (Microsoft)
- Python (Microsoft)
- Pylance (Microsoft)
- ES7+ React/Redux/React-Native snippets
- ESLint
- Prettier - Code formatter

**推荐扩展：**
- GitLens
- Thunder Client (API测试)
- Database Client (数据库管理)
- Auto Close Tag
- Auto Rename Tag

### 6.2 创建VSCode工作区配置

在项目根目录创建 `.vscode` 文件夹：

```bash
mkdir -p .vscode
```

我会为你创建配置文件。

### 6.3 打开项目

在WSL中打开VSCode：

```bash
cd ~/projects/"AI-Powered Platform for Buddhist Text Punctuation and Collation Research"
code .
```

## ✅ 第七步：验证安装

### 7.1 测试后端

在浏览器中访问：
- http://localhost:8000 - 应该看到API信息
- http://localhost:8000/health - 应该返回健康状态
- http://localhost:8000/docs - 应该看到Swagger API文档

### 7.2 测试前端

访问 http://localhost:3000，应该能看到：
- 平台主界面
- 顶部标题栏
- 侧边菜单
- 智能标点功能页面

### 7.3 测试数据库连接

```bash
# 在后端虚拟环境中测试
cd backend
source venv/bin/activate
python3 -c "
from app.core.database import engine
import asyncio

async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT version()')
        print('Database connected:', result.fetchone())

asyncio.run(test())
"
```

## 🔄 日常开发工作流

### 启动开发环境

创建启动脚本 `dev.sh`：

```bash
#!/bin/bash

# 启动PostgreSQL和Redis
sudo service postgresql start
sudo service redis-server start

# 在新终端启动后端
gnome-terminal --tab --title="Backend" -- bash -c "cd ~/projects/'AI-Powered Platform for Buddhist Text Punctuation and Collation Research'/backend && source venv/bin/activate && uvicorn app.main:app --reload; exec bash"

# 在新终端启动前端
gnome-terminal --tab --title="Frontend" -- bash -c "cd ~/projects/'AI-Powered Platform for Buddhist Text Punctuation and Collation Research'/frontend && npm run dev; exec bash"

echo "✅ 开发环境启动完成！"
echo "后端: http://localhost:8000"
echo "前端: http://localhost:3000"
```

赋予执行权限：
```bash
chmod +x dev.sh
```

### 在VSCode中集成终端

使用VSCode的集成终端（Ctrl + `）分别启动：

**终端1（后端）：**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**终端2（前端）：**
```bash
cd frontend
npm run dev
```

## 🐛 常见问题

### 问题1：PostgreSQL启动失败

```bash
# 检查状态
sudo service postgresql status

# 查看日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# 重启服务
sudo service postgresql restart
```

### 问题2：端口被占用

```bash
# 查看端口占用
sudo lsof -i :8000  # 后端端口
sudo lsof -i :3000  # 前端端口
sudo lsof -i :5432  # PostgreSQL端口
sudo lsof -i :6379  # Redis端口

# 杀死进程
sudo kill -9 <PID>
```

### 问题3：WSL中访问Windows文件系统慢

建议项目放在WSL文件系统中（`~/projects/`），而不是 `/mnt/c/`

### 问题4：数据库编码问题

```bash
# 重新创建数据库并指定编码
sudo -u postgres psql
DROP DATABASE buddhist_text;
CREATE DATABASE buddhist_text
    OWNER buddhist_user
    ENCODING 'UTF8'
    LC_COLLATE 'zh_CN.UTF-8'
    LC_CTYPE 'zh_CN.UTF-8'
    TEMPLATE template0;
```

### 问题5：Python包安装失败

```bash
# 确保安装了必要的系统包
sudo apt install python3.11-dev libpq-dev build-essential libssl-dev libffi-dev

# 清理pip缓存
pip cache purge

# 重新安装
pip install -r requirements.txt
```

## 📝 开发提示

### 1. 使用VSCode调试

后端调试配置会在 `.vscode/launch.json` 中提供。

### 2. 数据库管理

推荐使用以下工具：
- VSCode的 Database Client 扩展
- DBeaver (可在Windows中安装，通过localhost:5432连接WSL中的PostgreSQL)
- pgAdmin 4

### 3. API测试

- Swagger UI: http://localhost:8000/docs
- VSCode的Thunder Client扩展
- Postman

### 4. Git配置

```bash
# 配置Git（如果还没有）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

# 配置Git在WSL中的行尾符处理
git config --global core.autocrlf input
```

## 🎯 下一步

1. 阅读 [README.md](README.md) 了解项目整体架构
2. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解技术细节
3. 阅读 [佛典智能标点与校勘研究平台_PRD.md](佛典智能标点与校勘研究平台_PRD.md) 了解功能需求
4. 开始开发核心功能

## 🆘 需要帮助？

- PostgreSQL官方文档: https://www.postgresql.org/docs/
- Redis文档: https://redis.io/docs/
- FastAPI文档: https://fastapi.tiangolo.com/
- React文档: https://react.dev/

祝开发顺利！🚀
