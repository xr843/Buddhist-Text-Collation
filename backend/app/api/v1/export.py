"""
导出API端点
支持Word、TEI XML、CSV、Markdown等多种格式
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import csv
from io import StringIO, BytesIO

from app.services.export_word_service import WordExportService
from app.services.export_tei_service import TEIExportService
from app.services.local_storage_service import ProjectService, ExportHistoryService

router = APIRouter()


class ExportRequest(BaseModel):
    """导出请求"""
    project_id: Optional[int] = None  # 从数据库加载项目
    collation_data: Optional[Dict[str, Any]] = None  # 或直接传入数据
    export_format: str  # word, tei_xml, csv, markdown
    report_type: str = "multi_version"  # two_version 或 multi_version
    filename: Optional[str] = None


@router.post("/export/collation")
async def export_collation(request: ExportRequest):
    """
    导出校勘报告

    支持格式：
    - word: Microsoft Word格式（.docx）
    - tei_xml: TEI P5 XML格式（.xml）
    - csv: 逗号分隔值（.csv）
    - markdown: Markdown格式（.md）
    """
    # 获取数据
    if request.project_id:
        project = ProjectService.get_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        collation_data = {
            'base_name': project.base_name,
            'base_text': project.base_text,
            'collations': project.collation_texts_json or [],
            'differences': project.results_json.get('differences', []) if project.results_json else [],
            'statistics': project.results_json.get('statistics', {}) if project.results_json else {}
        }
    elif request.collation_data:
        collation_data = request.collation_data
    else:
        raise HTTPException(status_code=400, detail="必须提供project_id或collation_data")

    # 生成文件名
    base_name = collation_data.get('base_name', '校勘报告')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = request.filename or f"{base_name}_{timestamp}"

    # 根据格式导出
    try:
        if request.export_format == "word":
            return await export_word(collation_data, filename, request.report_type)
        elif request.export_format == "tei_xml":
            return await export_tei_xml(collation_data, filename)
        elif request.export_format == "csv":
            return await export_csv(collation_data, filename)
        elif request.export_format == "markdown":
            return await export_markdown(collation_data, filename)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {request.export_format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


async def export_word(collation_data: Dict, filename: str, report_type: str):
    """导出Word格式"""
    buffer = WordExportService.export_collation_report(collation_data, report_type)

    # 记录导出历史（如果有project_id）
    # ExportHistoryService.record_export(...)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.docx"
        }
    )


async def export_tei_xml(collation_data: Dict, filename: str):
    """导出TEI XML格式"""
    xml_string = TEIExportService.export_collation_tei(collation_data)

    # 验证XML
    is_valid, error = TEIExportService.validate_tei_xml(xml_string)
    if not is_valid:
        raise HTTPException(status_code=500, detail=f"生成的TEI XML无效: {error}")

    return Response(
        content=xml_string.encode('utf-8'),
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.xml"
        }
    )


async def export_csv(collation_data: Dict, filename: str):
    """导出CSV格式（增强版）"""
    output = StringIO()
    writer = csv.writer(output)

    # 基本信息
    writer.writerow(['# 校勘报告'])
    writer.writerow(['底本', collation_data.get('base_name', '')])

    collations = collation_data.get('collations', [])
    if collations:
        collation_names = ', '.join([c.get('name', '') for c in collations])
        writer.writerow(['校本', collation_names])

    differences = collation_data.get('differences', [])
    writer.writerow(['异文总数', len(differences)])
    writer.writerow(['生成时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])  # 空行

    # 统计信息
    statistics = collation_data.get('statistics', {})
    if statistics:
        writer.writerow(['# 统计信息'])
        if 'by_category' in statistics:
            for category, count in statistics['by_category'].items():
                writer.writerow([f'{category}', count])
        writer.writerow([])

    # 异文汇校表
    writer.writerow(['# 异文汇校表'])

    # 表头
    headers = ['序号', '位置', '上下文', '底本']
    for collation in collations:
        headers.append(collation.get('name', '校本'))
    headers.extend(['类型', '说明'])
    writer.writerow(headers)

    # 数据行
    for idx, diff in enumerate(differences, 1):
        row = [
            idx,
            diff.get('position', ''),
            diff.get('context', ''),
            diff.get('base_char', '')
        ]

        # 各校本异文
        variants_by_name = {v['name']: v for v in diff.get('variants', [])}
        for collation in collations:
            variant = variants_by_name.get(collation['name'])
            if variant:
                char = variant.get('char', '')
                category = variant.get('category', '')
                row.append(f"{char} ({category})")
            else:
                row.append('同底本')

        row.append(diff.get('category', ''))
        row.append(diff.get('note', ''))

        writer.writerow(row)

    # 返回CSV
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.csv"
        }
    )


async def export_markdown(collation_data: Dict, filename: str):
    """导出Markdown格式"""
    md_lines = []

    # 标题
    md_lines.append(f"# 校勘记\n")

    # 基本信息
    md_lines.append(f"## 基本信息\n")
    md_lines.append(f"- **底本**：{collation_data.get('base_name', '未命名')}")

    collations = collation_data.get('collations', [])
    if collations:
        collation_names = ', '.join([c.get('name', '') for c in collations])
        md_lines.append(f"- **校本**：{collation_names}")

    differences = collation_data.get('differences', [])
    md_lines.append(f"- **异文总数**：{len(differences)}")
    md_lines.append(f"- **生成时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n")

    # 统计信息
    statistics = collation_data.get('statistics', {})
    if statistics and 'by_category' in statistics:
        md_lines.append(f"## 统计分析\n")
        md_lines.append(f"### 异文类型分布\n")
        for category, count in statistics['by_category'].items():
            category_names = {
                'error': '讹误',
                'variant': '异体字',
                'yanwen': '衍文',
                'tuowen': '脱文',
                'daowen': '倒文'
            }
            cat_name = category_names.get(category, category)
            md_lines.append(f"- **{cat_name}**：{count}处")
        md_lines.append("")

    # 异文汇校表
    md_lines.append(f"## 异文汇校表\n")

    if differences:
        # Markdown表格
        headers = ['序号', '上下文', '底本'] + [c.get('name', f'校本{i+1}') for i, c in enumerate(collations)] + ['类型']
        md_lines.append('| ' + ' | '.join(headers) + ' |')
        md_lines.append('|' + '|'.join(['---' for _ in headers]) + '|')

        for idx, diff in enumerate(differences[:100], 1):  # 限制100条
            row = [
                str(idx),
                diff.get('context', '')[:15],  # 限制长度
                diff.get('base_char', '')
            ]

            variants_by_name = {v['name']: v for v in diff.get('variants', [])}
            for collation in collations:
                variant = variants_by_name.get(collation['name'])
                if variant:
                    char = variant.get('char', '')
                    category = variant.get('category', '')
                    # 根据类型添加标记
                    if category == 'error':
                        row.append(f'**{char}** 🔴')
                    elif category == 'variant':
                        row.append(f'{char} 🟢')
                    else:
                        row.append(char)
                else:
                    row.append('同底本')

            category = diff.get('category', '')
            category_names = {
                'error': '讹误',
                'variant': '异体字',
                'yanwen': '衍文',
                'tuowen': '脱文',
                'daowen': '倒文'
            }
            row.append(category_names.get(category, category))

            md_lines.append('| ' + ' | '.join(row) + ' |')

        if len(differences) > 100:
            md_lines.append(f"\n*注：仅显示前100条，完整数据请导出CSV格式*\n")
    else:
        md_lines.append("（无异文）\n")

    # 页脚
    md_lines.append(f"\n---\n")
    md_lines.append(f"*本报告由[佛典标点与校勘研究平台](https://github.com)生成于{datetime.now().strftime('%Y年%m月%d日')}*")

    markdown_content = '\n'.join(md_lines)

    return Response(
        content=markdown_content.encode('utf-8'),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.md"
        }
    )


@router.post("/export/phylogeny")
async def export_phylogeny(
    phylogeny_data: Dict[str, Any],
    export_format: str = "word",  # word, json
    filename: Optional[str] = None
):
    """导出版本谱系分析报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = filename or f"版本谱系分析_{timestamp}"

    try:
        if export_format == "word":
            buffer = WordExportService.export_phylogeny_report(phylogeny_data)
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.docx"
                }
            )
        elif export_format == "json":
            import json
            json_str = json.dumps(phylogeny_data, ensure_ascii=False, indent=2)
            return Response(
                content=json_str.encode('utf-8'),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.json"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
