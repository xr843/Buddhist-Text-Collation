"""
项目共享和协作API路由
包括成员管理、评论、编辑历史
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from ....core.database import get_db
from ....core.deps import (
    get_current_user_db,
    get_project_with_permission,
    check_project_owner,
    require_project_admin,
)
from ....models.user import User
from ....models.collaboration import (
    CollabProject,
    MemberRole,
    Comment,
)
from ....services.project_db_service import get_project_service
from .schemas import (
    MemberAdd,
    MemberUpdate,
    MemberListResponse,
    MemberResponse,
    CommentCreate,
    CommentUpdate,
    CommentListResponse,
    CommentResponse,
    HistoryListResponse,
    HistoryEntry,
    MessageResponse,
)

router = APIRouter()


def parse_member_role(role_str: str) -> MemberRole:
    """解析成员角色字符串"""
    role_map = {
        "viewer": MemberRole.VIEWER,
        "editor": MemberRole.EDITOR,
        "admin": MemberRole.ADMIN,
    }
    if role_str.lower() not in role_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色: {role_str}，有效值: viewer/editor/admin"
        )
    return role_map[role_str.lower()]


# ==================== 成员管理 ====================

@router.get("/projects/{project_id}/members", response_model=MemberListResponse, summary="获取项目成员列表")
async def list_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    获取项目成员列表
    需要是项目成员或所有者
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    service = get_project_service(db)
    members = await service.list_members(project_id)

    # 添加所有者信息
    owner_result = await db.execute(
        select(User).where(User.id == project.owner_id)
    )
    owner = owner_result.scalar_one_or_none()

    member_list = []

    # 先添加所有者
    if owner:
        member_list.append(MemberResponse(
            id=0,  # 所有者不是 project_members 表的记录
            user_id=owner.id,
            username=owner.username,
            full_name=owner.full_name,
            avatar_url=owner.avatar_url,
            role="owner",
            created_at=project.created_at,
        ))

    # 添加其他成员
    for member in members:
        member_list.append(MemberResponse(
            id=member["id"],
            user_id=member["user_id"],
            username=member["username"],
            full_name=member.get("full_name"),
            avatar_url=member.get("avatar_url"),
            role=member["role"],
            created_at=member.get("created_at"),
        ))

    return MemberListResponse(
        success=True,
        members=member_list,
    )


@router.post("/projects/{project_id}/share", summary="共享项目给用户")
async def share_project(
    project_id: str,
    request: MemberAdd,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    共享项目给指定用户
    需要是项目所有者或管理员
    """
    project = await require_project_admin(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    # 查找目标用户
    target_user = None
    if request.user_id:
        result = await db.execute(
            select(User).where(User.id == request.user_id)
        )
        target_user = result.scalar_one_or_none()
    elif request.username:
        result = await db.execute(
            select(User).where(User.username == request.username)
        )
        target_user = result.scalar_one_or_none()
    elif request.email:
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能共享给自己
    if target_user.id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能共享给项目所有者"
        )

    role = parse_member_role(request.role)

    service = get_project_service(db)
    member = await service.add_member(
        project_id=project_id,
        user_id=target_user.id,
        role=role,
        invited_by=current_user.id,
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户已经是项目成员"
        )

    return {
        "success": True,
        "message": f"已将 {target_user.username} 添加为项目成员",
        "member": {
            "user_id": target_user.id,
            "username": target_user.username,
            "role": role.value,
        }
    }


@router.put("/projects/{project_id}/share/{user_id}", summary="更新成员角色")
async def update_member_role(
    project_id: str,
    user_id: int,
    request: MemberUpdate,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    更新项目成员的角色
    需要是项目所有者或管理员
    """
    project = await require_project_admin(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    # 不能修改所有者的角色
    if user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改项目所有者的角色"
        )

    role = parse_member_role(request.role)

    service = get_project_service(db)
    member = await service.update_member_role(
        project_id=project_id,
        user_id=user_id,
        new_role=role,
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该用户不是项目成员"
        )

    return {
        "success": True,
        "message": "角色已更新",
        "role": role.value,
    }


@router.delete("/projects/{project_id}/share/{user_id}", summary="取消共享")
async def remove_project_member(
    project_id: str,
    user_id: int,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    移除项目成员
    需要是项目所有者或管理员，或者用户自己退出
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    # 不能移除所有者
    if user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除项目所有者"
        )

    # 检查权限：管理员可以移除任何成员，普通成员只能移除自己
    if current_user.id != user_id:
        # 需要管理员权限
        project = await require_project_admin(
            project_id=project_id,
            current_user=current_user,
            db=db,
        )

    service = get_project_service(db)
    success = await service.remove_member(
        project_id=project_id,
        user_id=user_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该用户不是项目成员"
        )

    return {
        "success": True,
        "message": "已移除项目成员",
    }


# ==================== 评论管理 ====================

@router.get("/projects/{project_id}/comments", response_model=CommentListResponse, summary="获取评论列表")
async def list_comments(
    project_id: str,
    variant_index: Optional[int] = Query(None, description="筛选指定异文位置的评论"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    获取项目评论列表
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    service = get_project_service(db)
    comments = await service.list_comments(
        project_id=project_id,
        variant_index=variant_index,
        limit=limit,
        offset=offset,
    )

    comment_list = [CommentResponse(**c) for c in comments]
    return CommentListResponse(
        success=True,
        comments=comment_list,
    )


@router.post("/projects/{project_id}/comments", summary="添加评论")
async def add_comment(
    project_id: str,
    request: CommentCreate,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    添加评论
    需要是项目成员
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    service = get_project_service(db)
    comment = await service.add_comment(
        project_id=project_id,
        user_id=current_user.id,
        content=request.content,
        variant_index=request.variant_index,
        parent_id=request.parent_id,
    )

    return {
        "success": True,
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "variant_index": comment.variant_index,
            "parent_id": comment.parent_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        }
    }


@router.put("/projects/{project_id}/comments/{comment_id}", summary="编辑评论")
async def edit_comment(
    project_id: str,
    comment_id: int,
    request: CommentUpdate,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    编辑评论（只能编辑自己的评论）
    """
    # 检查项目访问权限
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    # 检查评论所有权
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.project_id == project_id
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )

    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能编辑自己的评论"
        )

    service = get_project_service(db)
    updated = await service.update_comment(
        comment_id=comment_id,
        content=request.content,
    )

    return {
        "success": True,
        "comment": {
            "id": updated.id,
            "content": updated.content,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
    }


@router.delete("/projects/{project_id}/comments/{comment_id}", summary="删除评论")
async def delete_comment(
    project_id: str,
    comment_id: int,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    删除评论（只能删除自己的评论，管理员可删除任何评论）
    """
    # 检查项目访问权限
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    # 检查评论所有权
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.project_id == project_id
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )

    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能删除自己的评论"
        )

    service = get_project_service(db)
    await service.delete_comment(comment_id)

    return {
        "success": True,
        "message": "评论已删除",
    }


# ==================== 编辑历史 ====================

@router.get("/projects/{project_id}/history", response_model=HistoryListResponse, summary="获取编辑历史")
async def list_edit_history(
    project_id: str,
    action: Optional[str] = Query(None, description="筛选操作类型: create/update/decision/export/delete"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    获取项目编辑历史
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.VIEWER,
    )

    from ....models.collaboration import EditAction

    action_filter = None
    if action:
        try:
            action_filter = EditAction(action)
        except ValueError:
            pass

    service = get_project_service(db)
    history = await service.list_history(
        project_id=project_id,
        action=action_filter,
        limit=limit,
        offset=offset,
    )

    history_list = [HistoryEntry(**h) for h in history]
    return HistoryListResponse(
        success=True,
        history=history_list,
    )
