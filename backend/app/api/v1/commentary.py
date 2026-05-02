"""
注疏引证API路由 - 上传注疏、提取引文、匹配异文位置
"""
import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.commentary_service import commentary_service
from app.services.file_parser import file_parser_service
from app.services.project_storage import project_storage, ProjectType

router = APIRouter()


# ==================== Pydantic 模型 ====================

class CommentaryUploadResponse(BaseModel):
    """注疏上传响应"""
    commentary_id: str
    title: str
    citations_count: int
    message: str


class CommentaryMatchRequest(BaseModel):
    """注疏匹配请求"""
    position: int
    window_size: int = 10
    threshold: float = 0.75


class CommentaryListResponse(BaseModel):
    """注疏列表响应"""
    commentaries: List[Dict[str, Any]]


# ==================== API 端点 ====================

@router.post("/projects/{project_id}/commentary/upload")
async def upload_commentary(
    project_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    target_sutra: Optional[str] = Form(None),
    marker_patterns: Optional[str] = Form(None)
):
    """
    上传注疏文献并自动提取引文

    Args:
        project_id: 项目ID
        file: 注疏文本文件（.txt）
        title: 注疏标题
        source: 版本来源
        target_sutra: 目标经典
        marker_patterns: 自定义标记词（逗号分隔，如："论云,论曰,经云"）

    Returns:
        注疏ID和提取统计
    """
    try:
        # 1. 验证项目是否存在
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 读取文件内容
        content = await file.read()

        # 尝试UTF-8解码
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # 回退到GBK
            try:
                text = content.decode('gbk')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="文件编码不支持，请使用UTF-8或GBK编码")

        # 3. 提取引文
        custom_markers = None
        if marker_patterns:
            # 解析自定义标记词（逗号分隔）
            custom_markers = [
                f"{m.strip()}[:：]?\\s*"
                for m in marker_patterns.split(',')
                if m.strip()
            ]

        citations = commentary_service.extract_citations(
            text=text,
            marker_patterns=custom_markers
        )

        # 4. 生成注疏ID
        commentary_id = f"comm_{uuid.uuid4().hex[:8]}"

        # 5. 构建注疏数据
        commentary_data = {
            "commentary_id": commentary_id,
            "title": title or file.filename,
            "source": source or "未知",
            "target_sutra": target_sutra or "未知",
            "file_name": file.filename,
            "citations": [cit.to_dict() for cit in citations],
            "citations_count": len(citations),
            "indexed": True,
            "created_at": datetime.now().isoformat()
        }

        # 6. 保存注疏数据到文件
        commentary_dir = os.path.join("backend", "data", "commentaries")
        os.makedirs(commentary_dir, exist_ok=True)

        commentary_file = os.path.join(
            commentary_dir,
            f"{project_id}_commentary_{commentary_id}.json"
        )

        with open(commentary_file, 'w', encoding='utf-8') as f:
            json.dump(commentary_data, f, ensure_ascii=False, indent=2)

        # 7. 在项目中记录注疏关联
        if "commentaries" not in project["data"]:
            project["data"]["commentaries"] = []

        project["data"]["commentaries"].append({
            "commentary_id": commentary_id,
            "title": commentary_data["title"],
            "citations_count": len(citations)
        })

        project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data=project["data"]
        )

        return CommentaryUploadResponse(
            commentary_id=commentary_id,
            title=commentary_data["title"],
            citations_count=len(citations),
            message=f"成功提取 {len(citations)} 条引文"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 上传注疏失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/projects/{project_id}/commentary/match")
async def match_commentary(
    project_id: str,
    position: int = Query(..., description="异文位置（1-based）"),
    window_size: int = Query(10, description="窗口大小（前后字数）"),
    threshold: float = Query(0.75, ge=0.0, le=1.0, description="相似度阈值")
):
    """
    为指定异文位置匹配注疏引文

    Args:
        project_id: 项目ID
        position: 异文位置（1-based，与汇校表一致）
        window_size: 上下文窗口大小（默认10字）
        threshold: 相似度阈值（默认0.75）

    Returns:
        匹配结果列表
    """
    try:
        # 1. 验证项目
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取底本文本
        base_text_raw = project["data"].get("base", {}).get("text", "")
        if not base_text_raw:
            raise HTTPException(status_code=400, detail="项目无底本文本")

        # 规范化底本文本（与校勘服务一致）
        base_text = commentary_service.match_citation_to_position.__wrapped__.__globals__['collation_service'].normalize_text_for_comparison(base_text_raw)

        # 3. 加载注疏引文
        commentary_dir = os.path.join("backend", "data", "commentaries")
        all_citations = []

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["commentary_id"]
            comm_file = os.path.join(commentary_dir, f"{project_id}_commentary_{comm_id}.json")

            if os.path.exists(comm_file):
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)
                    all_citations.extend(comm_data.get("citations", []))

        if not all_citations:
            return {"matches": [], "message": "项目无关联注疏"}

        # 4. 匹配引文到指定位置
        position_0based = position - 1  # 转为0-based
        matches = []

        for cit_data in all_citations:
            match_result = commentary_service.match_citation_to_position(
                citation_text=cit_data["extracted_text"],
                base_text=base_text,
                position=position_0based,
                window_size=window_size,
                threshold=threshold
            )

            if match_result:
                matches.append({
                    "citation_id": cit_data["id"],
                    "position": position,
                    "marker": cit_data["marker"],
                    "context": f"{cit_data['context_before']}...{cit_data['context_after']}",
                    **match_result
                })

        # 5. 按相似度降序排列
        matches.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "matches": matches,
            "count": len(matches),
            "message": f"找到 {len(matches)} 条匹配引文"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 匹配引文失败: {e}")
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.get("/projects/{project_id}/commentary/list")
async def list_commentaries(project_id: str):
    """
    获取项目关联的注疏文献列表

    Args:
        project_id: 项目ID

    Returns:
        注疏列表
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        commentaries = project["data"].get("commentaries", [])

        return CommentaryListResponse(commentaries=commentaries)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取注疏列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/projects/{project_id}/commentary/{commentary_id}")
async def delete_commentary(project_id: str, commentary_id: str):
    """
    删除注疏文献

    Args:
        project_id: 项目ID
        commentary_id: 注疏ID

    Returns:
        删除结果
    """
    try:
        # 1. 验证项目
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 从项目中移除注疏记录
        commentaries = project["data"].get("commentaries", [])
        updated_commentaries = [
            c for c in commentaries
            if c["commentary_id"] != commentary_id
        ]

        if len(updated_commentaries) == len(commentaries):
            raise HTTPException(status_code=404, detail="注疏不存在")

        project["data"]["commentaries"] = updated_commentaries
        project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data=project["data"]
        )

        # 3. 删除注疏文件
        commentary_dir = os.path.join("backend", "data", "commentaries")
        commentary_file = os.path.join(
            commentary_dir,
            f"{project_id}_commentary_{commentary_id}.json"
        )

        if os.path.exists(commentary_file):
            os.remove(commentary_file)

        return {"message": f"注疏 {commentary_id} 已删除"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 删除注疏失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/projects/{project_id}/commentary/citations")
async def get_all_citations(
    project_id: str,
    window_size: int = Query(15, description="匹配窗口大小"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值")
):
    """
    获取项目所有引文及其匹配位置（用于注疏面板展示）

    Args:
        project_id: 项目ID
        window_size: 匹配窗口大小（默认15字）
        threshold: 相似度阈值（默认0.7）

    Returns:
        所有引文列表，每条引文包含匹配到的经文位置
    """
    try:
        # 1. 验证项目
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取底本文本
        base_text_raw = project["data"].get("base", {}).get("text", "")
        if not base_text_raw:
            return {"citations": [], "message": "项目无底本文本"}

        # 规范化底本文本
        from app.services.collation_service import collation_service
        base_text = collation_service.normalize_text_for_comparison(base_text_raw)

        # 3. 加载所有注疏引文
        commentary_dir = os.path.join("backend", "data", "commentaries")
        all_citations = []

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["commentary_id"]
            comm_title = comm_info.get("title", "未知注疏")
            comm_file = os.path.join(commentary_dir, f"{project_id}_commentary_{comm_id}.json")

            if os.path.exists(comm_file):
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)

                    for cit in comm_data.get("citations", []):
                        # 为每条引文匹配经文位置
                        matched_positions = _match_citation_to_text(
                            citation_text=cit["extracted_text"],
                            base_text=base_text,
                            window_size=window_size,
                            threshold=threshold
                        )

                        all_citations.append({
                            **cit,
                            "commentary_id": comm_id,
                            "commentary_title": comm_title,
                            "matched_positions": matched_positions
                        })

        return {
            "citations": all_citations,
            "total": len(all_citations),
            "matched_count": sum(1 for c in all_citations if c["matched_positions"]),
            "message": f"共 {len(all_citations)} 条引文"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取引文失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/projects/{project_id}/commentary/position/{position}")
async def get_citations_at_position(
    project_id: str,
    position: int,
    window_size: int = Query(10, description="匹配窗口大小"),
    threshold: float = Query(0.75, ge=0.0, le=1.0, description="相似度阈值")
):
    """
    获取指定位置匹配的所有注疏引文（用于校勘判取弹窗）

    Args:
        project_id: 项目ID
        position: 经文位置（1-based）
        window_size: 匹配窗口大小
        threshold: 相似度阈值

    Returns:
        该位置匹配的引文列表
    """
    try:
        # 1. 验证项目
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取底本文本
        base_text_raw = project["data"].get("base", {}).get("text", "")
        if not base_text_raw:
            return {"matches": [], "message": "项目无底本文本"}

        # 规范化底本文本
        from app.services.collation_service import collation_service
        base_text = collation_service.normalize_text_for_comparison(base_text_raw)

        # 3. 加载注疏引文并匹配
        commentary_dir = os.path.join("backend", "data", "commentaries")
        matches = []
        position_0based = position - 1

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["commentary_id"]
            comm_title = comm_info.get("title", "未知注疏")
            comm_file = os.path.join(commentary_dir, f"{project_id}_commentary_{comm_id}.json")

            if os.path.exists(comm_file):
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)

                    for cit in comm_data.get("citations", []):
                        match_result = commentary_service.match_citation_to_position(
                            citation_text=cit["extracted_text"],
                            base_text=base_text,
                            position=position_0based,
                            window_size=window_size,
                            threshold=threshold
                        )

                        if match_result:
                            matches.append({
                                "citation_id": cit["id"],
                                "commentary_id": comm_id,
                                "commentary_title": comm_title,
                                "marker": cit["marker"],
                                "text": cit["extracted_text"],
                                "context": f"{cit['context_before']}...{cit['context_after']}",
                                **match_result
                            })

        # 按相似度排序
        matches.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "position": position,
            "matches": matches,
            "count": len(matches),
            "message": f"找到 {len(matches)} 条匹配引文"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 获取位置引文失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/projects/{project_id}/commentary/batch-match")
async def batch_match_citations(
    project_id: str,
    window_size: int = Query(15, description="匹配窗口大小"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值")
):
    """
    批量匹配所有引文到经文位置

    Args:
        project_id: 项目ID
        window_size: 匹配窗口大小
        threshold: 相似度阈值

    Returns:
        匹配统计
    """
    try:
        # 1. 验证项目
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取底本文本
        base_text_raw = project["data"].get("base", {}).get("text", "")
        if not base_text_raw:
            return {"matched_count": 0, "message": "项目无底本文本"}

        # 规范化底本文本
        from app.services.collation_service import collation_service
        base_text = collation_service.normalize_text_for_comparison(base_text_raw)

        # 3. 遍历所有注疏并匹配
        commentary_dir = os.path.join("backend", "data", "commentaries")
        total_citations = 0
        matched_citations = 0

        for comm_info in project["data"].get("commentaries", []):
            comm_id = comm_info["commentary_id"]
            comm_file = os.path.join(commentary_dir, f"{project_id}_commentary_{comm_id}.json")

            if os.path.exists(comm_file):
                with open(comm_file, 'r', encoding='utf-8') as f:
                    comm_data = json.load(f)

                updated_citations = []
                for cit in comm_data.get("citations", []):
                    total_citations += 1

                    # 滑动窗口匹配
                    matched_positions = _match_citation_to_text(
                        citation_text=cit["extracted_text"],
                        base_text=base_text,
                        window_size=window_size,
                        threshold=threshold
                    )

                    cit["matched_positions"] = matched_positions
                    updated_citations.append(cit)

                    if matched_positions:
                        matched_citations += 1

                # 更新注疏文件（保存匹配结果）
                comm_data["citations"] = updated_citations
                comm_data["last_matched"] = datetime.now().isoformat()

                with open(comm_file, 'w', encoding='utf-8') as f:
                    json.dump(comm_data, f, ensure_ascii=False, indent=2)

        return {
            "total_citations": total_citations,
            "matched_count": matched_citations,
            "message": f"批量匹配完成：{matched_citations}/{total_citations} 条引文已匹配"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 批量匹配失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


def _match_citation_to_text(
    citation_text: str,
    base_text: str,
    window_size: int = 15,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    使用滑动窗口将引文匹配到经文的多个位置

    Args:
        citation_text: 引文文本（可能带标点）
        base_text: 经文文本（已规范化，通常无标点）
        window_size: 窗口大小
        threshold: 相似度阈值

    Returns:
        匹配位置列表
    """
    from app.services.collation_service import collation_service
    from app.services.collation.text_normalizer import extract_clean_text_with_mapping

    matches = []

    # 1. 规范化引文（去除换行、空格等）
    citation_normalized = collation_service.normalize_text_for_comparison(citation_text)

    # 2. 去除引文中的标点，因为底本通常无标点
    citation_clean, _ = extract_clean_text_with_mapping(citation_normalized)

    # 3. 处理"(至)"格式的范围引用
    # 如"無色法中...蘊得等性"需要拆分成首尾两部分匹配
    if "..." in citation_clean:
        return _match_range_citation(citation_clean, base_text, window_size, threshold)

    citation_len = len(citation_clean)

    if citation_len < 3:
        return []

    # 滑动窗口匹配
    step = max(1, window_size // 3)  # 步长
    for pos in range(0, len(base_text) - min(citation_len, len(base_text)) + 1, step):
        window_text = base_text[pos:pos + citation_len + window_size]

        similarity = collation_service._compute_similarity(
            citation_clean,
            window_text
        )

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
                    "matched_text": base_text[pos:pos + citation_len]
                })

    # 按相似度排序
    matches.sort(key=lambda x: x["similarity"], reverse=True)

    # 只返回前10个最佳匹配
    return matches[:10]


def _match_range_citation(
    citation_text: str,
    base_text: str,
    window_size: int = 15,
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    匹配"首...尾"格式的范围引用

    这种格式来自《述文记》等注疏，表示引用从"首部分"开始到"尾部分"结束的经文。
    例如："無色法中...蘊得等性" 需要在经文中找到以"無色法中"开头、以"蘊得等性"结尾的段落。

    Args:
        citation_text: "首...尾"格式的引文（已去标点）
        base_text: 经文文本
        window_size: 搜索窗口
        threshold: 相似度阈值

    Returns:
        匹配位置列表
    """
    from app.services.collation_service import collation_service

    matches = []

    # 拆分首尾
    parts = citation_text.split("...")
    if len(parts) != 2:
        return []

    start_text = parts[0].strip()
    end_text = parts[1].strip()

    if len(start_text) < 2 or len(end_text) < 2:
        return []

    # 策略：先找首部分匹配，然后在其后一定范围内找尾部分匹配
    # 经文段落通常不超过500字
    max_range = 500

    # 找所有首部分的匹配位置
    start_len = len(start_text)
    for pos in range(0, len(base_text) - start_len + 1):
        # 检查首部分匹配
        window = base_text[pos:pos + start_len]
        start_similarity = collation_service._compute_similarity(start_text, window)

        if start_similarity >= threshold:
            # 找到首部分匹配，在其后搜索尾部分
            search_end = min(pos + max_range, len(base_text))
            end_len = len(end_text)

            for end_pos in range(pos + start_len, search_end - end_len + 1):
                end_window = base_text[end_pos:end_pos + end_len]
                end_similarity = collation_service._compute_similarity(end_text, end_window)

                if end_similarity >= threshold:
                    # 找到完整匹配
                    overall_similarity = (start_similarity + end_similarity) / 2
                    matched_full = base_text[pos:end_pos + end_len]

                    # 避免重复
                    is_duplicate = any(
                        abs(m["position"] - (pos + 1)) < window_size
                        for m in matches
                    )

                    if not is_duplicate:
                        matches.append({
                            "position": pos + 1,  # 转为1-based
                            "similarity": round(overall_similarity, 4),
                            "matched_text": matched_full[:50] + ("..." if len(matched_full) > 50 else "")
                        })
                    break  # 找到第一个尾部匹配就停止

    # 按相似度排序
    matches.sort(key=lambda x: x["similarity"], reverse=True)

    return matches[:10]
