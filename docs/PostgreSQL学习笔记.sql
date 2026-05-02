-- ============================================================
-- PostgreSQL 学习笔记
-- 基于「佛典标点与校勘研究平台」项目
-- ============================================================
--
-- 使用方法：
--   1. 在 VS Code Database Client 中打开此文件
--   2. 选中要执行的SQL语句
--   3. 按 Ctrl+Enter 执行
--
-- 数据库连接信息：
--   主机: localhost
--   端口: 5433
--   数据库: buddhist_text
--   用户名: buddhist_user
--   密码: buddhist_pass
--
-- ============================================================


-- ************************************************************
-- 第一章：基础查询 (SELECT)
-- ************************************************************

-- ------------------------------------------------------------
-- 1.1 查询所有数据
-- ------------------------------------------------------------

-- 查询所有用户（* 表示所有列）
SELECT * FROM users;

-- 查询所有项目
SELECT * FROM collab_projects;


-- ------------------------------------------------------------
-- 1.2 选择特定列
-- ------------------------------------------------------------

-- 只查询用户名和邮箱
SELECT username, email FROM users;

-- 查询项目标题和类型
SELECT title, project_type, status FROM collab_projects;

-- 使用别名让结果更易读（AS 可以省略）
SELECT
    username AS 用户名,
    email AS 邮箱,
    created_at AS 注册时间
FROM users;


-- ------------------------------------------------------------
-- 1.3 条件筛选 (WHERE)
-- ------------------------------------------------------------

-- 查询管理员用户
SELECT * FROM users WHERE role = 'ADMIN';

-- 查询普通用户
SELECT * FROM users WHERE role = 'USER';

-- 查询已启用的用户
SELECT * FROM users WHERE is_active = true;

-- 查询私有项目
SELECT title, visibility FROM collab_projects WHERE visibility = 'PRIVATE';

-- 查询进行中的项目
SELECT title, status FROM collab_projects WHERE status = 'IN_PROGRESS';


-- ------------------------------------------------------------
-- 1.4 多条件查询 (AND / OR / NOT)
-- ------------------------------------------------------------

-- 查询启用的普通用户
SELECT * FROM users
WHERE role = 'USER' AND is_active = true;

-- 查询管理员或超级用户
SELECT * FROM users
WHERE role = 'ADMIN' OR is_superuser = true;

-- 查询非管理员
SELECT * FROM users
WHERE NOT role = 'ADMIN';
-- 或者
SELECT * FROM users
WHERE role != 'ADMIN';


-- ------------------------------------------------------------
-- 1.5 排序 (ORDER BY)
-- ------------------------------------------------------------

-- 按注册时间升序（最早的在前）
SELECT username, created_at FROM users
ORDER BY created_at ASC;

-- 按注册时间降序（最新的在前）
SELECT username, created_at FROM users
ORDER BY created_at DESC;

-- 多列排序：先按角色，再按注册时间
SELECT username, role, created_at FROM users
ORDER BY role, created_at DESC;


-- ------------------------------------------------------------
-- 1.6 限制结果数量 (LIMIT / OFFSET)
-- ------------------------------------------------------------

-- 只取前5条
SELECT * FROM users LIMIT 5;

-- 跳过前2条，取3条（分页常用）
SELECT * FROM users LIMIT 3 OFFSET 2;

-- 查询最新注册的3个用户
SELECT username, created_at FROM users
ORDER BY created_at DESC
LIMIT 3;


-- ------------------------------------------------------------
-- 1.7 模糊搜索 (LIKE / ILIKE)
-- ------------------------------------------------------------

-- 用户名包含 "test"（区分大小写）
SELECT * FROM users WHERE username LIKE '%test%';

-- 用户名包含 "test"（不区分大小写，PostgreSQL特有）
SELECT * FROM users WHERE username ILIKE '%test%';

-- 邮箱以 "admin" 开头
SELECT * FROM users WHERE email LIKE 'admin%';

-- 邮箱以 ".com" 结尾
SELECT * FROM users WHERE email LIKE '%.com';

-- 项目标题包含 "校勘"
SELECT title FROM collab_projects WHERE title LIKE '%校勘%';


-- ------------------------------------------------------------
-- 1.8 空值处理 (NULL)
-- ------------------------------------------------------------

-- 查询没有填写机构的用户
SELECT username, institution FROM users
WHERE institution IS NULL;

-- 查询已填写机构的用户
SELECT username, institution FROM users
WHERE institution IS NOT NULL;

-- 使用 COALESCE 设置默认值
SELECT
    username,
    COALESCE(institution, '未填写') AS 机构
FROM users;


-- ************************************************************
-- 第二章：聚合函数与分组
-- ************************************************************

-- ------------------------------------------------------------
-- 2.1 常用聚合函数
-- ------------------------------------------------------------

-- 统计用户总数
SELECT COUNT(*) AS 用户总数 FROM users;

-- 统计项目总数
SELECT COUNT(*) AS 项目总数 FROM collab_projects;

-- 统计有邮箱的用户数（COUNT忽略NULL）
SELECT COUNT(email) AS 有邮箱用户数 FROM users;

-- 统计不重复的角色数
SELECT COUNT(DISTINCT role) AS 角色种类 FROM users;


-- ------------------------------------------------------------
-- 2.2 分组统计 (GROUP BY)
-- ------------------------------------------------------------

-- 按角色统计用户数
SELECT
    role AS 角色,
    COUNT(*) AS 数量
FROM users
GROUP BY role;

-- 按项目类型统计
SELECT
    project_type AS 项目类型,
    COUNT(*) AS 数量
FROM collab_projects
GROUP BY project_type;

-- 按状态统计项目
SELECT
    status AS 状态,
    COUNT(*) AS 数量
FROM collab_projects
GROUP BY status;

-- 按可见性统计
SELECT
    visibility AS 可见性,
    COUNT(*) AS 数量
FROM collab_projects
GROUP BY visibility;


-- ------------------------------------------------------------
-- 2.3 分组过滤 (HAVING)
-- ------------------------------------------------------------

-- 找出拥有超过1个项目的用户
SELECT
    owner_id,
    COUNT(*) AS 项目数
FROM collab_projects
GROUP BY owner_id
HAVING COUNT(*) > 1;


-- ------------------------------------------------------------
-- 2.4 日期统计
-- ------------------------------------------------------------

-- 按月统计注册用户数
SELECT
    DATE_TRUNC('month', created_at) AS 月份,
    COUNT(*) AS 注册数
FROM users
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY 月份;

-- 按日期统计项目创建数
SELECT
    DATE(created_at) AS 日期,
    COUNT(*) AS 创建数
FROM collab_projects
GROUP BY DATE(created_at)
ORDER BY 日期 DESC;


-- ************************************************************
-- 第三章：表关联 (JOIN)
-- ************************************************************

-- ------------------------------------------------------------
-- 3.1 项目表结构说明
-- ------------------------------------------------------------
/*
本项目的核心表关系：

users (用户表)
  └── collab_projects (项目表) [owner_id -> users.id]
        ├── project_members (项目成员) [project_id -> collab_projects.id]
        ├── comments (评论) [project_id -> collab_projects.id]
        └── edit_history (编辑历史) [project_id -> collab_projects.id]
*/


-- ------------------------------------------------------------
-- 3.2 内连接 (INNER JOIN)
-- ------------------------------------------------------------

-- 查询项目及其所有者信息
SELECT
    p.title AS 项目名称,
    p.project_type AS 类型,
    u.username AS 所有者,
    u.email AS 邮箱
FROM collab_projects p
INNER JOIN users u ON p.owner_id = u.id;


-- ------------------------------------------------------------
-- 3.3 左连接 (LEFT JOIN)
-- ------------------------------------------------------------

-- 查询所有用户及其项目数（包括没有项目的用户）
SELECT
    u.username AS 用户名,
    u.email AS 邮箱,
    COUNT(p.id) AS 项目数量
FROM users u
LEFT JOIN collab_projects p ON u.id = p.owner_id
GROUP BY u.id, u.username, u.email
ORDER BY 项目数量 DESC;


-- ------------------------------------------------------------
-- 3.4 多表关联
-- ------------------------------------------------------------

-- 查询项目、所有者、成员信息
SELECT
    p.title AS 项目,
    owner.username AS 所有者,
    member.username AS 成员,
    pm.role AS 成员角色
FROM collab_projects p
JOIN users owner ON p.owner_id = owner.id
LEFT JOIN project_members pm ON p.id = pm.project_id
LEFT JOIN users member ON pm.user_id = member.id;


-- ------------------------------------------------------------
-- 3.5 自关联
-- ------------------------------------------------------------

-- 查询评论及其回复（comments表有parent_id自引用）
SELECT
    c1.content AS 原评论,
    c2.content AS 回复
FROM comments c1
LEFT JOIN comments c2 ON c1.id = c2.parent_id
WHERE c2.id IS NOT NULL;


-- ************************************************************
-- 第四章：JSONB 查询（PostgreSQL特色）
-- ************************************************************

-- ------------------------------------------------------------
-- 4.1 JSONB 基础
-- ------------------------------------------------------------
/*
本项目使用 JSONB 存储灵活的项目数据：
- collab_projects.data: 项目核心数据（底本、校本、异文等）
- collab_projects.project_meta: 项目元数据（统计信息）

JSONB 操作符：
- ->  : 获取JSON对象字段（返回JSON）
- ->> : 获取JSON对象字段（返回文本）
- @>  : 包含
- ?   : 键是否存在
*/

-- 查看项目的元数据
SELECT
    title,
    project_meta
FROM collab_projects
LIMIT 3;


-- ------------------------------------------------------------
-- 4.2 提取 JSONB 字段
-- ------------------------------------------------------------

-- 提取元数据中的具体字段
SELECT
    title AS 项目名称,
    project_meta->>'base_name' AS 底本名称,
    project_meta->>'variant_count' AS 异文数量,
    project_meta->>'collation_count' AS 校本数量
FROM collab_projects
WHERE project_type = 'MULTI_COLLATION';


-- ------------------------------------------------------------
-- 4.3 JSONB 条件筛选
-- ------------------------------------------------------------

-- 筛选异文数量超过100的项目
SELECT
    title,
    (project_meta->>'variant_count')::int AS 异文数
FROM collab_projects
WHERE (project_meta->>'variant_count')::int > 100;

-- 筛选有特定底本的项目
SELECT title
FROM collab_projects
WHERE project_meta->>'base_name' LIKE '%順正理論%';


-- ------------------------------------------------------------
-- 4.4 JSONB 数组操作
-- ------------------------------------------------------------

-- 查看校本名称列表（JSON数组）
SELECT
    title,
    project_meta->'collation_names' AS 校本列表
FROM collab_projects
WHERE project_meta->'collation_names' IS NOT NULL
LIMIT 1;

-- 展开JSON数组为多行
SELECT
    title,
    jsonb_array_elements_text(project_meta->'collation_names') AS 校本名称
FROM collab_projects
WHERE project_meta->'collation_names' IS NOT NULL
LIMIT 20;


-- ------------------------------------------------------------
-- 4.5 JSONB 聚合统计
-- ------------------------------------------------------------

-- 统计各项目的异文总数
SELECT
    SUM((project_meta->>'variant_count')::int) AS 异文总数
FROM collab_projects
WHERE project_meta->>'variant_count' IS NOT NULL;

-- 按项目类型统计平均异文数
SELECT
    project_type,
    AVG((project_meta->>'variant_count')::int)::int AS 平均异文数
FROM collab_projects
WHERE project_meta->>'variant_count' IS NOT NULL
GROUP BY project_type;


-- ************************************************************
-- 第五章：子查询与高级查询
-- ************************************************************

-- ------------------------------------------------------------
-- 5.1 子查询基础
-- ------------------------------------------------------------

-- 查询拥有项目的用户
SELECT * FROM users
WHERE id IN (
    SELECT DISTINCT owner_id FROM collab_projects
);

-- 查询没有项目的用户
SELECT * FROM users
WHERE id NOT IN (
    SELECT DISTINCT owner_id FROM collab_projects
);


-- ------------------------------------------------------------
-- 5.2 EXISTS 子查询
-- ------------------------------------------------------------

-- 查询有项目的用户（EXISTS效率通常更高）
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM collab_projects p WHERE p.owner_id = u.id
);


-- ------------------------------------------------------------
-- 5.3 WITH 子句 (CTE - 通用表表达式)
-- ------------------------------------------------------------

-- 使用 CTE 计算用户项目统计
WITH user_stats AS (
    SELECT
        owner_id,
        COUNT(*) AS project_count,
        MAX(created_at) AS last_project_time
    FROM collab_projects
    GROUP BY owner_id
)
SELECT
    u.username,
    u.email,
    COALESCE(s.project_count, 0) AS 项目数,
    s.last_project_time AS 最后创建时间
FROM users u
LEFT JOIN user_stats s ON u.id = s.owner_id
ORDER BY 项目数 DESC;


-- ------------------------------------------------------------
-- 5.4 窗口函数
-- ------------------------------------------------------------

-- 为每个用户的项目添加序号
SELECT
    u.username,
    p.title,
    p.created_at,
    ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY p.created_at) AS 项目序号
FROM users u
JOIN collab_projects p ON u.id = p.owner_id;

-- 计算累计项目数
SELECT
    DATE(created_at) AS 日期,
    COUNT(*) AS 当日新增,
    SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) AS 累计总数
FROM collab_projects
GROUP BY DATE(created_at)
ORDER BY 日期;


-- ************************************************************
-- 第六章：数据修改 (INSERT / UPDATE / DELETE)
-- ************************************************************

-- ------------------------------------------------------------
-- 6.1 插入数据 (INSERT)
-- ------------------------------------------------------------

-- 注意：以下为示例，请谨慎执行

-- 插入单条记录
-- INSERT INTO users (username, email, hashed_password, role, is_active)
-- VALUES ('newuser', 'new@example.com', 'hashed_pwd', 'USER', true);

-- 插入多条记录
-- INSERT INTO users (username, email, hashed_password, role, is_active)
-- VALUES
--     ('user1', 'user1@example.com', 'pwd1', 'USER', true),
--     ('user2', 'user2@example.com', 'pwd2', 'USER', true);


-- ------------------------------------------------------------
-- 6.2 更新数据 (UPDATE)
-- ------------------------------------------------------------

-- 更新单个字段
-- UPDATE users SET is_active = false WHERE username = 'testuser';

-- 更新多个字段
-- UPDATE users
-- SET institution = '研究院', research_field = '佛学'
-- WHERE username = 'admin';

-- 批量更新
-- UPDATE collab_projects SET status = 'COMPLETED'
-- WHERE created_at < '2026-01-01';


-- ------------------------------------------------------------
-- 6.3 删除数据 (DELETE)
-- ------------------------------------------------------------

-- 删除特定记录
-- DELETE FROM users WHERE username = 'testuser';

-- 删除符合条件的记录
-- DELETE FROM collab_projects WHERE status = 'DRAFT';

-- 清空表（保留表结构）
-- TRUNCATE TABLE edit_history;


-- ------------------------------------------------------------
-- 6.4 事务控制
-- ------------------------------------------------------------

-- 开始事务
-- BEGIN;

-- 执行操作
-- UPDATE users SET is_active = false WHERE id = 2;
-- DELETE FROM collab_projects WHERE owner_id = 2;

-- 确认无误后提交
-- COMMIT;

-- 或者回滚撤销
-- ROLLBACK;


-- ************************************************************
-- 第七章：实用管理操作
-- ************************************************************

-- ------------------------------------------------------------
-- 7.1 查看数据库信息
-- ------------------------------------------------------------

-- 查看所有表
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- 查看表结构
SELECT
    column_name AS 列名,
    data_type AS 数据类型,
    is_nullable AS 可空
FROM information_schema.columns
WHERE table_name = 'users';

-- 查看表大小
SELECT
    relname AS 表名,
    pg_size_pretty(pg_total_relation_size(relid)) AS 大小
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;


-- ------------------------------------------------------------
-- 7.2 索引管理
-- ------------------------------------------------------------

-- 查看表的索引
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'users';

-- 创建索引
-- CREATE INDEX idx_projects_title ON collab_projects(title);

-- 创建唯一索引
-- CREATE UNIQUE INDEX idx_users_email ON users(email);

-- 删除索引
-- DROP INDEX idx_projects_title;


-- ------------------------------------------------------------
-- 7.3 查询性能分析
-- ------------------------------------------------------------

-- 查看执行计划
EXPLAIN SELECT * FROM users WHERE username = 'admin';

-- 查看详细执行计划（包含实际执行时间）
EXPLAIN ANALYZE SELECT * FROM users WHERE username = 'admin';


-- ------------------------------------------------------------
-- 7.4 数据备份与恢复
-- ------------------------------------------------------------

-- 导出表数据到CSV（需要权限）
-- COPY users TO '/tmp/users_backup.csv' WITH CSV HEADER;

-- 从CSV导入数据
-- COPY users FROM '/tmp/users_backup.csv' WITH CSV HEADER;

-- 命令行备份整个数据库
-- pg_dump -h localhost -p 5433 -U buddhist_user buddhist_text > backup.sql

-- 命令行恢复数据库
-- psql -h localhost -p 5433 -U buddhist_user buddhist_text < backup.sql


-- ************************************************************
-- 第八章：常用查询模板（本项目专用）
-- ************************************************************

-- ------------------------------------------------------------
-- 8.1 用户管理查询
-- ------------------------------------------------------------

-- 用户概览
SELECT
    id,
    username AS 用户名,
    email AS 邮箱,
    role AS 角色,
    CASE WHEN is_active THEN '启用' ELSE '禁用' END AS 状态,
    COALESCE(institution, '-') AS 机构,
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS 注册时间,
    TO_CHAR(last_login, 'YYYY-MM-DD HH24:MI') AS 最后登录
FROM users
ORDER BY created_at DESC;

-- 用户活跃度分析
SELECT
    u.username,
    COUNT(p.id) AS 项目数,
    COUNT(c.id) AS 评论数,
    MAX(p.updated_at) AS 最后活动时间
FROM users u
LEFT JOIN collab_projects p ON u.id = p.owner_id
LEFT JOIN comments c ON u.id = c.user_id
GROUP BY u.id, u.username
ORDER BY 项目数 DESC;


-- ------------------------------------------------------------
-- 8.2 项目管理查询
-- ------------------------------------------------------------

-- 项目概览
SELECT
    p.id,
    p.title AS 项目名称,
    u.username AS 所有者,
    p.project_type AS 类型,
    p.status AS 状态,
    p.visibility AS 可见性,
    project_meta->>'variant_count' AS 异文数,
    TO_CHAR(p.created_at, 'YYYY-MM-DD') AS 创建日期
FROM collab_projects p
JOIN users u ON p.owner_id = u.id
ORDER BY p.created_at DESC;

-- 项目统计仪表盘
SELECT
    COUNT(*) AS 项目总数,
    COUNT(CASE WHEN status = 'IN_PROGRESS' THEN 1 END) AS 进行中,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS 已完成,
    COUNT(CASE WHEN status = 'DRAFT' THEN 1 END) AS 草稿,
    COUNT(CASE WHEN visibility = 'PUBLIC' THEN 1 END) AS 公开项目
FROM collab_projects;


-- ------------------------------------------------------------
-- 8.3 数据统计报表
-- ------------------------------------------------------------

-- 系统整体统计
SELECT
    (SELECT COUNT(*) FROM users) AS 用户总数,
    (SELECT COUNT(*) FROM users WHERE is_active = true) AS 活跃用户,
    (SELECT COUNT(*) FROM collab_projects) AS 项目总数,
    (SELECT COUNT(*) FROM comments) AS 评论总数,
    (SELECT SUM((project_meta->>'variant_count')::int)
     FROM collab_projects
     WHERE project_meta->>'variant_count' IS NOT NULL) AS 异文总数;

-- 每日新增统计
SELECT
    DATE(created_at) AS 日期,
    COUNT(*) AS 新增项目数
FROM collab_projects
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY 日期;


-- ============================================================
-- 学习建议：
-- 1. 从第一章开始，逐个执行理解
-- 2. 修改查询条件，观察结果变化
-- 3. 尝试组合不同的查询技巧
-- 4. 遇到不懂的，查阅 PostgreSQL 官方文档
-- ============================================================
