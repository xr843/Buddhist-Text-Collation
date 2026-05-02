"""
依赖注入模块
提供用户认证、权限检查等依赖项
"""
from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional, List

from .database import get_db
from .auth import get_current_user, get_current_user_optional, TokenData
from ..models.user import User, UserRole
from ..models.collaboration import (
    CollabProject,
    ProjectMember,
    MemberRole,
    ProjectVisibility,
)


class PermissionChecker:
    """权限检查器工厂"""

    def __init__(self, allowed_roles: Optional[List[MemberRole]] = None):
        """
        Args:
            allowed_roles: 允许的项目角色列表
        """
        self.allowed_roles = allowed_roles


async def get_current_user_db(
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户的数据库对象

    Returns:
        User对象

    Raises:
        HTTPException: 用户不存在或未激活
    """
    user_id = int(token_data.sub)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    return user


async def get_current_user_db_optional(
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户（可选，不强制认证）

    Returns:
        User对象或None
    """
    if not token_data:
        return None

    try:
        user_id = int(token_data.sub)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user if user and user.is_active else None
    except (ValueError, Exception):
        return None


async def require_admin(
    current_user: User = Depends(get_current_user_db)
) -> User:
    """
    要求当前用户是管理员

    Returns:
        管理员User对象

    Raises:
        HTTPException: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_project_with_permission(
    project_id: str = Path(..., description="项目ID"),
    current_user: Optional[User] = Depends(get_current_user_db_optional),
    db: AsyncSession = Depends(get_db),
    required_role: Optional[MemberRole] = None,
) -> CollabProject:
    """
    获取项目并检查访问权限

    Args:
        project_id: 项目ID
        current_user: 当前用户（可选）
        db: 数据库会话
        required_role: 要求的最低角色

    Returns:
        CollabProject对象

    Raises:
        HTTPException: 项目不存在或无权访问
    """
    # 获取项目
    result = await db.execute(
        select(CollabProject).where(CollabProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 公开项目：任何人都可以查看
    if project.visibility == ProjectVisibility.PUBLIC:
        if required_role is None or required_role == MemberRole.VIEWER:
            return project
        # 公开项目但需要编辑权限，则需要登录和权限检查
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要登录才能执行此操作",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 共享项目：登录用户可以只读访问
    if project.visibility == ProjectVisibility.SHARED:
        if current_user:
            if required_role is None or required_role == MemberRole.VIEWER:
                return project
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要登录才能访问",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 私有项目：需要是所有者或成员
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能访问",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 管理员可以访问所有项目
    if current_user.is_admin:
        return project

    # 检查是否是项目所有者
    if project.owner_id == current_user.id:
        return project

    # 检查项目成员权限
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此项目"
        )

    # 检查角色权限
    if required_role:
        role_hierarchy = {
            MemberRole.VIEWER: 0,
            MemberRole.EDITOR: 1,
            MemberRole.ADMIN: 2,
        }
        if role_hierarchy.get(member.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

    return project


def require_project_role(required_role: MemberRole):
    """
    创建项目权限检查依赖项

    Args:
        required_role: 要求的最低角色

    Returns:
        依赖项函数
    """
    async def _require_project_role(
        project_id: str = Path(..., description="项目ID"),
        current_user: User = Depends(get_current_user_db),
        db: AsyncSession = Depends(get_db),
    ) -> CollabProject:
        return await get_project_with_permission(
            project_id=project_id,
            current_user=current_user,
            db=db,
            required_role=required_role,
        )
    return _require_project_role


# 预定义的权限检查依赖项
require_project_viewer = require_project_role(MemberRole.VIEWER)
require_project_editor = require_project_role(MemberRole.EDITOR)
require_project_admin = require_project_role(MemberRole.ADMIN)


async def check_project_owner(
    project_id: str = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
) -> CollabProject:
    """
    检查当前用户是否是项目所有者

    Returns:
        CollabProject对象

    Raises:
        HTTPException: 用户不是项目所有者
    """
    result = await db.execute(
        select(CollabProject).where(CollabProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 管理员可以作为所有者操作
    if current_user.is_admin:
        return project

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有项目所有者可以执行此操作"
        )

    return project


async def get_user_role_in_project(
    project: CollabProject,
    user: User,
    db: AsyncSession,
) -> Optional[str]:
    """
    获取用户在项目中的角色

    Returns:
        角色名称: "owner" | "admin" | "editor" | "viewer" | None
    """
    # 所有者
    if project.owner_id == user.id:
        return "owner"

    # 系统管理员
    if user.is_admin:
        return "admin"

    # 项目成员
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()

    if member:
        return member.role.value

    # 共享可见项目
    if project.visibility == ProjectVisibility.SHARED:
        return "viewer"

    # 公开项目
    if project.visibility == ProjectVisibility.PUBLIC:
        return "viewer"

    return None
