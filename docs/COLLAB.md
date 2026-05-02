# 协作模块 / Collaboration Module

> 路由前缀 / Route prefix: `/api/v1/collab`
> 源码 / Source: `backend/app/api/v1/collab/`

让多位研究者在同一个校勘项目上共同工作：项目所有权、成员邀请、角色权限、批注、编辑历史。

## 协作模型 / Model

```
User
 ├─ owns ──→ Project (visibility: private | shared | public)
 │            │
 │            ├─ shared with ──→ Member (role: viewer | editor | admin)
 │            │
 │            ├─ has ──────────→ Comment (位置定位、可回复、可编辑)
 │            │
 │            └─ tracks ───────→ EditHistory (谁、何时、改了什么)
 │
 └─ shared as Member ─→ Project (其他人的项目)
```

### 角色 / Roles

| 角色 | 能做 |
|---|---|
| **owner** | 删除项目、改可见性、邀请/移除成员、所有 editor 权限 |
| **admin** | 改成员角色（除 owner）、所有 editor 权限 |
| **editor** | 改项目数据、写/改自己的评论 |
| **viewer** | 只读项目数据、看评论 |

## 端点一览 / Endpoints

### 项目 / Projects (`project_routes.py`)

| Method | Path | 权限 |
|---|---|---|
| `GET` | `/projects` | 列出**我**拥有的项目 |
| `GET` | `/projects/shared` | 列出**别人**共享给我的项目 |
| `GET` | `/projects/all` | 我能看到的全部（拥有 + 共享） |
| `POST` | `/projects` | 创建项目（自动成为 owner） |
| `GET` | `/projects/{id}` | 项目详情（需 viewer+） |
| `PUT` | `/projects/{id}` | 改标题/描述/状态/可见性（需 editor+） |
| `PUT` | `/projects/{id}/data` | 改核心校勘数据（需 editor+） |
| `PUT` | `/projects/{id}/visibility` | 改可见性（仅 owner） |
| `DELETE` | `/projects/{id}` | 删除项目（仅 owner） |

### 成员与共享 / Members & Sharing (`share_routes.py`)

| Method | Path | 权限 |
|---|---|---|
| `GET` | `/projects/{id}/members` | 列出成员（需 viewer+） |
| `POST` | `/projects/{id}/share` | 邀请用户为成员（需 admin/owner） |
| `PUT` | `/projects/{id}/share/{user_id}` | 改成员角色（需 admin/owner） |
| `DELETE` | `/projects/{id}/share/{user_id}` | 取消共享（需 admin/owner） |

### 评论 / Comments

| Method | Path | 权限 |
|---|---|---|
| `GET` | `/projects/{id}/comments` | 列出评论（需 viewer+） |
| `POST` | `/projects/{id}/comments` | 加评论（需 viewer+） |
| `PUT` | `/projects/{id}/comments/{cid}` | 改评论（仅作者） |
| `DELETE` | `/projects/{id}/comments/{cid}` | 删评论（作者或 admin/owner） |

### 历史 / History

| Method | Path | 权限 |
|---|---|---|
| `GET` | `/projects/{id}/history` | 编辑历史（需 viewer+） |

## 典型流程 / Typical Flow

```
Alice 创建项目 X，自动是 owner
  ↓
Alice 邀请 Bob (editor) 和 Carol (viewer)
  ↓
Bob 修改了底本 → 历史里出现 "Bob edited base text"
Carol 在某处加了评论 "此字疑误，参《大正藏》异文"
  ↓
Alice 看历史，approve Bob 的改动
  ↓
Alice 把项目改为 public 可见 → 任何登录用户可只读
```

## 数据模型 / Schemas

参考 `backend/app/api/v1/collab/schemas.py` 与 `backend/app/models/collaboration.py`。

## 已知限制 / Known Limitations (v0.1.0)

- ❌ **没有邀请通知**：邀请后被邀请者不会收到邮件 / 站内信。需手动告知。
- ❌ **没有实时协作锁**：两人同时改 `/data` 会互相覆盖，最后写的赢。Roadmap 中考虑乐观锁 + WebSocket 通知。
- ❌ **评论不能 @mention**

这些都在 [`ROADMAP.md`](../ROADMAP.md) 的 v0.3 阶段。

---

*相关文档 / See also: [`AUTH.md`](AUTH.md) · [`ADMIN.md`](ADMIN.md)*
