"""
句子级别对齐模块

包含：
- 句子分割
- 块对齐算法
- 对齐数据生成
"""
from typing import List, Dict
from difflib import SequenceMatcher

from .constants import PUNCT_MARKS_SET
from .text_utils import normalize_text, split_into_sentences, extract_clean_text


def generate_sentence_alignment(
    text1: str,
    text2: str,
    differences: List[Dict]
) -> List[Dict]:
    """
    生成句子级别的智能对齐数据

    重要原则：绝不修改原始文本和标点！
    - 内部处理使用标准化文本进行比较
    - 输出结果使用原始文本

    Args:
        text1: 第一个版本的文本（带标点）- 不会被修改
        text2: 第二个版本的文本（带标点）- 不会被修改
        differences: 标点差异列表

    Returns:
        对齐块列表（包含原始文本）
    """
    punct_marks = PUNCT_MARKS_SET

    print(f"\n=== 句子对齐调试（块对齐策略） ===")

    # 按句号分割成句子（保持原始文本！）
    sentences1 = split_into_sentences(text1)
    sentences2 = split_into_sentences(text2)

    print(f"版本1句子数: {len(sentences1)}")
    print(f"版本2句子数: {len(sentences2)}")

    # 提取纯文本和标准化文本（过滤标点和空白字符）
    clean_sentences1 = [extract_clean_text(s, punct_marks) for s in sentences1]
    clean_sentences2 = [extract_clean_text(s, punct_marks) for s in sentences2]
    normalized_sentences1 = [normalize_text(s) for s in clean_sentences1]
    normalized_sentences2 = [normalize_text(s) for s in clean_sentences2]

    # 使用块对齐算法
    result = _align_sentence_blocks(
        sentences1, sentences2,
        clean_sentences1, clean_sentences2,
        normalized_sentences1, normalized_sentences2,
        differences
    )

    print(f"总共生成 {len(result)} 个对齐块")
    print(f"=== 对齐调试结束 ===\n")

    return result


def _align_sentence_blocks(
    sentences1: List[str],
    sentences2: List[str],
    clean_sentences1: List[str],
    clean_sentences2: List[str],
    normalized_sentences1: List[str],
    normalized_sentences2: List[str],
    differences: List[Dict],
    target_block_size: int = 3  # 目标每块包含的句子数
) -> List[Dict]:
    """
    块对齐算法：将多个句子合并成块进行对齐

    支持 N句 对 M句 的灵活对齐（N, M 可以是 1-8）
    改进：双向位置索引 - 同时记录两个版本的位置
    """
    n1, n2 = len(sentences1), len(sentences2)
    result = []

    if n1 == 0 and n2 == 0:
        return result

    def get_combined_text(sentences: List[str], start: int, count: int) -> str:
        """合并多个句子的文本"""
        end = min(start + count, len(sentences))
        return ''.join(sentences[start:end])

    def get_combined_normalized(normalized: List[str], start: int, count: int) -> str:
        """合并多个句子的标准化文本"""
        end = min(start + count, len(normalized))
        return ''.join(normalized[start:end])

    def get_combined_clean_length(clean: List[str], start: int, count: int) -> int:
        """计算合并后的纯文本长度"""
        end = min(start + count, len(clean))
        return sum(len(c) for c in clean[start:end])

    def similarity(norm1: str, norm2: str) -> float:
        if not norm1 and not norm2:
            return 1.0
        if not norm1 or not norm2:
            return 0.0
        return SequenceMatcher(None, norm1, norm2).ratio()

    i1, i2 = 0, 0
    alignment_id = 1
    # 双向位置跟踪
    current_clean_pos_v1 = 0
    current_clean_pos_v2 = 0

    # 增大搜索范围到 8 句
    MAX_BLOCK_SIZE = 8

    while i1 < n1 or i2 < n2:
        if i1 >= n1:
            # 版本1结束，版本2剩余全部合并
            remaining2 = ''.join(sentences2[i2:])
            remaining_clean_len_v2 = get_combined_clean_length(clean_sentences2, i2, n2 - i2)
            result.append({
                "id": alignment_id,
                "sentence1": "",
                "sentence2": remaining2,
                "has_diff": True,
                "diff_positions": [],
                "diff_positions_v1": [],
                "diff_positions_v2": [],
                "clean_start_pos": current_clean_pos_v1,  # 兼容性
                "clean_start_pos_v1": current_clean_pos_v1,
                "clean_start_pos_v2": current_clean_pos_v2,
                "clean_end_pos": current_clean_pos_v1,
                "clean_end_pos_v1": current_clean_pos_v1,
                "clean_end_pos_v2": current_clean_pos_v2 + remaining_clean_len_v2,
                "has_text_diff": True,
                "alignment_type": "insert"
            })
            break

        if i2 >= n2:
            # 版本2结束，版本1剩余全部合并
            remaining1 = ''.join(sentences1[i1:])
            remaining_clean_len_v1 = get_combined_clean_length(clean_sentences1, i1, n1 - i1)
            result.append({
                "id": alignment_id,
                "sentence1": remaining1,
                "sentence2": "",
                "has_diff": True,
                "diff_positions": [],
                "diff_positions_v1": [],
                "diff_positions_v2": [],
                "clean_start_pos": current_clean_pos_v1,  # 兼容性
                "clean_start_pos_v1": current_clean_pos_v1,
                "clean_start_pos_v2": current_clean_pos_v2,
                "clean_end_pos": current_clean_pos_v1 + remaining_clean_len_v1,
                "clean_end_pos_v1": current_clean_pos_v1 + remaining_clean_len_v1,
                "clean_end_pos_v2": current_clean_pos_v2,
                "has_text_diff": True,
                "alignment_type": "delete"
            })
            break

        # 尝试不同的块组合，找到最佳匹配
        best_match = None
        best_score = -1

        # 尝试 count1 句 对 count2 句 (1-8句)
        for count1 in range(1, min(MAX_BLOCK_SIZE + 1, n1 - i1 + 1)):
            for count2 in range(1, min(MAX_BLOCK_SIZE + 1, n2 - i2 + 1)):
                norm1 = get_combined_normalized(normalized_sentences1, i1, count1)
                norm2 = get_combined_normalized(normalized_sentences2, i2, count2)
                sim = similarity(norm1, norm2)

                # 基础分 = 相似度
                score = sim

                # 对称性奖励：当 count1 == count2 时给予奖励
                if count1 == count2:
                    score += 0.05

                # 高相似度时的块大小奖励
                if sim > 0.9:
                    size_bonus = min(count1, count2) * 0.01
                    score += size_bonus

                # 块大小差异惩罚
                size_penalty = abs(count1 - count2) * 0.03
                score -= size_penalty

                # 前瞻机制
                next_i1 = i1 + count1
                next_i2 = i2 + count2
                if next_i1 < n1 and next_i2 < n2:
                    next_norm1 = normalized_sentences1[next_i1]
                    next_norm2 = normalized_sentences2[next_i2]
                    next_sim = similarity(next_norm1, next_norm2)
                    if next_sim > 0.8:
                        score += next_sim * 0.1

                if score > best_score:
                    best_score = score
                    best_match = (count1, count2, sim)

        count1, count2, sim = best_match

        # 合并句子
        combined1 = get_combined_text(sentences1, i1, count1)
        combined2 = get_combined_text(sentences2, i2, count2)
        clean_len_v1 = get_combined_clean_length(clean_sentences1, i1, count1)
        clean_len_v2 = get_combined_clean_length(clean_sentences2, i2, count2)

        # 收集差异位置（双向）
        diff_positions_v1 = [
            diff["position_v1"] for diff in differences
            if "position_v1" in diff and
            current_clean_pos_v1 <= diff["position_v1"] < current_clean_pos_v1 + clean_len_v1
        ]
        diff_positions_v2 = [
            diff["position_v2"] for diff in differences
            if "position_v2" in diff and
            current_clean_pos_v2 <= diff["position_v2"] < current_clean_pos_v2 + clean_len_v2
        ]
        # 兼容旧的 diff_positions
        diff_positions = [
            diff["position"] for diff in differences
            if current_clean_pos_v1 <= diff["position"] < current_clean_pos_v1 + clean_len_v1
        ]

        result.append({
            "id": alignment_id,
            "sentence1": combined1,
            "sentence2": combined2,
            "has_diff": len(diff_positions) > 0 or sim < 0.95,
            "diff_positions": diff_positions,  # 兼容性
            "diff_positions_v1": diff_positions_v1,
            "diff_positions_v2": diff_positions_v2,
            "clean_start_pos": current_clean_pos_v1,  # 兼容性
            "clean_start_pos_v1": current_clean_pos_v1,
            "clean_start_pos_v2": current_clean_pos_v2,
            "clean_end_pos": current_clean_pos_v1 + clean_len_v1,
            "clean_end_pos_v1": current_clean_pos_v1 + clean_len_v1,
            "clean_end_pos_v2": current_clean_pos_v2 + clean_len_v2,
            "has_text_diff": sim < 0.95,
            "similarity": round(sim, 3),
            "alignment_type": f"{count1}-to-{count2}"
        })

        current_clean_pos_v1 += clean_len_v1
        current_clean_pos_v2 += clean_len_v2
        i1 += count1
        i2 += count2
        alignment_id += 1

    return result
