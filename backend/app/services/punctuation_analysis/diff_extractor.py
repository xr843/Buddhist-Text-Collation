"""
标点差异提取模块

包含：
- 精确位置比较算法
- 对齐算法比较
- 差异类型判断
"""
from typing import List, Dict
from difflib import SequenceMatcher

from .constants import (
    PUNCT_MARKS_SET,
    PUNCTUATION_CATEGORIES,
    PUNCTUATION_NAMES,
)
from .text_utils import (
    normalize_text,
    build_punctuation_map,
    find_quote_chars,
    find_unknown_puncts,
    extract_clean_text,
)


def extract_punctuation_differences(text1: str, text2: str) -> List[Dict]:
    """
    提取所有标点差异（支持文字有差异的情况）

    算法：
    1. 如果纯文本长度相同，使用精确位置比较（即使有异体字差异）
    2. 如果长度不同，使用对齐算法

    改进：双向位置索引 - 同时记录两个版本的位置
    """
    differences = []
    punct_marks = PUNCT_MARKS_SET

    # 提取纯文本（去除标点和空白字符）
    clean_text1 = extract_clean_text(text1, punct_marks)
    clean_text2 = extract_clean_text(text2, punct_marks)

    print(f"\n=== 后端标点差异提取调试 ===")
    print(f"版本1长度: {len(text1)}, 纯文本长度: {len(clean_text1)}")
    print(f"版本2长度: {len(text2)}, 纯文本长度: {len(clean_text2)}")

    # 调试：检测文本中所有可能的引号类字符
    quotes1 = find_quote_chars(text1)
    quotes2 = find_quote_chars(text2)
    if quotes1:
        print(f"📝 版本1中的引号字符: {quotes1}")
    if quotes2:
        print(f"📝 版本2中的引号字符: {quotes2}")

    # 检查是否有引号未被识别
    for char, info in quotes2.items():
        if char not in punct_marks:
            print(f"❌ 版本2的引号 '{char}' (Unicode: {info['unicode']}) 未在标点集合中!")
    for char, info in quotes1.items():
        if char not in punct_marks:
            print(f"❌ 版本1的引号 '{char}' (Unicode: {info['unicode']}) 未在标点集合中!")

    # 调试：检测文本中可能遗漏的标点字符
    unknown1 = find_unknown_puncts(text1, punct_marks)
    unknown2 = find_unknown_puncts(text2, punct_marks)
    if unknown1:
        print(f"⚠️ 版本1中发现未识别的可能标点: {unknown1} (Unicode: {[hex(ord(c)) for c in unknown1]})")
    if unknown2:
        print(f"⚠️ 版本2中发现未识别的可能标点: {unknown2} (Unicode: {[hex(ord(c)) for c in unknown2]})")

    # 关键改进：只要纯文本长度相同，就使用精确位置比较
    if len(clean_text1) == len(clean_text2):
        differences = _extract_differences_exact(
            text1, text2, clean_text1, clean_text2, punct_marks
        )
    else:
        # 长度不同：使用对齐算法
        print(f"⚠️ 纯文本长度不同 ({len(clean_text1)} vs {len(clean_text2)})，使用对齐算法")

        # 标准化纯文本（统一异体字）
        normalized_text1 = normalize_text(clean_text1)
        normalized_text2 = normalize_text(clean_text2)

        differences = _extract_differences_with_alignment(
            text1, text2,
            clean_text1, clean_text2,
            normalized_text1, normalized_text2,
            punct_marks
        )

    print(f"总共发现 {len(differences)} 处标点差异")
    print(f"=== 调试结束 ===\n")

    return differences


def _extract_differences_exact(
    text1: str, text2: str,
    clean_text1: str, clean_text2: str,
    punct_marks: set
) -> List[Dict]:
    """
    精确位置比较算法（纯文本长度相同时使用）
    """
    differences = []

    print(f"✓ 纯文本长度相同，使用精确位置比较算法")
    punct_map1 = build_punctuation_map(text1, punct_marks)
    punct_map2 = build_punctuation_map(text2, punct_marks)

    print(f"版本1标点映射数量: {len(punct_map1)}")
    print(f"版本2标点映射数量: {len(punct_map2)}")

    # 检查句首标点差异（索引 -1）
    start_punct1 = punct_map1.get(-1, '')
    start_punct2 = punct_map2.get(-1, '')
    if start_punct1 != start_punct2:
        print(f"✓ 发现句首标点差异: v1='{start_punct1 or '无'}', v2='{start_punct2 or '无'}'")
        first_char = clean_text1[0] if clean_text1 else ''
        first_char2 = clean_text2[0] if clean_text2 else ''
        differences.append({
            "id": len(differences) + 1,
            "position": -1,  # 句首标点特殊位置
            "position_v1": -1,
            "position_v2": -1,
            "character": f"[句首]{first_char}",
            "character_v2": f"[句首]{first_char2}",
            "version1_punct": start_punct1 or "无",
            "version2_punct": start_punct2 or "无",
            "context": clean_text1[:30] if clean_text1 else "",
            "context_full": clean_text1[:30] if clean_text1 else "",
            "diff_type": get_diff_type(start_punct1, start_punct2),
            "category": get_punctuation_category(start_punct1, start_punct2),
            "punctuation_name": get_punctuation_name(start_punct1, start_punct2)
        })

    for i in range(len(clean_text1)):
        punct1 = punct_map1.get(i, '')
        punct2 = punct_map2.get(i, '')

        if punct1 != punct2:
            char = clean_text1[i]
            char2 = clean_text2[i]
            print(f"✓ 发现差异 位置{i}: 字符'{char}'/'{char2}' -> v1='{punct1 or '无'}', v2='{punct2 or '无'}'")

            context_start = max(0, i - 15)
            context_end = min(len(clean_text1), i + 15)

            differences.append({
                "id": len(differences) + 1,
                "position": i,  # 保留兼容性
                "position_v1": i,  # 版本1中的位置
                "position_v2": i,  # 版本2中的位置（长度相同时位置相同）
                "character": char,
                "character_v2": char2,  # 版本2中对应的字符
                "version1_punct": punct1 or "无",
                "version2_punct": punct2 or "无",
                "context": clean_text1[context_start:context_end],
                "context_full": clean_text1[context_start:context_end],
                "diff_type": get_diff_type(punct1, punct2),
                "category": get_punctuation_category(punct1, punct2),
                "punctuation_name": get_punctuation_name(punct1, punct2)
            })

    return differences


def _extract_differences_with_alignment(
    text1: str, text2: str,
    clean_text1: str, clean_text2: str,
    normalized_text1: str, normalized_text2: str,
    punct_marks: set
) -> List[Dict]:
    """
    使用字符级对齐算法比较标点差异（适用于个别字差异的场景）

    改进算法：确保所有对齐的字符对都正确比较标点，支持双向位置索引
    """
    differences = []

    # 构建标点映射
    punct_map1 = build_punctuation_map(text1, punct_marks)
    punct_map2 = build_punctuation_map(text2, punct_marks)

    # 使用标准化文本进行对齐
    matcher = SequenceMatcher(None, normalized_text1, normalized_text2)
    opcodes = matcher.get_opcodes()

    # 记录已比较过的位置，避免重复
    compared_positions = set()

    print(f"字符对齐分析：共 {len(opcodes)} 个操作块")

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            # 相同字符块：精确比较标点
            for k in range(i2 - i1):
                pos1 = i1 + k
                pos2 = j1 + k

                if pos1 in compared_positions:
                    continue
                compared_positions.add(pos1)

                char1 = clean_text1[pos1]
                char2 = clean_text2[pos2] if pos2 < len(clean_text2) else ''
                punct1 = punct_map1.get(pos1, '')
                punct2 = punct_map2.get(pos2, '')

                if punct1 != punct2:
                    _add_difference(
                        differences, pos1, pos2, char1, char2,
                        punct1, punct2, clean_text1, clean_text2
                    )

        elif tag == 'replace':
            # 替换块：尽可能比较标点
            len1 = i2 - i1
            len2 = j2 - j1

            # 使用较短的长度进行1:1比较
            min_len = min(len1, len2)
            for k in range(min_len):
                pos1 = i1 + k
                pos2 = j1 + k

                if pos1 in compared_positions:
                    continue
                compared_positions.add(pos1)

                char1 = clean_text1[pos1]
                char2 = clean_text2[pos2] if pos2 < len(clean_text2) else ''
                punct1 = punct_map1.get(pos1, '')
                punct2 = punct_map2.get(pos2, '')

                if punct1 != punct2:
                    _add_difference(
                        differences, pos1, pos2, char1, char2,
                        punct1, punct2, clean_text1, clean_text2,
                        note=f"(异文: {char1}↔{char2})"
                    )

            # 处理版本1多出的字符
            for k in range(min_len, len1):
                pos1 = i1 + k
                if pos1 in compared_positions:
                    continue
                compared_positions.add(pos1)

                char1 = clean_text1[pos1]
                punct1 = punct_map1.get(pos1, '')
                if punct1:
                    nearest_pos2 = j2 - 1 if j2 > 0 else 0
                    _add_difference(
                        differences, pos1, nearest_pos2, char1, '',
                        punct1, '', clean_text1, clean_text2,
                        note="(版本2无对应字)"
                    )

            # 处理版本2多出的字符
            for k in range(min_len, len2):
                pos2 = j1 + k
                punct2 = punct_map2.get(pos2, '')
                if punct2:
                    nearest_pos1 = i2 - 1 if i2 > 0 else 0
                    if nearest_pos1 not in compared_positions:
                        char1 = clean_text1[nearest_pos1] if nearest_pos1 < len(clean_text1) else ''
                        char2 = clean_text2[pos2] if pos2 < len(clean_text2) else ''
                        _add_difference(
                            differences, nearest_pos1, pos2, char1, char2,
                            '', punct2, clean_text1, clean_text2,
                            note=f"(版本2多出字: {char2})"
                        )

        elif tag == 'delete':
            # 版本1有，版本2没有的字符
            for k in range(i2 - i1):
                pos1 = i1 + k
                if pos1 in compared_positions:
                    continue
                compared_positions.add(pos1)

                char1 = clean_text1[pos1]
                punct1 = punct_map1.get(pos1, '')
                if punct1:
                    nearest_pos2 = j1 - 1 if j1 > 0 else 0
                    _add_difference(
                        differences, pos1, nearest_pos2, char1, '',
                        punct1, '', clean_text1, clean_text2,
                        note="(版本2无此字)"
                    )

        elif tag == 'insert':
            # 版本2有，版本1没有的字符
            for k in range(j2 - j1):
                pos2 = j1 + k
                punct2 = punct_map2.get(pos2, '')
                if punct2:
                    nearest_pos1 = i1 - 1 if i1 > 0 else 0
                    char1 = clean_text1[nearest_pos1] if nearest_pos1 < len(clean_text1) else ''
                    char2 = clean_text2[pos2] if pos2 < len(clean_text2) else ''
                    _add_difference(
                        differences, nearest_pos1, pos2, char1, char2,
                        '', punct2, clean_text1, clean_text2,
                        note=f"(版本2多出字: {char2})"
                    )

    # 按位置排序并重新编号，去重
    differences.sort(key=lambda x: x["position"])
    seen_positions = set()
    unique_differences = []
    for diff in differences:
        if diff["position"] not in seen_positions:
            seen_positions.add(diff["position"])
            unique_differences.append(diff)

    for i, diff in enumerate(unique_differences):
        diff["id"] = i + 1

    print(f"对齐算法发现 {len(unique_differences)} 处标点差异")
    return unique_differences


def _add_difference(
    differences: List[Dict],
    pos1: int, pos2: int,
    char1: str, char2: str,
    punct1: str, punct2: str,
    clean_text1: str, clean_text2: str,
    note: str = ""
):
    """添加一个标点差异到列表（支持双向位置索引）"""
    context_start = max(0, pos1 - 15)
    context_end = min(len(clean_text1), pos1 + 15)

    diff_entry = {
        "id": len(differences) + 1,
        "position": pos1,  # 保留兼容性
        "position_v1": pos1,  # 版本1中的位置
        "position_v2": pos2,  # 版本2中的位置
        "character": char1,
        "character_v2": char2,
        "version1_punct": punct1 or "无",
        "version2_punct": punct2 or "无",
        "context": clean_text1[context_start:context_end],
        "context_full": clean_text1[context_start:context_end],
        "diff_type": get_diff_type(punct1, punct2),
        "category": get_punctuation_category(punct1, punct2),
        "punctuation_name": get_punctuation_name(punct1, punct2)
    }

    if note:
        diff_entry["note"] = note

    differences.append(diff_entry)


def get_diff_type(punct1: str, punct2: str) -> str:
    """
    判断差异类型

    改进：对连续标点进行更精确的判断
    """
    if not punct1:
        return "新增标点"
    elif not punct2:
        return "删除标点"
    else:
        # 检查是否有共同前缀
        common_prefix_len = 0
        min_len = min(len(punct1), len(punct2))
        for i in range(min_len):
            if punct1[i] == punct2[i]:
                common_prefix_len += 1
            else:
                break

        if common_prefix_len == 0:
            return "替换标点"
        elif common_prefix_len == len(punct1) and len(punct2) > len(punct1):
            return "新增标点"
        elif common_prefix_len == len(punct2) and len(punct1) > len(punct2):
            return "删除标点"
        else:
            return "替换标点"


def get_punctuation_category(punct1: str, punct2: str) -> str:
    """获取标点符号类别"""
    punct = punct1 if punct1 else punct2

    for category, symbols in PUNCTUATION_CATEGORIES.items():
        if any(p in symbols for p in punct):
            return category

    return "其他"


def get_punctuation_name(punct1: str, punct2: str) -> str:
    """获取标点符号的具体名称"""
    punct = punct1 if punct1 else punct2

    if not punct or punct == "无":
        return "无标点"

    first_punct = punct[0]

    if first_punct in PUNCTUATION_NAMES:
        return PUNCTUATION_NAMES[first_punct]

    return first_punct
