"""
校本管理路由（追加/移除校本）
从 multi_collation.py 中提取
"""
import time
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Optional

from app.services.collation_service import collation_service
from app.services.file_parser import file_parser_service
from app.services.project_storage import project_storage, ProjectType

from .models import RemoveCollationsRequest
from .variant_table import generate_variant_table
from .phylogeny_utils import enrich_phylogeny_with_locations, calculate_phylogeny_analysis

router = APIRouter()


@router.post("/projects/{project_id}/add-collations")
async def add_collations_to_project(
    project_id: str,
    collation_files: List[UploadFile] = File(..., description="新增的校本文件列表"),
    collation_names: Optional[str] = Form(None, description="校本名称列表（逗号分隔）"),
):
    """
    向已有项目追加校本

    在不重新上传底本的情况下，追加新的校本进行对勘。
    """
    start_time = time.time()

    try:
        # 1. 获取现有项目
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        # 2. 获取底本信息
        base_info = project["data"]["base"]
        base_text = base_info["text"]
        base_name = base_info["name"]
        base_char_count = base_info["char_count"]
        existing_decisions = project.get("data", {}).get("decisions", {}) or {}
        canon_locations_override = project.get("data", {}).get("canon_locations_override", {}) or {}

        # 3. 获取现有校本
        existing_collations = project["data"]["collations"]
        existing_count = len(existing_collations)

        # 4. 验证校本数量（总数不超过30）
        if existing_count + len(collation_files) > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"校本总数不能超过30个（当前{existing_count}个，新增{len(collation_files)}个）"
            )

        # 5. 解析校本名称列表
        collation_name_list = []
        if collation_names:
            collation_name_list = [name.strip() for name in collation_names.split(",")]

        # 6. 解析新校本并进行对比
        new_collation_results = []
        for idx, coll_file in enumerate(collation_files):
            print(f"[追加校本] 解析校本{idx + 1}: {coll_file.filename}")

            coll_text, auto_coll_name, coll_char_count = await file_parser_service.parse_uploaded_file(coll_file)

            if idx < len(collation_name_list) and collation_name_list[idx]:
                final_coll_name = collation_name_list[idx]
            else:
                final_coll_name = auto_coll_name

            print(f"[追加校本] 对比: {base_name} vs {final_coll_name}")

            result = collation_service.collate_texts(
                text1=base_text,
                text2=coll_text,
                version1_name=base_name,
                version2_name=final_coll_name
            )

            new_collation_results.append({
                "collation_name": final_coll_name,
                "collation_file": coll_file.filename,
                "char_count": coll_char_count,
                "result": result
            })

        # 7. 合并校本结果
        all_collation_results = existing_collations + new_collation_results

        # 8. 重新生成汇总统计
        summary_stats = {
            "variant_chars": [],
            "error_chars": [],
            "yanwen_chars": [],
            "tuowen_chars": [],
        }
        for coll in all_collation_results:
            result = coll.get("result")
            if result:
                category_stats = result.get("statistics", {}).get("category_stats", {})
            else:
                category_stats = {}
            summary_stats["variant_chars"].append(category_stats.get("variant_chars", 0))
            summary_stats["error_chars"].append(category_stats.get("error_chars", 0))
            summary_stats["yanwen_chars"].append(category_stats.get("yanwen_chars", 0))
            summary_stats["tuowen_chars"].append(category_stats.get("tuowen_chars", 0))

        collation_names_list = [c["collation_name"] for c in all_collation_results]
        summary = {
            "base_name": base_name,
            "collation_names": collation_names_list,
            "stats_table": {
                "headers": ["差异类型", *collation_names_list, "合计"],
                "rows": [
                    {"type": "异体字", "type_key": "variant", "values": summary_stats["variant_chars"], "total": sum(summary_stats["variant_chars"])},
                    {"type": "讹误", "type_key": "error", "values": summary_stats["error_chars"], "total": sum(summary_stats["error_chars"])},
                    {"type": "衍文", "type_key": "yanwen", "values": summary_stats["yanwen_chars"], "total": sum(summary_stats["yanwen_chars"])},
                    {"type": "脱文", "type_key": "tuowen", "values": summary_stats["tuowen_chars"], "total": sum(summary_stats["tuowen_chars"])},
                ]
            }
        }

        # 9. 重新生成异文汇校表
        variant_table = generate_variant_table(base_text, base_name, all_collation_results)
        variant_table_data = {
            "headers": ["序号", "位置", "上下文", base_name, *collation_names_list, "类型"],
            "rows": variant_table,
            "total": len(variant_table)
        }

        # 10. 重新计算版本谱系（使用专业服务）
        collation_texts = {}
        for coll in all_collation_results:
            coll_name = coll["collation_name"]
            result = coll.get("result")
            if result:
                text2 = result.get("text2")
                if isinstance(text2, str) and text2:
                    collation_texts[coll_name] = text2

        phylogeny_analysis = calculate_phylogeny_analysis(
            base_text=base_text,
            base_name=base_name,
            collation_results=all_collation_results,
            collation_texts=collation_texts,
        )
        phylogeny_data = {
            "similarity_matrix": phylogeny_analysis["similarity_matrix"],
            "shared_errors": phylogeny_analysis["shared_errors"],
            "tree": phylogeny_analysis["tree"],
            "conclusions": phylogeny_analysis["conclusions"],
        }
        phylogeny_data = enrich_phylogeny_with_locations(
            phylogeny_data, canon_locations_override, base_name=base_name
        )

        # 11. 更新项目
        updated_project = project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data={
                "base": base_info,
                "collations": all_collation_results,
                "summary": summary,
                "variant_table": variant_table_data,
                "phylogeny": phylogeny_data,
                "decisions": existing_decisions,
                "canon_locations_override": canon_locations_override,
            },
            metadata={
                "base_name": base_name,
                "base_file": base_info.get("file", ""),
                "base_char_count": base_char_count,
                "collation_count": len(all_collation_results),
                "collation_names": collation_names_list,
                "variant_count": variant_table_data["total"],
                "diff_total": sum(r.get("total", 0) for r in summary.get("stats_table", {}).get("rows", [])),
            },
            merge_data=False,
        )

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "message": f"成功追加 {len(new_collation_results)} 个校本",
            "processing_time": processing_time,
            "project": {
                "id": updated_project["id"],
                "title": updated_project["title"],
                "updated_at": updated_project["updated_at"],
            },
            "total_collations": len(all_collation_results),
            "new_collations": [c["collation_name"] for c in new_collation_results],
            # 返回完整数据以便前端更新
            "base": base_info,
            "collations": all_collation_results,
            "summary": summary,
            "variant_table": variant_table_data,
            "phylogeny": phylogeny_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[追加校本] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[追加校本] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"追加校本失败: {str(e)}"
        )


@router.post("/projects/{project_id}/remove-collations")
async def remove_collations_from_project(project_id: str, request: RemoveCollationsRequest):
    """
    从已有项目移除一个或多个校本（会重新生成汇总统计/异文汇校表/谱系）。

    - indices: 0-based，基于 project.data.collations 的索引
    """
    start_time = time.time()

    try:
        project = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        base_info = project["data"]["base"]
        base_text = base_info["text"]
        base_name = base_info["name"]
        base_char_count = base_info.get("char_count", 0)
        canon_locations_override = project.get("data", {}).get("canon_locations_override", {}) or {}

        collations = list(project["data"].get("collations", []))
        if not collations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前项目没有可移除的校本"
            )

        indices = request.indices or []
        indices = sorted(set(int(i) for i in indices), reverse=True)
        if not indices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供要移除的校本索引 indices"
            )

        if any(i < 0 or i >= len(collations) for i in indices):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"校本索引越界（当前校本数 {len(collations)}）"
            )

        remaining = len(collations) - len(indices)
        if remaining < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="至少需要保留 1 个校本"
            )

        removed = []
        removed_names = set()
        for i in indices:
            item = collations.pop(i)
            removed.append(item)
            name = item.get("collation_name")
            if isinstance(name, str) and name:
                removed_names.add(name)

        # 重新生成汇总统计
        summary_stats = {
            "variant_chars": [],
            "error_chars": [],
            "yanwen_chars": [],
            "tuowen_chars": [],
        }
        for coll in collations:
            result = coll.get("result")
            category_stats = result.get("statistics", {}).get("category_stats", {}) if result else {}
            summary_stats["variant_chars"].append(category_stats.get("variant_chars", 0))
            summary_stats["error_chars"].append(category_stats.get("error_chars", 0))
            summary_stats["yanwen_chars"].append(category_stats.get("yanwen_chars", 0))
            summary_stats["tuowen_chars"].append(category_stats.get("tuowen_chars", 0))

        collation_names_list = [c.get("collation_name", "") for c in collations]
        summary = {
            "base_name": base_name,
            "collation_names": collation_names_list,
            "stats_table": {
                "headers": ["差异类型", *collation_names_list, "合计"],
                "rows": [
                    {"type": "异体字", "type_key": "variant", "values": summary_stats["variant_chars"], "total": sum(summary_stats["variant_chars"])},
                    {"type": "讹误", "type_key": "error", "values": summary_stats["error_chars"], "total": sum(summary_stats["error_chars"])},
                    {"type": "衍文", "type_key": "yanwen", "values": summary_stats["yanwen_chars"], "total": sum(summary_stats["yanwen_chars"])},
                    {"type": "脱文", "type_key": "tuowen", "values": summary_stats["tuowen_chars"], "total": sum(summary_stats["tuowen_chars"])},
                ]
            }
        }

        # 重新生成异文汇校表
        variant_table = generate_variant_table(base_text, base_name, collations)
        variant_table_data = {
            "headers": ["序号", "位置", "上下文", base_name, *collation_names_list, "类型"],
            "rows": variant_table,
            "total": len(variant_table)
        }

        # 重新计算版本谱系
        collation_texts = {}
        for coll in collations:
            coll_name = coll.get("collation_name")
            result = coll.get("result")
            text2 = result.get("text2") if result else None
            if isinstance(coll_name, str) and coll_name and isinstance(text2, str) and text2:
                collation_texts[coll_name] = text2

        phylogeny_analysis = calculate_phylogeny_analysis(
            base_text=base_text,
            base_name=base_name,
            collation_results=collations,
            collation_texts=collation_texts,
        )
        phylogeny_data = {
            "similarity_matrix": phylogeny_analysis["similarity_matrix"],
            "shared_errors": phylogeny_analysis["shared_errors"],
            "tree": phylogeny_analysis["tree"],
            "conclusions": phylogeny_analysis["conclusions"],
        }

        # 清理判取结果中引用已移除版本的条目
        decisions = project.get("data", {}).get("decisions", {}) or {}
        removed_decisions = 0
        if removed_names and isinstance(decisions, dict):
            new_decisions = {}
            for pos, decision in decisions.items():
                selected_version = None
                if isinstance(decision, dict):
                    selected_version = decision.get("selectedVersion")
                if selected_version in removed_names:
                    removed_decisions += 1
                    continue
                new_decisions[pos] = decision
            decisions = new_decisions

        updated_project = project_storage.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data={
                "base": base_info,
                "collations": collations,
                "summary": summary,
                "variant_table": variant_table_data,
                "phylogeny": phylogeny_data,
                "decisions": decisions,
                "canon_locations_override": canon_locations_override,
            },
            metadata={
                "base_name": base_name,
                "base_file": base_info.get("file", ""),
                "base_char_count": base_char_count,
                "collation_count": len(collations),
                "collation_names": collation_names_list,
                "variant_count": variant_table_data["total"],
                "diff_total": sum(r.get("total", 0) for r in summary.get("stats_table", {}).get("rows", [])),
                "decision_count": len(decisions) if isinstance(decisions, dict) else 0,
            },
            merge_data=False,
        )

        processing_time = round(time.time() - start_time, 2)

        return {
            "success": True,
            "message": f"成功移除 {len(removed)} 个校本",
            "processing_time": processing_time,
            "project": {
                "id": updated_project["id"],
                "title": updated_project["title"],
                "updated_at": updated_project["updated_at"],
            },
            "total_collations": len(collations),
            "removed_collations": [c.get("collation_name", "") for c in removed],
            "removed_decisions": removed_decisions,
            # 返回完整数据以便前端更新
            "base": base_info,
            "collations": collations,
            "summary": summary,
            "variant_table": variant_table_data,
            "phylogeny": phylogeny_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[移除校本] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[移除校本] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除校本失败: {str(e)}"
        )
