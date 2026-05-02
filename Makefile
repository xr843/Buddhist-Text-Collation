.PHONY: help install start stop clean test backend frontend db-start db-stop redis-start redis-stop

# 默认目标
.DEFAULT_GOAL := help

# 帮助信息
help:
	@echo "佛典智能标点与校勘研究平台 - 开发命令"
	@echo ""
	@echo "使用方法: make [命令]"
	@echo ""
	@echo "常用命令:"
	@echo "  make install       - 安装所有依赖（前端+后端）"
	@echo "  make start         - 启动开发环境（PostgreSQL + Redis + 后端 + 前端）"
	@echo "  make stop          - 停止所有服务"
	@echo "  make clean         - 清理临时文件和缓存"
	@echo ""
	@echo "后端命令:"
	@echo "  make backend       - 只启动后端服务"
	@echo "  make backend-test  - 运行后端测试"
	@echo "  make backend-lint  - 后端代码检查"
	@echo ""
	@echo "前端命令:"
	@echo "  make frontend      - 只启动前端服务"
	@echo "  make frontend-build- 构建前端生产版本"
	@echo "  make frontend-lint - 前端代码检查"
	@echo ""
	@echo "数据库命令:"
	@echo "  make db-start      - 启动PostgreSQL"
	@echo "  make db-stop       - 停止PostgreSQL"
	@echo "  make db-init       - 初始化数据库"
	@echo "  make db-reset      - 重置数据库（危险）"
	@echo ""
	@echo "Redis命令:"
	@echo "  make redis-start   - 启动Redis"
	@echo "  make redis-stop    - 停止Redis"
	@echo ""

# 安装所有依赖
install: backend-install frontend-install
	@echo "✅ 所有依赖安装完成"

# 后端依赖安装
backend-install:
	@echo "📦 安装后端依赖..."
	cd backend && python3.11 -m venv venv || true
	cd backend && source venv/bin/activate && pip install --upgrade pip
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	@echo "✓ 后端依赖安装完成"

# 前端依赖安装
frontend-install:
	@echo "📦 安装前端依赖..."
	cd frontend && npm install
	@echo "✓ 前端依赖安装完成"

# 启动所有服务
start:
	@echo "🚀 启动开发环境..."
	./start-dev.sh

# 停止所有服务
stop:
	@echo "🛑 停止所有服务..."
	./stop-dev.sh

# 启动数据库
db-start:
	@echo "📦 启动PostgreSQL..."
	sudo service postgresql start
	@echo "✓ PostgreSQL启动完成"

# 停止数据库
db-stop:
	@echo "🛑 停止PostgreSQL..."
	sudo service postgresql stop
	@echo "✓ PostgreSQL已停止"

# 初始化数据库
db-init:
	@echo "🔧 初始化数据库..."
	psql -U buddhist_user -d buddhist_text -h localhost -W < database/init.sql
	@echo "✓ 数据库初始化完成"

# 重置数据库（危险操作）
db-reset:
	@echo "⚠️  警告：此操作将删除所有数据！"
	@read -p "确认重置数据库? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		sudo -u postgres psql -c "DROP DATABASE IF EXISTS buddhist_text;"; \
		sudo -u postgres psql -c "CREATE DATABASE buddhist_text OWNER buddhist_user;"; \
		psql -U buddhist_user -d buddhist_text -h localhost < database/init.sql; \
		echo "\n✓ 数据库已重置"; \
	else \
		echo "\n取消重置"; \
	fi

# 启动Redis
redis-start:
	@echo "📦 启动Redis..."
	sudo service redis-server start
	@echo "✓ Redis启动完成"

# 停止Redis
redis-stop:
	@echo "🛑 停止Redis..."
	sudo service redis-server stop
	@echo "✓ Redis已停止"

# 只启动后端
backend:
	@echo "🔧 启动后端服务..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 后端测试
backend-test:
	@echo "🧪 运行后端测试..."
	cd backend && source venv/bin/activate && pytest -v

# 后端代码检查
backend-lint:
	@echo "🔍 后端代码检查..."
	cd backend && source venv/bin/activate && flake8 app/
	cd backend && source venv/bin/activate && black --check app/

# 只启动前端
frontend:
	@echo "🎨 启动前端服务..."
	cd frontend && npm run dev

# 前端构建
frontend-build:
	@echo "📦 构建前端..."
	cd frontend && npm run build
	@echo "✓ 前端构建完成"

# 前端代码检查
frontend-lint:
	@echo "🔍 前端代码检查..."
	cd frontend && npm run lint

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/uploads/* 2>/dev/null || true
	rm -rf backend/exports/* 2>/dev/null || true
	rm -rf backend/logs/* 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	@echo "✓ 清理完成"

# 查看日志
logs-backend:
	@echo "📋 后端日志..."
	tail -f backend/logs/app.log

# 查看所有运行的进程
ps:
	@echo "📊 运行中的服务:"
	@echo ""
	@echo "后端进程:"
	@pgrep -af "uvicorn app.main:app" || echo "  未运行"
	@echo ""
	@echo "前端进程:"
	@pgrep -af "vite" || echo "  未运行"
	@echo ""
	@echo "PostgreSQL:"
	@sudo service postgresql status 2>/dev/null | head -n 1 || echo "  未运行"
	@echo ""
	@echo "Redis:"
	@sudo service redis-server status 2>/dev/null | head -n 1 || echo "  未运行"
