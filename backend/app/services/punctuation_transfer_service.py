"""
标点迁移服务

功能：将一份已标点文本的标点符号迁移至另一份无标点的相似文本中。

核心算法：
1. 提取标点位置: source → (纯文字, 标点位置列表)
2. 文本对齐: 使用编辑距离(Levenshtein)对齐两个纯文本
3. 标点插入: 根据对齐映射，将标点插入目标文本对应位置
4. 智能验证: 检查标点位置是否合理，避免在词语中间断开
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import difflib

from app.utils.punctuation import PUNCTUATION_SET, strip_punctuation_and_whitespace


# 佛典常见不可分割的词语/短语（不应在中间插入标点）
# 这些词语如果被标点分割会导致语义错误
UNSPLITTABLE_PHRASES = {
    # 时间/场景词
    "爾時", "一時", "是時", "彼時", "何時", "時長", "食時", "一面",
    # 称谓
    "世尊", "如來", "菩薩", "比丘", "須菩提", "舍利弗", "阿難", "佛言", "佛告",
    "善男子", "善女人", "善男", "善女", "長老", "慧命", "大士", "大眾",
    # 常见词组
    "如是", "所以", "何以", "云何", "若有", "若無", "所有", "一切",
    "無量", "無邊", "無數", "無上", "正念", "正遍知", "正覺", "正等正覺",
    "阿耨多羅三藐三菩提", "般若波羅蜜", "涅槃", "眾生",
    # 动作词组
    "乞食", "乞已", "食已", "食訖", "洗足", "敷座", "結加趺坐", "結跏趺坐",
    "頂禮", "合掌", "恭敬", "白佛", "佛說", "從座起", "即從座起",
    "右膝著地", "偏袒右肩", "端身", "正念不動",
    # 地名
    "給孤獨園", "祇樹", "舍衛", "王舍城", "舍婆提", "舍婆提城",
    # 其他常见词
    "善哉", "希有", "稀有", "甚深", "微妙", "難信", "難解",
    "退坐", "右遶", "三匝", "佛足",
}

# 句末标点（通常表示句子结束）
SENTENCE_END_PUNCTUATION = {'。', '！', '？', '：', '；'}

# 句内标点（通常表示短暂停顿）
CLAUSE_PUNCTUATION = {'，', '、'}


@dataclass
class PunctuationMark:
    """标点符号位置信息"""
    position: int  # 字符位置（在纯文本中，该标点位于第position个字符之后）
    mark: str  # 标点符号


@dataclass
class TransferResult:
    """迁移结果"""
    result_text: str  # 迁移后的文本
    transferred_count: int  # 成功迁移的标点数量
    total_punctuation_count: int  # 源文本中的标点总数
    alignment_score: float  # 对齐分数（0-1）
    warnings: List[str]  # 警告信息


class PunctuationTransferService:
    """标点迁移服务"""

    def __init__(self):
        self.punctuation_set = PUNCTUATION_SET

    def transfer(
        self,
        source_text: str,
        target_text: str,
        preserve_existing_punctuation: bool = False
    ) -> TransferResult:
        """
        执行标点迁移

        Args:
            source_text: 源文本（带标点）
            target_text: 目标文本（无标点或少量标点）
            preserve_existing_punctuation: 是否保留目标文本中已有的标点

        Returns:
            TransferResult: 迁移结果
        """
        warnings = []

        # 1. 提取源文本的标点位置（基于纯文本）
        source_pure_text, punctuation_positions = self._extract_punctuation_positions(source_text)
        total_punctuation_count = len(punctuation_positions)

        # 2. 处理目标文本 - 保留换行符位置信息
        # 先记录目标文本中换行符的位置（基于去除标点后的纯文本索引）
        target_pure_text, newline_positions = self._extract_text_preserving_newlines(target_text)

        # 3. 检查纯文本的相似度
        alignment_score = self._compute_similarity(source_pure_text, target_pure_text)

        if alignment_score < 0.3:
            warnings.append(f"警告：两个文本的相似度较低（{alignment_score:.1%}），迁移结果可能不准确")

        # 4. 对齐两个纯文本
        position_mapping = self._align_texts(source_pure_text, target_pure_text)

        # 5. 根据对齐映射，将标点插入目标纯文本，同时保留换行符
        result_text, transferred_count = self._insert_punctuation_with_newlines(
            target_pure_text,
            punctuation_positions,
            position_mapping,
            source_text_len=len(source_pure_text),
            newline_positions=newline_positions
        )

        if transferred_count < total_punctuation_count:
            warnings.append(
                f"部分标点无法迁移：成功迁移 {transferred_count}/{total_punctuation_count} 个"
            )

        return TransferResult(
            result_text=result_text,
            transferred_count=transferred_count,
            total_punctuation_count=total_punctuation_count,
            alignment_score=alignment_score,
            warnings=warnings
        )

    def _extract_punctuation_positions(
        self, text: str
    ) -> Tuple[str, List[PunctuationMark]]:
        """
        提取文本中的标点位置

        Args:
            text: 带标点的文本

        Returns:
            (纯文本, 标点位置列表)
            标点位置列表中，position表示该标点位于纯文本第position个字符之后
        """
        pure_chars = []
        punctuation_positions = []
        char_index = 0

        i = 0
        while i < len(text):
            char = text[i]
            if char in self.punctuation_set:
                # 收集连续的标点符号
                punct_marks = char
                j = i + 1
                while j < len(text) and text[j] in self.punctuation_set:
                    punct_marks += text[j]
                    j += 1

                # 记录标点位置（位于当前字符位置之后）
                punctuation_positions.append(PunctuationMark(
                    position=char_index,
                    mark=punct_marks
                ))
                i = j
            elif char.isspace():
                # 跳过空白字符
                i += 1
            else:
                pure_chars.append(char)
                char_index += 1
                i += 1

        pure_text = ''.join(pure_chars)
        return pure_text, punctuation_positions

    def _extract_text_preserving_newlines(
        self, text: str
    ) -> Tuple[str, Dict[int, str]]:
        """
        提取纯文本，同时记录换行符位置

        Args:
            text: 原始文本（可能包含换行符和标点）

        Returns:
            (纯文本, 换行符位置字典)
            换行符位置字典: {纯文本中的字符索引: 该字符后的换行符}
        """
        pure_chars = []
        newline_positions: Dict[int, str] = {}
        char_index = 0

        i = 0
        while i < len(text):
            char = text[i]
            if char in self.punctuation_set:
                # 跳过标点
                i += 1
            elif char in '\n\r':
                # 记录换行符位置（在当前字符索引之后）
                # 收集连续的换行符
                newline_chars = char
                j = i + 1
                while j < len(text) and text[j] in '\n\r':
                    newline_chars += text[j]
                    j += 1
                # 标准化换行符
                newline_chars = '\n' if '\n' in newline_chars else newline_chars
                # 记录在当前纯文本位置之后
                if char_index in newline_positions:
                    newline_positions[char_index] += newline_chars
                else:
                    newline_positions[char_index] = newline_chars
                i = j
            elif char.isspace():
                # 跳过其他空白字符（空格、制表符等）
                i += 1
            else:
                pure_chars.append(char)
                char_index += 1
                i += 1

        pure_text = ''.join(pure_chars)
        return pure_text, newline_positions

    def _align_texts(
        self, source_text: str, target_text: str
    ) -> Dict[int, Optional[int]]:
        """
        对齐两个纯文本，建立源文本位置到目标文本位置的映射

        使用 difflib.SequenceMatcher 进行对齐

        Args:
            source_text: 源纯文本
            target_text: 目标纯文本

        Returns:
            位置映射字典: {源位置: 目标位置或None}
        """
        position_mapping: Dict[int, Optional[int]] = {}
        len(source_text)
        target_len = len(target_text)

        matcher = difflib.SequenceMatcher(None, source_text, target_text, autojunk=False)

        # 记录每个opcode的边界，用于后续处理删除区域
        opcodes = list(matcher.get_opcodes())

        for idx, (tag, i1, i2, j1, j2) in enumerate(opcodes):
            if tag == 'equal':
                # 相等部分：一一对应
                for offset in range(i2 - i1):
                    position_mapping[i1 + offset] = j1 + offset
            elif tag == 'replace':
                # 替换部分：尝试对齐（按比例映射）
                src_len = i2 - i1
                tgt_len = j2 - j1
                for offset in range(src_len):
                    # 按比例计算目标位置
                    if tgt_len > 0:
                        target_offset = int(offset * tgt_len / src_len)
                        position_mapping[i1 + offset] = j1 + target_offset
                    else:
                        position_mapping[i1 + offset] = j1
            elif tag == 'delete':
                # 删除部分：源文本有但目标文本没有
                # 改进：不设为None，而是映射到最近的有效目标位置
                # 找到下一个有效的目标位置（即delete区域结束后的位置）
                next_target_pos = j1  # delete区域对应的目标位置就是j1（因为j1==j2）

                # 查找下一个非delete操作的目标起始位置
                for future_idx in range(idx + 1, len(opcodes)):
                    future_tag, _, _, future_j1, _ = opcodes[future_idx]
                    if future_tag != 'delete':
                        next_target_pos = future_j1
                        break
                else:
                    # 如果后面没有非delete操作，使用目标文本末尾
                    next_target_pos = target_len

                # 将删除区域的所有位置映射到下一个有效位置
                for offset in range(i2 - i1):
                    position_mapping[i1 + offset] = next_target_pos
            elif tag == 'insert':
                # 插入部分：目标文本有但源文本没有，不需要处理
                pass

        return position_mapping

    def _insert_punctuation(
        self,
        target_text: str,
        punctuation_positions: List[PunctuationMark],
        position_mapping: Dict[int, Optional[int]],
        source_text_len: int = 0
    ) -> Tuple[str, int]:
        """
        根据位置映射，将标点插入目标文本

        Args:
            target_text: 目标纯文本
            punctuation_positions: 标点位置列表
            position_mapping: 位置映射
            source_text_len: 源纯文本长度（用于处理末尾标点）

        Returns:
            (插入标点后的文本, 成功迁移的标点数量)
        """
        # 构建目标文本中每个位置后应该插入的标点
        # {目标位置: 标点符号}
        target_punctuation: Dict[int, str] = {}
        transferred_count = 0
        target_text_len = len(target_text)

        for punct in punctuation_positions:
            source_pos = punct.position
            # 标点位于source_pos个字符之后
            # 需要找到对应的目标位置

            target_pos = None

            # 优先从映射中查找
            if source_pos in position_mapping:
                target_pos = position_mapping[source_pos]

            # 如果映射中没有或者映射为None，尝试其他策略
            if target_pos is None:
                if source_pos == 0:
                    # 文本开头的标点
                    target_pos = 0
                elif source_pos >= source_text_len and source_text_len > 0:
                    # 文本末尾的标点
                    target_pos = target_text_len
                else:
                    # 尝试找最近的有效映射位置
                    # 向前查找
                    for search_pos in range(source_pos - 1, -1, -1):
                        if search_pos in position_mapping and position_mapping[search_pos] is not None:
                            # 找到前一个有效位置，标点应该放在它后面
                            target_pos = position_mapping[search_pos]
                            # 但实际上应该放在下一个位置
                            if target_pos < target_text_len:
                                target_pos = target_pos + 1
                            break

                    # 如果向前没找到，向后查找
                    if target_pos is None:
                        for search_pos in range(source_pos + 1, source_text_len):
                            if search_pos in position_mapping and position_mapping[search_pos] is not None:
                                target_pos = position_mapping[search_pos]
                                break

            # 确保target_pos在有效范围内
            if target_pos is not None:
                target_pos = max(0, min(target_pos, target_text_len))
                # 合并同一位置的多个标点
                if target_pos in target_punctuation:
                    target_punctuation[target_pos] += punct.mark
                else:
                    target_punctuation[target_pos] = punct.mark
                transferred_count += 1

        # 构建结果文本
        result_chars = []

        # 处理开头的标点（位置0表示文本开始之前）
        if 0 in target_punctuation:
            result_chars.append(target_punctuation[0])

        for i, char in enumerate(target_text):
            result_chars.append(char)
            # 检查该位置后是否需要插入标点（i+1表示第i个字符之后，即第i+1个位置）
            if (i + 1) in target_punctuation:
                result_chars.append(target_punctuation[i + 1])

        return ''.join(result_chars), transferred_count

    def _insert_punctuation_with_newlines(
        self,
        target_text: str,
        punctuation_positions: List[PunctuationMark],
        position_mapping: Dict[int, Optional[int]],
        source_text_len: int,
        newline_positions: Dict[int, str]
    ) -> Tuple[str, int]:
        """
        根据位置映射，将标点插入目标文本，同时保留原始换行符
        增加智能验证，避免在不合理的位置插入标点

        Args:
            target_text: 目标纯文本
            punctuation_positions: 标点位置列表
            position_mapping: 位置映射
            source_text_len: 源纯文本长度
            newline_positions: 换行符位置字典

        Returns:
            (插入标点后的文本, 成功迁移的标点数量)
        """
        # 构建目标文本中每个位置后应该插入的标点
        target_punctuation: Dict[int, str] = {}
        transferred_count = 0
        target_text_len = len(target_text)

        for punct in punctuation_positions:
            source_pos = punct.position
            target_pos = None

            if source_pos in position_mapping:
                target_pos = position_mapping[source_pos]

            if target_pos is None:
                if source_pos == 0:
                    target_pos = 0
                elif source_pos >= source_text_len and source_text_len > 0:
                    target_pos = target_text_len
                else:
                    for search_pos in range(source_pos - 1, -1, -1):
                        if search_pos in position_mapping and position_mapping[search_pos] is not None:
                            target_pos = position_mapping[search_pos]
                            if target_pos < target_text_len:
                                target_pos = target_pos + 1
                            break
                    if target_pos is None:
                        for search_pos in range(source_pos + 1, source_text_len):
                            if search_pos in position_mapping and position_mapping[search_pos] is not None:
                                target_pos = position_mapping[search_pos]
                                break

            if target_pos is not None:
                target_pos = max(0, min(target_pos, target_text_len))

                # 智能验证：检查这个位置是否适合插入标点
                validated_pos, validated_punct = self._validate_punctuation_position(
                    target_text, target_pos, punct.mark
                )

                if validated_pos is not None and validated_punct:
                    if validated_pos in target_punctuation:
                        target_punctuation[validated_pos] += validated_punct
                    else:
                        target_punctuation[validated_pos] = validated_punct
                    transferred_count += 1

        # 构建结果文本，同时插入标点和换行符
        result_chars = []

        # 处理开头的换行符（位置0表示文本开始之前）
        if 0 in newline_positions:
            result_chars.append(newline_positions[0])

        # 处理开头的标点
        if 0 in target_punctuation:
            result_chars.append(target_punctuation[0])

        for i, char in enumerate(target_text):
            result_chars.append(char)
            pos = i + 1  # 当前字符之后的位置

            # 先插入标点，再插入换行符（标点在行末，换行在标点后）
            if pos in target_punctuation:
                result_chars.append(target_punctuation[pos])

            if pos in newline_positions:
                result_chars.append(newline_positions[pos])

        return ''.join(result_chars), transferred_count

    def _validate_punctuation_position(
        self,
        text: str,
        position: int,
        punct_mark: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        验证并调整标点位置，确保不会在词语中间插入标点

        Args:
            text: 目标纯文本
            position: 建议的插入位置（在第position个字符之后）
            punct_mark: 要插入的标点符号

        Returns:
            (调整后的位置, 调整后的标点) 或 (None, None) 如果应该跳过
        """
        text_len = len(text)

        # 边界情况
        if position <= 0:
            return (0, punct_mark)
        if position >= text_len:
            return (text_len, punct_mark)

        # 检查是否会分割不可分割的词语
        # 如果会分割词语，直接跳过这个标点（返回None）
        # 因为这说明源文本和目标文本在这个位置的内容不同
        for phrase in UNSPLITTABLE_PHRASES:
            phrase_len = len(phrase)

            # 检查这个词语是否跨越 position 位置
            for start in range(max(0, position - phrase_len + 1), min(position + 1, text_len - phrase_len + 1)):
                end = start + phrase_len
                substring = text[start:end]

                if substring == phrase:
                    # 找到了一个不可分割词语
                    # 检查 position 是否在词语中间（不包括词语开始前和结束后）
                    if start < position < end:
                        # position 在词语中间，跳过这个标点
                        return (None, None)

        # 额外检查：问号和感叹号通常只出现在特定语境
        if punct_mark in {'？', '！'}:
            context_start = max(0, position - 15)
            context = text[context_start:position]

            question_indicators = {'何', '云何', '幾', '誰', '孰', '安', '焉', '豈', '哉', '乎', '耶', '邪', '否'}
            has_question_word = any(ind in context for ind in question_indicators)

            if punct_mark == '？' and not has_question_word:
                punct_mark = '，'
            elif punct_mark == '！':
                exclaim_indicators = {'善哉', '希有', '甚深', '難信', '稀有', '奇哉', '善男子', '善女人'}
                has_exclaim_word = any(ind in context for ind in exclaim_indicators)
                if not has_exclaim_word:
                    punct_mark = '。'

        return (position, punct_mark)

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1）
        """
        matcher = difflib.SequenceMatcher(None, text1, text2, autojunk=False)
        return matcher.ratio()

    def remove_punctuation(self, text: str) -> str:
        """
        移除文本中的所有标点符号

        Args:
            text: 原始文本

        Returns:
            移除标点后的文本
        """
        return strip_punctuation_and_whitespace(text)

    def get_example_texts(self) -> Dict[str, str]:
        """
        获取示例文本

        Returns:
            {source: 源文本, target: 目标文本}
        """
        # 使用佛典文本作为示例
        source = """如是我聞。一時，佛在舍衛國祇樹給孤獨園。與大比丘眾千二百五十人俱。爾時，世尊食時，著衣持缽，入舍衛大城乞食。於其城中，次第乞已，還至本處。飯食訖，收衣缽，洗足已，敷座而坐。"""

        target = """如是我聞一時佛在舍衛國祇樹給孤獨園與大比丘眾千二百五十人俱爾時世尊食時著衣持缽入舍衛大城乞食於其城中次第乞已還至本處飯食訖收衣缽洗足已敷座而坐"""

        return {
            "source": source,
            "target": target
        }


# 创建全局服务实例
punctuation_transfer_service = PunctuationTransferService()
