"""
文字校勘服务 - 处理内容不一致的文本对比

此模块已重构为子模块结构，详见 collation/ 目录：
- collation/text_normalizer.py: 文本规范化工具
- collation/transposition_detector.py: 倒文检测与合并
- collation/sentence_aligner.py: 分句与对齐
- collation/statistics.py: 统计计算
- collation/display_formatter.py: 显示格式化
- collation/char_diff.py: 字符级差异计算
- collation/dp_aligner.py: 动态规划对齐
- collation/exporter.py: CSV导出
- collation/global_aligner.py: 全局字符对齐
- collation/__init__.py: CollationService 类组装

此文件保留以保持向后兼容性。
"""

# 从重构后的子模块导入所有内容
from app.services.collation import (
    CollationService,
    collation_service,
    # 文本规范化
    normalize_text_for_comparison,
    extract_clean_text_with_mapping,
    parse_text_to_chars_and_gaps,
    # 倒文检测
    is_transposition,
    detect_and_merge_transpositions,
    # 分句对齐
    split_sentences,
    compute_similarity,
    find_anchor_points,
    # 统计
    compute_alignment_statistics,
    # 显示格式化
    split_aligned_segments_for_display,
    merge_orphan_blocks,
    analyze_replace_segment_for_display,
    # 字符差异
    compute_char_diff,
    align_and_compare_segments,
    # 动态规划对齐
    dp_align_segment,
    align_sentences,
    # 导出
    export_to_csv,
    # 全局对齐
    global_char_alignment,
)

__all__ = [
    'CollationService',
    'collation_service',
    'normalize_text_for_comparison',
    'extract_clean_text_with_mapping',
    'parse_text_to_chars_and_gaps',
    'is_transposition',
    'detect_and_merge_transpositions',
    'split_sentences',
    'compute_similarity',
    'find_anchor_points',
    'compute_alignment_statistics',
    'split_aligned_segments_for_display',
    'merge_orphan_blocks',
    'analyze_replace_segment_for_display',
    'compute_char_diff',
    'align_and_compare_segments',
    'dp_align_segment',
    'align_sentences',
    'export_to_csv',
    'global_char_alignment',
]
