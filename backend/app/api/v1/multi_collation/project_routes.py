"""
项目管理路由
从 multi_collation.py 中提取
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from app.services.project_storage import project_storage, ProjectType, ProjectStatus

from .models import ProjectUpdateRequest, UpdateCanonLocationsRequest
from .phylogeny_utils import enrich_phylogeny_with_locations

router = APIRouter()


@router.get("/projects")
async def list_projects(
    status: Optional[str] = Query(None, description="筛选状态：draft/in_progress/completed"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取多版本对勘项目列表

    返回项目摘要信息（不含完整数据），按更新时间倒序排列。
    """
    try:
        # 转换状态参数
        project_status = None
        if status:
            try:
                project_status = ProjectStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的状态值: {status}"
                )

        result = project_storage.list_projects(
            ProjectType.MULTI_COLLATION,
            status=project_status,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "total": result["total"],
            "items": result["items"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}"
        )


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """
    获取项目详情

    返回完整的项目数据，包括对勘结果、异文汇校表等。
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        # 兼容历史项目：动态补齐地理位置信息（不落盘）
        try:
            phylogeny = project.get("data", {}).get("phylogeny")
            base_name = project.get("data", {}).get("base", {}).get("name", "") or project.get("metadata", {}).get("base_name", "")
            canon_locations_override = project.get("data", {}).get("canon_locations_override", {}) or {}
            if isinstance(phylogeny, dict):
                project["data"]["phylogeny"] = enrich_phylogeny_with_locations(
                    phylogeny, canon_locations_override, base_name=base_name
                )
        except Exception:
            pass

        return {
            "success": True,
            "project": project,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目详情失败: {str(e)}"
        )


@router.put("/projects/{project_id}")
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """
    更新项目信息

    支持更新项目标题和描述。
    """
    try:
        project = project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            title=request.title,
            description=request.description,
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        return {
            "success": True,
            "project": {
                "id": project["id"],
                "title": project["title"],
                "description": project.get("description", ""),
                "updated_at": project["updated_at"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新项目失败: {str(e)}"
        )


@router.post("/projects/{project_id}/canon-locations")
async def upsert_canon_locations(project_id: str, request: UpdateCanonLocationsRequest):
    """
    更新项目的版本地理位置信息（用于"地理分布图"）

    - locations: { 版本全名: 位置信息 }
    - 会保存到 project.data.canon_locations_override
    - 返回谱系数据中合并后的 canon_locations
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        override = project.get("data", {}).get("canon_locations_override", {}) or {}
        for name, loc in (request.locations or {}).items():
            override[name] = loc.model_dump()

        project["data"]["canon_locations_override"] = override

        phylogeny = project.get("data", {}).get("phylogeny")
        if isinstance(phylogeny, dict):
            base_name = project.get("data", {}).get("base", {}).get("name", "") or project.get("metadata", {}).get("base_name", "")
            project["data"]["phylogeny"] = enrich_phylogeny_with_locations(
                phylogeny, override, base_name=base_name
            )

        updated_project = project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data=project["data"],
            metadata=project.get("metadata", {}),
            merge_data=False,
        )

        canon_locations = {}
        try:
            canon_locations = (
                updated_project.get("data", {})
                .get("phylogeny", {})
                .get("canon_locations", {})
            )
        except Exception:
            canon_locations = {}

        return {
            "success": True,
            "canon_locations": canon_locations,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新地理位置信息失败: {str(e)}"
        )


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目

    删除后不可恢复。
    """
    try:
        success = project_storage.delete_project(ProjectType.MULTI_COLLATION, project_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        return {
            "success": True,
            "message": f"项目已删除: {project_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除项目失败: {str(e)}"
        )
