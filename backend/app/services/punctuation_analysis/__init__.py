"""
标点差异分析服务模块

此模块已重构为子模块结构：
- constants.py: 标点符号常量和映射
- text_utils.py: 文本处理工具函数
- diff_extractor.py: 标点差异提取
- sentence_alignment.py: 句子级别对齐
- style_report.py: 风格报告和统计
"""
from typing import List, Dict

from .constants import (
    PUNCT_MARKS_STR,
    PUNCT_MARKS_SET,
    VARIANT_CHAR_MAP,
    PUNCTUATION_CATEGORIES,
    RESEARCH_CATEGORIES,
    PUNCTUATION_NAMES,
    CLOSING_MARKS,
)
from .text_utils import (
    normalize_text,
    normalize_for_comparison,
    build_punctuation_map,
    split_into_sentences,
    find_quote_chars,
    find_unknown_puncts,
    extract_clean_text,
)
from .diff_extractor import (
    extract_punctuation_differences,
    get_diff_type,
    get_punctuation_category,
    get_punctuation_name,
)
from .sentence_alignment import generate_sentence_alignment
from .style_report import (
    generate_style_report,
    categorize_differences,
    calculate_research_stats,
    generate_context_slices,
)


class PunctuationAnalysisService:
    """标点差异分析服务"""

    # 保留类级别常量以兼容旧代码
    PUNCT_MARKS_STR = PUNCT_MARKS_STR
    PUNCT_MARKS_SET = PUNCT_MARKS_SET
    VARIANT_CHAR_MAP = VARIANT_CHAR_MAP
    PUNCTUATION_CATEGORIES = PUNCTUATION_CATEGORIES
    RESEARCH_CATEGORIES = RESEARCH_CATEGORIES
    PUNCTUATION_NAMES = PUNCTUATION_NAMES

    def analyze_punctuation_differences(
        self,
        text1: str,
        text2: str,
        version1_name: str = "版本A",
        version2_name: str = "版本B"
    ) -> dict:
        """
        分析两个版本的标点差异

        Returns:
            {
                "differences": [...],  # 所有差异列表
                "categories": {...},   # 差异归类统计
                "style_report": {...}, # 标点风格报告
                "context_slices": [...], # 上下文切片
                "sentence_alignment": [...] # 句子级别对齐数据
            }
        """
        # 1. 提取所有标点差异
        differences = self._extract_punctuation_differences(text1, text2)

        # 2. 差异归类统计
        categories = self._categorize_differences(differences)

        # 3. 生成标点风格报告
        style_report = self._generate_style_report(text1, text2, version1_name, version2_name)

        # 4. 生成上下文切片
        context_slices = self._generate_context_slices(text1, text2, differences)

        # 5. 生成句子级别对齐数据
        sentence_alignment = self.generate_sentence_alignment(text1, text2, differences)

        # 6. 计算研究统计数据
        research_stats = self._calculate_research_stats(differences)

        return {
            "version1_name": version1_name,
            "version2_name": version2_name,
            "differences": differences,
            "categories": categories,
            "style_report": style_report,
            "context_slices": context_slices,
            "sentence_alignment": sentence_alignment,
            "research_stats": research_stats
        }

    def _normalize_text(self, text: str) -> str:
        """标准化文本：将异体字统一为标准形式"""
        return normalize_text(text)

    def _extract_punctuation_differences(self, text1: str, text2: str) -> List[Dict]:
        """提取所有标点差异"""
        return extract_punctuation_differences(text1, text2)

    def _build_punctuation_map(self, text: str, punct_marks: set) -> Dict[int, str]:
        """构建字符位置到标点符号的映射"""
        return build_punctuation_map(text, punct_marks)

    def _get_diff_type(self, punct1: str, punct2: str) -> str:
        """判断差异类型"""
        return get_diff_type(punct1, punct2)

    def _get_punctuation_category(self, punct1: str, punct2: str) -> str:
        """获取标点符号类别"""
        return get_punctuation_category(punct1, punct2)

    def _get_punctuation_name(self, punct1: str, punct2: str) -> str:
        """获取标点符号的具体名称"""
        return get_punctuation_name(punct1, punct2)

    def _categorize_differences(self, differences: List[Dict]) -> Dict:
        """差异归类统计"""
        return categorize_differences(differences)

    def _generate_style_report(
        self,
        text1: str,
        text2: str,
        version1_name: str,
        version2_name: str
    ) -> Dict:
        """生成标点风格报告"""
        return generate_style_report(text1, text2, version1_name, version2_name)

    def _count_punctuation(self, text: str, punct_marks: set) -> Dict[str, int]:
        """统计标点符号使用频率"""
        counts = {}
        for char in text:
            if char in punct_marks:
                counts[char] = counts.get(char, 0) + 1
        return counts

    def _calculate_research_stats(self, differences: List[Dict]) -> Dict:
        """计算标点研究统计数据"""
        return calculate_research_stats(differences)

    def _generate_context_slices(
        self,
        text1: str,
        text2: str,
        differences: List[Dict]
    ) -> List[Dict]:
        """生成上下文切片"""
        return generate_context_slices(text1, text2, differences)

    def _rebuild_text_with_punct(self, clean_text: str, original_text: str, start: int, end: int) -> str:
        """根据干净文本和原文重建带标点的文本片段"""
        return clean_text

    def generate_sentence_alignment(
        self,
        text1: str,
        text2: str,
        differences: List[Dict]
    ) -> List[Dict]:
        """生成句子级别的智能对齐数据"""
        return generate_sentence_alignment(text1, text2, differences)

    def _split_into_sentences(self, text: str) -> List[str]:
        """按句号、问号、感叹号拆分文本为句子列表"""
        return split_into_sentences(text)

    def _normalize_for_comparison(self, text: str) -> str:
        """只用于内部比较的文本标准化"""
        return normalize_for_comparison(text)


# 创建全局服务实例
punctuation_analysis_service = PunctuationAnalysisService()


# 导出所有公共API
__all__ = [
    # 主服务
    'PunctuationAnalysisService',
    'punctuation_analysis_service',
    # 常量
    'PUNCT_MARKS_STR',
    'PUNCT_MARKS_SET',
    'VARIANT_CHAR_MAP',
    'PUNCTUATION_CATEGORIES',
    'RESEARCH_CATEGORIES',
    'PUNCTUATION_NAMES',
    'CLOSING_MARKS',
    # 文本工具
    'normalize_text',
    'normalize_for_comparison',
    'build_punctuation_map',
    'split_into_sentences',
    'find_quote_chars',
    'find_unknown_puncts',
    'extract_clean_text',
    # 差异提取
    'extract_punctuation_differences',
    'get_diff_type',
    'get_punctuation_category',
    'get_punctuation_name',
    # 句子对齐
    'generate_sentence_alignment',
    # 风格报告
    'generate_style_report',
    'categorize_differences',
    'calculate_research_stats',
    'generate_context_slices',
]
