"""
文本处理工具函数

包含：
- 文本标准化
- 标点映射构建
- 辅助函数
"""
from typing import Dict, List
import re

from .constants import VARIANT_CHAR_MAP, PUNCT_MARKS_SET, CLOSING_MARKS


def normalize_text(text: str) -> str:
    """
    标准化文本：将异体字统一为标准形式

    用于比较时忽略异体字差异，专注于标点差异
    """
    result = []
    for char in text:
        normalized = VARIANT_CHAR_MAP.get(char, char)
        result.append(normalized)
    return ''.join(result)


def normalize_for_comparison(text: str) -> str:
    """
    只用于内部比较的文本标准化

    注意：此函数的结果仅用于相似度计算，绝不用于显示！
    """
    # 将换行替换为空格
    text = re.sub(r'\n+', ' ', text)
    # 将多个连续空格替换为单个空格
    text = re.sub(r' +', ' ', text)
    return text.strip()


def build_punctuation_map(text: str, punct_marks: set = None) -> Dict[int, str]:
    """
    构建字符位置到标点符号的映射

    改进：
    1. 跳过空白字符，与前端保持一致
    2. 支持句首标点检测（使用 -1 作为键）

    返回:
        Dict[int, str]: 位置到标点的映射
        - 键 -1: 句首标点（文本开头的标点）
        - 键 0, 1, 2, ...: 每个字符后的标点
    """
    if punct_marks is None:
        punct_marks = PUNCT_MARKS_SET

    punct_map = {}
    char_index = 0
    i = 0

    # 检查句首标点（文本以标点开头的情况）
    start_punct = ''
    while i < len(text) and (text[i] in punct_marks or text[i].isspace()):
        if text[i] in punct_marks:
            start_punct += text[i]
        i += 1
    if start_punct:
        punct_map[-1] = start_punct  # 使用 -1 作为句首标点的键

    while i < len(text):
        char = text[i]

        # 跳过标点符号
        if char in punct_marks:
            i += 1
            continue

        # 跳过空白字符（不计入索引）
        if char.isspace():
            i += 1
            continue

        # 非标点非空白字符：收集其后的所有连续标点
        punct = ''
        j = i + 1
        while j < len(text) and text[j] in punct_marks:
            punct += text[j]
            j += 1

        if punct:
            punct_map[char_index] = punct

        char_index += 1
        i = j

    return punct_map


def split_into_sentences(text: str) -> List[str]:
    """
    按句号、问号、感叹号拆分文本为句子列表

    示例：
        "如是我闻。一时，佛在舍卫国。" -> ["如是我闻。", "一时，佛在舍卫国。"]
        "佛言："善哉。"阿难白佛。" -> ["佛言："善哉。"", "阿难白佛。"]
    """
    pattern = f'([。？！][{re.escape(CLOSING_MARKS)}]*)'
    parts = re.split(pattern, text)

    sentences = []
    for i in range(0, len(parts) - 1, 2):
        sentence = parts[i] + (parts[i + 1] if i + 1 < len(parts) else '')
        if sentence.strip():  # 只添加非空句子
            sentences.append(sentence)

    # 处理最后可能没有句号的部分
    if len(parts) % 2 == 1 and parts[-1].strip():
        sentences.append(parts[-1])

    return sentences


def find_quote_chars(text: str) -> dict:
    """找出文本中所有可能是引号的字符"""
    quotes = {}
    quote_ranges = [
        (0x0022, 0x0022),  # "
        (0x0027, 0x0027),  # '
        (0x00AB, 0x00BB),  # « »
        (0x2018, 0x201F),  # ' ' ‚ ‛ " " „ ‟
        (0x2032, 0x2037),  # ′ ″ ‴ ‵ ‶ ‷
        (0x2039, 0x203A),  # ‹ ›
        (0x300C, 0x300F),  # 「 」 『 』
        (0x301D, 0x301F),  # 〝 〞 〟
        (0xFF02, 0xFF02),  # ＂
        (0xFF07, 0xFF07),  # ＇
        (0xFF62, 0xFF63),  # ｢ ｣
    ]
    for char in text:
        code = ord(char)
        for start, end in quote_ranges:
            if start <= code <= end:
                if char not in quotes:
                    quotes[char] = {'count': 0, 'unicode': hex(code)}
                quotes[char]['count'] += 1
                break
    return quotes


def find_unknown_puncts(text: str, known_puncts: set = None) -> set:
    """找出文本中可能是标点但未被识别的字符"""
    if known_puncts is None:
        known_puncts = PUNCT_MARKS_SET

    unknown = set()
    for char in text:
        if not char.isalnum() and not char.isspace() and char not in known_puncts:
            # 检查是否是CJK字符（中文字符）
            code = ord(char)
            is_cjk = (0x4E00 <= code <= 0x9FFF or  # CJK统一汉字
                      0x3400 <= code <= 0x4DBF or  # CJK扩展A
                      0x20000 <= code <= 0x2A6DF)  # CJK扩展B
            if not is_cjk:
                unknown.add(char)
    return unknown


def extract_clean_text(text: str, punct_marks: set = None) -> str:
    """提取纯文本（去除标点和空白字符）"""
    if punct_marks is None:
        punct_marks = PUNCT_MARKS_SET
    return ''.join(c for c in text if c not in punct_marks and not c.isspace())
