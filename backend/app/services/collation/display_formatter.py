"""
显示格式化模块
从 collation_service.py 中提取
"""
from typing import List, Dict, Callable

from .transposition_detector import is_transposition


def analyze_replace_segment_for_display(
    t1: str,
    t2: str,
    is_variant_func: Callable[[str, str], bool]
) -> tuple:
    """
    对 replace segment 进行字符级细分，用于前端显示

    使用与 compute_alignment_statistics 完全相同的逻辑，确保数据一致性

    Args:
        t1: 版本1的文本
        t2: 版本2的文本
        is_variant_func: 异体字判断函数

    Returns:
        (segments1, segments2) - 两个版本的细分 segment 列表
    """
    import difflib

    segments1 = []
    segments2 = []

    # 使用 difflib 进行字符级对齐
    sub_matcher = difflib.SequenceMatcher(None, t1, t2, autojunk=False)

    for sub_tag, si1, si2, sj1, sj2 in sub_matcher.get_opcodes():
        if sub_tag == "equal":
            # 相同部分
            text = t1[si1:si2]
            for char in text:
                segments1.append({"text": char, "type": "equal", "is_punct": False, "category": None})
                segments2.append({"text": char, "type": "equal", "is_punct": False, "category": None})
        elif sub_tag == "delete":
            # 版本1有，版本2无 → 脱文
            for char in t1[si1:si2]:
                segments1.append({"text": char, "type": "delete", "is_punct": False, "category": "tuowen"})
        elif sub_tag == "insert":
            # 版本1无，版本2有 → 衍文
            for char in t2[sj1:sj2]:
                segments2.append({"text": char, "type": "insert", "is_punct": False, "category": "yanwen"})
        elif sub_tag == "replace":
            # 替换：需要进一步细分（与 compute_alignment_statistics 完全一致）
            sub_t1 = t1[si1:si2]
            sub_t2 = t2[sj1:sj2]

            if len(sub_t1) == 1 and len(sub_t2) == 1:
                # 单字符对单字符：判断异体字/讹误
                category = "variant" if is_variant_func(sub_t1, sub_t2) else "error"
                segments1.append({"text": sub_t1, "type": "replace", "is_punct": False, "category": category})
                segments2.append({"text": sub_t2, "type": "replace", "is_punct": False, "category": category})
            elif len(sub_t1) == len(sub_t2):
                # 长度相等的多字符替换
                # 核心修复：对于长度相等的情况，直接逐字符配对
                # 因为 difflib 无法识别异体字关系（如 即→卽, 為→爲）
                # 它们在 Unicode 编码上完全不同，difflib 会返回整体 replace
                # 但我们应该逐字符判断是异体字还是讹误
                for i in range(len(sub_t1)):
                    char1 = sub_t1[i]
                    char2 = sub_t2[i]
                    category = "variant" if is_variant_func(char1, char2) else "error"
                    segments1.append({"text": char1, "type": "replace", "is_punct": False, "category": category})
                    segments2.append({"text": char2, "type": "replace", "is_punct": False, "category": category})
            else:
                # 长度不等：无法确定配对，分别作为脱文和衍文处理
                for char in sub_t1:
                    segments1.append({"text": char, "type": "delete", "is_punct": False, "category": "tuowen"})
                for char in sub_t2:
                    segments2.append({"text": char, "type": "insert", "is_punct": False, "category": "yanwen"})

    return segments1, segments2


def split_aligned_segments_for_display(
    aligned_segments: List[Dict],
    is_variant_func: Callable[[str, str], bool],
    target_length: int = 80
) -> List[Dict]:
    """
    将全局对齐结果分段，用于前端展示

    核心原则：保持两个版本的对齐关系
    - 基于对齐结果分块，不是各自按字数分块
    - 同一块内的文字是对齐的，方便用户比对

    Args:
        aligned_segments: 全局对齐的segments（已经对齐好的）
        is_variant_func: 异体字判断函数
        target_length: 每块目标字数（默认80字）

    Returns:
        展示块列表
    """
    if not aligned_segments:
        return []

    display_blocks = []
    current_segments = []
    current_len = 0  # 以较长的一方计算长度

    def flush_block():
        """将当前累积的segments生成一个展示块"""
        nonlocal current_segments, current_len

        if not current_segments:
            return

        # 拼接文本和构建高亮segments
        text1_parts = []
        text2_parts = []
        segments1 = []
        segments2 = []
        has_diff = False

        for seg in current_segments:
            t1 = seg["text1"]
            t2 = seg["text2"]
            seg_type = seg["type"]

            text1_parts.append(t1)
            text2_parts.append(t2)

            if seg_type == "equal":
                if t1:
                    segments1.append({"text": t1, "type": "equal", "is_punct": False, "category": None})
                if t2:
                    segments2.append({"text": t2, "type": "equal", "is_punct": False, "category": None})
            else:
                has_diff = True
                # 根据类型确定 category
                if seg_type == "delete":
                    # 脱文：逐字符添加，便于精确定位
                    for char in t1:
                        segments1.append({"text": char, "type": "delete", "is_punct": False, "category": "tuowen"})
                elif seg_type == "insert":
                    # 衍文：逐字符添加，便于精确定位
                    for char in t2:
                        segments2.append({"text": char, "type": "insert", "is_punct": False, "category": "yanwen"})
                elif seg_type == "replace":
                    # 优先检测倒文（2-3字反序）- 倒文归类为讹误
                    if is_transposition(t1, t2):
                        # 倒文作为整体处理，归类为讹误
                        if t1:
                            segments1.append({"text": t1, "type": "replace", "is_punct": False, "category": "error"})
                        if t2:
                            segments2.append({"text": t2, "type": "replace", "is_punct": False, "category": "error"})
                    else:
                        # 关键修复：对 replace segment 进行字符级细分
                        # 使用与 compute_alignment_statistics 相同的逻辑
                        sub_segs1, sub_segs2 = analyze_replace_segment_for_display(t1, t2, is_variant_func)
                        segments1.extend(sub_segs1)
                        segments2.extend(sub_segs2)
                else:
                    # 未知类型，保持原样
                    if t1:
                        segments1.append({"text": t1, "type": seg_type, "is_punct": False, "category": None})
                    if t2:
                        segments2.append({"text": t2, "type": seg_type, "is_punct": False, "category": None})

        block = {
            "id": len(display_blocks) + 1,
            "type": "replace" if has_diff else "equal",
            "sentence1": "".join(text1_parts),
            "sentence2": "".join(text2_parts),
            "has_diff": has_diff,
            "char_diff": {
                "segments1": segments1,
                "segments2": segments2,
                "diff_type": "text_only" if has_diff else None,
            } if segments1 or segments2 else None,
            "index1": None,
            "index2": None,
        }

        display_blocks.append(block)
        current_segments = []
        current_len = 0

    # 遍历对齐好的segments，按累积字数分块
    for seg in aligned_segments:
        t1 = seg["text1"]
        t2 = seg["text2"]
        seg_type = seg["type"]
        seg_len = max(len(t1), len(t2))  # 以较长的一方计算

        # 如果这个segment很长，需要拆分
        if seg_len > target_length:
            # 先flush当前累积的
            if current_segments:
                flush_block()

            # 拆分长segment，保持对齐
            start = 0
            while start < max(len(t1), len(t2)):
                end = start + target_length
                chunk1 = t1[start:end] if start < len(t1) else ""
                chunk2 = t2[start:end] if start < len(t2) else ""

                # 只有当两边都取完了，或者至少有一边有内容时才创建块
                if chunk1 or chunk2:
                    current_segments = [{
                        "type": seg_type,
                        "text1": chunk1,
                        "text2": chunk2,
                    }]
                    flush_block()

                start = end
        else:
            # 检查是否需要先flush（累积超过目标长度）
            if current_len + seg_len > target_length and current_segments:
                flush_block()

            # 添加到当前块
            current_segments.append(seg)
            current_len += seg_len

    # 处理剩余的
    flush_block()

    # 后处理：合并"孤儿块"（太小的块合并到相邻块）
    min_block_size = 20  # 最小块长度阈值
    display_blocks = merge_orphan_blocks(display_blocks, min_block_size)

    print(f"[分块] 按{target_length}字分块（保持对齐），合并孤儿块后共 {len(display_blocks)} 块")

    return display_blocks


def merge_orphan_blocks(blocks: List[Dict], min_size: int) -> List[Dict]:
    """
    合并"孤儿块"（太小的块合并到相邻块）

    Args:
        blocks: 原始块列表
        min_size: 最小块长度阈值，小于此值的块会被合并

    Returns:
        合并后的块列表
    """
    if len(blocks) <= 1:
        return blocks

    merged_blocks = []

    for block in blocks:
        block_len = max(len(block["sentence1"]), len(block["sentence2"]))

        # 如果块太小且前面有块，合并到前一个块
        if block_len < min_size and merged_blocks:
            prev = merged_blocks[-1]

            # 合并文本
            prev["sentence1"] += block["sentence1"]
            prev["sentence2"] += block["sentence2"]

            # 合并 char_diff segments
            if prev["char_diff"] and block["char_diff"]:
                prev["char_diff"]["segments1"].extend(block["char_diff"]["segments1"])
                prev["char_diff"]["segments2"].extend(block["char_diff"]["segments2"])
                # 更新 diff_type
                if block["has_diff"]:
                    prev["char_diff"]["diff_type"] = "text_only"
            elif block["char_diff"]:
                prev["char_diff"] = block["char_diff"]

            # 更新 has_diff 和 type
            if block["has_diff"]:
                prev["has_diff"] = True
                prev["type"] = "replace"

        else:
            merged_blocks.append(block)

    # 重新分配连续的 ID
    for idx, block in enumerate(merged_blocks):
        block["id"] = idx + 1

    return merged_blocks
