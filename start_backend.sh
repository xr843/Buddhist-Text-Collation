#!/bin/bash
# ===================================================
# 项目启动脚本 - 后端服务
# ===================================================

# 端口配置（默认8001用于本地开发，Docker用8000）
PORT=${1:-8001}

echo "============================================"
echo " 启动后端服务 (FastAPI + AI服务)"
echo " 模式: 本地开发 (端口 $PORT)"
echo "============================================"
echo ""

# 进入后端目录
cd "/home/lqsxi/projects/AI-Powered Platform for Buddhist Text Punctuation and Collation Research/backend"

# 激活虚拟环境
echo "[1/2] 激活Python虚拟环境..."
source venv/bin/activate

# 启动FastAPI服务
echo ""
echo "[2/2] 启动FastAPI服务..."
echo ""
echo "服务地址: http://localhost:$PORT"
echo "API文档: http://localhost:$PORT/docs"
echo ""
echo "提示: Docker后端运行在8000端口（同事使用）"
echo "按 Ctrl+C 停止服务"
echo "============================================"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
