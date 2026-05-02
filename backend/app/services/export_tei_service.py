"""
TEI XML格式导出服务
符合TEI P5国际标准
"""
from lxml import etree
from datetime import datetime
from typing import Dict, List, Any
from io import BytesIO


class TEIExportService:
    """TEI XML导出服务"""

    # TEI P5 命名空间
    TEI_NS = "http://www.tei-c.org/ns/1.0"
    NSMAP = {None: TEI_NS}

    @staticmethod
    def export_collation_tei(collation_data: Dict[str, Any]) -> str:
        """
        导出校勘数据为TEI XML格式

        Args:
            collation_data: 校勘数据
                {
                    'base_name': str,
                    'base_text': str,
                    'collations': List[{'name': str, 'text': str}],
                    'differences': List[{...}]
                }

        Returns:
            str: TEI XML字符串
        """
        TEI = f"{{{TEIExportService.TEI_NS}}}"

        # 根元素
        root = etree.Element(f"{TEI}TEI", nsmap=TEIExportService.NSMAP)

        # teiHeader
        tei_header = TEIExportService._create_tei_header(collation_data)
        root.append(tei_header)

        # text
        text_elem = etree.SubElement(root, f"{TEI}text")
        body = etree.SubElement(text_elem, f"{TEI}body")

        # 添加校勘条目
        differences = collation_data.get('differences', [])
        base_text = collation_data.get('base_text', '')
        base_name = collation_data.get('base_name', 'base')

        TEIExportService._add_collation_entries(
            body,
            differences,
            base_text,
            base_name,
            collation_data.get('collations', [])
        )

        # 输出XML字符串
        xml_str = etree.tostring(
            root,
            encoding='unicode',
            pretty_print=True,
            xml_declaration=True
        )

        return xml_str

    @staticmethod
    def _create_tei_header(data: Dict) -> etree.Element:
        """创建TEI Header"""
        TEI = f"{{{TEIExportService.TEI_NS}}}"

        tei_header = etree.Element(f"{TEI}teiHeader")

        # fileDesc
        file_desc = etree.SubElement(tei_header, f"{TEI}fileDesc")

        # titleStmt
        title_stmt = etree.SubElement(file_desc, f"{TEI}titleStmt")
        title = etree.SubElement(title_stmt, f"{TEI}title")
        base_name = data.get('base_name', '未命名')
        title.text = f"《{base_name}》校勘记"

        # 责任说明（可选）
        resp_stmt = etree.SubElement(title_stmt, f"{TEI}respStmt")
        resp = etree.SubElement(resp_stmt, f"{TEI}resp")
        resp.text = "校勘者"
        name = etree.SubElement(resp_stmt, f"{TEI}name")
        name.text = "佛典标点与校勘研究平台用户"

        # publicationStmt
        pub_stmt = etree.SubElement(file_desc, f"{TEI}publicationStmt")
        publisher = etree.SubElement(pub_stmt, f"{TEI}publisher")
        publisher.text = "佛典标点与校勘研究平台"
        date = etree.SubElement(pub_stmt, f"{TEI}date")
        date.set("when", datetime.now().strftime("%Y-%m-%d"))
        date.text = datetime.now().strftime("%Y年%m月%d日")

        # sourceDesc
        source_desc = etree.SubElement(file_desc, f"{TEI}sourceDesc")

        # 底本
        bibl = etree.SubElement(source_desc, f"{TEI}bibl")
        bibl.set("xml:id", "base")
        bibl.text = data.get('base_name', '未命名底本')

        # 校本列表
        list_bibl = etree.SubElement(source_desc, f"{TEI}listBibl")
        for idx, collation in enumerate(data.get('collations', []), 1):
            bibl_coll = etree.SubElement(list_bibl, f"{TEI}bibl")
            bibl_coll.set("xml:id", f"wit{idx}")
            bibl_coll.text = collation.get('name', f'校本{idx}')

        # encodingDesc（编码说明）
        encoding_desc = etree.SubElement(tei_header, f"{TEI}encodingDesc")
        var_encoding = etree.SubElement(encoding_desc, f"{TEI}variantEncoding")
        var_encoding.set("method", "parallel-segmentation")
        var_encoding.set("location", "internal")

        return tei_header

    @staticmethod
    def _add_collation_entries(
        body: etree.Element,
        differences: List[Dict],
        base_text: str,
        base_name: str,
        collations: List[Dict]
    ):
        """添加校勘条目"""
        TEI = f"{{{TEIExportService.TEI_NS}}}"

        # 按位置排序
        sorted_diffs = sorted(differences, key=lambda x: x.get('position', 0))

        current_pos = 0

        for diff in sorted_diffs:
            position = diff.get('position', 0)

            # 添加中间的正常文本
            if position > current_pos:
                normal_text = base_text[current_pos:position]
                if normal_text.strip():
                    p = etree.SubElement(body, f"{TEI}p")
                    p.text = normal_text

            # 添加 <app> 校勘条目
            app = etree.SubElement(body, f"{TEI}app")

            # <lem> 底本读法
            lem = etree.SubElement(app, f"{TEI}lem")
            lem.set("wit", f"#{base_name}")
            lem.text = diff.get('base_char', '')

            # <rdg> 各校本读法
            variants = diff.get('variants', [])
            for variant in variants:
                rdg = etree.SubElement(app, f"{TEI}rdg")
                rdg.set("wit", f"#{variant.get('name', 'unknown')}")
                rdg.text = variant.get('char', '')

                # 添加类型属性
                category = variant.get('category', '')
                if category:
                    category_map = {
                        'error': 'orthographic-error',
                        'variant': 'orthographic-variant',
                        'yanwen': 'addition',
                        'tuowen': 'omission',
                        'daowen': 'transposition'
                    }
                    rdg_type = category_map.get(category, category)
                    rdg.set("type", rdg_type)

            # <note> 注释
            note_text = diff.get('note', '')
            context = diff.get('context', '')
            if note_text or context:
                note = etree.SubElement(app, f"{TEI}note")
                if context:
                    note.text = f"上下文：{context}。"
                if note_text:
                    note.text = (note.text or '') + note_text

            # 更新位置
            base_char_len = len(diff.get('base_char', ''))
            current_pos = position + base_char_len

        # 添加剩余文本
        if current_pos < len(base_text):
            remaining_text = base_text[current_pos:]
            if remaining_text.strip():
                p = etree.SubElement(body, f"{TEI}p")
                p.text = remaining_text

    @staticmethod
    def export_simple_text_tei(
        title: str,
        author: str,
        text_content: str,
        witnesses: List[str] = None
    ) -> str:
        """
        导出简单文本为TEI格式（不含校勘）

        Args:
            title: 文献标题
            author: 作者
            text_content: 文本内容
            witnesses: 见证本列表

        Returns:
            str: TEI XML字符串
        """
        TEI = f"{{{TEIExportService.TEI_NS}}}"

        root = etree.Element(f"{TEI}TEI", nsmap=TEIExportService.NSMAP)

        # teiHeader（简化版）
        tei_header = etree.SubElement(root, f"{TEI}teiHeader")
        file_desc = etree.SubElement(tei_header, f"{TEI}fileDesc")

        title_stmt = etree.SubElement(file_desc, f"{TEI}titleStmt")
        title_elem = etree.SubElement(title_stmt, f"{TEI}title")
        title_elem.text = title

        if author:
            author_elem = etree.SubElement(title_stmt, f"{TEI}author")
            author_elem.text = author

        pub_stmt = etree.SubElement(file_desc, f"{TEI}publicationStmt")
        p = etree.SubElement(pub_stmt, f"{TEI}p")
        p.text = f"Generated by Buddhist Text Platform on {datetime.now().strftime('%Y-%m-%d')}"

        source_desc = etree.SubElement(file_desc, f"{TEI}sourceDesc")
        p2 = etree.SubElement(source_desc, f"{TEI}p")
        p2.text = "Digital transcription"

        # text
        text_elem = etree.SubElement(root, f"{TEI}text")
        body = etree.SubElement(text_elem, f"{TEI}body")

        # 分段处理文本
        paragraphs = text_content.split('\n\n')
        for para_text in paragraphs:
            if para_text.strip():
                para = etree.SubElement(body, f"{TEI}p")
                para.text = para_text.strip()

        xml_str = etree.tostring(
            root,
            encoding='unicode',
            pretty_print=True,
            xml_declaration=True
        )

        return xml_str

    @staticmethod
    def validate_tei_xml(xml_string: str) -> tuple[bool, str]:
        """
        验证TEI XML是否格式正确

        Returns:
            (is_valid, error_message)
        """
        try:
            etree.fromstring(xml_string.encode('utf-8'))
            return True, ""
        except etree.XMLSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# 使用示例
if __name__ == "__main__":
    # 示例数据
    sample_data = {
        'base_name': '《金刚经》大正藏版',
        'base_text': '如是我闻。一时佛在舍卫国。',
        'collations': [
            {'name': '高丽藏', 'text': '如是吾闻。一时佛在舍卫国。'},
            {'name': '思溪藏', 'text': '如是我闻。一时佛在舍卫国。'}
        ],
        'differences': [
            {
                'position': 2,
                'context': '如是我闻',
                'base_char': '我',
                'variants': [
                    {'name': '高丽藏', 'char': '吾', 'category': 'error'}
                ],
                'note': '高丽藏作"吾"，疑为讹误'
            }
        ]
    }

    tei_xml = TEIExportService.export_collation_tei(sample_data)
    print(tei_xml)

    # 验证
    is_valid, error = TEIExportService.validate_tei_xml(tei_xml)
    print(f"\n验证结果：{'通过' if is_valid else '失败'}")
    if error:
        print(f"错误信息：{error}")
