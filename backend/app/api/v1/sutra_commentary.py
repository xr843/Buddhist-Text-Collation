"""
经论-注疏关联API路由

独立于版本对勘的模块，专门用于：
1. 上传经论原文和注疏文本
2. 自动提取注疏中的引文
3. 建立引文与经论原文的双向关联
4. 支持从经论文本点击跳转到注疏，或从注疏引文跳转到经论原文
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.project_storage import project_storage, ProjectType
from app.services.commentary_service import commentary_service

router = APIRouter()


# ==================== Pydantic 模型 ====================

class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    name: str
    description: Optional[str] = None


class CreateProjectResponse(BaseModel):
    """创建项目响应"""
    id: str
    name: str
    message: str


class ProjectSummary(BaseModel):
    """项目摘要"""
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    sutra_title: Optional[str] = None
    commentary_count: int = 0
    citation_count: int = 0


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    items: List[ProjectSummary]


class SutraUploadResponse(BaseModel):
    """经论上传响应"""
    title: str
    char_count: int
    message: str


class CommentaryInfo(BaseModel):
    """注疏信息"""
    id: str
    title: str
    citations_count: int
    matched_count: int
    upload_time: str


class CommentaryUploadResponse(BaseModel):
    """注疏上传响应"""
    id: str
    title: str
    citations_count: int
    message: str


class CitationMatch(BaseModel):
    """引文匹配结果"""
    position: int
    similarity: float
    matched_text: str


class CitationItem(BaseModel):
    """引文条目"""
    id: str
    marker: str
    extracted_text: str
    context_before: str
    context_after: str
    commentary_id: str
    commentary_title: str
    matched_positions: List[CitationMatch]


class MatchRequest(BaseModel):
    """匹配请求"""
    window_size: int = 15
    threshold: float = 0.7


# ==================== 项目管理 API ====================

@router.post("/projects", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest):
    """
    创建经论-注疏关联项目

    Args:
        request: 包含项目名称和描述

    Returns:
        创建的项目信息
    """
    try:
        # 初始化项目数据结构
        initial_data = {
            "sutra": None,  # 经论原文
            "commentaries": [],  # 注疏列表
            "matches": [],  # 匹配结果缓存
        }

        project = project_storage.create_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            title=request.name,
            description=request.description,
            data=initial_data,
            metadata={
                "sutra_title": None,
                "commentary_count": 0,
                "citation_count": 0,
            }
        )

        return CreateProjectResponse(
            id=project["id"],
            name=project["title"],
            message="项目创建成功"
        )

    except Exception as e:
        print(f"[错误] 创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    获取项目列表

    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        项目列表
    """
    try:
        result = project_storage.list_projects(
            project_type=ProjectType.SUTRA_COMMENTARY,
            limit=limit,
            offset=offset
        )

        items = []
        for item in result["items"]:
            metadata = item.get("metadata", {})
            items.append(ProjectSummary(
                id=item["id"],
                name=item["title"],
                description=item.get("description", ""),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                sutra_title=metadata.get("sutra_title"),
                commentary_count=metadata.get("commentary_count", 0),
                citation_count=metadata.get("citation_count", 0),
            ))

        return ProjectListResponse(
            total=result["total"],
            items=items
        )

    except Exception as e:
        print(f"[错误] 获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """
    获取项目详情

    Args:
        project_id: 项目ID

    Returns:
        项目完整信息
    """
    try:
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        return project

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取项目详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@router.put("/projects/{project_id}")
async def update_project(project_id: str, request: CreateProjectRequest):
    """
    更新项目基本信息

    Args:
        project_id: 项目ID
        request: 更新内容

    Returns:
        更新后的项目信息
    """
    try:
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        updated = project_storage.update_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            project_id=project_id,
            title=request.name,
            description=request.description
        )

        return {"message": "更新成功", "project": updated}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 更新项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目

    Args:
        project_id: 项目ID

    Returns:
        删除结果
    """
    try:
        # 检查项目是否存在
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 删除关联的注疏文件
        commentary_dir = Path("backend/data/sutra_commentary")
        for comm in project["data"].get("commentaries", []):
            comm_file = commentary_dir / f"{project_id}_{comm['id']}.json"
            if comm_file.exists():
                comm_file.unlink()

        # 删除项目
        success = project_storage.delete_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除失败")

        return {"message": "项目已删除"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 删除项目失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 经论管理 API ====================

@router.post("/projects/{project_id}/sutra", response_model=SutraUploadResponse)
async def upload_sutra(
    project_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None)
):
    """
    上传经论原文

    Args:
        project_id: 项目ID
        file: 经论文本文件（.txt）
        title: 经论标题
        source: 来源（如CBETA经号）

    Returns:
        上传结果
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 读取文件
        content = await file.read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('gbk')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="文件编码不支持，请使用UTF-8或GBK编码")

        # 构建经论数据
        sutra_title = title or file.filename or "未命名经论"
        sutra_data = {
            "title": sutra_title,
            "content": text,
            "source": source or "",
            "file_name": file.filename,
            "char_count": len(text),
            "upload_time": datetime.now().isoformat()
        }

        # 更新项目
        project["data"]["sutra"] = sutra_data
        project["metadata"]["sutra_title"] = sutra_title

        project_storage.update_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            project_id=project_id,
            data=project["data"],
            metadata=project["metadata"],
            merge_data=False
        )

        return SutraUploadResponse(
            title=sutra_title,
            char_count=len(text),
            message="经论上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 上传经论失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.put("/projects/{project_id}/sutra")
async def update_sutra(
    project_id: str,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    source: Optional[str] = Form(None)
):
    """
    更新经论信息

    Args:
        project_id: 项目ID
        title: 新标题
        content: 新内容
        source: 新来源

    Returns:
        更新结果
    """
    try:
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        sutra = project["data"].get("sutra")
        if not sutra:
            raise HTTPException(status_code=400, detail="项目尚未上传经论")

        if title:
            sutra["title"] = title
            project["metadata"]["sutra_title"] = title
        if content:
            sutra["content"] = content
            sutra["char_count"] = len(content)
        if source:
            sutra["source"] = source

        project["data"]["sutra"] = sutra

        project_storage.update_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            project_id=project_id,
            data=project["data"],
            metadata=project["metadata"],
            merge_data=False
        )

        return {"message": "经论更新成功", "sutra": sutra}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 更新经论失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# ==================== 注疏管理 API ====================

@router.post("/projects/{project_id}/commentary", response_model=CommentaryUploadResponse)
async def upload_commentary(
    project_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    marker_patterns: Optional[str] = Form(None)
):
    """
    上传注疏文本并自动提取引文

    Args:
        project_id: 项目ID
        file: 注疏文本文件（.txt）
        title: 注疏标题
        marker_patterns: 自定义标记词（逗号分隔，如："论云,论曰,经云"）

    Returns:
        上传结果和引文提取统计
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 读取文件
        content = await file.read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('gbk')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="文件编码不支持，请使用UTF-8或GBK编码")

        # 提取引文
        custom_markers = None
        if marker_patterns:
            custom_markers = [
                f"{m.strip()}[:：]?\\s*"
                for m in marker_patterns.split(',')
                if m.strip()
            ]

        citations = commentary_service.extract_citations(
            text=text,
            marker_patterns=custom_markers
        )

        # 生成注疏ID
        commentary_id = f"comm_{uuid.uuid4().hex[:8]}"

        # 构建注疏数据
        commentary_title = title or file.filename or "未命名注疏"
        commentary_data = {
            "id": commentary_id,
            "title": commentary_title,
            "content": text,
            "file_name": file.filename,
            "citations": [cit.to_dict() for cit in citations],
            "citations_count": len(citations),
            "matched_count": 0,
            "upload_time": datetime.now().isoformat()
        }

        # 保存注疏数据到文件
        commentary_dir = Path("backend/data/sutra_commentary")
        commentary_dir.mkdir(parents=True, exist_ok=True)

        commentary_file = commentary_dir / f"{project_id}_{commentary_id}.json"
        with open(commentary_file, 'w', encoding='utf-8') as f:
            json.dump(commentary_data, f, ensure_ascii=False, indent=2)

        # 更新项目中的注疏列表
        if "commentaries" not in project["data"]:
            project["data"]["commentaries"] = []

        project["data"]["commentaries"].append({
            "id": commentary_id,
            "title": commentary_title,
            "citations_count": len(citations),
            "matched_count": 0,
            "upload_time": commentary_data["upload_time"]
        })

        # 更新元数据
        total_citations = sum(
            c.get("citations_count", 0)
            for c in project["data"]["commentaries"]
        )
        project["metadata"]["commentary_count"] = len(project["data"]["commentaries"])
        project["metadata"]["citation_count"] = total_citations

        project_storage.update_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            project_id=project_id,
            data=project["data"],
            metadata=project["metadata"],
            merge_data=False
        )

        return CommentaryUploadResponse(
            id=commentary_id,
            title=commentary_title,
            citations_count=len(citations),
            message=f"成功提取 {len(citations)} 条引文"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 上传注疏失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/projects/{project_id}/commentary")
async def list_commentaries(project_id: str):
    """
    获取项目关联的注疏列表

    Args:
        project_id: 项目ID

    Returns:
        注疏列表
    """
    try:
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        commentaries = project["data"].get("commentaries", [])

        return {"commentaries": commentaries, "total": len(commentaries)}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取注疏列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/projects/{project_id}/commentary/{commentary_id}")
async def get_commentary(project_id: str, commentary_id: str):
    """
    获取注疏详情（包含引文列表）

    Args:
        project_id: 项目ID
        commentary_id: 注疏ID

    Returns:
        注疏完整信息
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 读取注疏文件
        commentary_file = Path(f"backend/data/sutra_commentary/{project_id}_{commentary_id}.json")
        if not commentary_file.exists():
            raise HTTPException(status_code=404, detail="注疏不存在")

        with open(commentary_file, 'r', encoding='utf-8') as f:
            commentary_data = json.load(f)

        return commentary_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取注疏详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/projects/{project_id}/commentary/{commentary_id}")
async def delete_commentary(project_id: str, commentary_id: str):
    """
    删除注疏

    Args:
        project_id: 项目ID
        commentary_id: 注疏ID

    Returns:
        删除结果
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 从项目中移除注疏记录
        commentaries = project["data"].get("commentaries", [])
        updated_commentaries = [c for c in commentaries if c["id"] != commentary_id]

        if len(updated_commentaries) == len(commentaries):
            raise HTTPException(status_code=404, detail="注疏不存在")

        project["data"]["commentaries"] = updated_commentaries

        # 更新元数据
        total_citations = sum(
            c.get("citations_count", 0)
            for c in updated_commentaries
        )
        project["metadata"]["commentary_count"] = len(updated_commentaries)
        project["metadata"]["citation_count"] = total_citations

        project_storage.update_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            project_id=project_id,
            data=project["data"],
            metadata=project["metadata"],
            merge_data=False
        )

        # 删除注疏文件
        commentary_file = Path(f"backend/data/sutra_commentary/{project_id}_{commentary_id}.json")
        if commentary_file.exists():
            commentary_file.unlink()

        return {"message": f"注疏 {commentary_id} 已删除"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 删除注疏失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 匹配功能 API ====================

@router.post("/projects/{project_id}/match")
async def execute_match(
    project_id: str,
    window_size: int = Query(15, description="匹配窗口大小"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值")
):
    """
    执行引文与经论的批量匹配

    Args:
        project_id: 项目ID
        window_size: 匹配窗口大小
        threshold: 相似度阈值

    Returns:
        匹配统计
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取经论文本
        sutra = project["data"].get("sutra")
        if not sutra or not sutra.get("content"):
            raise HTTPException(status_code=400, detail="项目尚未上传经论")

        sutra_text = sutra["content"]

        # 规范化经论文本
        from app.services.collation_service import collation_service
        sutra_normalized = collation_service.normalize_text_for_comparison(sutra_text)

        # 遍历所有注疏进行匹配
        commentary_dir = Path("backend/data/sutra_commentary")
        total_citations = 0
        matched_citations = 0

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["id"]
            comm_file = commentary_dir / f"{project_id}_{comm_id}.json"

            if comm_file.exists():
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)

                updated_citations = []
                comm_matched = 0

                for cit in comm_data.get("citations", []):
                    total_citations += 1

                    # 匹配引文到经论
                    matched_positions = _match_citation_to_sutra(
                        citation_text=cit["extracted_text"],
                        sutra_text=sutra_normalized,
                        window_size=window_size,
                        threshold=threshold
                    )

                    cit["matched_positions"] = matched_positions
                    updated_citations.append(cit)

                    if matched_positions:
                        matched_citations += 1
                        comm_matched += 1

                # 更新注疏文件
                comm_data["citations"] = updated_citations
                comm_data["last_matched"] = datetime.now().isoformat()

                with open(comm_file, 'w', encoding='utf-8') as f:
                    json.dump(comm_data, f, ensure_ascii=False, indent=2)

                # 更新项目中的注疏匹配计数
                for c in project["data"]["commentaries"]:
                    if c["id"] == comm_id:
                        c["matched_count"] = comm_matched
                        break

        # 保存项目更新
        project_storage.update_project(
            project_type=ProjectType.SUTRA_COMMENTARY,
            project_id=project_id,
            data=project["data"],
            merge_data=False
        )

        return {
            "total_citations": total_citations,
            "matched_count": matched_citations,
            "match_rate": round(matched_citations / total_citations * 100, 2) if total_citations > 0 else 0,
            "message": f"匹配完成：{matched_citations}/{total_citations} 条引文已匹配"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 执行匹配失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.get("/projects/{project_id}/citations")
async def get_all_citations(
    project_id: str,
    commentary_id: Optional[str] = Query(None, description="筛选特定注疏"),
    matched_only: bool = Query(False, description="仅返回已匹配的引文")
):
    """
    获取所有引文及其匹配结果

    Args:
        project_id: 项目ID
        commentary_id: 可选，筛选特定注疏的引文
        matched_only: 是否仅返回已匹配的引文

    Returns:
        引文列表
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 加载注疏引文
        commentary_dir = Path("backend/data/sutra_commentary")
        all_citations = []

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["id"]

            # 筛选特定注疏
            if commentary_id and comm_id != commentary_id:
                continue

            comm_file = commentary_dir / f"{project_id}_{comm_id}.json"

            if comm_file.exists():
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)

                for cit in comm_data.get("citations", []):
                    # 筛选已匹配
                    if matched_only and not cit.get("matched_positions"):
                        continue

                    all_citations.append({
                        **cit,
                        "commentary_id": comm_id,
                        "commentary_title": comm_info.get("title", "未知注疏")
                    })

        return {
            "citations": all_citations,
            "total": len(all_citations),
            "matched_count": sum(1 for c in all_citations if c.get("matched_positions"))
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取引文失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/projects/{project_id}/position/{position}")
async def get_citations_at_position(
    project_id: str,
    position: int,
    window_size: int = Query(20, description="查询窗口大小")
):
    """
    根据经论位置反查关联的引文（用于从经论跳转到注疏）

    Args:
        project_id: 项目ID
        position: 经论中的字符位置（1-based）
        window_size: 查询窗口大小

    Returns:
        该位置关联的引文列表
    """
    try:
        # 验证项目
        project = project_storage.get_project(ProjectType.SUTRA_COMMENTARY, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 加载所有注疏引文，查找覆盖该位置的引文
        commentary_dir = Path("backend/data/sutra_commentary")
        matches = []

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["id"]
            comm_file = commentary_dir / f"{project_id}_{comm_id}.json"

            if comm_file.exists():
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)

                for cit in comm_data.get("citations", []):
                    matched_positions = cit.get("matched_positions", [])

                    for match in matched_positions:
                        match_pos = match.get("position", 0)
                        match_len = len(match.get("matched_text", ""))

                        # 检查位置是否在匹配范围内
                        if match_pos <= position <= match_pos + match_len + window_size:
                            matches.append({
                                "citation_id": cit["id"],
                                "commentary_id": comm_id,
                                "commentary_title": comm_info.get("title", "未知注疏"),
                                "marker": cit["marker"],
                                "extracted_text": cit["extracted_text"],
                                "context_before": cit.get("context_before", ""),
                                "context_after": cit.get("context_after", ""),
                                "match_position": match_pos,
                                "similarity": match.get("similarity", 0),
                                "matched_text": match.get("matched_text", "")
                            })

        # 按相似度排序
        matches.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "position": position,
            "citations": matches,
            "count": len(matches)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 位置反查失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 工具函数 ====================

def _match_citation_to_sutra(
    citation_text: str,
    sutra_text: str,
    window_size: int = 15,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    将引文匹配到经论文本的位置

    Args:
        citation_text: 引文文本
        sutra_text: 经论文本（已规范化）
        window_size: 窗口大小
        threshold: 相似度阈值

    Returns:
        匹配位置列表
    """
    from app.services.collation_service import collation_service
    from app.services.collation.text_normalizer import extract_clean_text_with_mapping

    matches = []

    # 规范化引文
    citation_normalized = collation_service.normalize_text_for_comparison(citation_text)

    # 去除引文中的标点
    citation_clean, _ = extract_clean_text_with_mapping(citation_normalized)

    # 处理"(至)"格式的范围引用
    if "..." in citation_clean:
        return _match_range_citation(citation_clean, sutra_text, window_size, threshold)

    citation_len = len(citation_clean)

    if citation_len < 3:
        return []

    # 滑动窗口匹配
    step = max(1, window_size // 3)
    for pos in range(0, len(sutra_text) - min(citation_len, len(sutra_text)) + 1, step):
        window_text = sutra_text[pos:pos + citation_len + window_size]

        similarity = collation_service._compute_similarity(citation_clean, window_text)

        if similarity >= threshold:
            # 避免重复添加相近位置
            is_duplicate = any(
                abs(m["position"] - (pos + 1)) < window_size
                for m in matches
            )

            if not is_duplicate:
                matches.append({
                    "position": pos + 1,  # 转为1-based
                    "similarity": round(similarity, 4),
                    "matched_text": sutra_text[pos:pos + citation_len]
                })

    # 按相似度排序
    matches.sort(key=lambda x: x["similarity"], reverse=True)

    return matches[:10]


def _match_range_citation(
    citation_text: str,
    sutra_text: str,
    window_size: int = 15,
    threshold: float = 0.5  # 降低阈值，因为古文异体字多
) -> List[Dict[str, Any]]:
    """
    匹配"首...尾"格式的范围引用

    改进策略：
    1. 先用首部文本进行快速定位
    2. 支持部分匹配（首部前几个字匹配即可）
    3. 动态调整尾部搜索范围
    """
    from app.services.collation_service import collation_service

    matches = []

    parts = citation_text.split("...")
    if len(parts) != 2:
        return []

    start_text = parts[0].strip()
    end_text = parts[1].strip()

    if len(start_text) < 2 or len(end_text) < 2:
        return []

    # 动态设置搜索范围：根据引文长度调整
    max_range = max(300, len(start_text) * 20)  # 至少300字，或首部文本长度的20倍
    start_len = len(start_text)
    end_len = len(end_text)

    # 策略1: 精确匹配首部前几个关键字
    # 取首部的前3-5个字作为锚点
    anchor_len = min(5, max(3, start_len // 2))
    anchor_text = start_text[:anchor_len]

    # 快速定位锚点位置
    anchor_positions = []
    pos = 0
    while True:
        idx = sutra_text.find(anchor_text, pos)
        if idx == -1:
            break
        anchor_positions.append(idx)
        pos = idx + 1

    # 如果精确匹配找不到，尝试模糊匹配
    if not anchor_positions:
        # 使用滑动窗口进行模糊匹配
        step = max(1, start_len // 2)
        for pos in range(0, len(sutra_text) - start_len + 1, step):
            window = sutra_text[pos:pos + start_len]
            similarity = collation_service._compute_similarity(start_text, window)
            if similarity >= threshold:
                anchor_positions.append(pos)

    # 对每个锚点位置进行完整匹配
    for anchor_pos in anchor_positions:
        # 验证首部匹配
        start_window = sutra_text[anchor_pos:anchor_pos + start_len + 3]  # 多取3字容错
        start_similarity = collation_service._compute_similarity(start_text, start_window[:start_len])

        if start_similarity < threshold:
            continue

        # 搜索尾部
        search_start = anchor_pos + start_len
        search_end = min(anchor_pos + max_range, len(sutra_text))

        best_end_match = None
        best_end_similarity = 0

        # 从后向前搜索尾部（通常尾部在较远处）
        for end_pos in range(search_end - end_len, search_start, -1):
            end_window = sutra_text[end_pos:end_pos + end_len]
            end_similarity = collation_service._compute_similarity(end_text, end_window)

            if end_similarity >= threshold and end_similarity > best_end_similarity:
                best_end_similarity = end_similarity
                best_end_match = end_pos
                if end_similarity >= 0.9:  # 找到高质量匹配就停止
                    break

        if best_end_match is not None:
            overall_similarity = (start_similarity + best_end_similarity) / 2
            matched_full = sutra_text[anchor_pos:best_end_match + end_len]

            # 去重
            is_duplicate = any(
                abs(m["position"] - (anchor_pos + 1)) < window_size
                for m in matches
            )

            if not is_duplicate:
                matches.append({
                    "position": anchor_pos + 1,  # 1-based
                    "similarity": round(overall_similarity, 4),
                    "matched_text": matched_full[:80] + ("..." if len(matched_full) > 80 else "")
                })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches[:5]  # 返回最多5个最佳匹配
