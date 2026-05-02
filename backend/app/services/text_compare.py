"""
文本对比服务
"""
import difflib
from typing import List, Dict, Tuple
from enum import Enum

from app.utils.punctuation import PUNCTUATION_SET, strip_punctuation_and_whitespace


class DiffType(str, Enum):
    """差异类型"""
    EQUAL = "equal"  # 相同
    INSERT = "insert"  # 插入
    DELETE = "delete"  # 删除
    REPLACE = "replace"  # 替换


class TextComparisonService:
    """文本对比服务"""

    def compare_texts(
        self,
        text1: str,
        text2: str,
        version1_name: str = "版本A",
        version2_name: str = "版本B"
    ) -> dict:
        """
        对比两个文本版本

        Args:
            text1: 第一个文本版本
            text2: 第二个文本版本
            version1_name: 版本1名称
            version2_name: 版本2名称

        Returns:
            {
                "differences": [...],  # 差异列表
                "statistics": {...},   # 统计信息
                "similarity": 0.95     # 相似度
            }
        """
        # 【关键修复】规范化文本，移除排版差异（换行符等）
        # 这样可以正确对比"高丽版每行20字"和"福州版每行40字"这种情况
        normalized_text1 = self.normalize_text_for_comparison(text1)
        normalized_text2 = self.normalize_text_for_comparison(text2)

        # 计算差异（使用规范化后的文本）
        differences = self._compute_differences(normalized_text1, normalized_text2)

        # 计算统计信息（使用规范化后的文本）
        statistics = self._compute_statistics(normalized_text1, normalized_text2, differences)

        # 计算相似度（使用规范化后的文本）
        similarity = self._compute_similarity(normalized_text1, normalized_text2)

        return {
            "version1_name": version1_name,
            "version2_name": version2_name,
            "differences": differences,
            "statistics": statistics,
            "similarity": similarity
        }

    def compare_punctuation(
        self,
        text1: str,
        text2: str,
        version1_name: str = "版本A",
        version2_name: str = "版本B"
    ) -> dict:
        """
        仅对比标点符号差异

        Args:
            text1: 第一个文本版本（带标点）
            text2: 第二个文本版本（带标点）
            version1_name: 版本1名称
            version2_name: 版本2名称

        Returns:
            标点差异信息
        """
        # 提取标点符号位置
        punct_marks = PUNCTUATION_SET

        # 移除标点后的文本
        clean_text1 = strip_punctuation_and_whitespace(text1)
        clean_text2 = strip_punctuation_and_whitespace(text2)

        # 检查纯文本是否相同
        if clean_text1 != clean_text2:
            return {
                "error": "两个版本的纯文本内容不同，无法进行标点对比",
                "text_similarity": self._compute_similarity(clean_text1, clean_text2)
            }

        # 找出标点差异
        punct_differences = self._find_punctuation_differences(text1, text2, clean_text1)

        return {
            "version1_name": version1_name,
            "version2_name": version2_name,
            "base_text": clean_text1,
            "punctuation_differences": punct_differences,
            "total_differences": len(punct_differences)
        }

    def _compute_differences(self, text1: str, text2: str) -> List[Dict]:
        """
        计算文本差异（字符级）

        Returns:
            差异列表，每个差异包含：
            {
                "type": "insert/delete/replace/equal",
                "position": 123,
                "text1": "原文内容",
                "text2": "新文内容",
                "context_before": "前文",
                "context_after": "后文"
            }
        """
        # 使用difflib的SequenceMatcher进行差异分析
        matcher = difflib.SequenceMatcher(None, text1, text2)
        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue  # 跳过相同的部分

            diff_type = self._map_tag_to_type(tag)

            # 提取上下文
            context_start = max(0, i1 - 20)
            context_end = min(len(text1), i2 + 20)
            context_before = text1[context_start:i1]
            context_after = text1[i2:context_end]

            difference = {
                "type": diff_type.value,  # 使用 .value 确保JSON可序列化
                "position": i1,
                "text1": text1[i1:i2],
                "text2": text2[j1:j2],
                "context_before": context_before,
                "context_after": context_after,
                "text1_range": [i1, i2],
                "text2_range": [j1, j2]
            }

            differences.append(difference)

        return differences

    def _find_punctuation_differences(
        self,
        text1: str,
        text2: str,
        base_text: str
    ) -> List[Dict]:
        """
        找出标点符号的差异

        Args:
            text1: 版本1（带标点）
            text2: 版本2（带标点）
            base_text: 纯文本（无标点）

        Returns:
            标点差异列表
        """
        punct_marks = PUNCTUATION_SET
        differences = []

        # 为每个版本建立字符到标点的映射
        punct_map1 = self._build_punctuation_map(text1, punct_marks)
        punct_map2 = self._build_punctuation_map(text2, punct_marks)

        # 遍历纯文本的每个字符位置
        for i, char in enumerate(base_text):
            punct1 = punct_map1.get(i, '')
            punct2 = punct_map2.get(i, '')

            if punct1 != punct2:
                # 找到标点差异
                context_start = max(0, i - 10)
                context_end = min(len(base_text), i + 10)

                differences.append({
                    "position": i,
                    "character": char,
                    "version1_punct": punct1,
                    "version2_punct": punct2,
                    "context": base_text[context_start:context_end]
                })

        return differences

    def _build_punctuation_map(self, text: str, punct_marks: set) -> Dict[int, str]:
        """
        构建字符位置到标点符号的映射

        Args:
            text: 带标点的文本
            punct_marks: 标点符号集合

        Returns:
            {字符位置: 后续标点符号}
        """
        punct_map = {}
        char_index = 0

        i = 0
        while i < len(text):
            if text[i] not in punct_marks:
                # 收集该字符后的标点
                punct = ''
                j = i + 1
                while j < len(text) and text[j] in punct_marks:
                    punct += text[j]
                    j += 1

                if punct:
                    punct_map[char_index] = punct

                char_index += 1
                i = j
            else:
                i += 1

        return punct_map

    def _compute_statistics(
        self,
        text1: str,
        text2: str,
        differences: List[Dict]
    ) -> dict:
        """计算统计信息"""
        insertions = sum(1 for d in differences if d['type'] == DiffType.INSERT.value)
        deletions = sum(1 for d in differences if d['type'] == DiffType.DELETE.value)
        replacements = sum(1 for d in differences if d['type'] == DiffType.REPLACE.value)

        return {
            "text1_length": len(text1),
            "text2_length": len(text2),
            "total_differences": len(differences),
            "insertions": insertions,
            "deletions": deletions,
            "replacements": replacements
        }

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（0-1之间）

        使用SequenceMatcher的ratio方法
        """
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return round(matcher.ratio(), 4)

    def _map_tag_to_type(self, tag: str) -> DiffType:
        """将difflib的tag映射到我们的DiffType"""
        mapping = {
            'insert': DiffType.INSERT,
            'delete': DiffType.DELETE,
            'replace': DiffType.REPLACE,
            'equal': DiffType.EQUAL
        }
        return mapping.get(tag, DiffType.EQUAL)

    def normalize_text_for_comparison(self, text: str) -> str:
        """
        规范化文本用于对比（移除排版差异）

        核心改进：处理不同排版格式的佛典文本
        - 移除换行符（解决每行字数不同的问题）
        - 保留句末标点（。！？等）
        - 移除多余空白

        Args:
            text: 原始文本

        Returns:
            规范化后的文本
        """
        import re

        # 1. 将所有换行符替换为空字符（关键修复！）
        # 这样可以消除"高丽版每行20字 vs 福州版每行40字"的排版差异
        text = text.replace('\n', '').replace('\r', '')

        # 2. 将全角空格和制表符替换为空字符
        text = text.replace('\u3000', '').replace('\t', '')

        # 3. 移除连续的空格，保留单个空格
        text = re.sub(r' +', ' ', text)

        # 4. 移除首尾空白
        text = text.strip()

        return text

    def check_pure_text_consistency(self, text1: str, text2: str) -> Tuple[bool, str, str]:
        """
        检测两个文本的纯文本是否一致（移除标点后）

        Args:
            text1: 第一个文本
            text2: 第二个文本

        Returns:
            (是否一致, 纯文本1, 纯文本2)
        """
        clean_text1 = strip_punctuation_and_whitespace(text1)
        clean_text2 = strip_punctuation_and_whitespace(text2)

        is_consistent = (clean_text1 == clean_text2)

        return is_consistent, clean_text1, clean_text2

    def generate_side_by_side_view(
        self,
        text1: str,
        text2: str,
        differences: List[Dict]
    ) -> dict:
        """
        生成并排视图数据

        Returns:
            {
                "left": [{"text": "...", "highlight": true/false, "type": "..."}],
                "right": [{"text": "...", "highlight": true/false, "type": "..."}]
            }
        """
        # 简化实现：将文本按差异分段
        left_segments = []
        right_segments = []

        # TODO: 实现完整的并排视图生成逻辑
        # 这需要更复杂的算法来对齐两个版本的文本

        return {
            "left": left_segments,
            "right": right_segments
        }

    def generate_inline_view(
        self,
        text1: str,
        text2: str,
        differences: List[Dict]
    ) -> List[Dict]:
        """
        生成内联视图数据

        Returns:
            [
                {"text": "相同部分", "type": "equal"},
                {"text": "删除内容", "type": "delete"},
                {"text": "插入内容", "type": "insert"},
                ...
            ]
        """
        inline_segments = []

        matcher = difflib.SequenceMatcher(None, text1, text2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                inline_segments.append({
                    "text": text1[i1:i2],
                    "type": "equal"
                })
            elif tag == 'delete':
                inline_segments.append({
                    "text": text1[i1:i2],
                    "type": "delete"
                })
            elif tag == 'insert':
                inline_segments.append({
                    "text": text2[j1:j2],
                    "type": "insert"
                })
            elif tag == 'replace':
                inline_segments.append({
                    "text": text1[i1:i2],
                    "type": "delete"
                })
                inline_segments.append({
                    "text": text2[j1:j2],
                    "type": "insert"
                })

        return inline_segments


# 创建全局服务实例
text_comparison_service = TextComparisonService()
