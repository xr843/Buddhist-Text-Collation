"""
文本规范化工具
从 collation_service.py 中提取
"""
import re
from typing import Tuple, List, Dict


def normalize_text_for_comparison(text: str) -> str:
    """
    规范化文本用于对比（移除所有排版差异和不可见字符）

    处理策略：
    - 移除所有换行符、回车符
    - 移除所有空格（全角、半角、制表符等）
    - 移除所有零宽字符（ZWJ、ZWNJ、ZWSP、BOM等）
    - 只保留有意义的文字和标点

    这样可以让对比集中在真正的文字差异上，
    而不是被排版空格或不可见字符干扰。

    Args:
        text: 原始文本

    Returns:
        规范化后的文本（无空格、无零宽字符）
    """
    # 1. 移除所有换行符和回车符
    text = text.replace('\n', '').replace('\r', '')

    # 2. 移除所有类型的空格：
    #    - 半角空格 (U+0020)
    #    - 全角空格 (U+3000)
    #    - 制表符 (U+0009)
    #    - 不间断空格 (U+00A0)
    #    - 其他Unicode空白字符
    text = re.sub(r'[\s\u3000\u00A0]+', '', text)

    # 3. 移除所有零宽字符和不可见控制字符：
    #    - U+200B: 零宽空格 (Zero Width Space)
    #    - U+200C: 零宽非连接符 (Zero Width Non-Joiner)
    #    - U+200D: 零宽连接符 (Zero Width Joiner)
    #    - U+200E: 从左到右标记 (Left-to-Right Mark)
    #    - U+200F: 从右到左标记 (Right-to-Left Mark)
    #    - U+FEFF: 字节顺序标记 (BOM) / 零宽非断空格
    #    - U+2060: 单词连接符 (Word Joiner)
    #    - U+2061-U+2064: 不可见数学运算符
    text = re.sub(r'[\u200B-\u200F\uFEFF\u2060-\u2064]+', '', text)

    return text


def extract_clean_text_with_mapping(text: str) -> Tuple[str, Dict[int, int]]:
    """
    提取纯文本（去除标点），并建立位置映射

    Args:
        text: 原文（带标点）

    Returns:
        (clean_text, pos_map)
        - clean_text: 纯文本字符串
        - pos_map: {纯文本位置 -> 原文位置}

    示例:
        输入: "世尊告诸比丘：云何为苦？"
        输出: ("世尊告诸比丘云何为苦", {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:7, 7:8, 8:9, 9:10, 11:12})
    """
    # 定义标点符号集合
    punct_pattern = re.compile(r'[。，、；：？！""''（）《》【】·…—\\s\\n\\r\\t\u3000]')

    clean_chars = []
    pos_map = {}  # clean_pos -> original_pos

    for i, char in enumerate(text):
        if not punct_pattern.match(char):
            # 是文字，不是标点
            pos_map[len(clean_chars)] = i
            clean_chars.append(char)

    clean_text = ''.join(clean_chars)
    return clean_text, pos_map


def parse_text_to_chars_and_gaps(text: str) -> Tuple[List[str], List[str]]:
    """
    将文本解析为：
    1. 纯汉字列表 (chars)
    2. 间隙标点列表 (gaps) - 长度为 len(chars) + 1
       gaps[i] 表示 chars[i] *之前* 的标点
       gaps[-1] 表示最后一个字 *之后* 的标点
    """
    chars = []
    gaps = []
    current_gap = ""

    # 定义标点集合 (包含空白)
    puncts = set('。，、；：？！""''（）《》【】·…—\s\n\r\t \u3000')

    for char in text:
        if char in puncts or not char.strip():  # 标点或空白
            current_gap += char
        else:
            # 是文字
            gaps.append(current_gap)
            chars.append(char)
            current_gap = ""  # 重置 Gap

    # 添加最后的 Gap
    gaps.append(current_gap)

    return chars, gaps
