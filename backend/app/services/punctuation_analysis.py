"""
标点差异分析服务 - 专业的标点分析工作台

此模块已重构为子模块结构，详见 punctuation_analysis/ 目录：
- punctuation_analysis/constants.py: 标点符号常量和映射
- punctuation_analysis/text_utils.py: 文本处理工具函数
- punctuation_analysis/diff_extractor.py: 标点差异提取
- punctuation_analysis/sentence_alignment.py: 句子级别对齐
- punctuation_analysis/style_report.py: 风格报告和统计
- punctuation_analysis/__init__.py: 模块组装与服务类

此文件保留以保持向后兼容性。
"""

# 从重构后的子模块导入所有内容
from app.services.punctuation_analysis import (
    # 主服务
    PunctuationAnalysisService,
    punctuation_analysis_service,
    # 常量
    PUNCT_MARKS_STR,
    PUNCT_MARKS_SET,
    VARIANT_CHAR_MAP,
    PUNCTUATION_CATEGORIES,
    RESEARCH_CATEGORIES,
    PUNCTUATION_NAMES,
    CLOSING_MARKS,
    # 文本工具
    normalize_text,
    normalize_for_comparison,
    build_punctuation_map,
    split_into_sentences,
    find_quote_chars,
    find_unknown_puncts,
    extract_clean_text,
    # 差异提取
    extract_punctuation_differences,
    get_diff_type,
    get_punctuation_category,
    get_punctuation_name,
    # 句子对齐
    generate_sentence_alignment,
    # 风格报告
    generate_style_report,
    categorize_differences,
    calculate_research_stats,
    generate_context_slices,
)


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
