"""
标点版本对比项目管理路由

包含：
- 标点版本对比项目CRUD
- 标点判取保存与获取
- 标点定本生成
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.project_storage import project_storage, ProjectType, ProjectStatus

from .models import ProjectUpdateRequest, PunctuationDecisionsRequest
from .definitive_generator import generate_punctuation_definitive_text

router = APIRouter()


@router.get("/punctuation/projects")
async def list_punctuation_projects(
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """获取标点版本对比项目列表"""
    try:
        project_status = None
        if status:
            try:
                project_status = ProjectStatus(status)
            except ValueError:
                pass

        result = project_storage.list_projects(
            ProjectType.PUNCTUATION,
            status=project_status,
            limit=limit,
            offset=offset,
        )
        return {"success": True, "total": result["total"], "items": result["items"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/punctuation/projects/{project_id}")
async def get_punctuation_project(project_id: str):
    """获取标点版本对比项目详情"""
    try:
        project = project_storage.get_project(ProjectType.PUNCTUATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@router.put("/punctuation/projects/{project_id}")
async def update_punctuation_project(project_id: str, request: ProjectUpdateRequest):
    """更新标点版本对比项目信息"""
    try:
        project = project_storage.update_project(
            ProjectType.PUNCTUATION, project_id,
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


@router.delete("/punctuation/projects/{project_id}")
async def delete_punctuation_project(project_id: str):
    """删除标点版本对比项目"""
    try:
        success = project_storage.delete_project(ProjectType.PUNCTUATION, project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
        return {"success": True, "message": f"项目已删除: {project_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


# ==================== 标点判取与定本生成 ====================

@router.post("/punctuation/projects/{project_id}/decisions")
async def save_punctuation_decisions(project_id: str, request: PunctuationDecisionsRequest):
    """
    保存标点判取结果

    将用户对标点差异的判取决定保存到项目中。
    """
    try:
        # 获取项目
        project = project_storage.get_project(ProjectType.PUNCTUATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

        # 更新项目数据中的判取结果
        if "data" not in project:
            project["data"] = {}
        project["data"]["decisions"] = request.decisions

        # 保存更新后的项目
        updated_project = project_storage.update_project_data(
            ProjectType.PUNCTUATION,
            project_id,
            project["data"]
        )

        if not updated_project:
            raise HTTPException(status_code=500, detail="保存判取结果失败")

        return {
            "success": True,
            "message": f"已保存 {len(request.decisions)} 条判取结果",
            "decision_count": len(request.decisions),
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[保存标点判取] 错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"保存判取结果失败: {str(e)}")


@router.get("/punctuation/projects/{project_id}/decisions")
async def get_punctuation_decisions(project_id: str):
    """
    获取标点判取结果
    """
    try:
        project = project_storage.get_project(ProjectType.PUNCTUATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

        decisions = project.get("data", {}).get("decisions", {})

        return {
            "success": True,
            "decisions": decisions,
            "decision_count": len(decisions),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取判取结果失败: {str(e)}")


@router.post("/punctuation/projects/{project_id}/generate-definitive")
async def generate_punctuation_definitive(project_id: str):
    """
    生成标点定本

    基于版本1的文本和判取结果，生成标点定本。
    对于判取为version2的差异，将版本1的标点替换为版本2的标点。

    返回:
    - text: 定本文本
    - notes: 标点改易记
    - statistics: 统计信息
    """
    try:
        # 1. 获取项目数据
        project = project_storage.get_project(ProjectType.PUNCTUATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

        # 2. 提取必要数据
        data = project.get("data", {})
        result = data.get("result", {})
        decisions = data.get("decisions", {})

        text1 = result.get("text1", "")
        text2 = result.get("text2", "")
        version1_name = result.get("version1_name", "版本1")
        version2_name = result.get("version2_name", "版本2")

        # 获取标点差异列表
        punct_analysis = result.get("punctuation_analysis", {})
        differences = punct_analysis.get("differences", [])

        if not text1:
            raise HTTPException(status_code=400, detail="项目缺少版本1文本")

        if not decisions:
            raise HTTPException(status_code=400, detail="没有判取结果，请先进行标点判取")

        # 3. 生成定本
        definitive_result = generate_punctuation_definitive_text(
            base_text=text1,
            other_text=text2,
            differences=differences,
            decisions=decisions,
            version1_name=version1_name,
            version2_name=version2_name,
        )

        return {
            "success": True,
            **definitive_result
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[生成标点定本] 错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成标点定本失败: {str(e)}")
