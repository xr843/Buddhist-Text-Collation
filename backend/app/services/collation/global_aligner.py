"""
全局字符对齐模块
从 collation_service.py 中提取
"""
import difflib
from typing import List, Dict

from .transposition_detector import detect_and_merge_transpositions


def global_char_alignment(text1: str, text2: str) -> List[Dict]:
    """
    全局字符级对齐（核心算法）

    使用difflib对两个完整文本进行字符级对齐，
    生成一系列segments，每个segment标记为equal/insert/delete/replace

    关键优化：先将异体字标准化，再对比
    这样可以避免"為"被当作脱文、"之失爲"被当作衍文的问题
    正确的结果应该是："之失"是衍文，"為"→"爲"是异体字

    Returns:
        [
            {"type": "equal", "text1": "相同文本", "text2": "相同文本"},
            {"type": "replace", "text1": "眾", "text2": "紫"},
            {"type": "equal", "text1": "賢造", "text2": "賢造"},
            ...
        ]
    """
    from app.services.variant_dict import get_standard_form

    # 1. 将异体字标准化（关键优化！）
    # 这样 difflib 就能识别 "為" 和 "爲" 是"相同"的
    std_text1 = ''.join(get_standard_form(c) for c in text1)
    std_text2 = ''.join(get_standard_form(c) for c in text2)

    # 2. 对比标准化后的文本
    matcher = difflib.SequenceMatcher(None, std_text1, std_text2, autojunk=False)
    segments = []

    # 3. 生成 segment 时使用原始字符
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        orig_text1 = text1[i1:i2]
        orig_text2 = text2[j1:j2]

        # 如果标准化后相同，但原始字符不同，说明是异体字
        if tag == "equal" and orig_text1 != orig_text2:
            tag = "replace"  # 改为 replace，后续会识别为异体字

        segment = {
            "type": tag,
            "text1": orig_text1,
            "text2": orig_text2,
            "pos1": [i1, i2],
            "pos2": [j1, j2],
        }
        segments.append(segment)

    # 4. 后处理：检测相邻的 delete/insert 是否构成倒文
    segments = detect_and_merge_transpositions(segments)

    return segments
