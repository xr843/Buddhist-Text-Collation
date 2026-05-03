"""
版本谱系树标准格式导出路由（Newick / NEXUS）。

让 UPGMA 结果能直接进 FigTree、SplitsTree、Bio.Phylo 等学术工具链。
"""
from __future__ import annotations

import time
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.phylogeny_service import phylogeny_service
from app.services.project_storage import project_storage, ProjectType

router = APIRouter()


class PhylogenyExportRequest(BaseModel):
    project_id: str = Field(..., description="多校项目 ID")
    format: Literal["newick", "nexus"] = Field("newick")
    tree_name: str = Field("phylogeny", max_length=64)


def _extract_phylogeny(project: dict) -> tuple[dict, Optional[dict]]:
    """从项目结构里取 (tree, similarity_matrix)；任一缺失抛 404。"""
    data = (project.get("data") if isinstance(project, dict) else None) or {}
    nested_analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else {}
    candidates = [
        data.get("phylogeny"),
        data.get("phylogeny_analysis"),
        nested_analysis.get("phylogeny"),
    ]
    payload = next((c for c in candidates if isinstance(c, dict) and c.get("tree")), None)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该项目尚未生成版本谱系；请先在多校页面运行谱系分析。",
        )
    return payload["tree"], payload.get("similarity_matrix")


@router.post("/phylogeny/export")
async def export_phylogeny(request: PhylogenyExportRequest):
    """导出 Newick 或 NEXUS。两种格式都能用 FigTree 直接打开。"""
    project = project_storage.get_project(ProjectType.MULTI_COLLATION, request.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目不存在: {request.project_id}",
        )

    tree, similarity_matrix = _extract_phylogeny(project)

    if request.format == "newick":
        content = phylogeny_service.to_newick(tree)
        content_type = "text/x-nh; charset=utf-8"
        file_ext = "nwk"
    else:
        content = phylogeny_service.to_nexus(
            tree, similarity_matrix=similarity_matrix, tree_name=request.tree_name
        )
        content_type = "text/x-nexus; charset=utf-8"
        file_ext = "nex"

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"phylogeny_{request.project_id}_{timestamp}.{file_ext}"

    return {
        "success": True,
        "format": request.format,
        "content": content,
        "content_type": content_type,
        "filename": filename,
    }
