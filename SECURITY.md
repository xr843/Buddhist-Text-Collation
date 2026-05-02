# 安全策略 / Security Policy

## 报告漏洞 / Reporting a Vulnerability

如果你发现了安全漏洞，**请勿**在公开 Issues 中讨论。

If you discover a security vulnerability, **please do not** open a public issue.

请通过以下方式私下联系维护者 / Please report privately via:

- GitHub 私信 / GitHub Security Advisories（推荐 / preferred）：
  仓库主页 → **Security** → **Report a vulnerability**
- 邮件 / Email: xianren843@protonmail.com

我们会在 **3 个工作日内**回复，并在确认后协调披露窗口。

We aim to respond within **3 business days** and will coordinate a disclosure
timeline upon confirmation.

## 支持的版本 / Supported Versions

仅 `main` 分支接受安全补丁。Only the `main` branch receives security patches.

## 部署侧硬性要求 / Deployment Requirements

部署到公网前**必须**完成：

Before deploying to a public network, you **must**:

1. 用强随机值覆盖 `SECRET_KEY` / `UMAMI_APP_SECRET` / `UMAMI_DB_PASSWORD`
   （`python -c "import secrets; print(secrets.token_urlsafe(48))"`）
2. 设置 `DEBUG=false`、`ENV=production`
3. 显式列出 `BACKEND_CORS_ORIGINS` 和 `ALLOWED_HOSTS`，**不要**使用 `*`
4. 在反向代理（nginx/Caddy）层启用 HTTPS、HSTS、合理的 rate limit
5. 数据库账号最小权限；不暴露 5432/6379 公网端口
6. 定期更新依赖（`pip-audit`、`npm audit`）

## 已知限制 / Known Limitations

当前版本未实现以下能力，自部署者需自行评估风险：

- OCR / 部分导入导出接口尚未做完整 RBAC 校验
- JWT 仅 access/refresh，未做 server 端撤销黑名单
- 登录/注册无失败次数锁定

The above are tracked on the roadmap; contributions welcome.
