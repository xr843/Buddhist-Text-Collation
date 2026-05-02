"""
CSV导出模块
从 collation_service.py 中提取
"""
import csv
import io
from typing import List, Dict


def export_to_csv(
    aligned_segments: List[Dict],
    statistics: dict,
    version1_name: str = "版本A",
    version2_name: str = "版本B",
) -> str:
    """
    将差异结果导出为 CSV 格式

    Args:
        aligned_segments: 全局对齐的segments
        statistics: 统计信息（包含 diff_details）
        version1_name: 版本1名称
        version2_name: 版本2名称

    Returns:
        CSV 格式的字符串
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # ===== 第一部分：统计摘要 =====
    writer.writerow(["=" * 20 + " 统计摘要 " + "=" * 20])
    writer.writerow([])
    writer.writerow(["项目", "数值"])
    writer.writerow([f"{version1_name}字数", statistics.get("version1_length", 0)])
    writer.writerow([f"{version2_name}字数", statistics.get("version2_length", 0)])
    writer.writerow(["总差异处数", statistics.get("total_differences", 0)])
    writer.writerow(["替换次数", statistics.get("replacements", 0)])
    writer.writerow(["删除次数", statistics.get("deletions", 0)])
    writer.writerow(["新增次数", statistics.get("insertions", 0)])
    writer.writerow(["总改动字符数", statistics.get("total_changed_chars", 0)])
    writer.writerow([])

    # ===== 第二部分：详细差异列表 =====
    diff_details = statistics.get("diff_details", {})

    # 替换表
    writer.writerow(["=" * 20 + " 替换详情 " + "=" * 20])
    writer.writerow([])
    writer.writerow(["序号", f"{version1_name}（原）", f"{version2_name}（新）", "出现次数"])
    replaced = diff_details.get("replaced", [])
    for idx, item in enumerate(replaced, 1):
        writer.writerow([idx, item["from"], item["to"], item["count"]])
    if not replaced:
        writer.writerow(["", "（无替换）", "", ""])
    writer.writerow([])

    # 删除表
    writer.writerow(["=" * 20 + " 删除详情 " + "=" * 20])
    writer.writerow([])
    writer.writerow(["序号", f"{version1_name}有/{version2_name}无", "出现次数"])
    deleted = diff_details.get("deleted", [])
    for idx, item in enumerate(deleted, 1):
        writer.writerow([idx, item["char"], item["count"]])
    if not deleted:
        writer.writerow(["", "（无删除）", ""])
    writer.writerow([])

    # 新增表
    writer.writerow(["=" * 20 + " 新增详情 " + "=" * 20])
    writer.writerow([])
    writer.writerow(["序号", f"{version1_name}无/{version2_name}有", "出现次数"])
    inserted = diff_details.get("inserted", [])
    for idx, item in enumerate(inserted, 1):
        writer.writerow([idx, item["char"], item["count"]])
    if not inserted:
        writer.writerow(["", "（无新增）", ""])
    writer.writerow([])

    # ===== 第三部分：逐条差异记录（含上下文） =====
    writer.writerow(["=" * 20 + " 逐条差异记录 " + "=" * 20])
    writer.writerow([])
    writer.writerow(["序号", "差异类型", f"{version1_name}文字", f"{version2_name}文字", "上下文（前）", "上下文（后）"])

    diff_idx = 0
    context_len = 10  # 上下文长度

    for i, seg in enumerate(aligned_segments):
        if seg["type"] != "equal":
            diff_idx += 1
            seg_type = seg["type"]
            text1 = seg["text1"]
            text2 = seg["text2"]

            # 获取上下文
            context_before = ""
            context_after = ""

            # 向前找上下文
            for j in range(i - 1, -1, -1):
                prev_text = aligned_segments[j]["text1"] or aligned_segments[j]["text2"]
                context_before = prev_text + context_before
                if len(context_before) >= context_len:
                    context_before = context_before[-context_len:]
                    break

            # 向后找上下文
            for j in range(i + 1, len(aligned_segments)):
                next_text = aligned_segments[j]["text1"] or aligned_segments[j]["text2"]
                context_after = context_after + next_text
                if len(context_after) >= context_len:
                    context_after = context_after[:context_len]
                    break

            # 类型映射
            type_map = {
                "replace": "替换",
                "delete": "删除",
                "insert": "新增",
            }

            writer.writerow([
                diff_idx,
                type_map.get(seg_type, seg_type),
                text1 or "（无）",
                text2 or "（无）",
                context_before,
                context_after,
            ])

    if diff_idx == 0:
        writer.writerow(["", "（无差异）", "", "", "", ""])

    return output.getvalue()
