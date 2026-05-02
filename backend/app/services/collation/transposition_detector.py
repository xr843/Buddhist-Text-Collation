"""
倒文检测与合并模块
从 collation_service.py 中提取
"""
from typing import List, Dict


def is_transposition(text1: str, text2: str) -> bool:
    """
    检测是否为倒文（2-6字的字序颠倒）- 宽松定义

    宽松定义：只要字符集合相同但顺序不同，就视为倒文
    例如:
      - "一切" ↔ "切一" (2字倒文)
      - "ABC" ↔ "CBA" (3字完全颠倒)
      - "ABC" ↔ "BCA" (3字循环移位，也算倒文)
      - "如是我闻" ↔ "我闻如是" (4字倒文，佛典常见)
      - "ABCDEF" ↔ "FEDCBA" (6字倒文)

    Args:
        text1: 版本1的文本片段
        text2: 版本2的文本片段

    Returns:
        如果是倒文返回True，否则返回False
    """
    # 长度必须相等
    if len(text1) != len(text2):
        return False
    # 支持2-6字的倒文检测（覆盖佛典四字格律和偈颂半句）
    if len(text1) < 2 or len(text1) > 6:
        return False
    # 文本必须不同（相同不算倒文）
    if text1 == text2:
        return False
    # 宽松定义：字符集合相同但顺序不同
    # 使用 sorted 比较，这样可以检测任意顺序变化
    return sorted(text1) == sorted(text2)


def detect_and_merge_transpositions(segments: List[Dict]) -> List[Dict]:
    """
    后处理：检测倒文并合并相关 segments

    核心问题：diff 算法可能把 "切一" vs "一切" 拆分成：
      - insert '一' (在位置1)
      - equal '切'
      - delete '一' (在位置2)
    而不是识别为倒文。

    检测逻辑（改进版）：
    1. 只从 insert 或 delete 开始扫描窗口
    2. 按顺序收集窗口内的字符，构建底本和校本的文本
    3. 如果字符集合相同（2-3字）且顺序不同，合并为倒文

    Args:
        segments: 原始的 aligned_segments 列表

    Returns:
        处理后的 segments 列表
    """
    if not segments or len(segments) < 2:
        return segments

    result = []
    i = 0

    while i < len(segments):
        seg = segments[i]

        # 只从 insert 或 delete 开始检测倒文
        if seg["type"] not in ("insert", "delete"):
            result.append(seg)
            i += 1
            continue

        # 尝试检测倒文：向后看一个窗口（最多7个segments，支持6字倒文）
        found_transposition = False

        for window_size in [2, 3, 4, 5, 6, 7]:  # 尝试不同窗口大小，支持2-6字倒文
            if i + window_size > len(segments):
                continue

            window = segments[i:i + window_size]

            # 按窗口顺序组合字符（关键修复！）
            text1_order = ""  # 底本字符顺序
            text2_order = ""  # 校本字符顺序
            has_delete = False
            has_insert = False
            first_pos1 = None
            first_pos2 = None

            for seg_in_window in window:
                if seg_in_window["type"] == "delete":
                    text1_order += seg_in_window["text1"]
                    has_delete = True
                    if first_pos1 is None:
                        first_pos1 = seg_in_window.get("pos1")
                elif seg_in_window["type"] == "insert":
                    text2_order += seg_in_window["text2"]
                    has_insert = True
                    if first_pos2 is None:
                        first_pos2 = seg_in_window.get("pos2")
                elif seg_in_window["type"] == "equal":
                    text1_order += seg_in_window["text1"]
                    text2_order += seg_in_window["text2"]
                    if first_pos1 is None:
                        first_pos1 = seg_in_window.get("pos1")
                    if first_pos2 is None:
                        first_pos2 = seg_in_window.get("pos2")

            # 检查是否构成倒文：
            # 条件1: 必须同时有 delete 和 insert
            # 条件2: 字符集合相同
            # 条件3: 总字符数为 2-6（覆盖佛典四字格律和偈颂半句）
            # 条件4: 顺序不同
            if (has_delete and has_insert and
                len(text1_order) >= 2 and len(text1_order) <= 6 and
                len(text1_order) == len(text2_order) and
                text1_order != text2_order and
                sorted(text1_order) == sorted(text2_order)):

                # 构成倒文！合并为一个 replace segment
                merged_seg = {
                    "type": "replace",
                    "text1": text1_order,
                    "text2": text2_order,
                    "pos1": first_pos1,
                    "pos2": first_pos2,
                    "_is_merged_transposition": True,
                }
                result.append(merged_seg)
                print(f"[倒文检测] 合并 {window_size} 个 segments 为倒文: '{text1_order}' ↔ '{text2_order}'")
                i += window_size
                found_transposition = True
                break

        if not found_transposition:
            result.append(seg)
            i += 1

    return result
