"""
校勘记智能生成服务

基于四校法判取结果，自动生成符合《中华大藏经》体例的校勘记。

《中华大藏经》体例格式示例：
    九五五页中一六行第九字"及"，磧、普、南作"以"。
    九五五页中一七行第七字"有"，丽、资、普作"又"。
    九五五页下一〇行第一〇字"昏"，磧、普作"惛"。

简化格式（无页码行号时）：
    【1】第23字"住"，丽、房作"往"。
    【2】第45字"云"，据正删。
    【3】第67字，据频补"何"。
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class CollationNote(BaseModel):
    """校勘记条目"""
    index: int                          # 序号
    position: int                       # 字符位置（0-based）
    position_display: str               # 显示格式：第23字
    original_char: str                  # 原字（底本）
    replacement_char: str               # 改字（校本）
    action: str                         # 动作：改/删/补/乙/不改
    source_versions: List[str]          # 依据版本
    explanation: str                    # AI生成的说明（按：...）
    category: str                       # 异文类型：讹误/衍文/脱文/异体字/倒文
    uncertain: bool = False             # 是否存疑
    formatted_text: str                 # 完整格式化文本
    decision_data: Optional[Dict] = None  # 原始判取数据


class CollationNoteGenerator:
    """校勘记智能生成服务"""

    # 中文引号常量
    LQ = "\u201c"  # 左引号 "
    RQ = "\u201d"  # 右引号 "

    # 版本名称简称映射
    VERSION_ABBREVIATIONS = {
        "丽藏": "丽",
        "高丽藏": "丽",
        "高丽大藏经": "丽",
        "房山石经": "房",
        "房山": "房",
        "磧砂藏": "磧",
        "碛砂藏": "磧",
        "普宁藏": "普",
        "南藏": "南",
        "永乐南藏": "南",
        "永乐北藏": "北",
        "北藏": "北",
        "资福藏": "资",
        "大正藏": "正",
        "大正新修大藏经": "正",
        "频伽藏": "频",
        "频伽精舍校刊大藏经": "频",
        "嘉兴藏": "嘉",
        "卍续藏": "卍",
        "卍正藏": "卍",
        "龙藏": "龙",
        "清藏": "清",
        "乾隆大藏经": "龙",
        "赵城金藏": "金",
        "金藏": "金",
        "中华大藏经": "中",
        "敦煌写本": "敦",
        "敦煌": "敦",
        "宋本": "宋",
        "元本": "元",
        "明本": "明",
        "宫本": "宫",
        "圣本": "圣",
        "甲本": "甲",
        "乙本": "乙",
        "丙本": "丙",
        "丁本": "丁",
    }

    # 对校依据模板
    DUIJIAO_TEMPLATES = {
        "majority": "多数版本作「{text}」",
        "early_version": "「{version}」本年代较早",
        "authoritative": "「{version}」本为权威版本",
        "single_version": "「{version}」本作「{text}」",
    }

    # 本校依据模板
    BENJIAO_TEMPLATES = {
        "context_consistent": "同经前后文一致",
        "inner_consistent": "同经第{ref}处亦作「{text}」",
        "style_conform": "符合本经体例",
        "parallel_passage": "与他处对应文句相合",
    }

    # 他校依据模板
    TAJIAO_TEMPLATES = {
        "commentary_match": "某注疏引作「{text}」",
        "other_sutra_match": "「{sutra}」引作「{text}」",
        "citation_evidence": "历代引用多作「{text}」",
    }

    # 理校依据模板
    LIJIAO_TEMPLATES = {
        "semantic_smooth": "义理更通顺",
        "form_similar_error": "形近「{char1}」「{char2}」而讹",
        "sound_similar_error": "音近「{char1}」「{char2}」而讹",
        "grammar_correct": "文法更通顺",
        "context_required": "文意不完，当补「{text}」字",
    }

    # 异文类型对应的动作词
    CATEGORY_ACTIONS = {
        "讹误": "改",
        "error": "改",
        "衍文": "删",
        "yanwen": "删",
        "脱文": "补",
        "tuowen": "补",
        "异体字": "不改",
        "variant": "不改",
        "倒文": "乙",
        "daowen": "乙",
    }

    def _abbreviate_version(self, version_name: str) -> str:
        """
        将版本全名转换为简称

        规则：
        - 【中系●高麗再雕增上寺版】→ 丽增
        - 【中系●大正藏佛陀基金會版】→ 大正
        - 【北系●房山石經北京華夏版】→ 房山
        - 【南系●崇寧】→ 崇寧
        - 【南系●洪武南藏川佛協版】→ 洪武
        """
        import re

        # 先尝试完全匹配预定义简称
        if version_name in self.VERSION_ABBREVIATIONS:
            return self.VERSION_ABBREVIATIONS[version_name]

        # 尝试从【系●版本名...】格式中提取
        # 例如：【中系●高麗再雕增上寺版】《阿毗達磨順正理論》卷13
        bracket_match = re.search(r'【[^●]*●([^】]+)】', version_name)
        if bracket_match:
            content = bracket_match.group(1)  # 如：高麗再雕增上寺版

            # 特定版本的简称规则
            abbreviation_rules = [
                # 高丽系
                (r'高[麗丽]再雕增上寺', '丽增'),
                (r'高[麗丽]再雕', '丽再'),
                (r'高[麗丽]初雕', '丽初'),
                (r'高[麗丽]', '丽'),

                # 大正藏系
                (r'大正藏', '大正'),
                (r'大正', '大正'),

                # 房山石经
                (r'房山石[經经]', '房山'),
                (r'房山', '房山'),

                # 南藏系
                (r'崇[寧宁]', '崇宁'),
                (r'洪武南藏', '洪武'),
                (r'洪武', '洪武'),
                (r'永[樂乐]南藏', '永乐南'),
                (r'永[樂乐]北藏', '永乐北'),
                (r'嘉[興兴]', '嘉兴'),

                # 磧砂藏
                (r'[磧碛]砂', '碛砂'),

                # 其他
                (r'普[寧宁]', '普宁'),
                (r'[頻频]伽', '频伽'),
                (r'[龍龙]藏', '龙藏'),
                (r'乾隆', '乾隆'),
                (r'赵城金藏', '赵城'),
                (r'金藏', '金藏'),
                (r'敦煌', '敦煌'),
                (r'资福', '资福'),
                (r'卍[續续]藏', '卍续'),
                (r'卍正藏', '卍正'),
                (r'中[華华]', '中华'),

                # CBETA 特殊格式
                (r'CBETA', 'CBETA'),
            ]

            for pattern, abbr in abbreviation_rules:
                if re.search(pattern, content):
                    return abbr

            # 如果没有匹配到规则，取版本名的前2-4个有意义的字
            # 去掉"版"字和出版社信息
            clean_content = re.sub(r'(版|出版|基金會|基金会|佛協|佛协|華夏|华夏).*$', '', content)
            if clean_content:
                # 取前2-4个字符作为简称
                return clean_content[:4] if len(clean_content) > 4 else clean_content

            return content[:2] if len(content) > 2 else content

        # 尝试部分匹配预定义简称
        for full_name, abbr in self.VERSION_ABBREVIATIONS.items():
            if full_name in version_name or version_name in full_name:
                return abbr

        # 无法匹配时，取前2-4个字
        if len(version_name) <= 4:
            return version_name
        return version_name[:4]

    def _abbreviate_versions(self, versions: List[str]) -> List[str]:
        """批量转换版本简称"""
        return [self._abbreviate_version(v) for v in versions]

    def generate_notes(
        self,
        decisions: Dict[str, Dict[str, Any]],
        base_text: str,
        base_name: str,
        collation_names: List[str],
        variant_table: Optional[List[Dict]] = None
    ) -> List[CollationNote]:
        """
        生成校勘记列表

        Args:
            decisions: 判取结果字典，key为位置字符串
            base_text: 底本文本
            base_name: 底本名称
            collation_names: 校本名称列表
            variant_table: 异文汇校表（可选，用于获取更多上下文）

        Returns:
            CollationNote列表，按位置排序
        """
        if not decisions:
            return []

        # 构建异文表位置索引
        variant_by_pos = {}
        if variant_table:
            for row in variant_table:
                pos = row.get("position")
                if pos is not None:
                    # position可能是1-based，需要转换
                    variant_by_pos[pos] = row
                    variant_by_pos[pos - 1] = row  # 同时存储0-based

        notes = []
        sorted_positions = sorted(decisions.keys(), key=lambda x: int(x))

        for idx, pos_str in enumerate(sorted_positions, 1):
            pos = int(pos_str)
            decision = decisions[pos_str]

            # 获取异文表行（用于上下文等）
            variant_row = variant_by_pos.get(pos) or variant_by_pos.get(pos + 1)

            note = self.generate_single_note(
                index=idx,
                position=pos,
                decision=decision,
                base_text=base_text,
                base_name=base_name,
                variant_row=variant_row,
                collation_names=collation_names
            )
            notes.append(note)

        return notes

    def generate_single_note(
        self,
        index: int,
        position: int,
        decision: Dict[str, Any],
        base_text: str,
        base_name: str,
        variant_row: Optional[Dict] = None,
        collation_names: Optional[List[str]] = None
    ) -> CollationNote:
        """
        生成单条校勘记

        Args:
            index: 序号
            position: 位置（0-based）
            decision: 判取数据
            base_text: 底本文本
            base_name: 底本名称
            variant_row: 异文表行（可选）
            collation_names: 校本名称列表（可选）

        Returns:
            CollationNote对象
        """
        selected_version = decision.get("selectedVersion", "")
        selected_text = decision.get("selectedText", "")
        custom_text = decision.get("customText")
        uncertain = decision.get("uncertain", False)
        user_note = decision.get("note", "")

        # 获取原字
        if variant_row:
            original_char = variant_row.get("base_char", "")
        elif 0 <= position < len(base_text):
            original_char = base_text[position]
        else:
            original_char = "?"

        # 使用自定义文字或选择的文字
        replacement_char = custom_text if custom_text else selected_text

        # 确定异文类型
        category = self._determine_category(
            decision, original_char, replacement_char, variant_row
        )

        # 确定动作
        action = self._determine_action(category, original_char, replacement_char, selected_version, base_name)

        # 确定依据版本
        source_versions = self._get_source_versions(decision, selected_version, base_name)

        # 生成AI说明
        explanation = self._generate_explanation(
            decision, category, original_char, replacement_char,
            source_versions, user_note
        )

        # 格式化位置显示（1-based）
        position_display = f"第{position + 1}字"

        # 生成完整格式化文本
        formatted_text = self._format_note_text(
            index=index,
            position_display=position_display,
            original_char=original_char,
            replacement_char=replacement_char,
            action=action,
            source_versions=source_versions,
            explanation=explanation,
            category=category,
            uncertain=uncertain
        )

        return CollationNote(
            index=index,
            position=position,
            position_display=position_display,
            original_char=original_char,
            replacement_char=replacement_char,
            action=action,
            source_versions=source_versions,
            explanation=explanation,
            category=category,
            uncertain=uncertain,
            formatted_text=formatted_text,
            decision_data=decision
        )

    def _determine_category(
        self,
        decision: Dict,
        original_char: str,
        replacement_char: str,
        variant_row: Optional[Dict]
    ) -> str:
        """确定异文类型"""
        # 优先使用异文表中的分类
        if variant_row:
            cat = variant_row.get("category", "")
            if cat:
                return cat

        # 根据字符特征判断
        if original_char == "∅" or original_char == "":
            return "衍文"  # 底本无此字，校本有 = 衍文（底本衍）
        if replacement_char == "∅" or replacement_char == "":
            return "脱文"  # 底本有此字，采用删除 = 脱文（底本脱）

        # 检查是否有理校依据中的形近/音近判断
        lijiao = decision.get("lijiao", [])
        if "form_similar_error" in lijiao or "sound_similar_error" in lijiao:
            return "讹误"

        # 默认根据四校依据综合判断
        duijiao = decision.get("duijiao", [])
        benjiao = decision.get("benjiao", [])
        tajiao = decision.get("tajiao", [])

        # 如果有对校/本校/他校依据，通常是讹误
        if duijiao or benjiao or tajiao or lijiao:
            return "讹误"

        return "讹误"  # 默认

    def _determine_action(
        self,
        category: str,
        original_char: str,
        replacement_char: str,
        selected_version: str,
        base_name: str
    ) -> str:
        """确定动作词"""
        # 如果选择底本，不改
        if selected_version == base_name and original_char == replacement_char:
            return "不改"

        # 异体字通常不改
        if category in ("异体字", "variant"):
            return "不改"

        # 根据类型确定动作
        action = self.CATEGORY_ACTIONS.get(category, "改")

        # 特殊处理衍文和脱文
        if category in ("衍文", "yanwen"):
            if original_char == "∅":
                # 底本无此字 = 校本衍，底本正确，删校本
                return "删"
            else:
                # 底本有此字 = 底本衍，需删底本
                return "删"

        if category in ("脱文", "tuowen"):
            if replacement_char == "∅":
                # 选择删除 = 底本脱
                return "删"
            else:
                # 补入文字
                return "补"

        return action

    def _get_source_versions(
        self,
        decision: Dict,
        selected_version: str,
        base_name: str
    ) -> List[str]:
        """获取依据版本列表"""
        sources = []

        # 主要依据是选择的版本
        if selected_version and selected_version != base_name:
            sources.append(selected_version)

        # 从对校依据中提取版本名
        duijiao = decision.get("duijiao", [])
        for item in duijiao:
            if isinstance(item, str) and "_" in item:
                # 格式如 "majority_丽藏" 或 "authoritative_大正藏"
                parts = item.split("_")
                if len(parts) > 1:
                    version_name = parts[1]
                    if version_name not in sources:
                        sources.append(version_name)

        return sources if sources else [selected_version] if selected_version else []

    def _generate_explanation(
        self,
        decision: Dict,
        category: str,
        original_char: str,
        replacement_char: str,
        source_versions: List[str],
        user_note: str
    ) -> str:
        """生成AI说明文字（按：...）"""
        explanations = []

        duijiao = decision.get("duijiao", [])
        benjiao = decision.get("benjiao", [])
        tajiao = decision.get("tajiao", [])
        lijiao = decision.get("lijiao", [])
        commentary_matches = decision.get("commentary_matches", [])

        # 对校依据说明
        for item in duijiao:
            if isinstance(item, str):
                if item.startswith("majority"):
                    explanations.append(f"多数版本作「{replacement_char}」")
                elif item.startswith("early_version"):
                    version = item.split("_")[1] if "_" in item else source_versions[0] if source_versions else ""
                    explanations.append(f"「{version}」本年代较早")
                elif item.startswith("authoritative"):
                    version = item.split("_")[1] if "_" in item else source_versions[0] if source_versions else ""
                    explanations.append(f"「{version}」为权威版本")

        # 本校依据说明
        for item in benjiao:
            if isinstance(item, str):
                if item == "context_consistent":
                    explanations.append("同经前后文一致")
                elif item == "style_conform":
                    explanations.append("符合本经体例")
                elif item == "parallel_passage":
                    explanations.append("与他处对应文句相合")

        # 他校依据说明
        for item in tajiao:
            if isinstance(item, str):
                if item == "commentary_match":
                    if commentary_matches:
                        # 使用实际注疏名称
                        sutra_name = commentary_matches[0].get("sutra_name", "某注疏")
                        explanations.append(f"「{sutra_name}」引作「{replacement_char}」")
                    else:
                        explanations.append(f"注疏引作「{replacement_char}」")
                elif item == "other_sutra_match":
                    explanations.append("他经引用同")

        # 理校依据说明
        for item in lijiao:
            if isinstance(item, str):
                if item == "semantic_smooth":
                    explanations.append("义理更通顺")
                elif item == "form_similar_error":
                    explanations.append(f"形近「{original_char}」「{replacement_char}」而讹")
                elif item == "sound_similar_error":
                    explanations.append(f"音近「{original_char}」「{replacement_char}」而讹")
                elif item == "grammar_correct":
                    explanations.append("文法更通顺")
                elif item == "context_required":
                    explanations.append(f"文意不完，当补「{replacement_char}」字")

        # 如果有用户备注，添加到说明中
        if user_note:
            explanations.append(user_note)

        # 组合说明
        if explanations:
            return "按：" + "，".join(explanations) + "。"
        else:
            # 生成默认说明
            return self._generate_default_explanation(category, original_char, replacement_char)

    def _generate_default_explanation(
        self,
        category: str,
        original_char: str,
        replacement_char: str
    ) -> str:
        """生成默认说明"""
        if category in ("异体字", "variant"):
            return f"按：「{original_char}」「{replacement_char}」为异体字，义同。"
        elif category in ("衍文", "yanwen"):
            if original_char == "∅":
                return f"按：「{replacement_char}」为衍文。"
            else:
                return f"按：「{original_char}」为衍文。"
        elif category in ("脱文", "tuowen"):
            if replacement_char and replacement_char != "∅":
                return f"按：文意不完，当补「{replacement_char}」字。"
            else:
                return "按：此处有脱文。"
        elif category in ("倒文", "daowen"):
            return f"按：「{original_char}」当作「{replacement_char}」，文字颠倒。"
        else:
            return ""

    def _format_note_text(
        self,
        index: int,
        position_display: str,
        original_char: str,
        replacement_char: str,
        action: str,
        source_versions: List[str],
        explanation: str,
        category: str,
        uncertain: bool
    ) -> str:
        """
        格式化校勘记文本

        《中华大藏经》体例格式：
            九五五页中一六行第九字"及"，磧、普、南作"以"。

        简化格式（无页码行号时）：
            【1】第23字"住"，丽、房作"往"。
        """
        # 存疑标记
        uncertain_mark = "（存疑）" if uncertain else ""

        # 依据版本简称（用顿号连接）
        abbr_versions = self._abbreviate_versions(source_versions)
        version_text = "、".join(abbr_versions) if abbr_versions else ""

        # 使用类常量
        LQ = self.LQ
        RQ = self.RQ

        # 根据动作类型生成不同格式
        # 《中华大藏经》体例：第X字"原"，某、某作"改"。
        if action == "改":
            if version_text:
                # 【1】第23字"住"，丽、房作"往"。
                main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}，{version_text}作{LQ}{replacement_char}{RQ}。"
            else:
                main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}改{LQ}{replacement_char}{RQ}。"

        elif action == "删":
            # 衍文：【2】第45字"云"，据正删。 或 【2】第45字"云"，某无。
            if original_char and original_char != "∅":
                if version_text:
                    # 《中华大藏经》体例：某无
                    main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}，{version_text}无。"
                else:
                    main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}删。"
            else:
                # 校本衍文
                main_text = f"【{index}】{position_display}删{LQ}{replacement_char}{RQ}。"

        elif action == "补":
            # 脱文：【3】第67字，据频补"何"。 或 某有"何"字。
            if version_text:
                main_text = f"【{index}】{position_display}，{version_text}有{LQ}{replacement_char}{RQ}字。"
            else:
                main_text = f"【{index}】{position_display}补{LQ}{replacement_char}{RQ}。"

        elif action == "乙":
            # 倒文：【5】第89字"AB"乙。
            if version_text:
                main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}，{version_text}作{LQ}{replacement_char}{RQ}。"
            else:
                main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}{LQ}{replacement_char}{RQ}乙。"

        elif action == "不改":
            # 异体字或不改：【4】第89字"義"，某作"义"，异体不改。
            if category in ("异体字", "variant"):
                if version_text:
                    main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}，{version_text}作{LQ}{replacement_char}{RQ}，异体不改。"
                else:
                    main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}{LQ}{replacement_char}{RQ}异体，不改。"
            else:
                main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}，不改。"

        else:
            main_text = f"【{index}】{position_display}{LQ}{original_char}{RQ}，{version_text}作{LQ}{replacement_char}{RQ}。"

        # 组合完整文本
        full_text = main_text
        if explanation:
            full_text += explanation
        if uncertain_mark:
            full_text += uncertain_mark

        return full_text

    def format_notes_for_export(
        self,
        notes: List[CollationNote],
        format_type: str = "plain"
    ) -> str:
        """
        格式化校勘记用于导出

        Args:
            notes: 校勘记列表
            format_type: 格式类型 - plain/markdown/html

        Returns:
            格式化的文本
        """
        if format_type == "markdown":
            lines = ["# 校勘记\n"]
            for note in notes:
                lines.append(f"{note.formatted_text}\n")
            return "\n".join(lines)

        elif format_type == "html":
            lines = ["<h1>校勘记</h1>", "<div class='collation-notes'>"]
            for note in notes:
                uncertain_class = " uncertain" if note.uncertain else ""
                lines.append(f"<p class='note{uncertain_class}'>{note.formatted_text}</p>")
            lines.append("</div>")
            return "\n".join(lines)

        else:  # plain
            return "\n".join([note.formatted_text for note in notes])


# 单例服务实例
collation_note_generator = CollationNoteGenerator()
