"""LaTeX / Markdown 导出 + Newick / NEXUS 导出的单元测试。"""
from __future__ import annotations

from app.services.collation_note_service import (
    CollationNote,
    CollationNoteService,
    NoteType,
)
from app.services.phylogeny_service import PhylogenyAnalysisService


def _sample_notes() -> list[CollationNote]:
    return [
        CollationNote(
            index=1,
            position=2,
            note_type=NoteType.VARIANT,
            base_text="智",
            variant_text="知",
            base_version="高麗",
            variant_version="磧砂",
            context_before="般若",
            context_after="慧",
            annotation="异体",
        ),
        CollationNote(
            index=2,
            position=10,
            note_type=NoteType.TUOWEN,
            base_text="是",
            variant_text="",
            base_version="高麗",
            variant_version="磧砂",
            context_before="如",
            context_after="经",
            annotation=None,
        ),
    ]


class TestLatexExport:
    def test_emits_reledmac_apparatus(self):
        notes = _sample_notes()
        out = CollationNoteService().export_to_latex(
            notes=notes,
            title="般若波罗蜜多心经 校勘",
            base_version="高麗",
            variant_version="磧砂",
            base_text="般若智慧如是经",
        )
        assert "\\beginnumbering" in out
        assert "\\endnumbering" in out
        assert "\\edtext" in out
        assert "\\Afootnote" in out

    def test_escapes_special_characters(self):
        note = CollationNote(
            index=1,
            position=0,
            note_type=NoteType.VARIANT,
            base_text="A&B",
            variant_text="100%",
            base_version="X",
            variant_version="Y_v2",
            context_before="",
            context_after="",
            annotation=None,
        )
        out = CollationNoteService().export_to_latex(
            notes=[note], base_version="X", variant_version="Y_v2"
        )
        assert "A\\&B" in out
        assert "100\\%" in out
        # version sigla used in \textsuperscript should be alphanumeric only
        assert "\\textsuperscript{Y}" in out

    def test_handles_empty_lemma_as_omission(self):
        note = CollationNote(
            index=1,
            position=0,
            note_type=NoteType.YANWEN,
            base_text="",
            variant_text="多",
            base_version="A",
            variant_version="B",
            context_before="",
            context_after="",
            annotation=None,
        )
        out = CollationNoteService().export_to_latex(notes=[note])
        assert "\\textit{(om.)}" in out

    def test_overlapping_notes_are_skipped(self):
        """重叠 span 不应破坏 lemma 对齐 — 第二个 note 直接跳过。"""
        notes = [
            CollationNote(
                index=1, position=2, note_type=NoteType.VARIANT,
                base_text="智慧", variant_text="知慧",
                base_version="A", variant_version="B",
                context_before="", context_after="", annotation=None,
            ),
            CollationNote(
                index=2, position=3, note_type=NoteType.VARIANT,
                base_text="慧", variant_text="惠",
                base_version="A", variant_version="B",
                context_before="", context_after="", annotation=None,
            ),
        ]
        out = CollationNoteService().export_to_latex(
            notes=notes, base_text="般若智慧如", base_version="A", variant_version="B",
        )
        # 第一个 lemma 出现，第二个被跳过（"惠" 不应作为 reading 出现）
        assert "\\edtext{智慧}" in out
        assert "惠" not in out

    def test_inline_apparatus_keeps_base_text_intact(self):
        """带 base_text 时未覆盖的字符必须按原样保留，且总长度不变（除转义）。"""
        notes = [_sample_notes()[0]]
        base = "般若智慧如是经"
        out = CollationNoteService().export_to_latex(
            notes=notes,
            base_text=base,
            base_version="A",
            variant_version="B",
        )
        # 原文里未被 lemma 覆盖的字符（般若 + 慧如是经）必须出现
        for ch in "般若慧如是经":
            assert ch in out


class TestMarkdownExport:
    def test_includes_table_header_and_rows(self):
        out = CollationNoteService().export_to_markdown(
            notes=_sample_notes(),
            title="测试",
            base_version="高麗",
            variant_version="磧砂",
        )
        assert out.startswith("# 测试")
        assert "| # |" in out
        assert "高麗" in out
        assert "磧砂" in out
        # 两条 note → 表格里至少出现底本字
        assert "智" in out
        assert "是" in out

    def test_escapes_pipes_in_cells(self):
        note = CollationNote(
            index=1,
            position=0,
            note_type=NoteType.VARIANT,
            base_text="a|b",
            variant_text="c",
            base_version="X",
            variant_version="Y",
            context_before="",
            context_after="",
            annotation=None,
        )
        out = CollationNoteService().export_to_markdown(notes=[note])
        assert "a\\|b" in out

    def test_empty_notes_renders_placeholder(self):
        out = CollationNoteService().export_to_markdown(notes=[], title="x")
        assert "（无校勘记）" in out


class TestNewickExport:
    def test_simple_tree(self):
        tree = {
            "name": "底本",
            "children": [
                {"name": "A", "similarity": 0.9, "children": []},
                {"name": "B", "similarity": 0.7, "children": []},
            ],
        }
        out = PhylogenyAnalysisService.to_newick(tree)
        assert out.endswith(";")
        assert "A:0.100000" in out
        assert "B:0.300000" in out
        assert out.startswith("(")
        assert ")底本;" in out

    def test_quotes_labels_with_special_chars(self):
        tree = {
            "name": "Root",
            "children": [
                {"name": "A B", "similarity": 0.5, "children": []},
                {"name": "X(1)", "similarity": 0.4, "children": []},
            ],
        }
        out = PhylogenyAnalysisService.to_newick(tree)
        assert "'A B'" in out
        assert "'X(1)'" in out

    def test_nested_internal_groups(self):
        tree = {
            "name": "底",
            "children": [
                {
                    "name": "组1",
                    "is_group": True,
                    "children": [
                        {"name": "A", "similarity": 0.9, "children": []},
                        {"name": "B", "similarity": 0.85, "children": []},
                    ],
                },
                {"name": "C", "similarity": 0.5, "children": []},
            ],
        }
        out = PhylogenyAnalysisService.to_newick(tree)
        assert "(A:0.100000,B:0.150000)组1" in out


class TestNexusExport:
    def test_contains_required_blocks(self):
        tree = {
            "name": "底",
            "children": [
                {"name": "A", "similarity": 0.9, "children": []},
                {"name": "B", "similarity": 0.8, "children": []},
            ],
        }
        sim = {
            "names": ["底", "A", "B"],
            "matrix": [[1.0, 0.9, 0.8], [0.9, 1.0, 0.7], [0.8, 0.7, 1.0]],
        }
        out = PhylogenyAnalysisService.to_nexus(tree, similarity_matrix=sim)
        assert out.startswith("#NEXUS")
        assert "BEGIN TAXA;" in out
        assert "BEGIN TREES;" in out
        assert "BEGIN DISTANCES;" in out
        assert "NTAX=3" in out
        # tree line present
        assert "TREE phylogeny =" in out

    def test_distances_block_optional(self):
        tree = {
            "name": "X",
            "children": [{"name": "Y", "similarity": 0.5, "children": []}],
        }
        out = PhylogenyAnalysisService.to_nexus(tree)
        assert "BEGIN DISTANCES;" not in out
