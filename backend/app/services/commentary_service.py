"""
注疏引证服务 - 自动提取注疏引文并与正文匹配

基于混合策略：
1. 标记词正则提取引文（"论云""论曰"等）
2. 文本相似度匹配（复用collation_service）
"""

import re
import uuid
from typing import List, Dict, Optional, Any
from functools import lru_cache


class Citation:
    """引文数据结构"""
    def __init__(
        self,
        citation_id: str,
        marker: str,
        extracted_text: str,
        original_text: str,
        start_pos: int,
        end_pos: int,
        context_before: str = "",
        context_after: str = ""
    ):
        self.id = citation_id
        self.marker = marker
        self.extracted_text = extracted_text
        self.original_text = original_text
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.context_before = context_before
        self.context_after = context_after

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "marker": self.marker,
            "extracted_text": self.extracted_text,
            "original_text": self.original_text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "context_before": self.context_before,
            "context_after": self.context_after
        }


class CommentaryService:
    """注疏引证服务"""

    # 默认标记词正则模式（支持扩展）
    # 支持多种注疏文献的引用格式
    # 注意：这些标记词后面的内容是引用经论原文，需要与经论匹配
    DEFAULT_MARKERS = [
        # 常见引用标记
        r"论云[:：]?\s*",
        r"论曰[:：]?\s*",
        r"經云[:：]?\s*",
        r"经云[:：]?\s*",
        r"颂曰[:：]?\s*",
        r"頌曰[:：]?\s*",
        r"本论云[:：]?\s*",
        r"如论(?:所)?说[:：]?\s*",
        # 繁体版本
        r"論曰[:：]?\s*",
        r"論云[:：]?\s*",
        # 其他常用格式
        r"文云[:：]?\s*",
        r"文曰[:：]?\s*",
        r"彼云[:：]?\s*",
        r"彼曰[:：]?\s*",
        r"又云[:：]?\s*",
        r"又曰[:：]?\s*",
        r"故云[:：]?\s*",
        r"故曰[:：]?\s*",
        r"此云[:：]?\s*",
        r"此曰[:：]?\s*",
        r"今云[:：]?\s*",
        r"今曰[:：]?\s*",
        r"如云[:：]?\s*",
        r"如曰[:：]?\s*",
    ]

    # 注疏作者解释标记（这些标记后面是注疏作者的解释，不是引文）
    # 用于识别注疏结构，不作为引文提取
    COMMENTARY_MARKERS = [
        r"述曰[:：]?\s*",  # 《述文记》元瑜法师的解释
        r"解云[:：]?\s*",  # 另一种解释方式
        r"釋曰[:：]?\s*",
        r"释曰[:：]?\s*",
        r"疏曰[:：]?\s*",
        r"記曰[:：]?\s*",
        r"记曰[:：]?\s*",
    ]

    # 经文直接引用格式（述文记等特殊格式）
    # 如："無色法中(至)蘊得等性。" 表示引用经文从"無色法中"到"蘊得等性"
    # 这是《述文记》的核心引文格式，必须正确匹配
    CITATION_RANGE_PATTERN = r"([^\n○\[\]]{2,30})[\(（]至[\)）]([^\n。]{2,40})[。]"

    def __init__(self):
        """初始化服务"""
        pass

    def extract_citations(
        self,
        text: str,
        marker_patterns: Optional[List[str]] = None
    ) -> List[Citation]:
        """
        从注疏文本中提取引文

        算法流程：
        1. 使用标记词正则定位引文起点
        2. 从起点向后扫描至句末标点（最大200字）
        3. 去除标记词，提取纯引文
        4. 过滤过短引文（< 5字）
        5. 记录位置和上下文（前后各30字）
        6. 额外提取"首...(至)...尾。"格式的经文引用

        Args:
            text: 注疏原文
            marker_patterns: 自定义标记词正则（可选）

        Returns:
            引文列表
        """
        patterns = marker_patterns or self.DEFAULT_MARKERS
        citations = []
        citation_positions = set()  # 用于去重

        # 1. 提取常规标记词格式的引文
        for pattern in patterns:
            try:
                for match in re.finditer(pattern, text):
                    marker = match.group()
                    start = match.end()

                    # 向后扫描至句末（最大200字）
                    end = self._find_citation_end(text, start, max_len=200)
                    extracted = text[start:end].strip()

                    # 过滤过短引文（< 5字）
                    if len(extracted) < 5:
                        continue

                    # 去重：相同位置的引文只保留一个
                    pos_key = (match.start(), end)
                    if pos_key in citation_positions:
                        continue
                    citation_positions.add(pos_key)

                    # 提取上下文（前后各30字）
                    context_before = text[max(0, match.start() - 30):match.start()]
                    context_after = text[end:min(len(text), end + 30)]

                    # 生成唯一ID
                    citation_id = f"cit_{uuid.uuid4().hex[:8]}"

                    citation = Citation(
                        citation_id=citation_id,
                        marker=marker.strip(),
                        extracted_text=extracted,
                        original_text=text[match.start():end],
                        start_pos=match.start(),
                        end_pos=end,
                        context_before=context_before,
                        context_after=context_after
                    )
                    citations.append(citation)

            except re.error as e:
                print(f"[警告] 正则模式错误: {pattern}, 错误: {e}")
                continue

        # 2. 提取"首...(至)...尾。"格式的经文引用（如《述文记》格式）
        # 这种格式表示引用经文从"首"到"尾"的内容
        range_citations = self._extract_range_citations(text, citation_positions)
        citations.extend(range_citations)

        print(f"[提取完成] 共提取 {len(citations)} 条引文（标记词: {len(citations) - len(range_citations)}, 范围引用: {len(range_citations)}）")
        return citations

    def _extract_range_citations(
        self,
        text: str,
        existing_positions: set
    ) -> List[Citation]:
        """
        提取"首...(至)...尾。"格式的经文引用

        这种格式常见于《述文记》等注疏，表示引用原经文从某字到某字的内容。
        例如："無色法中(至)蘊得等性。" 表示引用《顺正理论》中"無色法中...蘊得等性"这段内容

        《述文记》的典型结构：
        1. 经文引用：「無色法中(至)蘊得等性。」
        2. 注疏解释：「述曰：此下明非色非心法...」

        Args:
            text: 注疏原文
            existing_positions: 已提取的位置集合（用于去重）

        Returns:
            引文列表
        """
        citations = []

        # 匹配 "首部分(至)尾部分。" 或 "首部分（至）尾部分。" 格式
        # 改进：放宽字符限制，只排除换行和方括号（校注标记）
        # 首部分：2-30个字符
        # 尾部分：2-40个字符直到句号
        pattern = r"([^\n\[\]]{2,30})[\(（]至[\)）]([^\n。\[\]]{2,40})[。]"

        try:
            for match in re.finditer(pattern, text):
                start_text = match.group(1).strip()
                end_text = match.group(2).strip()
                full_match = match.group(0)

                # 跳过太短的引用
                if len(start_text) < 2 or len(end_text) < 2:
                    continue

                # 跳过包含校注标记的（如 [1]、[A1] 等）
                if re.search(r'\[[A-Za-z]?\d+[A-Za-z]?\]', full_match):
                    continue

                # 跳过以注疏标记开头的（如"述曰"后面的内容不是引文）
                if re.match(r'^(述曰|解云|釋曰|释曰|疏曰|記曰|记曰)', start_text):
                    continue

                # 清理start_text中可能包含的引用标记前缀（如"論曰："）
                start_text_clean = re.sub(
                    r'^(論曰|论曰|頌曰|颂曰|經曰|经曰|論云|论云|經云|经云)[:：]?\s*',
                    '',
                    start_text
                )
                if len(start_text_clean) < 2:
                    continue

                # 去重
                pos_key = (match.start(), match.end())
                if pos_key in existing_positions:
                    continue
                existing_positions.add(pos_key)

                # 构造引文：首部分...尾部分
                # 这个格式便于后续与原经文匹配
                extracted = f"{start_text_clean}...{end_text}"

                # 提取上下文
                context_before = text[max(0, match.start() - 30):match.start()]
                context_after = text[match.end():min(len(text), match.end() + 30)]

                citation_id = f"cit_{uuid.uuid4().hex[:8]}"

                citation = Citation(
                    citation_id=citation_id,
                    marker="(至)",  # 使用特殊标记表示这是范围引用
                    extracted_text=extracted,
                    original_text=full_match,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context_before=context_before,
                    context_after=context_after
                )
                citations.append(citation)

        except re.error as e:
            print(f"[警告] 范围引用正则错误: {e}")

        return citations

    def _find_citation_end(
        self,
        text: str,
        start: int,
        max_len: int = 200
    ) -> int:
        """
        定位引文结束位置

        扫描规则：
        1. 遇到句末标点（。！？」』"）则结束
        2. 遇到引号闭合则结束
        3. 达到最大长度则结束

        Args:
            text: 文本
            start: 起始位置
            max_len: 最大扫描长度

        Returns:
            结束位置
        """
        # 句末标点集合
        end_markers = set('。！？」』"')

        for i in range(start, min(start + max_len, len(text))):
            if text[i] in end_markers:
                return i + 1

        return min(start + max_len, len(text))

    def match_citation_to_position(
        self,
        citation_text: str,
        base_text: str,
        position: int,
        window_size: int = 10,
        threshold: float = 0.75
    ) -> Optional[Dict[str, Any]]:
        """
        将引文匹配到异文位置

        算法流程：
        1. 从position向前后各扩展window_size字符（窗口）
        2. 对窗口文本与引文计算相似度（复用collation_service）
        3. 相似度 >= threshold 则匹配成功
        4. 返回置信度（high: >=0.9, medium: 0.75-0.9, low: <0.75）

        Args:
            citation_text: 引文文本
            base_text: 底本全文
            position: 异文位置（0-based）
            window_size: 窗口大小（默认10字）
            threshold: 相似度阈值（默认0.75）

        Returns:
            匹配结果（失败返回None）
        """
        from app.services.collation_service import collation_service

        # 1. 提取窗口文本
        window_start = max(0, position - window_size)
        window_end = min(len(base_text), position + window_size + 1)
        window_text = base_text[window_start:window_end]

        # 规范化文本（去除标点、空格，便于对比）
        normalized_window = collation_service.normalize_text_for_comparison(window_text)
        normalized_citation = collation_service.normalize_text_for_comparison(citation_text)

        # 2. 计算相似度（复用现有算法）
        similarity = collation_service._compute_similarity(
            normalized_window,
            normalized_citation
        )

        # 3. 阈值判断
        if similarity < threshold:
            return None

        # 4. 计算置信度
        if similarity >= 0.9:
            confidence = 'high'
        elif similarity >= 0.75:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            "similarity": round(similarity, 4),
            "confidence": confidence,
            "matched_text": window_text,
            "commentary_text": citation_text
        }

    def match_all_citations_to_variants(
        self,
        citations: List[Citation],
        base_text: str,
        variant_positions: List[int],
        window_size: int = 10,
        threshold: float = 0.75
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        为所有异文位置批量匹配引文

        Args:
            citations: 引文列表
            base_text: 底本全文
            variant_positions: 异文位置列表（0-based）
            window_size: 窗口大小
            threshold: 相似度阈值

        Returns:
            {position: [match1, match2, ...]}
        """
        all_matches = {}

        for position in variant_positions:
            position_matches = []

            for citation in citations:
                match_result = self.match_citation_to_position(
                    citation_text=citation.extracted_text,
                    base_text=base_text,
                    position=position,
                    window_size=window_size,
                    threshold=threshold
                )

                if match_result:
                    position_matches.append({
                        "citation_id": citation.id,
                        "position": position,
                        "marker": citation.marker,
                        "context": f"{citation.context_before}...{citation.context_after}",
                        **match_result
                    })

            # 按相似度降序排列（最匹配的在前）
            position_matches.sort(key=lambda x: x["similarity"], reverse=True)

            if position_matches:
                all_matches[position] = position_matches

        return all_matches

    @lru_cache(maxsize=1000)
    def _cached_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        缓存的相似度计算（避免重复计算）

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1）
        """
        from app.services.collation_service import collation_service
        return collation_service._compute_similarity(text1, text2)


# 创建全局实例
commentary_service = CommentaryService()
