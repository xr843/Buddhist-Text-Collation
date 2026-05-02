"""
两版本对勘项目管理路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.project_storage import project_storage, ProjectType, ProjectStatus

from .models import ProjectUpdateRequest

router = APIRouter()


@router.get("/two-version/projects")
async def list_two_version_projects(
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """获取两版本对勘项目列表"""
    try:
        project_status = None
        if status:
            try:
                project_status = ProjectStatus(status)
            except ValueError:
                pass

        result = project_storage.list_projects(
            ProjectType.TWO_VERSION,
            status=project_status,
            limit=limit,
            offset=offset,
        )
        return {"success": True, "total": result["total"], "items": result["items"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/two-version/projects/{project_id}")
async def get_two_version_project(project_id: str):
    """获取两版本对勘项目详情"""
    try:
        project = project_storage.get_project(ProjectType.TWO_VERSION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@router.put("/two-version/projects/{project_id}")
async def update_two_version_project(project_id: str, request: ProjectUpdateRequest):
    """更新两版本对勘项目信息"""
    try:
        project = project_storage.update_project(
            ProjectType.TWO_VERSION, project_id,
            title=request.title, description=request.description,
        )
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        return {
            "success": True,
            "project": {
                "id": project["id"],
                "title": project["title"],
                "description": project.get("description", ""),
                "updated_at": project["updated_at"],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新项目失败: {str(e)}")


@router.delete("/two-version/projects/{project_id}")
async def delete_two_version_project(project_id: str):
    """删除两版本对勘项目"""
    try:
        success = project_storage.delete_project(ProjectType.TWO_VERSION, project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        return {"success": True, "message": f"项目已删除: {project_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")
