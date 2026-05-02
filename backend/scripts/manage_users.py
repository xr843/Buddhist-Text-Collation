"""
用户管理脚本

使用方法：
    cd backend
    source venv/bin/activate

    # 列出所有用户
    python scripts/manage_users.py list

    # 创建普通用户（为同事创建账号）
    python scripts/manage_users.py create <username> <email> <password> [姓名]
    python scripts/manage_users.py create zhangsan zhangsan@lab.edu Pass123 张三
    python scripts/manage_users.py create lisi lisi@university.edu MyPass456 李四

    # 创建管理员
    python scripts/manage_users.py create-admin <username> <email> <password>

    # 重置密码
    python scripts/manage_users.py reset-password <username> <new_password>

    # 禁用用户
    python scripts/manage_users.py disable <username>

    # 启用用户
    python scripts/manage_users.py enable <username>

    # 设置角色
    python scripts/manage_users.py set-role <username> <admin|user>
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def get_session():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session(), engine


async def list_users():
    """列出所有用户"""
    session, engine = await get_session()
    async with session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        print(f"\n{'ID':<5} {'用户名':<15} {'邮箱':<30} {'角色':<10} {'状态':<8} {'创建时间'}")
        print("-" * 100)
        for u in users:
            status = "✅ 启用" if u.is_active else "❌ 禁用"
            created = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "-"
            print(f"{u.id:<5} {u.username:<15} {u.email:<30} {u.role.value:<10} {status:<8} {created}")
        print(f"\n共 {len(users)} 个用户")
    await engine.dispose()


async def create_user(username: str, email: str, password: str, role: str = "user", full_name: str = None):
    """创建用户账户"""
    session, engine = await get_session()
    async with session:
        # 检查是否已存在
        result = await session.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            print(f"❌ 用户名 {username} 已存在")
            await engine.dispose()
            return

        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"❌ 邮箱 {email} 已被使用")
            await engine.dispose()
            return

        user_role = UserRole.ADMIN if role.lower() == "admin" else UserRole.USER
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=user_role,
            is_active=True,
            is_superuser=(role.lower() == "admin"),
        )
        session.add(user)
        await session.commit()
        role_name = "管理员" if user_role == UserRole.ADMIN else "普通用户"
        print(f"✅ {role_name} {username} 创建成功")
        print(f"   邮箱: {email}")
        print(f"   密码: {password}")
    await engine.dispose()


async def create_admin(username: str, email: str, password: str):
    """创建管理员账户"""
    await create_user(username, email, password, role="admin")


async def reset_password(username: str, new_password: str):
    """重置用户密码"""
    session, engine = await get_session()
    async with session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(f"❌ 用户 {username} 不存在")
            return

        user.hashed_password = get_password_hash(new_password)
        await session.commit()
        print(f"✅ 用户 {username} 密码已重置")
    await engine.dispose()


async def set_user_status(username: str, is_active: bool):
    """设置用户状态"""
    session, engine = await get_session()
    async with session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(f"❌ 用户 {username} 不存在")
            return

        user.is_active = is_active
        await session.commit()
        status = "启用" if is_active else "禁用"
        print(f"✅ 用户 {username} 已{status}")
    await engine.dispose()


async def set_role(username: str, role: str):
    """设置用户角色"""
    session, engine = await get_session()
    async with session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(f"❌ 用户 {username} 不存在")
            return

        try:
            user.role = UserRole(role.lower())
            await session.commit()
            print(f"✅ 用户 {username} 角色已设置为 {role}")
        except ValueError:
            print(f"❌ 无效角色: {role}，可选: admin, user")
    await engine.dispose()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "list":
        asyncio.run(list_users())

    elif command == "create":
        if len(sys.argv) < 5:
            print("用法: python manage_users.py create <username> <email> <password> [full_name]")
            print("示例: python manage_users.py create zhangsan zhangsan@lab.edu Pass123 张三")
            return
        full_name = sys.argv[5] if len(sys.argv) > 5 else None
        asyncio.run(create_user(sys.argv[2], sys.argv[3], sys.argv[4], "user", full_name))

    elif command == "create-admin":
        if len(sys.argv) != 5:
            print("用法: python manage_users.py create-admin <username> <email> <password>")
            return
        asyncio.run(create_admin(sys.argv[2], sys.argv[3], sys.argv[4]))

    elif command == "reset-password":
        if len(sys.argv) != 4:
            print("用法: python manage_users.py reset-password <username> <new_password>")
            return
        asyncio.run(reset_password(sys.argv[2], sys.argv[3]))

    elif command == "disable":
        if len(sys.argv) != 3:
            print("用法: python manage_users.py disable <username>")
            return
        asyncio.run(set_user_status(sys.argv[2], False))

    elif command == "enable":
        if len(sys.argv) != 3:
            print("用法: python manage_users.py enable <username>")
            return
        asyncio.run(set_user_status(sys.argv[2], True))

    elif command == "set-role":
        if len(sys.argv) != 4:
            print("用法: python manage_users.py set-role <username> <admin|user>")
            return
        asyncio.run(set_role(sys.argv[2], sys.argv[3]))

    else:
        print(f"未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
