"""
导出功能路由

包含：
- 导出校勘记接口
"""
import time
from fastapi import APIRouter, HTTPException, status

from app.services.collation_service import collation_service

from .models import ExportCollationNotesRequest

router = APIRouter()


@router.post("/export-collation-notes")
async def export_collation_notes(request: ExportCollationNotesRequest):
    """
    导出校勘记

    支持格式：
    - txt: 传统校勘记格式（参照陈垣《校勘学释例》）
    - tei-xml: TEI P5 Critical Apparatus格式
    - latex: reledmac critical apparatus（可直接编译进 LaTeX 论文）
    - markdown: 便于贴入 Notion/GitHub 的表格式
    - json: 结构化JSON格式
    - csv: 学术CSV格式

    返回：
    - content: 导出内容
    - format: 导出格式
    - filename: 建议的文件名
    """
    from app.services.collation_note_service import collation_note_service

    try:
        # 1. 规范化文本
        normalized_text1 = collation_service.normalize_text_for_comparison(request.text1)
        normalized_text2 = collation_service.normalize_text_for_comparison(request.text2)

        # 2. 获取对齐结果
        aligned_segments = collation_service._global_char_alignment(normalized_text1, normalized_text2)

        # 3. 计算统计信息
        collation_service._compute_alignment_statistics(
            aligned_segments, normalized_text1, normalized_text2
        )

        # 4. 生成校勘记
        notes = collation_note_service.generate_notes_from_alignment(
            aligned_segments=aligned_segments,
            base_text=normalized_text1,
            base_version=request.version1_name,
            variant_version=request.version2_name
        )

        # 5. 根据格式导出
        export_format = request.format.lower()
        content = ""
        content_type = "text/plain"
        file_ext = "txt"

        if export_format == "txt":
            content = collation_note_service.export_to_txt(
                notes=notes,
                title=request.title,
                include_context=request.include_context
            )
            content_type = "text/plain; charset=utf-8"
            file_ext = "txt"

        elif export_format == "tei-xml" or export_format == "xml":
            content = collation_note_service.export_to_tei_xml(
                notes=notes,
                title=request.title,
                base_version=request.version1_name,
                variant_version=request.version2_name
            )
            content_type = "application/xml; charset=utf-8"
            file_ext = "xml"

        elif export_format == "json":
            content = collation_note_service.export_to_json(
                notes=notes,
                include_metadata=True
            )
            content_type = "application/json; charset=utf-8"
            file_ext = "json"

        elif export_format == "csv":
            content = collation_note_service.export_to_csv_academic(
                notes=notes
            )
            content_type = "text/csv; charset=utf-8"
            file_ext = "csv"

        elif export_format in ("latex", "tex"):
            content = collation_note_service.export_to_latex(
                notes=notes,
                title=request.title,
                base_version=request.version1_name,
                variant_version=request.version2_name,
                base_text=normalized_text1,
            )
            content_type = "application/x-tex; charset=utf-8"
            file_ext = "tex"

        elif export_format in ("markdown", "md"):
            content = collation_note_service.export_to_markdown(
                notes=notes,
                title=request.title,
                base_version=request.version1_name,
                variant_version=request.version2_name,
            )
            content_type = "text/markdown; charset=utf-8"
            file_ext = "md"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的导出格式: {export_format}，支持: txt, tei-xml, latex, markdown, json, csv"
            )

        # 生成文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"校勘记_{request.version1_name}_{request.version2_name}_{timestamp}.{file_ext}"

        return {
            "success": True,
            "content": content,
            "format": export_format,
            "content_type": content_type,
            "filename": filename,
            "note_count": len(notes),
            "statistics": {
                "total_notes": len(notes),
                "by_type": collation_note_service._compute_note_statistics(notes)["by_type"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        print(f"[导出校勘记] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[导出校勘记] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出校勘记失败: {str(e)}"
        )
