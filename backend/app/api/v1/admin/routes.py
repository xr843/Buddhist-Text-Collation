"""
管理员API路由
用户管理、系统统计等
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from ....core.database import get_db
from ....core.deps import require_admin
from ....models.user import User, UserRole
from ....models.collaboration import CollabProject, CollabProjectType

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/users", summary="获取用户列表")
async def list_users(
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户列表（管理员专用）
    """
    # 构建查询条件
    conditions = []

    if search:
        conditions.append(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    if role:
        try:
            role_enum = UserRole(role)
            conditions.append(User.role == role_enum)
        except ValueError:
            pass

    if is_active is not None:
        conditions.append(User.is_active == is_active)

    # 查询总数
    count_query = select(func.count(User.id))
    if conditions:
        count_query = count_query.where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 查询用户列表
    query = select(User)
    if conditions:
        query = query.where(*conditions)
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    items = []
    for user in users:
        items.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if user.role else "user",
            "is_active": user.is_active,
            "institution": user.institution,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        })

    return {
        "success": True,
        "total": total,
        "items": items,
    }


@router.get("/users/{user_id}", summary="获取用户详情")
async def get_user_detail(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定用户的详细信息
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 统计用户的项目数
    project_count_result = await db.execute(
        select(func.count(CollabProject.id)).where(CollabProject.owner_id == user_id)
    )
    project_count = project_count_result.scalar() or 0

    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if user.role else "user",
            "is_active": user.is_active,
            "institution": user.institution,
            "research_field": user.research_field,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "project_count": project_count,
        }
    }


@router.put("/users/{user_id}", summary="更新用户信息")
async def update_user(
    user_id: int,
    role: Optional[str] = Query(None, description="新角色"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户信息（管理员专用）
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能修改自己的状态
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的账户状态"
        )

    if role is not None:
        try:
            user.role = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的角色: {role}"
            )

    if is_active is not None:
        user.is_active = is_active

    await db.commit()
    await db.refresh(user)

    return {
        "success": True,
        "message": "用户信息已更新",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value if user.role else "user",
            "is_active": user.is_active,
        }
    }


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    删除用户（管理员专用）
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )

    await db.delete(user)
    await db.commit()

    return {
        "success": True,
        "message": f"用户 {user.username} 已删除",
    }


@router.get("/stats", summary="获取系统统计")
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取系统统计信息
    """
    # 用户统计
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active)
    )).scalar() or 0
    admin_users = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    )).scalar() or 0

    # 项目统计
    total_projects = (await db.execute(
        select(func.count(CollabProject.id))
    )).scalar() or 0

    # 按类型统计项目
    project_by_type = {}
    for ptype in CollabProjectType:
        count = (await db.execute(
            select(func.count(CollabProject.id)).where(
                CollabProject.project_type == ptype
            )
        )).scalar() or 0
        project_by_type[ptype.value] = count

    return {
        "success": True,
        "stats": {
            "users": {
                "total": total_users,
                "active": active_users,
                "admin": admin_users,
            },
            "projects": {
                "total": total_projects,
                "by_type": project_by_type,
            },
        }
    }
