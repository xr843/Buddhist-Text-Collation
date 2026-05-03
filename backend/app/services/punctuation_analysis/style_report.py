"""
标点风格报告和统计模块

包含：
- 标点风格报告生成
- 差异分类统计
- 研究统计计算
- 上下文切片生成
"""
from typing import List, Dict

from .constants import (
    PUNCT_MARKS_SET,
    PUNCTUATION_NAMES,
    RESEARCH_CATEGORIES,
)
from .text_utils import extract_clean_text


def generate_style_report(
    text1: str,
    text2: str,
    version1_name: str,
    version2_name: str
) -> Dict:
    """生成标点风格报告"""
    punct_marks = PUNCT_MARKS_SET

    # 统计每个版本的标点使用情况
    version1_stats = _count_punctuation(text1, punct_marks)
    version2_stats = _count_punctuation(text2, punct_marks)

    # 计算标点密度
    clean_text1 = extract_clean_text(text1, punct_marks)
    clean_text2 = extract_clean_text(text2, punct_marks)

    version1_density = len([c for c in text1 if c in punct_marks]) / len(clean_text1) if clean_text1 else 0
    version2_density = len([c for c in text2 if c in punct_marks]) / len(clean_text2) if clean_text2 else 0

    return {
        "version1": {
            "name": version1_name,
            "total_punctuation": sum(version1_stats.values()),
            "punctuation_density": round(version1_density * 100, 2),
            "punctuation_distribution": version1_stats
        },
        "version2": {
            "name": version2_name,
            "total_punctuation": sum(version2_stats.values()),
            "punctuation_density": round(version2_density * 100, 2),
            "punctuation_distribution": version2_stats
        }
    }


def _count_punctuation(text: str, punct_marks: set) -> Dict[str, int]:
    """统计标点符号使用频率"""
    counts = {}
    for char in text:
        if char in punct_marks:
            counts[char] = counts.get(char, 0) + 1
    return counts


def categorize_differences(differences: List[Dict]) -> Dict:
    """差异归类统计 - 按具体标点符号分类"""
    categories = {}

    for diff in differences:
        # 获取涉及的标点符号
        punct = diff["version1_punct"] if diff["version1_punct"] != "无" else diff["version2_punct"]

        # 取第一个标点符号作为分类依据
        first_punct = punct[0] if punct and punct != "无" else "其他"

        # 生成分类名称
        if first_punct in PUNCTUATION_NAMES:
            category_name = f"{first_punct}（{PUNCTUATION_NAMES[first_punct]}）"
        else:
            category_name = f"{first_punct}（其他）"

        # 添加到对应分类
        if category_name not in categories:
            categories[category_name] = []
        categories[category_name].append(diff)

    # 统计每个类别的数量
    category_stats = {
        key: {
            "count": len(value),
            "items": value
        }
        for key, value in categories.items()
    }

    return category_stats


def calculate_research_stats(differences: List[Dict]) -> Dict:
    """计算标点研究统计数据"""
    total_count = len(differences)
    sentence_end_count = 0  # 句末点号差异
    sentence_inner_count = 0  # 句内点号差异
    mark_count = 0  # 标号差异

    for diff in differences:
        # 获取涉及的标点符号
        punct = diff["version1_punct"] if diff["version1_punct"] != "无" else diff["version2_punct"]

        if punct and punct != "无":
            first_punct = punct[0]

            # 判断属于哪种类型
            if first_punct in RESEARCH_CATEGORIES['句末点号']:
                sentence_end_count += 1
            elif first_punct in RESEARCH_CATEGORIES['句内点号']:
                sentence_inner_count += 1
            elif first_punct in RESEARCH_CATEGORIES['标号']:
                mark_count += 1

    return {
        "total_count": total_count,
        "sentence_end_count": sentence_end_count,
        "sentence_inner_count": sentence_inner_count,
        "mark_count": mark_count
    }


def generate_context_slices(
    text1: str,
    text2: str,
    differences: List[Dict]
) -> List[Dict]:
    """生成上下文切片，方便用户审查每个差异"""
    context_slices = []

    punct_marks = PUNCT_MARKS_SET
    clean_text = extract_clean_text(text1, punct_marks)

    for diff in differences:
        position = diff["position"]

        # 找到包含该位置的句子或段落
        start = max(0, position - 30)
        end = min(len(clean_text), position + 30)

        # 构建带标点的上下文
        context_v1 = _rebuild_text_with_punct(clean_text[start:end], text1, start, end)
        context_v2 = _rebuild_text_with_punct(clean_text[start:end], text2, start, end)

        context_slices.append({
            "id": diff["id"],
            "position": position,
            "character": diff["character"],
            "version1_context": context_v1,
            "version2_context": context_v2,
            "version1_punct": diff["version1_punct"],
            "version2_punct": diff["version2_punct"],
            "category": diff["category"],
            "diff_type": diff["diff_type"],
            "punctuation_name": diff["punctuation_name"]
        })

    return context_slices


def _rebuild_text_with_punct(clean_text: str, original_text: str, start: int, end: int) -> str:
    """根据干净文本和原文重建带标点的文本片段"""
    # 简化实现：直接返回原文的对应片段
    return clean_text
