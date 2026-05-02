"""
协作项目API路由
支持数据库存储和权限控制
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ....core.database import get_db
from ....core.deps import (
    get_current_user_db,
    get_current_user_db_optional,
    get_project_with_permission,
    check_project_owner,
    get_user_role_in_project,
)
from ....models.user import User
from ....models.collaboration import (
    CollabProject,
    CollabProjectType,
    CollabProjectStatus,
    ProjectVisibility,
    MemberRole,
)
from ....services.project_db_service import get_project_service
from .schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectDataUpdate,
    ProjectListResponse,
    ProjectSummary,
    ProjectDetail,
    MessageResponse,
)
from ..multi_collation.phylogeny_utils import enrich_phylogeny_with_locations, enrich_phylogeny_with_lineage

router = APIRouter()


def parse_project_type(type_str: Optional[str]) -> Optional[CollabProjectType]:
    """解析项目类型字符串"""
    if not type_str:
        return None
    try:
        return CollabProjectType(type_str)
    except ValueError:
        return None


def parse_project_status(status_str: Optional[str]) -> Optional[CollabProjectStatus]:
    """解析项目状态字符串"""
    if not status_str:
        return None
    try:
        return CollabProjectStatus(status_str)
    except ValueError:
        return None


def parse_visibility(vis_str: Optional[str]) -> Optional[ProjectVisibility]:
    """解析可见性字符串"""
    if not vis_str:
        return None
    try:
        return ProjectVisibility(vis_str)
    except ValueError:
        return None


@router.get("/projects", response_model=ProjectListResponse, summary="获取我的项目列表")
async def list_my_projects(
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选: draft/in_progress/completed"),
    visibility: Optional[str] = Query(None, description="可见性筛选: private/shared/public"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户拥有的项目列表
    """
    service = get_project_service(db)
    result = await service.list_user_owned_projects(
        user_id=current_user.id,
        project_type=parse_project_type(project_type),
        status=parse_project_status(status),
        limit=limit,
        offset=offset,
    )

    items = [ProjectSummary(**item) for item in result["items"]]
    return ProjectListResponse(
        success=True,
        total=result["total"],
        items=items,
    )


@router.get("/projects/shared", response_model=ProjectListResponse, summary="获取共享给我的项目")
async def list_shared_projects(
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    获取共享给当前用户的项目列表（不包括自己拥有的）
    """
    service = get_project_service(db)
    result = await service.list_shared_with_user(
        user_id=current_user.id,
        project_type=parse_project_type(project_type),
        limit=limit,
        offset=offset,
    )

    items = [ProjectSummary(**item) for item in result["items"]]
    return ProjectListResponse(
        success=True,
        total=result["total"],
        items=items,
    )


@router.get("/projects/all", response_model=ProjectListResponse, summary="获取所有可访问的项目")
async def list_all_accessible_projects(
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: Optional[User] = Depends(get_current_user_db_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户可访问的所有项目（包括自己的、共享的、公开的）
    未登录用户只能看到公开项目
    """
    service = get_project_service(db)

    if current_user:
        result = await service.list_projects(
            user_id=current_user.id,
            project_type=parse_project_type(project_type),
            status=parse_project_status(status),
            include_shared=True,
            limit=limit,
            offset=offset,
        )
    else:
        # 未登录只能看公开项目
        result = await service.list_projects(
            project_type=parse_project_type(project_type),
            status=parse_project_status(status),
            visibility=ProjectVisibility.PUBLIC,
            limit=limit,
            offset=offset,
        )

    items = [ProjectSummary(**item) for item in result["items"]]
    return ProjectListResponse(
        success=True,
        total=result["total"],
        items=items,
    )


@router.post("/projects", summary="创建项目")
async def create_project(
    request: ProjectCreate,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的协作项目
    """
    service = get_project_service(db)

    project_type = parse_project_type(request.project_type)
    if not project_type:
        project_type = CollabProjectType.MULTI_COLLATION

    visibility = parse_visibility(request.visibility)
    if not visibility:
        visibility = ProjectVisibility.PRIVATE

    project = await service.create_project(
        owner_id=current_user.id,
        title=request.title,
        description=request.description,
        project_type=project_type,
        visibility=visibility,
    )

    return {
        "success": True,
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "project_type": project.project_type.value if project.project_type else None,
            "visibility": project.visibility.value if project.visibility else None,
            "status": project.status.value if project.status else None,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        }
    }


@router.get("/projects/{project_id}", summary="获取项目详情")
async def get_project_detail(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user_db_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    获取项目详情，包含完整的项目数据
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=None,  # 只要能访问就行
    )

    # 获取用户角色
    my_role = None
    if current_user:
        my_role = await get_user_role_in_project(project, current_user, db)

    # 获取成员列表
    service = get_project_service(db)
    members = await service.list_members(project_id)

    # 兼容历史项目：补齐地理位置和版本源流
    data = project.data or {}
    try:
        phylogeny = data.get("phylogeny")
        base_name = data.get("base", {}).get("name", "") or (project.project_meta or {}).get("base_name", "")
        canon_locations_override = data.get("canon_locations_override", {}) or {}

        if isinstance(phylogeny, dict):
            phylogeny = enrich_phylogeny_with_locations(
                phylogeny, canon_locations_override, base_name=base_name
            )
            if 'lineage' not in phylogeny:
                phylogeny = enrich_phylogeny_with_lineage(phylogeny)
            data["phylogeny"] = phylogeny
    except Exception:
        pass

    return {
        "success": True,
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "project_type": project.project_type.value if project.project_type else None,
            "visibility": project.visibility.value if project.visibility else None,
            "status": project.status.value if project.status else None,
            "owner_id": project.owner_id,
            "data": data,
            "metadata": project.project_meta or {},
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "members": members,
            "my_role": my_role,
        }
    }


@router.put("/projects/{project_id}", summary="更新项目信息")
async def update_project_info(
    project_id: str,
    request: ProjectUpdate,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    更新项目基本信息（标题、描述、状态、可见性）
    需要编辑权限
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.EDITOR,
    )

    service = get_project_service(db)

    updated = await service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        status=parse_project_status(request.status),
        visibility=parse_visibility(request.visibility),
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )

    return {
        "success": True,
        "project": {
            "id": updated.id,
            "title": updated.title,
            "description": updated.description,
            "status": updated.status.value if updated.status else None,
            "visibility": updated.visibility.value if updated.visibility else None,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
    }


@router.put("/projects/{project_id}/data", summary="更新项目数据")
async def update_project_data(
    project_id: str,
    request: ProjectDataUpdate,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    更新项目核心数据（校勘数据等）
    需要编辑权限
    """
    project = await get_project_with_permission(
        project_id=project_id,
        current_user=current_user,
        db=db,
        required_role=MemberRole.EDITOR,
    )

    service = get_project_service(db)

    updated = await service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        data=request.data,
        metadata=request.metadata,
        merge_data=request.merge,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )

    return {
        "success": True,
        "message": "数据更新成功",
        "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
    }


@router.put("/projects/{project_id}/visibility", summary="设置项目可见性")
async def set_project_visibility(
    project_id: str,
    visibility: str = Query(..., description="可见性: private/shared/public"),
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    设置项目可见性
    只有所有者可以修改
    """
    project = await check_project_owner(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    vis = parse_visibility(visibility)
    if not vis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的可见性值: {visibility}"
        )

    service = get_project_service(db)
    updated = await service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        visibility=vis,
    )

    return {
        "success": True,
        "visibility": vis.value,
    }


@router.delete("/projects/{project_id}", summary="删除项目")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    """
    删除项目（只有所有者可以删除）
    """
    project = await check_project_owner(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    service = get_project_service(db)
    success = await service.delete_project(project_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )

    return {
        "success": True,
        "message": f"项目已删除: {project_id}",
    }
