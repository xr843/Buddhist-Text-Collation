"""
校勘记格式生成服务

支持生成符合学术规范的校勘记格式：
1. TXT格式 - 传统校勘记体例（参照陈垣《校勘学释例》）
2. TEI-XML格式 - 数字人文标准格式
3. JSON格式 - 结构化数据

参考文献：
- 陈垣《校勘学释例》
- TEI P5 Guidelines: Critical Apparatus
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom


class NoteType(Enum):
    """校勘记类型"""
    VARIANT = "异文"      # 异体字
    ERROR = "讹误"        # 讹字
    YANWEN = "衍文"       # 多出的字
    TUOWEN = "脱文"       # 缺少的字
    DAOWEN = "倒文"       # 字序颠倒
    PUNCTUATION = "标点"  # 标点差异


@dataclass
class CollationNote:
    """校勘记条目"""
    index: int                    # 序号
    position: int                 # 在底本中的位置（字符索引）
    note_type: NoteType           # 校勘类型
    base_text: str                # 底本文字
    variant_text: str             # 校本文字
    base_version: str             # 底本名称
    variant_version: str          # 校本名称
    context_before: str           # 前文（上下文）
    context_after: str            # 后文（上下文）
    annotation: Optional[str] = None  # 按语/备注


class CollationNoteService:
    """校勘记生成服务"""

    def __init__(self):
        self.notes: List[CollationNote] = []

    def generate_notes_from_alignment(
        self,
        aligned_segments: List[Dict],
        base_text: str,
        base_version: str = "底本",
        variant_version: str = "校本",
        context_length: int = 10,
        max_replace_split: int = 20,
    ) -> List[CollationNote]:
        """
        从对齐结果生成“可追溯”的校勘记（含位置与上下文）。

        约定（与 collation_service 输出一致）：
        - delete: 底本有，校本无（脱文）
        - insert: 底本无，校本有（衍文）
        - replace: 底/校不同（异体字/讹误/倒文）
        """
        from app.services.variant_dict import is_variant

        notes: List[CollationNote] = []
        note_index = 0
        base_pos = 0  # 在底本文本中的全局位置（字符索引）

        def ctx_before(pos: int) -> str:
            start = max(0, pos - context_length)
            return base_text[start:pos]

        def ctx_after(pos: int, base_len: int) -> str:
            start = min(len(base_text), pos + base_len)
            end = min(len(base_text), start + context_length)
            return base_text[start:end]

        for seg in aligned_segments:
            seg_type = seg.get("type")
            t1 = seg.get("text1") or ""
            t2 = seg.get("text2") or ""

            if seg_type == "equal":
                base_pos += len(t1)
                continue

            if seg_type == "delete":
                # 脱文：逐字记录，方便定位
                for ch in t1:
                    note_index += 1
                    notes.append(CollationNote(
                        index=note_index,
                        position=base_pos,
                        note_type=NoteType.TUOWEN,
                        base_text=ch,
                        variant_text="",
                        base_version=base_version,
                        variant_version=variant_version,
                        context_before=ctx_before(base_pos),
                        context_after=ctx_after(base_pos, 1),
                    ))
                    base_pos += 1
                continue

            if seg_type == "insert":
                # 衍文：底本位置不变，逐字记录
                for ch in t2:
                    note_index += 1
                    notes.append(CollationNote(
                        index=note_index,
                        position=base_pos,
                        note_type=NoteType.YANWEN,
                        base_text="",
                        variant_text=ch,
                        base_version=base_version,
                        variant_version=variant_version,
                        context_before=ctx_before(base_pos),
                        context_after=ctx_after(base_pos, 0),
                    ))
                continue

            if seg_type == "replace":
                # 倒文优先整体记一条（便于学术叙述）
                if seg.get("_is_merged_transposition") or self._is_transposition(t1, t2):
                    note_index += 1
                    notes.append(CollationNote(
                        index=note_index,
                        position=base_pos,
                        note_type=NoteType.DAOWEN,
                        base_text=t1,
                        variant_text=t2,
                        base_version=base_version,
                        variant_version=variant_version,
                        context_before=ctx_before(base_pos),
                        context_after=ctx_after(base_pos, len(t1)),
                    ))
                    base_pos += len(t1)
                    continue

                # 可控范围内的等长替换：逐字分类为异体字/讹误
                if t1 and t2 and len(t1) == len(t2) and len(t1) <= max_replace_split:
                    for i in range(len(t1)):
                        c1 = t1[i]
                        c2 = t2[i]
                        category = NoteType.VARIANT if is_variant(c1, c2) else NoteType.ERROR
                        note_index += 1
                        notes.append(CollationNote(
                            index=note_index,
                            position=base_pos,
                            note_type=category,
                            base_text=c1,
                            variant_text=c2,
                            base_version=base_version,
                            variant_version=variant_version,
                            context_before=ctx_before(base_pos),
                            context_after=ctx_after(base_pos, 1),
                        ))
                        base_pos += 1
                    continue

                # 其他情况：整体作为一条讹误/异文记录（不强行拆分）
                note_type = self._determine_note_type(seg_type, t1, t2, seg)
                note_index += 1
                notes.append(CollationNote(
                    index=note_index,
                    position=base_pos,
                    note_type=note_type,
                    base_text=t1,
                    variant_text=t2,
                    base_version=base_version,
                    variant_version=variant_version,
                    context_before=ctx_before(base_pos),
                    context_after=ctx_after(base_pos, len(t1)),
                ))
                base_pos += len(t1)
                continue

            # 兜底：未知类型不生成条目，但尽量推进 base_pos（避免无限循环）
            if t1:
                base_pos += len(t1)

        self.notes = notes
        return notes

    def generate_notes_from_statistics(
        self,
        aligned_segments: List[Dict],
        statistics: Dict,
        base_version: str = "底本",
        variant_version: str = "校本",
        context_length: int = 10
    ) -> List[CollationNote]:
        """
        兼容入口：历史上该方法基于统计信息生成校勘记，会丢失定位。

        现在改为基于 aligned_segments 生成，并尝试从 statistics 中获取底本文本，
        如缺失则使用拼接得到的底本文本。
        """
        base_text = statistics.get("base_text")
        if not isinstance(base_text, str):
            base_text = "".join(
                (seg.get("text1") or "")
                for seg in aligned_segments
                if seg.get("type") in ("equal", "delete", "replace")
            )

        return self.generate_notes_from_alignment(
            aligned_segments=aligned_segments,
            base_text=base_text,
            base_version=base_version,
            variant_version=variant_version,
            context_length=context_length,
        )

    def _get_context_before(self, segments: List[Dict], current_idx: int, length: int) -> str:
        """获取前文上下文"""
        context = ""
        for j in range(current_idx - 1, -1, -1):
            prev_text = segments[j].get("text1") or segments[j].get("text2", "")
            context = prev_text + context
            if len(context) >= length:
                break
        # 清理换行符和特殊字符，确保CSV兼容
        context = context[-length:] if len(context) > length else context
        return context.replace('\n', '').replace('\r', '').replace('\t', ' ')

    def _get_context_after(self, segments: List[Dict], current_idx: int, length: int) -> str:
        """获取后文上下文"""
        context = ""
        for j in range(current_idx + 1, len(segments)):
            next_text = segments[j].get("text1") or segments[j].get("text2", "")
            context = context + next_text
            if len(context) >= length:
                break
        # 清理换行符和特殊字符，确保CSV兼容
        context = context[:length] if len(context) > length else context
        return context.replace('\n', '').replace('\r', '').replace('\t', ' ')

    def _determine_note_type(self, seg_type: str, text1: str, text2: str, seg: Dict) -> NoteType:
        """确定校勘记类型"""
        if seg_type == "delete":
            return NoteType.TUOWEN
        elif seg_type == "insert":
            return NoteType.YANWEN
        elif seg_type == "replace":
            # 检查是否为倒文
            if seg.get("_is_merged_transposition") or self._is_transposition(text1, text2):
                return NoteType.DAOWEN
            # 检查是否为异体字
            if len(text1) == 1 and len(text2) == 1:
                from app.services.variant_dict import is_variant
                if is_variant(text1, text2):
                    return NoteType.VARIANT
            return NoteType.ERROR
        return NoteType.ERROR

    def _is_transposition(self, text1: str, text2: str) -> bool:
        """检测是否为倒文（2-6字）"""
        if len(text1) != len(text2) or len(text1) < 2 or len(text1) > 6:
            return False
        if text1 == text2:
            return False
        return sorted(text1) == sorted(text2)

    def export_to_txt(
        self,
        notes: Optional[List[CollationNote]] = None,
        title: str = "校勘记",
        include_context: bool = True
    ) -> str:
        """
        导出为传统校勘记TXT格式

        格式参照陈垣《校勘学释例》：
        [序号] “底本文字”，校本作“校本文字”。（按语）

        Args:
            notes: 校勘记列表（默认使用self.notes）
            title: 标题
            include_context: 是否包含上下文

        Returns:
            TXT格式字符串
        """
        notes = notes or self.notes
        if not notes:
            return f"【{title}】\n\n（无校勘记）"

        lines = [
            f"【{title}】",
            f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            f"共 {len(notes)} 条校勘记",
            "",
            "=" * 50,
            ""
        ]

        for note in notes:
            line = self._format_note_txt(note, include_context)
            lines.append(line)
            lines.append("")

        return "\n".join(lines)

    def _format_note_txt(
        self,
        note: CollationNote,
        include_context: bool
    ) -> str:
        """格式化单条校勘记为TXT"""
        parts = [f"[{note.index}]"]

        # 上下文（可选）
        if include_context and note.context_before:
            parts.append(f"……{note.context_before}")

        # 根据类型生成校勘语
        if note.note_type == NoteType.TUOWEN:
            # 脱文：底本有，校本无
            parts.append(f"“{note.base_text or '□'}”")
            parts.append(f"，{note.variant_version}无此字")
        elif note.note_type == NoteType.YANWEN:
            # 衍文：底本无，校本有
            parts.append("（底本无）")
            parts.append(f"{note.variant_version}有“{note.variant_text or '□'}”字")
        elif note.note_type == NoteType.DAOWEN:
            # 倒文
            parts.append(f"“{note.base_text}”")
            parts.append(f"，{note.variant_version}作“{note.variant_text}”，疑倒文")
        elif note.note_type == NoteType.VARIANT:
            # 异体字
            parts.append(f"“{note.base_text}”")
            parts.append(f"，{note.variant_version}作“{note.variant_text}”，异体字")
        else:
            # 讹误
            parts.append(f"“{note.base_text}”")
            parts.append(f"，{note.variant_version}作“{note.variant_text}”")

        # 上下文后文
        if include_context and note.context_after:
            parts.append(f"{note.context_after}……")

        parts.append("。")

        # 按语
        if note.annotation:
            parts.append(f"（按：{note.annotation}）")

        return "".join(parts)

    def export_to_tei_xml(
        self,
        notes: Optional[List[CollationNote]] = None,
        title: str = "校勘记",
        base_version: str = "底本",
        variant_version: str = "校本"
    ) -> str:
        """
        导出为TEI-XML格式

        遵循TEI P5 Guidelines的Critical Apparatus模块

        Args:
            notes: 校勘记列表
            title: 标题
            base_version: 底本名称
            variant_version: 校本名称

        Returns:
            TEI-XML格式字符串
        """
        notes = notes or self.notes

        # 创建根元素
        tei = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")

        # teiHeader
        header = ET.SubElement(tei, "teiHeader")
        file_desc = ET.SubElement(header, "fileDesc")
        title_stmt = ET.SubElement(file_desc, "titleStmt")
        title_elem = ET.SubElement(title_stmt, "title")
        title_elem.text = title

        # 版本信息
        source_desc = ET.SubElement(file_desc, "sourceDesc")
        list_wit = ET.SubElement(source_desc, "listWit")

        wit_base = ET.SubElement(list_wit, "witness")
        wit_base.set("{http://www.w3.org/XML/1998/namespace}id", "base")
        wit_base.text = base_version

        wit_var = ET.SubElement(list_wit, "witness")
        wit_var.set("{http://www.w3.org/XML/1998/namespace}id", "var")
        wit_var.text = variant_version

        # text/body
        text = ET.SubElement(tei, "text")
        body = ET.SubElement(text, "body")

        # 校勘记列表
        app_list = ET.SubElement(body, "listApp")
        app_list.set("type", "critical-apparatus")

        for note in notes:
            app = self._create_tei_app_element(note)
            app_list.append(app)

        # 格式化输出
        xml_str = ET.tostring(tei, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ", encoding=None)

    def _create_tei_app_element(self, note: CollationNote) -> ET.Element:
        """创建TEI <app> 元素"""
        app = ET.Element("app")
        app.set("n", str(note.index))
        app.set("type", note.note_type.value)
        app.set("loc", str(note.position))

        # 底本读法
        lem = ET.SubElement(app, "lem")
        lem.set("wit", "#base")
        lem.text = note.base_text or "（无）"

        # 校本读法
        rdg = ET.SubElement(app, "rdg")
        rdg.set("wit", "#var")
        rdg.text = note.variant_text or "（无）"

        # 校勘说明（按语）
        if note.annotation:
            note_elem = ET.SubElement(app, "note")
            note_elem.text = note.annotation

        # 上下文（可选，便于复核与引用）
        if note.context_before or note.context_after:
            ctx = ET.SubElement(app, "note")
            ctx.set("type", "context")
            ctx.text = f"{note.context_before}【{note.base_text or '□'}】{note.context_after}"

        return app

    def export_to_json(
        self,
        notes: Optional[List[CollationNote]] = None,
        include_metadata: bool = True
    ) -> str:
        """
        导出为JSON格式

        Args:
            notes: 校勘记列表
            include_metadata: 是否包含元数据

        Returns:
            JSON格式字符串
        """
        notes = notes or self.notes

        data = {
            "notes": [
                {
                    "index": note.index,
                    "position": note.position,
                    "type": note.note_type.value,
                    "base_text": note.base_text,
                    "variant_text": note.variant_text,
                    "base_version": note.base_version,
                    "variant_version": note.variant_version,
                    "context_before": note.context_before,
                    "context_after": note.context_after,
                    "annotation": note.annotation
                }
                for note in notes
            ]
        }

        if include_metadata:
            data["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "total_notes": len(notes),
                "statistics": self._compute_note_statistics(notes)
            }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _compute_note_statistics(self, notes: List[CollationNote]) -> Dict:
        """计算校勘记统计"""
        stats = {
            "by_type": {}
        }

        for note in notes:
            # 按校勘类型统计
            note_type = note.note_type.value
            if note_type not in stats["by_type"]:
                stats["by_type"][note_type] = 0
            stats["by_type"][note_type] += 1

        return stats

    def export_to_csv_academic(
        self,
        notes: Optional[List[CollationNote]] = None
    ) -> str:
        """
        导出为学术CSV格式

        Args:
            notes: 校勘记列表

        Returns:
            CSV格式字符串
        """
        import csv
        import io

        notes = notes or self.notes
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # 检查是否有任何按语内容
        has_annotation = any(note.annotation for note in notes)

        # 表头
        headers = [
            "序号", "位置", "类型", "底本文字", "校本文字",
            "前文", "后文", "底本", "校本"
        ]
        if has_annotation:
            headers.append("按语")
        writer.writerow(headers)

        # 数据行
        for note in notes:
            # 清理文本中的换行符
            context_before = (note.context_before or "").replace('\n', '').replace('\r', '')
            context_after = (note.context_after or "").replace('\n', '').replace('\r', '')

            row = [
                note.index,
                note.position,
                note.note_type.value,
                note.base_text or "（无）",
                note.variant_text or "（无）",
                context_before,
                context_after,
                note.base_version,
                note.variant_version
            ]
            if has_annotation:
                row.append(note.annotation or "")
            writer.writerow(row)

        return output.getvalue()


# 创建全局服务实例
collation_note_service = CollationNoteService()
