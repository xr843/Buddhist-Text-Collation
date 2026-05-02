"""
校勘判取路由
从 multi_collation.py 中提取
"""
from fastapi import APIRouter, HTTPException, status

from app.services.project_storage import project_storage, ProjectType

from .models import SaveDecisionsRequest, GenerateDefinitiveTextRequest

router = APIRouter()


@router.get("/projects/{project_id}/decisions")
async def get_decisions(project_id: str):
    """
    获取项目的校勘判取结果

    返回该项目已保存的所有判取决策。
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        # 从项目数据中获取判取结果
        decisions = project.get("data", {}).get("decisions", {})

        return {
            "success": True,
            "project_id": project_id,
            "decisions": decisions,
            "total": len(decisions),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取判取结果失败: {str(e)}"
        )


@router.post("/projects/{project_id}/decisions")
async def save_decisions(project_id: str, request: SaveDecisionsRequest):
    """
    保存校勘判取结果

    保存或更新项目的判取决策。支持增量保存。
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        # 获取现有判取结果
        existing_decisions = project.get("data", {}).get("decisions", {})

        # 合并新的判取结果
        for pos, decision in request.decisions.items():
            existing_decisions[pos] = decision.model_dump()

        # 更新项目数据
        project["data"]["decisions"] = existing_decisions

        # 计算判取统计
        total_decisions = len(existing_decisions)
        uncertain_count = sum(1 for d in existing_decisions.values() if d.get("uncertain", False))
        decided_count = total_decisions - uncertain_count

        # 更新 metadata
        project["metadata"]["decision_count"] = total_decisions
        project["metadata"]["decided_count"] = decided_count
        project["metadata"]["uncertain_count"] = uncertain_count

        # 保存项目
        updated_project = project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data=project["data"],
            metadata=project["metadata"],
            merge_data=False,
        )

        return {
            "success": True,
            "message": f"已保存 {len(request.decisions)} 条判取结果",
            "project_id": project_id,
            "total_decisions": total_decisions,
            "decided_count": decided_count,
            "uncertain_count": uncertain_count,
            "updated_at": updated_project["updated_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[保存判取] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[保存判取] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存判取结果失败: {str(e)}"
        )


@router.delete("/projects/{project_id}/decisions/{position}")
async def delete_decision(project_id: str, position: int):
    """
    删除单条判取结果
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        decisions = project.get("data", {}).get("decisions", {})
        pos_key = str(position)

        if pos_key not in decisions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"判取结果不存在: 位置 {position}"
            )

        del decisions[pos_key]
        project["data"]["decisions"] = decisions

        # 更新统计
        total_decisions = len(decisions)
        uncertain_count = sum(1 for d in decisions.values() if d.get("uncertain", False))
        project["metadata"]["decision_count"] = total_decisions
        project["metadata"]["decided_count"] = total_decisions - uncertain_count
        project["metadata"]["uncertain_count"] = uncertain_count

        project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data=project["data"],
            metadata=project["metadata"],
            merge_data=False,
        )

        return {
            "success": True,
            "message": f"已删除位置 {position} 的判取结果",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除判取结果失败: {str(e)}"
        )


@router.post("/projects/{project_id}/generate-definitive-text")
async def generate_definitive_text(
    project_id: str,
    request: GenerateDefinitiveTextRequest = GenerateDefinitiveTextRequest()
):
    """
    生成定本文本

    基于底本和判取结果，生成校勘后的定本文本。

    参数:
    - include_uncertain: 是否将存疑项也应用到定本（默认不应用）

    返回:
    - definitive_text: 定本文本
    - collation_notes: 校勘记（按位置排列的判取说明）
    - statistics: 统计信息
    """
    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        # 获取底本文本
        base_text = project["data"]["base"]["text"]
        base_name = project["data"]["base"]["name"]

        # 获取判取结果
        decisions = project.get("data", {}).get("decisions", {})

        if not decisions:
            return {
                "success": True,
                "definitive_text": base_text,
                "collation_notes": [],
                "statistics": {
                    "base_char_count": len(base_text),
                    "applied_count": 0,
                    "skipped_uncertain_count": 0,
                    "total_decisions": 0,
                },
                "message": "无判取结果，返回原始底本文本",
            }

        # 按位置排序判取结果（从后往前应用，避免位置偏移）
        sorted_decisions = sorted(
            decisions.items(),
            key=lambda x: int(x[0]),
            reverse=True
        )

        # 生成定本
        definitive_chars = list(base_text)
        collation_notes = []
        applied_count = 0
        skipped_uncertain_count = 0

        for pos_str, decision in sorted_decisions:
            pos = int(pos_str)

            # 如果存疑且不包含存疑项，跳过
            if decision.get("uncertain", False) and not request.include_uncertain:
                skipped_uncertain_count += 1
                collation_notes.append({
                    "position": pos,
                    "status": "skipped",
                    "reason": "存疑待考",
                    "original": base_text[pos] if pos < len(base_text) else "",
                    "decision": decision,
                })
                continue

            # 应用判取结果
            selected_text = decision.get("selectedText", "")
            original_char = base_text[pos] if pos < len(base_text) else ""

            # 如果选择的是底本，不需要替换
            if decision.get("selectedVersion") == base_name and selected_text == original_char:
                collation_notes.append({
                    "position": pos,
                    "status": "unchanged",
                    "reason": "采用底本",
                    "original": original_char,
                    "decision": decision,
                })
                continue

            # 替换字符
            if pos < len(definitive_chars):
                # 处理替换（可能是单字替换或多字替换/删除）
                if selected_text == "∅" or selected_text == "":
                    # 脱文判取：删除该字符
                    definitive_chars[pos] = ""
                else:
                    definitive_chars[pos] = selected_text

                applied_count += 1
                collation_notes.append({
                    "position": pos,
                    "status": "applied",
                    "original": original_char,
                    "replacement": selected_text,
                    "decision": decision,
                })

        # 合并生成定本文本
        definitive_text = "".join(definitive_chars)

        # 按位置正序排列校勘记
        collation_notes.sort(key=lambda x: x["position"])

        # 生成校勘记文本格式
        formatted_notes = []
        for note in collation_notes:
            if note["status"] == "applied":
                decision = note["decision"]
                basis = []
                if decision.get("duijiao"):
                    basis.append("对校")
                if decision.get("benjiao"):
                    basis.append("本校")
                if decision.get("tajiao"):
                    basis.append("他校")
                if decision.get("lijiao"):
                    basis.append("理校")

                formatted_notes.append({
                    "position": note["position"],
                    "text": f"「{note['original']}」改「{note['replacement']}」",
                    "version": decision.get("selectedVersion", ""),
                    "basis": "、".join(basis) if basis else "无",
                    "note": decision.get("note", ""),
                })

        return {
            "success": True,
            "definitive_text": definitive_text,
            "collation_notes": formatted_notes,
            "statistics": {
                "base_char_count": len(base_text),
                "definitive_char_count": len(definitive_text),
                "total_decisions": len(decisions),
                "applied_count": applied_count,
                "skipped_uncertain_count": skipped_uncertain_count,
                "unchanged_count": len(decisions) - applied_count - skipped_uncertain_count,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[生成定本] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[生成定本] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成定本失败: {str(e)}"
        )
