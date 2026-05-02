"""
一底多校对比核心路由
从 multi_collation.py 中提取
"""
import time
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any

from app.services.collation_service import collation_service
from app.services.file_parser import file_parser_service
from app.services.project_storage import project_storage, ProjectType

from .variant_table import generate_variant_table
from .phylogeny_utils import enrich_phylogeny_with_locations, calculate_phylogeny_analysis

router = APIRouter()


@router.post("/compare")
async def multi_collation_compare(
    base_file: UploadFile = File(..., description="底本文件"),
    collation_files: List[UploadFile] = File(..., description="校本文件列表（1-30个）"),
    base_name: Optional[str] = Form(None, description="底本名称"),
    collation_names: Optional[str] = Form(None, description="校本名称列表（逗号分隔）"),
    project_title: Optional[str] = Form(None, description="项目标题（可选，默认使用底本名称）"),
    project_id: Optional[str] = Form(None, description="项目ID（传入则更新现有项目）"),
    auto_save: bool = Form(True, description="是否自动保存项目"),
):
    """
    一底多校对比接口

    上传一个底本文件和多个校本文件，系统自动进行一对多校勘。

    - **base_file**: 底本文件（txt或docx）
    - **collation_files**: 校本文件列表（1-30个）
    - **base_name**: 底本名称（可选）
    - **collation_names**: 校本名称列表，逗号分隔（可选）

    返回各校本与底本的校勘结果和汇总统计。
    """
    start_time = time.time()

    try:
        # 若更新已有项目，保留用户手工补充的地理位置信息
        canon_locations_override: Dict[str, Any] = {}
        if project_id:
            existing = project_storage.get_project(ProjectType.MULTI_COLLATION, project_id)
            if existing:
                canon_locations_override = existing.get("data", {}).get("canon_locations_override", {}) or {}

        # 1. 验证校本数量
        if len(collation_files) < 1 or len(collation_files) > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="校本数量必须为1-30个"
            )

        # 2. 解析底本
        print(f"[一底多校] 解析底本: {base_file.filename}")
        base_text, auto_base_name, base_char_count = await file_parser_service.parse_uploaded_file(base_file)
        final_base_name = base_name or auto_base_name

        # 3. 解析校本名称列表
        collation_name_list = []
        if collation_names:
            collation_name_list = [name.strip() for name in collation_names.split(",")]

        # 4. 解析所有校本并进行对比
        collation_results = []
        summary_stats = {
            "variant_chars": [],    # 异体字
            "error_chars": [],      # 讹误（含倒文）
            "yanwen_chars": [],     # 衍文
            "tuowen_chars": [],     # 脱文
        }

        for idx, coll_file in enumerate(collation_files):
            print(f"[一底多校] 解析校本{idx + 1}: {coll_file.filename}")

            # 解析校本文件
            coll_text, auto_coll_name, coll_char_count = await file_parser_service.parse_uploaded_file(coll_file)

            # 确定校本名称
            if idx < len(collation_name_list) and collation_name_list[idx]:
                final_coll_name = collation_name_list[idx]
            else:
                final_coll_name = auto_coll_name

            print(f"[一底多校] 对比: {final_base_name} vs {final_coll_name}")

            # 调用现有的校勘服务
            result = collation_service.collate_texts(
                text1=base_text,
                text2=coll_text,
                version1_name=final_base_name,
                version2_name=final_coll_name
            )

            # 收集结果
            collation_results.append({
                "collation_name": final_coll_name,
                "collation_file": coll_file.filename,
                "char_count": coll_char_count,
                "result": result
            })

            # 收集汇总统计（倒文已合并到讹误中）
            category_stats = result.get("statistics", {}).get("category_stats", {})
            summary_stats["variant_chars"].append(category_stats.get("variant_chars", 0))
            summary_stats["error_chars"].append(category_stats.get("error_chars", 0))
            summary_stats["yanwen_chars"].append(category_stats.get("yanwen_chars", 0))
            summary_stats["tuowen_chars"].append(category_stats.get("tuowen_chars", 0))

        # 5. 计算处理时间
        processing_time = round(time.time() - start_time, 2)

        # 6. 构建汇总统计
        collation_names_list = [r["collation_name"] for r in collation_results]
        summary = {
            "base_name": final_base_name,
            "collation_names": collation_names_list,
            "stats_table": {
                "headers": ["差异类型", *collation_names_list, "合计"],
                "rows": [
                    {
                        "type": "异体字",
                        "type_key": "variant",
                        "values": summary_stats["variant_chars"],
                        "total": sum(summary_stats["variant_chars"])
                    },
                    {
                        "type": "讹误",
                        "type_key": "error",
                        "values": summary_stats["error_chars"],
                        "total": sum(summary_stats["error_chars"])
                    },
                    {
                        "type": "衍文",
                        "type_key": "yanwen",
                        "values": summary_stats["yanwen_chars"],
                        "total": sum(summary_stats["yanwen_chars"])
                    },
                    {
                        "type": "脱文",
                        "type_key": "tuowen",
                        "values": summary_stats["tuowen_chars"],
                        "total": sum(summary_stats["tuowen_chars"])
                    },
                ]
            }
        }

        # 7. 生成异文汇校表
        print("[一底多校] 生成异文汇校表...")
        variant_table = generate_variant_table(
            base_text=base_text,
            base_name=final_base_name,
            collation_results=collation_results
        )
        print(f"[一底多校] 异文汇校表共 {len(variant_table)} 条记录")

        # 如果只有一个校本，需要特殊处理
        if len(collation_results) == 1:
            vt_stats = {"异体字": 0, "讹误": 0, "衍文": 0, "脱文": 0}
            for row in variant_table:
                cat = row.get("category", "")
                if cat in vt_stats:
                    vt_stats[cat] += 1

            summary["stats_table"]["rows"][0]["values"] = [vt_stats["异体字"]]
            summary["stats_table"]["rows"][1]["values"] = [vt_stats["讹误"]]
            summary["stats_table"]["rows"][2]["values"] = [vt_stats["衍文"]]
            summary["stats_table"]["rows"][3]["values"] = [vt_stats["脱文"]]

            summary["stats_table"]["rows"][0]["total"] = vt_stats["异体字"]
            summary["stats_table"]["rows"][1]["total"] = vt_stats["讹误"]
            summary["stats_table"]["rows"][2]["total"] = vt_stats["衍文"]
            summary["stats_table"]["rows"][3]["total"] = vt_stats["脱文"]

            coll = collation_results[0]
            coll_result = coll.get("result")
            if coll_result and "statistics" in coll_result and "category_stats" in coll_result["statistics"]:
                coll_result["statistics"]["category_stats"]["variant_chars"] = vt_stats["异体字"]
                coll_result["statistics"]["category_stats"]["error_chars"] = vt_stats["讹误"]
                coll_result["statistics"]["category_stats"]["yanwen_chars"] = vt_stats["衍文"]
                coll_result["statistics"]["category_stats"]["tuowen_chars"] = vt_stats["脱文"]
            print(f"[一底多校] 单校本统计已更新: 异体字={vt_stats['异体字']}, 讹误={vt_stats['讹误']}, 衍文={vt_stats['衍文']}, 脱文={vt_stats['脱文']}")

        # 8. 计算版本谱系（使用专业服务）
        print("[一底多校] 计算版本谱系（专业分析）...")

        collation_texts = {}
        for coll in collation_results:
            coll_name = coll["collation_name"]
            coll_result = coll.get("result")
            if coll_result:
                side_by_side = coll_result.get("side_by_side", {})
                if side_by_side and "text2" in side_by_side:
                    collation_texts[coll_name] = side_by_side["text2"]

        phylogeny_analysis = calculate_phylogeny_analysis(
            base_text=base_text,
            base_name=final_base_name,
            collation_results=collation_results,
            collation_texts=collation_texts,
        )

        phylogeny_data = {
            "similarity_matrix": phylogeny_analysis["similarity_matrix"],
            "shared_errors": phylogeny_analysis["shared_errors"],
            "tree": phylogeny_analysis["tree"],
            "conclusions": phylogeny_analysis["conclusions"],
        }
        phylogeny_data = enrich_phylogeny_with_locations(
            phylogeny_data, canon_locations_override, base_name=final_base_name
        )

        # 9. 构建结果数据
        base_info = {
            "name": final_base_name,
            "file": base_file.filename,
            "char_count": base_char_count,
            "text": base_text
        }

        variant_table_data = {
            "headers": ["序号", "位置", "上下文", final_base_name, *collation_names_list, "类型"],
            "rows": variant_table,
            "total": len(variant_table)
        }

        # 10. 自动保存项目
        saved_project = None
        if auto_save:
            try:
                title = project_title or f"{final_base_name} 校勘项目"
                saved_project = project_storage.save_multi_collation(
                    title=title,
                    base_info=base_info,
                    collation_results=collation_results,
                    summary=summary,
                    variant_table=variant_table_data,
                    phylogeny=phylogeny_data,
                    project_id=project_id,
                )
                print(f"[一底多校] 项目已保存: {saved_project['id']}")
            except Exception as e:
                print(f"[一底多校] 保存项目失败: {e}")

        # 11. 返回结果
        result = {
            "success": True,
            "mode": "multi_collation",
            "mode_description": "一底多校模式",
            "processing_time": processing_time,
            "base": base_info,
            "collations": collation_results,
            "summary": summary,
            "variant_table": variant_table_data,
            "phylogeny": phylogeny_data,
        }

        if saved_project:
            result["project"] = {
                "id": saved_project["id"],
                "title": saved_project["title"],
                "created_at": saved_project["created_at"],
                "updated_at": saved_project["updated_at"],
            }

        return result

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        print(f"[一底多校] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[一底多校] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"一底多校对比失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "一底多校服务正常"
    }
