"""
分句对齐模块
从 collation_service.py 中提取
"""
import re
import difflib
from typing import List, Dict, Tuple


def split_sentences(text: str) -> List[str]:
    """
    将文本分句（智能分段策略）

    策略优先级：
    1. 优先使用句末标点（。！？）分句
    2. 如果分句结果太少（<5句且文本>500字），尝试使用逗号/分号分句
    3. 如果仍然太少，按固定字数分段（每80字）
    4. 确保每个"句子"不会太长（>200字时强制拆分）

    Args:
        text: 输入文本

    Returns:
        句子列表
    """
    # 尝试用句末标点分句
    sentences = _split_by_punctuation(text, r"[。！？]")

    # 检查分句效果
    text_len = len(text)
    avg_len = text_len / max(len(sentences), 1)

    # 如果分句太少（平均句子长度>150字），尝试用逗号/分号分句
    if avg_len > 150 and text_len > 200:
        print(f"[分句] 句末标点分句效果不佳（平均{avg_len:.0f}字/句），尝试逗号分句")
        sentences = _split_by_punctuation(text, r"[。！？，、；：]")
        avg_len = text_len / max(len(sentences), 1)

    # 如果还是太少（平均>100字），按固定字数分段
    if avg_len > 100 and text_len > 200:
        print(f"[分句] 标点分句仍不够细（平均{avg_len:.0f}字/句），使用固定字数分段")
        sentences = _split_by_fixed_length(text, target_length=80)

    # 最后检查：确保没有超长句子（>300字的强制拆分）
    final_sentences = []
    for sent in sentences:
        if len(sent) > 300:
            # 超长句子再次拆分
            sub_sents = _split_by_fixed_length(sent, target_length=80)
            final_sentences.extend(sub_sents)
        else:
            final_sentences.append(sent)

    print(f"[分句] 最终分句数: {len(final_sentences)}，平均长度: {text_len / max(len(final_sentences), 1):.1f}字")

    return final_sentences


def _split_by_punctuation(text: str, pattern: str) -> List[str]:
    """
    根据标点符号分句

    Args:
        text: 输入文本
        pattern: 分句标点的正则表达式

    Returns:
        句子列表
    """
    # 引号类型（配对）
    quote_pairs = [
        ('"', '"'),  # 中文双引号
        ("「", "」"),  # 中文方括号引号
        ("『", "』"),  # 中文书名号引号
        ("（", "）"),  # 中文圆括号
        ("《", "》"),  # 中文书名号
    ]

    # 分句（保留标点，并处理引号配对）
    sentences = []
    current = ""
    quote_stack = []  # 引号栈，用于跟踪未闭合的引号

    for i, char in enumerate(text):
        current += char

        # 检查是否是引号开始
        for open_q, close_q in quote_pairs:
            if char == open_q:
                quote_stack.append(close_q)
                break
            elif char == close_q:
                # 引号结束，弹出栈
                if quote_stack and quote_stack[-1] == close_q:
                    quote_stack.pop()
                break

        # 如果遇到分句标点
        if re.match(pattern, char):
            # 检查下一个字符是否是引号结束符
            if i + 1 < len(text):
                next_char = text[i + 1]
                # 如果下一个字符是引号结束符，继续累积
                is_quote_end = any(
                    next_char == close_q for _, close_q in quote_pairs
                )
                if is_quote_end:
                    continue

            # 如果当前在引号内（栈不为空），不分句
            if len(quote_stack) > 0:
                continue

            # 否则分句
            if current.strip():
                sentences.append(current.strip())
            current = ""
            quote_stack = []  # 重置引号栈

    # 处理最后一句（可能没有句末标点）
    if current.strip():
        sentences.append(current.strip())

    return sentences


def _split_by_fixed_length(text: str, target_length: int = 80) -> List[str]:
    """
    按固定字数分段（智能断点）

    会尝试在标点处断开，避免把词语拆开

    Args:
        text: 输入文本
        target_length: 目标每段长度

    Returns:
        分段后的句子列表
    """
    # 移除换行符，但记录换行位置作为优先断点
    text = text.replace('\n', '').replace('\r', '')

    if len(text) <= target_length:
        return [text] if text.strip() else []

    sentences = []
    current_start = 0

    # 可以断开的标点符号（优先级从高到低）
    break_chars = set('。！？；：，、）」』"\'')

    while current_start < len(text):
        # 计算当前段的结束位置
        end_pos = min(current_start + target_length, len(text))

        # 如果还没到文本末尾，尝试找一个好的断点
        if end_pos < len(text):
            # 在目标位置附近（前后20字）寻找标点断点
            search_start = max(current_start + target_length - 20, current_start)
            search_end = min(current_start + target_length + 20, len(text))

            best_break = -1
            # 优先在目标位置之前找断点
            for i in range(end_pos - 1, search_start - 1, -1):
                if text[i] in break_chars:
                    best_break = i + 1  # 断点在标点之后
                    break

            # 如果前面没找到，在后面找
            if best_break == -1:
                for i in range(end_pos, search_end):
                    if text[i] in break_chars:
                        best_break = i + 1
                        break

            # 如果找到了好的断点，使用它
            if best_break != -1:
                end_pos = best_break

        # 提取当前段
        segment = text[current_start:end_pos].strip()
        if segment:
            sentences.append(segment)

        current_start = end_pos

    return sentences


def compute_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（0-1）- 基于纯文本（忽略标点）"""
    # 提取纯文本（去除所有标点符号和空白）
    punct_pattern = r'[。，、；：？！""' "（）《》【】·…—\s]"
    text1_clean = re.sub(punct_pattern, "", text1)
    text2_clean = re.sub(punct_pattern, "", text2)

    # 空句子处理
    if not text1_clean and not text2_clean:
        return 1.0  # 两个都是空/纯标点 -> 视为相同
    if not text1_clean or not text2_clean:
        return 0.0  # 一个有文字，一个没有 -> 完全不同

    # 计算纯文本相似度
    matcher = difflib.SequenceMatcher(None, text1_clean, text2_clean)
    return round(matcher.ratio(), 4)


def find_anchor_points(
    sentences1: List[str],
    sentences2: List[str],
    similarity_threshold: float = 0.95,
) -> List[Tuple[int, int, float]]:
    """
    查找锚点句子（高置信度的匹配对）

    Args:
        sentences1: 版本1的句子列表
        sentences2: 版本2的句子列表
        similarity_threshold: 锚点相似度阈值

    Returns:
        锚点列表 [(index1, index2, similarity), ...]
    """
    anchors = []
    used2 = set()

    for i1, sent1 in enumerate(sentences1):
        best_match = None
        best_similarity = similarity_threshold
        best_i2 = None

        for i2, sent2 in enumerate(sentences2):
            if i2 in used2:
                continue

            sim = compute_similarity(sent1, sent2)
            if sim > best_similarity:
                best_similarity = sim
                best_match = sent2
                best_i2 = i2

        if best_match is not None:
            # 验证：确保是双向最佳匹配（避免一对多）
            reverse_best_i1 = None
            reverse_best_sim = 0
            for j1, s1 in enumerate(sentences1):
                if j1 == i1:
                    continue
                sim = compute_similarity(s1, best_match)
                if sim > reverse_best_sim:
                    reverse_best_sim = sim
                    reverse_best_i1 = j1

            # 如果双向都是最佳匹配，才作为锚点
            if reverse_best_i1 is None or reverse_best_sim < best_similarity:
                anchors.append((i1, best_i2, best_similarity))
                used2.add(best_i2)

    # 按位置排序
    anchors.sort(key=lambda x: (x[0], x[1]))
    return anchors
