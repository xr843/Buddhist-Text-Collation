#!/bin/bash
# ===================================================
# 项目启动脚本 - 前端服务
# ===================================================

echo "============================================"
echo " 启动前端服务 (React)"
echo "============================================"
echo ""

# 可选：指定后端端口（默认 8001；如需连接 Docker 后端(8000) 可用 8000）
API_PORT=${1:-${VITE_API_PORT:-8001}}
export VITE_API_PORT="$API_PORT"

# 进入前端目录（脚本所在目录的 frontend/ 子目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/frontend"

# 检查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "[提示] 首次运行，正在安装依赖..."
    npm install
    echo ""
fi

# 启动React开发服务器
echo "启动React开发服务器 (Vite)..."
echo ""
echo "前端地址: http://localhost:5173"
echo "API代理到: http://localhost:$API_PORT"
echo ""
echo "提示: 如需连接 Docker 后端(8000)，例如:"
echo "      ./start_frontend.sh 8000"
echo "      VITE_API_PORT=8000 npm run dev"
echo ""
echo "按 Ctrl+C 停止服务"
echo "============================================"
echo ""

npm run dev
