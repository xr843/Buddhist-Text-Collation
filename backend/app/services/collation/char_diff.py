"""
字符级差异计算模块
从 collation_service.py 中提取
"""
import difflib
import re
from typing import List, Dict, Tuple


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


def align_and_compare_segments(
    segments1: list,
    segments2: list,
    has_text_diff: bool,
    has_punct_diff: bool
) -> Tuple[list, list, bool, bool]:
    """
    对齐并比对两个版本的segments，修正type

    关键修复：如果对应位置的text不同但type是equal，修正为replace
    这是修复纯文本对齐算法的关键步骤
    """
    # 确保两个版本的segments长度相同
    if len(segments1) != len(segments2):
        print(f"[警告] segments长度不一致: {len(segments1)} vs {len(segments2)}")
        return segments1, segments2, has_text_diff, has_punct_diff

    # 逐个比对对应位置的segments
    for i in range(len(segments1)):
        seg1 = segments1[i]
        seg2 = segments2[i]

        # 只处理type为equal的情况（其他类型已经正确标记为差异）
        if seg1['type'] == 'equal' and seg2['type'] == 'equal':
            # 检查text是否真的相同
            if seg1['text'] != seg2['text']:
                # text不同！需要修正为replace
                seg1['type'] = 'replace'
                seg2['type'] = 'replace'

                # 更新差异统计
                if seg1['is_punct'] or seg2['is_punct']:
                    has_punct_diff = True
                else:
                    has_text_diff = True

    return segments1, segments2, has_text_diff, has_punct_diff


def compute_char_diff(text1: str, text2: str) -> Dict:
    """
    计算两个句子的字符级差异（优化版 - 先对齐纯文本）

    核心改进：
    1. 先提取纯文本（去除标点）
    2. 对纯文本进行diff对齐
    3. 回填标点并生成segments

    这样可以避免标点差异导致的文字对齐错乱

    Args:
        text1: 句子1
        text2: 句子2

    Returns:
        {
            "segments1": [{"text": "相同部分", "type": "equal", "is_punct": false}, ...],
            "segments2": [{"text": "不同部分", "type": "delete", "is_punct": true}, ...],
            "diff_type": "punct_only" | "text_only" | "mixed" | null
        }
    """
    # 1. 提取纯文本并建立位置映射
    clean1, pos_map1 = extract_clean_text_with_mapping(text1)
    clean2, pos_map2 = extract_clean_text_with_mapping(text2)

    # 2. 对纯文本进行diff（这样不受标点影响）
    matcher = difflib.SequenceMatcher(None, clean1, clean2)

    # 3. 构建对齐结构
    segments1 = []
    segments2 = []
    has_text_diff = False  # 是否有文字差异
    has_punct_diff = False  # 是否有标点差异

    last_orig_pos1 = 0
    last_orig_pos2 = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            # 文字相同 - 一一对齐
            for k in range(i2 - i1):
                clean_pos1 = i1 + k
                clean_pos2 = j1 + k

                orig_pos1 = pos_map1[clean_pos1]
                orig_pos2 = pos_map2[clean_pos2]

                # 添加之前的标点（如果有）
                if orig_pos1 > last_orig_pos1:
                    punct_seg = text1[last_orig_pos1:orig_pos1]
                    segments1.append({"text": punct_seg, "type": "equal", "is_punct": True})

                if orig_pos2 > last_orig_pos2:
                    punct_seg = text2[last_orig_pos2:orig_pos2]
                    segments2.append({"text": punct_seg, "type": "equal", "is_punct": True})

                # 添加文字（相同的）
                char = clean1[clean_pos1]
                segments1.append({"text": char, "type": "equal", "is_punct": False})
                segments2.append({"text": char, "type": "equal", "is_punct": False})

                last_orig_pos1 = orig_pos1 + 1
                last_orig_pos2 = orig_pos2 + 1

        elif tag == "delete":
            # V1有，V2无（文字删除）
            for k in range(i2 - i1):
                clean_pos1 = i1 + k
                orig_pos1 = pos_map1[clean_pos1]

                # 添加之前的标点
                if orig_pos1 > last_orig_pos1:
                    punct_seg = text1[last_orig_pos1:orig_pos1]
                    segments1.append({"text": punct_seg, "type": "delete", "is_punct": True})
                    has_punct_diff = True

                # 添加被删除的文字
                char = clean1[clean_pos1]
                segments1.append({"text": char, "type": "delete", "is_punct": False})
                has_text_diff = True

                last_orig_pos1 = orig_pos1 + 1

        elif tag == "insert":
            # V2有，V1无（文字插入）
            for k in range(j2 - j1):
                clean_pos2 = j1 + k
                orig_pos2 = pos_map2[clean_pos2]

                # 添加之前的标点
                if orig_pos2 > last_orig_pos2:
                    punct_seg = text2[last_orig_pos2:orig_pos2]
                    segments2.append({"text": punct_seg, "type": "insert", "is_punct": True})
                    has_punct_diff = True

                # 添加插入的文字
                char = clean2[clean_pos2]
                segments2.append({"text": char, "type": "insert", "is_punct": False})
                has_text_diff = True

                last_orig_pos2 = orig_pos2 + 1

        elif tag == "replace":
            # 文字替换
            len1 = i2 - i1
            len2 = j2 - j1

            # 处理V1侧
            for k in range(len1):
                clean_pos1 = i1 + k
                orig_pos1 = pos_map1[clean_pos1]

                if orig_pos1 > last_orig_pos1:
                    punct_seg = text1[last_orig_pos1:orig_pos1]
                    segments1.append({"text": punct_seg, "type": "replace", "is_punct": True})
                    has_punct_diff = True

                char = clean1[clean_pos1]
                segments1.append({"text": char, "type": "replace", "is_punct": False})
                last_orig_pos1 = orig_pos1 + 1

            # 处理V2侧
            for k in range(len2):
                clean_pos2 = j1 + k
                orig_pos2 = pos_map2[clean_pos2]

                if orig_pos2 > last_orig_pos2:
                    punct_seg = text2[last_orig_pos2:orig_pos2]
                    segments2.append({"text": punct_seg, "type": "replace", "is_punct": True})

                char = clean2[clean_pos2]
                segments2.append({"text": char, "type": "replace", "is_punct": False})
                last_orig_pos2 = orig_pos2 + 1

            has_text_diff = True

    # 4. 添加末尾的标点
    if last_orig_pos1 < len(text1):
        punct_seg = text1[last_orig_pos1:]
        segments1.append({"text": punct_seg, "type": "equal", "is_punct": True})

    if last_orig_pos2 < len(text2):
        punct_seg = text2[last_orig_pos2:]
        segments2.append({"text": punct_seg, "type": "equal", "is_punct": True})

    # 5. 关键修复：后处理比对对应位置的segments，修正type
    segments1, segments2, has_text_diff, has_punct_diff = align_and_compare_segments(
        segments1, segments2, has_text_diff, has_punct_diff
    )

    # 6. 确定差异类型
    diff_type = None
    if has_text_diff and has_punct_diff:
        diff_type = "mixed"
    elif has_text_diff:
        diff_type = "text_only"
    elif has_punct_diff:
        diff_type = "punct_only"

    return {
        "segments1": segments1,
        "segments2": segments2,
        "diff_type": diff_type,
    }
