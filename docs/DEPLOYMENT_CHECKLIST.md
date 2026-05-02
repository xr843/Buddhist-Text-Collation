# 部署检查清单 - V2.4

## ✅ 后端部署检查

### 1. 依赖安装
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**关键依赖**：
- ✅ redis>=5.0.0（异步缓存）
- ✅ lxml==5.1.0（TEI XML解析）
- ✅ python-docx==1.1.0（Word导出）
- ✅ httpx==0.25.2（CBETA数据获取）
- ✅ sqlalchemy==2.0.23（数据库ORM）

### 2. 数据库初始化
```bash
# SQLite数据库会自动创建在 data/local_storage.db
# 确保data目录存在且有写权限
mkdir -p data
chmod 755 data
```

### 3. 环境变量检查
检查 `.env` 文件包含以下配置：
```bash
# 基本配置
APP_NAME="佛典标点与校勘研究平台"
APP_VERSION="2.4"
ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8001

# 数据库（SQLite本地存储）
DATABASE_URL=sqlite:///./data/local_storage.db

# Redis（可选，支持降级）
REDIS_HOST=localhost
REDIS_PORT=6379

# API密钥
OPENAI_API_KEY=your_key_here
```

### 4. 启动服务
```bash
./start_backend.sh
```

**验证启动成功**：
- ✅ 访问 http://localhost:8001/health
- ✅ 访问 http://localhost:8001/docs（API文档）
- ✅ 检查日志无ERROR

### 5. API端点验证
```bash
# 运行测试脚本
python3 test_api_endpoints.py
```

**预期结果**：
- ✅ CBETA API（3个端点）
- ✅ 导出API（2个端点）
- ✅ 对勘API（正常）

---

## ✅ 前端部署检查

### 1. 依赖安装
```bash
cd frontend
npm install
```

**关键依赖**：
- ✅ react@18+
- ✅ antd@5+
- ✅ echarts-for-react（图表可视化）
- ✅ react-router-dom（路由）

### 2. 配置检查
检查 `vite.config.ts` 的代理配置：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true
    }
  }
}
```

### 3. 启动开发服务器
```bash
npm run dev
```

**验证启动成功**：
- ✅ 访问 http://localhost:5173
- ✅ 左侧菜单显示"CBETA导入"
- ✅ 控制台无ERROR

### 4. 功能测试

#### 4.1 CBETA导入测试
1. 点击左侧菜单"CBETA导入"
2. 搜索框输入"金刚经"
3. 点击搜索
4. 查看结果列表
5. 点击"导入"按钮
6. 验证Modal弹窗（底本/校本选择）

#### 4.2 地理分布图测试
1. 进入"多版本对勘"
2. 上传底本和校本
3. 点击"分析谱系"
4. 切换到"地理分布图"Tab
5. 验证中国地图显示
6. 鼠标悬停查看版本信息

#### 4.3 导出功能测试
1. 完成一次对勘
2. 点击"导出"按钮
3. 选择Word格式
4. 验证文件下载
5. 用Word打开检查格式

---

## ✅ Docker部署（推荐）

### 1. 构建镜像
```bash
# 后端
cd backend
docker build -t buddhist-collation-backend:2.4 .

# 前端
cd frontend
docker build -t buddhist-collation-frontend:2.4 .
```

### 2. Docker Compose启动
```bash
docker-compose up -d
```

**服务端口**：
- 后端：http://localhost:8000
- 前端：http://localhost:3000

### 3. 检查容器状态
```bash
docker-compose ps
docker-compose logs backend
docker-compose logs frontend
```

---

## 🔧 常见问题排查

### 问题1：后端启动失败 - `metadata` 保留字错误
**症状**：
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved
```

**解决方案**：
已修复，`app/models/task.py` 中 `metadata` 已改为 `task_metadata`

---

### 问题2：缺少依赖模块
**症状**：
```
ModuleNotFoundError: No module named 'redis'
ModuleNotFoundError: No module named 'lxml'
```

**解决方案**：
```bash
cd backend
source venv/bin/activate
pip install redis lxml httpx python-docx
```

---

### 问题3：CBETA导入时网络错误
**症状**：
```
Failed to fetch CBETA XML: Connection timeout
```

**原因**：
- 需要访问GitHub CBETA仓库
- 可能被GFW阻断

**解决方案**：
1. 配置代理：
```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

2. 或使用CBETA本地镜像（待实现）

---

### 问题4：前端路由404
**症状**：
访问 `/cbeta-import` 显示404

**检查项**：
1. 确认 `App.tsx` 已添加路由
2. 确认 `MainLayout.tsx` 菜单项已添加
3. 清除浏览器缓存
4. 重新启动前端服务

---

### 问题5：地理分布图空白
**症状**：
谱系分析页面地理分布图Tab为空

**可能原因**：
1. 版本名称不在 `canon_locations.py` 中
2. 缺少地理坐标数据

**检查**：
```python
# 查看支持的版本
from app.services.canon_locations import CANON_LOCATIONS
print(CANON_LOCATIONS.keys())
```

---

### 问题6：Word导出中文乱码
**症状**：
导出的Word文档中文显示为方框

**解决方案**：
1. 确认系统已安装宋体（SimSun）
2. Windows默认已安装
3. Linux需安装：
```bash
sudo apt-get install fonts-wqy-zenhei
```

---

## 📊 性能优化建议

### 1. Redis缓存（推荐）
安装Redis提升性能：
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

### 2. 数据库索引
SQLite数据库会自动创建必要索引，无需手动优化

### 3. 静态资源CDN
生产环境可将前端静态资源部署到CDN

---

## 🔒 安全检查

### 1. API密钥保护
确保 `.env` 文件不被提交到Git：
```bash
# .gitignore应包含
.env
*.env
```

### 2. CORS配置
生产环境需限制CORS来源：
```python
# backend/app/core/config.py
BACKEND_CORS_ORIGINS = [
    "https://your-domain.com"
]
```

### 3. 速率限制
已启用速率限制（60请求/分钟），可根据需要调整

---

## 📝 部署完成验证清单

勾选以下项目确认部署成功：

**后端**：
- [ ] 依赖安装完成（redis, lxml, httpx, python-docx）
- [ ] 数据库初始化（SQLite文件已创建）
- [ ] 环境变量配置正确
- [ ] 服务启动成功（http://localhost:8001）
- [ ] API文档可访问（/docs）
- [ ] 健康检查通过（/health）
- [ ] 48个API端点全部注册

**前端**：
- [ ] 依赖安装完成
- [ ] 开发服务器启动（http://localhost:5173）
- [ ] 主页加载正常
- [ ] 左侧菜单显示"CBETA导入"
- [ ] 控制台无ERROR

**功能验证**：
- [ ] CBETA搜索功能正常
- [ ] 地理分布图显示正常
- [ ] Word导出功能正常
- [ ] TEI XML导出功能正常

**Docker部署（可选）**：
- [ ] 后端镜像构建成功
- [ ] 前端镜像构建成功
- [ ] docker-compose启动成功
- [ ] 容器健康检查通过

---

## 🚀 生产环境部署建议

### 1. 反向代理（Nginx）
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
    }

    # 后端API
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 进程管理（Supervisor/Systemd）
```ini
# /etc/supervisor/conf.d/buddhist-collation.conf
[program:backend]
directory=/path/to/backend
command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
autostart=true
autorestart=true
```

### 3. 日志管理
- 使用loguru配置日志轮转
- 集成ELK/Grafana监控

### 4. 备份策略
- 定期备份PostgreSQL/SQLite数据库
- 备份用户上传的项目数据

---

**部署完成！** 🎉

如有问题，请查看：
- 完整文档：`README.md`
- 开发总结：`DEVELOPMENT_SUMMARY_V2.4.md`
- 快速上手：`QUICK_START_V2.4.md`
