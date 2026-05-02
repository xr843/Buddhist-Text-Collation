"""
统计计算模块
从 collation_service.py 中提取
"""
import difflib
from collections import Counter
from typing import List, Dict, Callable

from .transposition_detector import is_transposition


def compute_alignment_statistics(
    aligned_segments: List[Dict],
    text1: str,
    text2: str,
    is_variant_func: Callable[[str, str], bool],
    classify_func: Callable[[str, str], str]
) -> dict:
    """
    计算对齐统计信息，包括详细的差异字符统计

    Args:
        aligned_segments: 对齐后的segments列表
        text1: 版本1文本
        text2: 版本2文本
        is_variant_func: 异体字判断函数
        classify_func: 差异分类函数

    返回：
    - 基础统计（总差异数、各类型数量等）
    - 详细差异（具体哪些字被删除/插入/替换，及出现次数）
    """
    total_diffs = 0
    inserted_chars = 0
    deleted_chars = 0
    replaced_chars = 0

    # 详细差异收集
    deleted_list = []      # 被删除的字符
    inserted_list = []     # 被插入的字符
    replaced_pairs = []    # 替换对 (原字符, 新字符)
    transposed_pairs = []  # 倒文对 (原文本, 新文本)

    for seg in aligned_segments:
        if seg["type"] == "insert":
            total_diffs += 1
            text = seg["text2"]
            inserted_chars += len(text)
            inserted_list.extend(list(text))

        elif seg["type"] == "delete":
            total_diffs += 1
            text = seg["text1"]
            deleted_chars += len(text)
            deleted_list.extend(list(text))

        elif seg["type"] == "replace":
            total_diffs += 1
            t1 = seg["text1"]
            t2 = seg["text2"]
            replaced_chars += max(len(t1), len(t2))

            # 优先检测倒文（2-3字反序）
            if is_transposition(t1, t2):
                transposed_pairs.append((t1, t2))
                continue  # 倒文不再做字符级细分

            # 使用 difflib 进行字符级对齐，确保正确配对
            sub_matcher = difflib.SequenceMatcher(None, t1, t2, autojunk=False)

            for sub_tag, si1, si2, sj1, sj2 in sub_matcher.get_opcodes():
                if sub_tag == "equal":
                    # 相同，跳过
                    pass
                elif sub_tag == "delete":
                    # 版本1有，版本2无 → 删除（脱文）
                    chars = list(t1[si1:si2])
                    deleted_list.extend(chars)
                    deleted_chars += len(chars)
                elif sub_tag == "insert":
                    # 版本1无，版本2有 → 新增（衍文）
                    chars = list(t2[sj1:sj2])
                    inserted_list.extend(chars)
                    inserted_chars += len(chars)
                elif sub_tag == "replace":
                    # 替换：只有单字符对单字符才是真正的一对一替换
                    sub_t1 = t1[si1:si2]
                    sub_t2 = t2[sj1:sj2]

                    if len(sub_t1) == 1 and len(sub_t2) == 1:
                        # 真正的一对一替换（最可靠）
                        replaced_pairs.append((sub_t1, sub_t2))
                    elif len(sub_t1) == len(sub_t2):
                        # 长度相等的多字符替换：逐字符配对
                        for i in range(len(sub_t1)):
                            replaced_pairs.append((sub_t1[i], sub_t2[i]))
                    else:
                        # 长度不等的替换，无法确定配对，分别计入删除和新增
                        del_chars = list(sub_t1)
                        ins_chars = list(sub_t2)
                        deleted_list.extend(del_chars)
                        inserted_list.extend(ins_chars)
                        deleted_chars += len(del_chars)
                        inserted_chars += len(ins_chars)

    # 统计各字符出现次数
    deleted_counter = Counter(deleted_list)
    inserted_counter = Counter(inserted_list)
    replaced_counter = Counter(replaced_pairs)
    transposed_counter = Counter(transposed_pairs)

    # 转换为前端友好的格式，并进行分类
    def counter_to_list(counter, is_pair=False, is_transposed=False):
        """将Counter转换为排序后的列表，并进行分类"""
        items = []
        for item, count in counter.most_common():
            if is_transposed:
                # 倒文：归类为讹误
                items.append({
                    "from": item[0],
                    "to": item[1],
                    "count": count,
                    "category": "error",
                    "category_cn": "讹误（倒文）"
                })
            elif is_pair:
                char1, char2 = item[0], item[1]
                # 分类：异体字 or 讹误
                category = classify_func(char1, char2)
                items.append({
                    "from": char1,
                    "to": char2,
                    "count": count,
                    "category": category,
                    "category_cn": "异体字" if category == "variant" else "讹误"
                })
            else:
                items.append({
                    "char": item,
                    "count": count,
                    "category": "text_diff"
                })
        return items

    # 计算分类统计
    replaced_list = counter_to_list(replaced_counter, is_pair=True)
    transposed_list = counter_to_list(transposed_counter, is_transposed=True)
    variant_count = sum(item["count"] for item in replaced_list if item["category"] == "variant")
    error_count = sum(item["count"] for item in replaced_list if item["category"] == "error")
    daowen_count = sum(item["count"] for item in transposed_list)
    total_error_count = error_count + daowen_count

    return {
        # 基础统计
        "version1_length": len(text1),
        "version2_length": len(text2),
        "total_differences": total_diffs,
        "insertions": sum(1 for s in aligned_segments if s["type"] == "insert"),
        "deletions": sum(1 for s in aligned_segments if s["type"] == "delete"),
        "replacements": sum(1 for s in aligned_segments if s["type"] == "replace"),
        "inserted_chars": inserted_chars,
        "deleted_chars": deleted_chars,
        "replaced_chars": replaced_chars,
        "total_changed_chars": inserted_chars + deleted_chars + replaced_chars,

        # 分类统计（倒文已合并到讹误中）
        "category_stats": {
            "variant_chars": variant_count,
            "error_chars": total_error_count,
            "yanwen_chars": inserted_chars,
            "tuowen_chars": deleted_chars,
        },

        # 详细差异统计（增加分类）
        "diff_details": {
            "deleted": counter_to_list(deleted_counter),
            "inserted": counter_to_list(inserted_counter),
            "replaced": replaced_list,
            "transposed": transposed_list,
        }
    }
