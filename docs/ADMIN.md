# 管理员模块 / Admin Module

> 路由前缀 / Route prefix: `/api/v1/admin`
> 源码 / Source: `backend/app/api/v1/admin/`

**面向**：自部署平台的 sysadmin / 站长。普通研究用户不需要这块。

**权限**：所有端点都要求 `current_user.role == UserRole.ADMIN`。普通注册用户没有 admin 权限。

## 端点一览 / Endpoints

| Method | Path | 用途 |
|---|---|---|
| `GET` | `/users` | 列出所有用户（支持分页、搜索） |
| `GET` | `/users/{id}` | 用户详情 |
| `PUT` | `/users/{id}` | 改用户信息（含 `role`、`is_active`） |
| `DELETE` | `/users/{id}` | 删除用户（软删 / 硬删按实现） |
| `GET` | `/stats` | 系统统计：总用户数 / 活跃用户 / 管理员数 / 项目数等 |

## 怎么把一个用户提升为 admin / How to promote

v0.1.0 没有"创建第一个 admin"的引导流程——常规思路：

### 方案 A：直接改数据库（最直接）

```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

### 方案 B：写一个 alembic 迁移 / 脚本（更工程化）

可以放到 `backend/scripts/promote_to_admin.py`（roadmap 待加）。

### 方案 C：让首个注册用户自动是 admin

这是常见 self-host 套路，但目前未实现。如果你部署给学校 / 寺院 / 研究所自用，建议用方案 A 一次性搞定。

## 端点细节 / Endpoint Details

### `GET /users`

```
Query params:
  skip: int = 0
  limit: int = 50
  search?: str        # 模糊匹配 email / full_name
  role?: viewer|editor|admin
  is_active?: bool

Response:
  { items: [...], total: 123 }
```

### `GET /stats`

```
Response:
  {
    total_users: 234,
    active_users: 198,
    admin_users: 3,
    total_projects: 89,
    ...
  }
```

适合做后台 dashboard。

## 安全建议 / Security Notes

1. **管理员账号不要日常使用**——单独建一个 admin 账号，只在管理时切。
2. **公网部署**：在 nginx 层把 `/api/v1/admin/*` 限制到内网 IP / VPN，多一层防护。
3. **审计**：所有 admin 操作都应该走 EditHistory 记录。当前 v0.1.0 这部分**未实现**，是一个 roadmap 项。

## 客户端 / Frontend

前端 admin 页面在 `frontend/src/pages/admin/`，菜单入口默认对**非 admin** 隐藏。

---

*相关文档 / See also: [`AUTH.md`](AUTH.md) · [`COLLAB.md`](COLLAB.md) · [`SECURITY.md`](../SECURITY.md)*
