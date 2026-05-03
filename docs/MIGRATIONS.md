# Database Migrations / 数据库迁移

后端使用 [Alembic](https://alembic.sqlalchemy.org/) 管理 schema 演化。
The backend uses Alembic for schema migrations.

## 首次部署 / Fresh deployment

```bash
cd backend
alembic upgrade head
```

会自动创建所有表（基线 migration `0001_baseline` 调用 `Base.metadata.create_all`）。
Creates all tables from the baseline revision.

## 已有部署（v0.1.0 之前 `create_all` 起来的）/ Existing deployment

> v0.1.0 之前，开发环境通过 `Base.metadata.create_all` 直接建表，没有
> migration 历史。引入 Alembic 后，这些已有 schema 的部署需要打一次 stamp，
> 告诉 Alembic"baseline 已应用"，避免重复建表报错。

```bash
cd backend
alembic stamp 0001_baseline
```

之后所有新 migration 都按正常流程 `alembic upgrade head`。

## 新增 schema 改动 / Adding a new migration

```bash
cd backend
# 改完 app/models/*.py 之后：
alembic revision --autogenerate -m "短描述"
# 检查 alembic/versions/<新文件>.py，必要时手改
alembic upgrade head
```

**务必** 检查 autogenerate 输出 —— 它对枚举改名、约束重排、JSONB 默认值
等场景判断不准。提交前在本地完整 `upgrade` + `downgrade` 跑一遍。

## CI

`alembic upgrade head` 在 CI 的 `migration-smoke` job 里跑，对一个临时
postgres 容器验证基线 + 后续所有 migration 都能干净 apply。

## 配置 / Configuration

`alembic/env.py` 直接从 `app.core.config.settings.DATABASE_URL` 读连接串，
**不**写到 `alembic.ini` 里——避免凭据泄露到仓库。
asyncpg URL 会自动转成 psycopg2 给 Alembic（runner 是同步的）。
