"""
数据迁移脚本：将JSON项目数据迁移到PostgreSQL数据库

使用方法：
    python -m scripts.migrate_json_to_db

或者：
    cd backend
    python scripts/migrate_json_to_db.py

功能：
    1. 创建默认管理员账户（如果不存在）
    2. 读取所有JSON项目文件
    3. 将项目数据迁移到collab_projects表
    4. 验证数据完整性
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.collaboration import (
    CollabProject,
    CollabProjectType,
    CollabProjectStatus,
    ProjectVisibility,
)
from app.services.project_storage import ProjectType


# 项目类型映射
TYPE_MAPPING = {
    "multi_collation": CollabProjectType.MULTI_COLLATION,
    "two_version": CollabProjectType.TWO_VERSION,
    "punctuation": CollabProjectType.PUNCTUATION,
}

# 状态映射
STATUS_MAPPING = {
    "draft": CollabProjectStatus.DRAFT,
    "in_progress": CollabProjectStatus.IN_PROGRESS,
    "completed": CollabProjectStatus.COMPLETED,
}


async def create_admin_user(session: AsyncSession) -> User:
    """创建默认管理员账户"""
    # 检查是否已存在管理员
    result = await session.execute(
        select(User).where(User.role == UserRole.ADMIN)
    )
    admin = result.scalar_one_or_none()

    if admin:
        print(f"✅ 已存在管理员账户: {admin.username}")
        return admin

    # 创建新管理员
    admin = User(
        username="admin",
        email="admin@localhost.local",
        hashed_password=get_password_hash("admin123"),  # 默认密码，请在生产环境修改
        full_name="系统管理员",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
        institution="系统",
    )

    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    print(f"✅ 创建管理员账户: {admin.username} (密码: admin123，请尽快修改)")
    return admin


async def migrate_project(
    session: AsyncSession,
    project_data: dict,
    owner_id: int,
    project_type: ProjectType,
) -> Optional[CollabProject]:
    """迁移单个项目"""
    try:
        project_id = project_data.get("id")

        # 检查是否已存在
        result = await session.execute(
            select(CollabProject).where(CollabProject.id == project_id)
        )
        if result.scalar_one_or_none():
            print(f"  ⏭️  项目已存在，跳过: {project_id}")
            return None

        # 解析项目类型
        collab_type = TYPE_MAPPING.get(
            project_data.get("type", project_type.value),
            CollabProjectType.MULTI_COLLATION
        )

        # 解析状态
        status = STATUS_MAPPING.get(
            project_data.get("status", "in_progress"),
            CollabProjectStatus.IN_PROGRESS
        )

        # 解析时间
        created_at = None
        updated_at = None
        try:
            if project_data.get("created_at"):
                created_at = datetime.fromisoformat(project_data["created_at"].replace("Z", "+00:00"))
            if project_data.get("updated_at"):
                updated_at = datetime.fromisoformat(project_data["updated_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

        # 创建项目记录
        project = CollabProject(
            id=project_id,
            owner_id=owner_id,
            title=project_data.get("title", "未命名项目"),
            description=project_data.get("description", ""),
            project_type=collab_type,
            status=status,
            visibility=ProjectVisibility.PRIVATE,  # 迁移的项目默认私有
            data=project_data.get("data", {}),
            project_meta=project_data.get("metadata", {}),
        )

        if created_at:
            project.created_at = created_at
        if updated_at:
            project.updated_at = updated_at

        session.add(project)
        await session.commit()

        print(f"  ✅ 迁移成功: {project_id} ({project.title})")
        return project

    except Exception as e:
        print(f"  ❌ 迁移失败: {project_data.get('id', 'unknown')} - {e}")
        await session.rollback()
        return None


async def migrate_projects(session: AsyncSession, admin: User):
    """迁移所有项目"""
    base_dir = Path(__file__).parent.parent / "data" / "projects"

    if not base_dir.exists():
        print(f"⚠️ 项目目录不存在: {base_dir}")
        return 0

    total_count = 0
    success_count = 0

    # 遍历各类型目录
    for project_type in ProjectType:
        type_dir = base_dir / project_type.value

        if not type_dir.exists():
            continue

        json_files = list(type_dir.glob("*.json"))
        print(f"\n📁 {project_type.value}: 发现 {len(json_files)} 个项目")

        for json_file in json_files:
            total_count += 1
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    project_data = json.load(f)

                result = await migrate_project(
                    session, project_data, admin.id, project_type
                )
                if result:
                    success_count += 1

            except json.JSONDecodeError as e:
                print(f"  ❌ JSON解析失败: {json_file.name} - {e}")
            except Exception as e:
                print(f"  ❌ 读取失败: {json_file.name} - {e}")

    return total_count, success_count


async def verify_migration(session: AsyncSession):
    """验证迁移结果"""
    from sqlalchemy import func

    result = await session.execute(
        select(func.count(CollabProject.id))
    )
    count = result.scalar() or 0

    print(f"\n📊 数据库中共有 {count} 个协作项目")

    # 按类型统计
    for project_type in CollabProjectType:
        result = await session.execute(
            select(func.count(CollabProject.id)).where(
                CollabProject.project_type == project_type
            )
        )
        type_count = result.scalar() or 0
        if type_count > 0:
            print(f"   - {project_type.value}: {type_count} 个")


async def main():
    """主函数"""
    print("=" * 60)
    print("📦 JSON项目数据 → PostgreSQL 迁移工具")
    print("=" * 60)

    # 创建数据库引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )

    # 创建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ 数据库表结构已创建/更新")

    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 1. 创建管理员账户
        print("\n🔧 步骤 1: 检查/创建管理员账户")
        admin = await create_admin_user(session)

        # 2. 迁移项目数据
        print("\n🔧 步骤 2: 迁移项目数据")
        total, success = await migrate_projects(session, admin)

        # 3. 验证迁移结果
        print("\n🔧 步骤 3: 验证迁移结果")
        await verify_migration(session)

        # 总结
        print("\n" + "=" * 60)
        print(f"📝 迁移完成！")
        print(f"   总项目数: {total}")
        print(f"   成功迁移: {success}")
        print(f"   跳过/失败: {total - success}")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
