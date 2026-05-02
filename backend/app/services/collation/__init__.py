"""
文字校勘服务模块

从 collation_service.py 重构而来，将大型服务类拆分为多个专注的模块：
- text_normalizer: 文本规范化工具
- transposition_detector: 倒文检测与合并
- sentence_aligner: 分句与对齐
- statistics: 统计计算
- display_formatter: 显示格式化
- char_diff: 字符级差异计算
- dp_aligner: 动态规划对齐
- exporter: CSV导出
- global_aligner: 全局字符对齐
"""
import difflib
from typing import List, Dict

# 导入子模块
from .text_normalizer import (
    normalize_text_for_comparison,
    extract_clean_text_with_mapping,
    parse_text_to_chars_and_gaps,
)
from .transposition_detector import (
    is_transposition,
    detect_and_merge_transpositions,
)
from .sentence_aligner import (
    split_sentences,
    compute_similarity,
    find_anchor_points,
)
from .statistics import compute_alignment_statistics
from .display_formatter import (
    split_aligned_segments_for_display,
    merge_orphan_blocks,
    analyze_replace_segment_for_display,
)
from .char_diff import (
    compute_char_diff,
    align_and_compare_segments,
)
from .dp_aligner import (
    dp_align_segment,
    align_sentences,
)
from .exporter import export_to_csv
from .global_aligner import global_char_alignment


class CollationService:
    """文字校勘服务（用于纯文本内容不同的对比）"""

    def normalize_text_for_comparison(self, text: str) -> str:
        """规范化文本用于对比（移除所有排版差异和不可见字符）"""
        return normalize_text_for_comparison(text)

    def collate_texts(
        self,
        text1: str,
        text2: str,
        version1_name: str = "版本A",
        version2_name: str = "版本B",
    ) -> dict:
        """
        对比两个内容不同的文本版本（文字校勘）

        核心算法：先全局字符级对齐，再分段展示
        这样可以确保只有真正差异的字符被高亮，而不是整段标红
        """
        # 1. 规范化文本，移除排版差异（换行符等）
        normalized_text1 = normalize_text_for_comparison(text1)
        normalized_text2 = normalize_text_for_comparison(text2)

        # 2. 全局字符级对齐（核心！）
        aligned_segments = self._global_char_alignment(normalized_text1, normalized_text2)

        # 3. 将对齐结果分段展示（每段约80-100字）
        aligned_sentences = self._split_aligned_segments_for_display(aligned_segments)

        # 4. 计算统计信息
        statistics = self._compute_alignment_statistics(aligned_segments, normalized_text1, normalized_text2)

        # 5. 计算相似度
        similarity = self._compute_similarity(normalized_text1, normalized_text2)

        return {
            "mode": "collation",
            "mode_description": "文字校勘模式",
            "version1_name": version1_name,
            "version2_name": version2_name,
            "text1": normalized_text1,
            "text2": normalized_text2,
            "differences": [],  # 保留兼容性
            "statistics": statistics,
            "similarity": similarity,
            "side_by_side": {"segments": aligned_segments, "total_segments": len(aligned_segments)},
            "aligned_sentences": aligned_sentences,
        }

    def _is_transposition(self, text1: str, text2: str) -> bool:
        """检测是否为倒文（2-6字的字序颠倒）"""
        return is_transposition(text1, text2)

    def _detect_and_merge_transpositions(self, segments: List[Dict]) -> List[Dict]:
        """后处理：检测倒文并合并相关 segments"""
        return detect_and_merge_transpositions(segments)

    def _analyze_replace_segment_for_display(self, t1: str, t2: str, is_variant_func) -> tuple:
        """对 replace segment 进行字符级细分，用于前端显示"""
        return analyze_replace_segment_for_display(t1, t2, is_variant_func)

    def _global_char_alignment(self, text1: str, text2: str) -> List[Dict]:
        """全局字符级对齐（核心算法）"""
        return global_char_alignment(text1, text2)

    def _split_aligned_segments_for_display(
        self,
        aligned_segments: List[Dict],
        target_length: int = 80
    ) -> List[Dict]:
        """将全局对齐结果分段，用于前端展示"""
        from app.services.variant_dict import is_variant
        return split_aligned_segments_for_display(aligned_segments, is_variant, target_length)

    def _merge_orphan_blocks(self, blocks: List[Dict], min_size: int) -> List[Dict]:
        """合并"孤儿块"（太小的块合并到相邻块）"""
        return merge_orphan_blocks(blocks, min_size)

    def _compute_alignment_statistics(
        self,
        aligned_segments: List[Dict],
        text1: str,
        text2: str
    ) -> dict:
        """计算对齐统计信息，包括详细的差异字符统计"""
        from app.services.variant_dict import classify_difference, is_variant
        return compute_alignment_statistics(
            aligned_segments, text1, text2,
            is_variant_func=is_variant,
            classify_func=classify_difference
        )

    def align_text_and_punctuation(self, text1: str, text2: str) -> List[Dict]:
        """
        纯文本基准对齐 + 标点回填算法

        核心逻辑：
        1. 抽离纯文本（去除标点）
        2. 对纯文本进行 Diff
        3. 回填标点并生成对齐单元 (Token)
        """
        # 1. 预处理：解析文本为 (Chars, Gaps)
        chars1, gaps1 = parse_text_to_chars_and_gaps(text1)
        chars2, gaps2 = parse_text_to_chars_and_gaps(text2)

        # 2. 对纯汉字序列进行 Diff
        matcher = difflib.SequenceMatcher(None, chars1, chars2)
        aligned_tokens = []

        # 3. 遍历 Diff 结果并回填标点
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            len1 = i2 - i1
            len2 = j2 - j1
            max_len = max(len1, len2)

            for k in range(max_len):
                idx1 = i1 + k if k < len1 else None
                idx2 = j1 + k if k < len2 else None

                token = {
                    "type": tag,
                    "char_v1": chars1[idx1] if idx1 is not None else None,
                    "char_v2": chars2[idx2] if idx2 is not None else None,
                    "pre_punct_v1": gaps1[idx1] if idx1 is not None else "",
                    "pre_punct_v2": gaps2[idx2] if idx2 is not None else "",
                    "status": "MATCH",
                }

                if tag == "equal":
                    p1 = token["pre_punct_v1"]
                    p2 = token["pre_punct_v2"]
                    if p1 != p2:
                        token["status"] = "PUNCT_DIFF"
                    else:
                        token["status"] = "MATCH"
                else:
                    token["status"] = "TEXT_DIFF"
                    if tag == "replace":
                        p1 = token["pre_punct_v1"]
                        p2 = token["pre_punct_v2"]
                        if p1 != p2:
                            token["status"] = "BOTH_DIFF"

                aligned_tokens.append(token)

        # 4. 处理最后的标点 (Tail Gap)
        tail_gap1 = gaps1[-1] if gaps1 else ""
        tail_gap2 = gaps2[-1] if gaps2 else ""

        if tail_gap1 or tail_gap2:
            token = {
                "type": "equal",
                "char_v1": "",
                "char_v2": "",
                "pre_punct_v1": tail_gap1,
                "pre_punct_v2": tail_gap2,
                "status": "MATCH" if tail_gap1 == tail_gap2 else "PUNCT_DIFF",
            }
            aligned_tokens.append(token)

        return aligned_tokens

    def _parse_text_to_chars_and_gaps(self, text: str) -> tuple:
        """将文本解析为纯汉字列表和间隙标点列表"""
        return parse_text_to_chars_and_gaps(text)

    def _compute_differences(self, text1: str, text2: str) -> List[Dict]:
        """计算文本差异（优化用于文字校勘）"""
        matcher = difflib.SequenceMatcher(None, text1, text2)
        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            context_start = max(0, i1 - 30)
            context_end = min(len(text1), i2 + 30)

            difference = {
                "type": tag,
                "position": i1,
                "version1_text": text1[i1:i2],
                "version2_text": text2[j1:j2],
                "context_before": text1[context_start:i1],
                "context_after": text1[i2:context_end],
                "version1_range": [i1, i2],
                "version2_range": [j1, j2],
            }

            differences.append(difference)

        return differences

    def _compute_statistics(
        self, text1: str, text2: str, differences: List[Dict]
    ) -> dict:
        """计算校勘统计信息"""
        insertions = sum(1 for d in differences if d["type"] == "insert")
        deletions = sum(1 for d in differences if d["type"] == "delete")
        replacements = sum(1 for d in differences if d["type"] == "replace")

        inserted_chars = sum(
            len(d["version2_text"]) for d in differences if d["type"] == "insert"
        )
        deleted_chars = sum(
            len(d["version1_text"]) for d in differences if d["type"] == "delete"
        )
        replaced_chars = sum(
            len(d["version1_text"]) for d in differences if d["type"] == "replace"
        )

        return {
            "version1_length": len(text1),
            "version2_length": len(text2),
            "total_differences": len(differences),
            "insertions": insertions,
            "deletions": deletions,
            "replacements": replacements,
            "inserted_chars": inserted_chars,
            "deleted_chars": deleted_chars,
            "replaced_chars": replaced_chars,
            "total_changed_chars": inserted_chars + deleted_chars + replaced_chars,
        }

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（0-1）- 基于纯文本（忽略标点）"""
        return compute_similarity(text1, text2)

    def _generate_side_by_side(self, text1: str, text2: str) -> dict:
        """生成并排对比数据（适合前端渲染）"""
        matcher = difflib.SequenceMatcher(None, text1, text2)
        segments = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            segment = {
                "type": tag,
                "left": text1[i1:i2],
                "right": text2[j1:j2],
                "left_range": [i1, i2],
                "right_range": [j1, j2],
            }
            segments.append(segment)

        return {"segments": segments, "total_segments": len(segments)}

    def _split_sentences(self, text: str) -> List[str]:
        """将文本分句（智能分段策略）"""
        return split_sentences(text)

    def _split_by_punctuation(self, text: str, pattern: str) -> List[str]:
        """根据标点符号分句"""
        from .sentence_aligner import _split_by_punctuation
        return _split_by_punctuation(text, pattern)

    def _split_by_fixed_length(self, text: str, target_length: int = 80) -> List[str]:
        """按固定字数分段（智能断点）"""
        from .sentence_aligner import _split_by_fixed_length
        return _split_by_fixed_length(text, target_length)

    def _align_sentences(self, text1: str, text2: str) -> List[Dict]:
        """对齐两个文本的句子（锚点对齐 + 动态规划全局最优）"""
        return align_sentences(
            text1, text2,
            split_sentences_func=split_sentences,
            find_anchors_func=find_anchor_points
        )

    def _find_anchor_points(
        self,
        sentences1: List[str],
        sentences2: List[str],
        similarity_threshold: float = 0.95,
    ) -> List[tuple]:
        """查找锚点句子（高置信度的匹配对）"""
        return find_anchor_points(sentences1, sentences2, similarity_threshold)

    def _dp_align_segment(
        self, sentences1: List[str], sentences2: List[str], offset1: int, offset2: int
    ) -> List[Dict]:
        """使用动态规划对齐一个分段的句子"""
        return dp_align_segment(sentences1, sentences2, offset1, offset2)

    def _compute_char_diff(self, text1: str, text2: str) -> Dict:
        """计算两个句子的字符级差异（优化版 - 先对齐纯文本）"""
        return compute_char_diff(text1, text2)

    def _extract_clean_text_with_mapping(self, text: str) -> tuple:
        """提取纯文本（去除标点），并建立位置映射"""
        return extract_clean_text_with_mapping(text)

    def _align_and_compare_segments(
        self,
        segments1: list,
        segments2: list,
        has_text_diff: bool,
        has_punct_diff: bool
    ) -> tuple:
        """对齐并比对两个版本的segments，修正type"""
        return align_and_compare_segments(segments1, segments2, has_text_diff, has_punct_diff)

    def export_to_csv(
        self,
        aligned_segments: List[Dict],
        statistics: dict,
        version1_name: str = "版本A",
        version2_name: str = "版本B",
    ) -> str:
        """将差异结果导出为 CSV 格式"""
        return export_to_csv(aligned_segments, statistics, version1_name, version2_name)


# 创建全局实例
collation_service = CollationService()


# 导出所有公共API
__all__ = [
    # 主服务类
    'CollationService',
    'collation_service',
    # 文本规范化
    'normalize_text_for_comparison',
    'extract_clean_text_with_mapping',
    'parse_text_to_chars_and_gaps',
    # 倒文检测
    'is_transposition',
    'detect_and_merge_transpositions',
    # 分句对齐
    'split_sentences',
    'compute_similarity',
    'find_anchor_points',
    # 统计
    'compute_alignment_statistics',
    # 显示格式化
    'split_aligned_segments_for_display',
    'merge_orphan_blocks',
    'analyze_replace_segment_for_display',
    # 字符差异
    'compute_char_diff',
    'align_and_compare_segments',
    # 动态规划对齐
    'dp_align_segment',
    'align_sentences',
    # 导出
    'export_to_csv',
    # 全局对齐
    'global_char_alignment',
]
