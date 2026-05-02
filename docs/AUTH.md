# 认证模块 / Authentication Module

> 路由前缀 / Route prefix: `/api/v1/auth`
> 源码 / Source: `backend/app/api/v1/auth/`

本平台采用 **JWT** 双令牌方案：短期 `access_token`（默认 30 分钟）+ 长期 `refresh_token`（默认 7 天）。

## 端点一览 / Endpoints

| Method | Path | 用途 | 是否需要登录 |
|---|---|---|---|
| `POST` | `/register` | 注册新用户 | ❌ |
| `POST` | `/login` | 邮箱+密码登录，返回双令牌 | ❌ |
| `POST` | `/refresh` | 用 refresh_token 换新 access_token | ❌ |
| `POST` | `/logout` | 注销（client 端清 token；server 当前无黑名单） | ✅ |
| `GET` | `/me` | 获取当前用户信息 | ✅ |
| `PUT` | `/me` | 更新姓名 / 邮箱 / 头像等 | ✅ |
| `PUT` | `/password` | 修改密码（需提供旧密码） | ✅ |

## 流程图 / Flow

```
┌──────────────┐   POST /register / /login   ┌──────────────┐
│   Client     │ ───────────────────────────▶│   Backend    │
│              │   { email, password }       │              │
│              │ ◀───────────────────────────│   FastAPI    │
│              │   { access_token (30min),   │              │
│              │     refresh_token (7d) }    │              │
└──────────────┘                             └──────────────┘
       │
       │  以后每个请求加 Header:
       │  Authorization: Bearer <access_token>
       ▼
┌──────────────────────────────────────────┐
│  当 access_token 401（过期）            │
│    POST /refresh + refresh_token        │
│    → 拿到新的 access_token，继续        │
│  当 refresh_token 也过期 → 重新 /login  │
└──────────────────────────────────────────┘
```

## 数据模型 / Schemas

参考 `backend/app/api/v1/auth/schemas.py`。关键字段：

```python
RegisterRequest:  email, password (>=6), full_name?
LoginRequest:     email, password
TokenResponse:    access_token, refresh_token, token_type="bearer"
UserResponse:     id, email, full_name, role, is_active, created_at
```

## 部署侧注意 / Deployment notes

⚠️ 公网部署前，**必须**完成（详见 [`SECURITY.md`](../SECURITY.md)）：

1. `SECRET_KEY` 用强随机值（`python -c "import secrets; print(secrets.token_urlsafe(48))"`）
2. 反向代理（nginx/Caddy）启用 HTTPS——JWT 在明文传输下可被窃听
3. 在反向代理或 FastAPI 层为 `/auth/login` 与 `/auth/register` 启用更严的 rate limit（默认是全局 60/min；登录/注册建议 5/min + 失败锁定）
4. 当前**无 server 端 token 撤销黑名单**——一旦签发，access_token 在 30 分钟内有效；refresh_token 在 7 天内有效。token 失窃只能等过期。
   未来 roadmap：JTI + Redis 黑名单，参考 [#34 / Roadmap](../ROADMAP.md)。

## 客户端用法 / Client usage

参考 `frontend/src/services/authApi.ts` 与 `frontend/src/store/authStore.ts`。

```typescript
// 登录
const { access_token, refresh_token } = await authApi.login(email, password)
localStorage.setItem('access_token', access_token)
localStorage.setItem('refresh_token', refresh_token)

// 后续请求（axios 拦截器自动加 Authorization Header）
await api.get('/multi-collation/projects')

// access 401 时，axios 拦截器自动 /refresh 重试
```

## 常见问题 / FAQ

**Q: 我能直接 `localStorage.getItem('access_token')` 吗？**
A: 可以，但请意识到 XSS 风险。当前是 client-stored token；roadmap 中考虑改成 httpOnly cookie + CSRF token 方案。

**Q: 注册需要邮箱验证吗？**
A: v0.1.0 不验证。生产部署前建议加邮箱链接确认，避免恶意批量注册。

**Q: 怎么改密码长度等校验规则？**
A: `backend/app/api/v1/auth/schemas.py` 里 `RegisterRequest.password` 的 Pydantic 验证器。

---

*相关文档 / See also: [`COLLAB.md`](COLLAB.md) · [`ADMIN.md`](ADMIN.md) · [`SECURITY.md`](../SECURITY.md)*
