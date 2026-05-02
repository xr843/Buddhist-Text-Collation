"""
高丽大藏经异体字典 OCR提取脚本

从扫描版PDF中提取正字和异体字对应关系
"""

import fitz  # PyMuPDF
import easyocr
import re
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Set
import warnings
warnings.filterwarnings('ignore')

# PDF 路径（请通过环境变量覆盖；本仓库不再分发原始 PDF）
import os
PDF_PATH = os.environ.get("PDF_PATH", "/path/to/your_variants_dictionary.pdf")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./korean_tripitaka_output")


class KoreanTripitakaExtractor:
    """高丽大藏经异体字典提取器"""

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化OCR (启用GPU加速)
        print("初始化EasyOCR (繁体中文+英文, GPU加速)...")
        self.reader = easyocr.Reader(['ch_tra', 'en'], gpu=True, verbose=False)

        # 存储提取的数据
        self.variant_pairs: List[Tuple[str, str]] = []  # (正字, 异体字)
        self.entries: List[Dict] = []  # 完整条目

    def extract_page_image(self, doc: fitz.Document, page_num: int, dpi: int = 200) -> str:
        """提取PDF页面为图像"""
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img_path = self.output_dir / f"page_{page_num:04d}.png"
        pix.save(str(img_path))
        return str(img_path)

    def ocr_image(self, img_path: str) -> List[Tuple[str, float]]:
        """OCR识别图像"""
        result = self.reader.readtext(img_path, detail=1)
        # 返回 (文本, 置信度) 列表
        return [(item[1], item[2]) for item in result]

    def parse_ocr_result(self, ocr_results: List[Tuple[str, float]]) -> List[Dict]:
        """解析OCR结果，提取正字和异体字"""
        entries = []
        current_entry = None

        # 常用虚词和非异体字词列表（这些通常出现在释义中，不是异体字）
        common_words = set('之也的是為于於在有不以與及或者所則而已乎矣焉哉'
                          '上下左右中內外前後東西南北大小多少高低長短'
                          '一二三四五六七八九十百千萬億'
                          '曰云言謂稱作正又亦音反切同從聲義'
                          '今古新舊本原首尾始終')

        # 合并所有文本用于模式匹配
        all_text = ' '.join([text for text, _ in ocr_results])

        for text, conf in ocr_results:
            text = text.strip()
            if not text:
                continue

            # 匹配正字条目：[字] 或 【字】格式
            standard_match = re.match(r'[\[【](.{1,2})[\]】]', text)
            if standard_match:
                char = standard_match.group(1)
                if len(char) == 1 and '\u4e00' <= char <= '\u9fff':
                    # 保存前一个条目
                    if current_entry and current_entry.get('variants'):
                        entries.append(current_entry)
                    # 开始新条目
                    current_entry = {
                        'standard': char,
                        'variants': set(),
                        'related_forms': [],  # 通过模式匹配找到的相关字形
                        'raw_text': [text]
                    }
                    continue

            # 如果有当前条目，分析文本提取异体字
            if current_entry:
                current_entry['raw_text'].append(text)

                # 模式1: "正作X" - X是正字的另一种写法
                for match in re.finditer(r'正作([^\s,，、。]+)', text):
                    chars = match.group(1)
                    for c in chars:
                        if self._is_cjk_char(c) and c != current_entry['standard']:
                            current_entry['related_forms'].append(('正作', c))

                # 模式2: "又作X"、"亦作X" - X是异体字
                for match in re.finditer(r'[又亦]作([^\s,，、。]+)', text):
                    chars = match.group(1)
                    for c in chars:
                        if self._is_cjk_char(c) and c != current_entry['standard']:
                            current_entry['variants'].add(c)
                            current_entry['related_forms'].append(('又作', c))

                # 模式3: "同X" - 与X同
                for match in re.finditer(r'同([^\s,，、。上下]+)', text):
                    chars = match.group(1)
                    for c in chars:
                        if self._is_cjk_char(c) and c != current_entry['standard'] and c not in common_words:
                            current_entry['variants'].add(c)
                            current_entry['related_forms'].append(('同', c))

                # 模式4: 识别可能的异体字形（出现在正字旁边的单字，置信度较高）
                # 只接受高置信度（>0.8）的单字
                if conf > 0.8 and len(text) == 1:
                    c = text
                    if self._is_cjk_char(c) and c != current_entry['standard'] and c not in common_words:
                        current_entry['variants'].add(c)

        # 保存最后一个条目
        if current_entry and current_entry.get('variants'):
            current_entry['variants'] = list(current_entry['variants'])
            entries.append(current_entry)

        # 转换set为list
        for entry in entries:
            if isinstance(entry.get('variants'), set):
                entry['variants'] = list(entry['variants'])

        return entries

    def _is_cjk_char(self, char: str) -> bool:
        """判断是否为CJK字符"""
        if len(char) != 1:
            return False
        code = ord(char)
        # CJK基本区、扩展A/B/C/D/E/F区
        return (0x4E00 <= code <= 0x9FFF or   # 基本区
                0x3400 <= code <= 0x4DBF or   # 扩展A
                0x20000 <= code <= 0x2A6DF or # 扩展B
                0x2A700 <= code <= 0x2B73F or # 扩展C
                0x2B740 <= code <= 0x2B81F or # 扩展D
                0x2B820 <= code <= 0x2CEAF or # 扩展E
                0x2CEB0 <= code <= 0x2EBEF or # 扩展F
                0x30000 <= code <= 0x3134F)   # 扩展G

    def process_page_range(self, start_page: int, end_page: int, save_images: bool = False):
        """处理指定范围的页面"""
        print(f"打开PDF: {self.pdf_path}")
        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)
        print(f"PDF总页数: {total_pages}")

        end_page = min(end_page, total_pages)

        for page_num in range(start_page, end_page):
            print(f"\n处理第 {page_num + 1}/{total_pages} 页...")

            # 提取页面图像
            img_path = self.extract_page_image(doc, page_num)

            # OCR识别
            ocr_results = self.ocr_image(img_path)
            print(f"  OCR识别到 {len(ocr_results)} 个文本块")

            # 解析结果
            entries = self.parse_ocr_result(ocr_results)
            print(f"  提取到 {len(entries)} 个条目")

            for entry in entries:
                self.entries.append(entry)
                for variant in entry['variants']:
                    self.variant_pairs.append((entry['standard'], variant))

            # 清理临时图像
            if not save_images:
                os.remove(img_path)

        doc.close()

    def save_results(self):
        """保存提取结果"""
        # 保存完整条目
        entries_path = self.output_dir / "entries.json"
        with open(entries_path, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)
        print(f"保存条目到: {entries_path}")

        # 保存正字-异体字对
        pairs_path = self.output_dir / "variant_pairs.txt"
        with open(pairs_path, 'w', encoding='utf-8') as f:
            for std, var in self.variant_pairs:
                f.write(f"{std}\t{var}\n")
        print(f"保存异体字对到: {pairs_path}")

        # 统计
        print(f"\n统计:")
        print(f"  - 总条目数: {len(self.entries)}")
        print(f"  - 总异体字对: {len(self.variant_pairs)}")
        unique_standards = set(e['standard'] for e in self.entries)
        print(f"  - 唯一正字数: {len(unique_standards)}")


def test_extraction():
    """测试提取几页"""
    extractor = KoreanTripitakaExtractor(PDF_PATH, OUTPUT_DIR)

    # 测试处理第50-55页（正文部分）
    extractor.process_page_range(50, 55, save_images=True)
    extractor.save_results()

    # 显示样本结果
    print("\n样本条目:")
    for entry in extractor.entries[:10]:
        print(f"  正字: {entry['standard']}, 异体字: {entry['variants'][:5]}")


def batch_extraction(start_page: int = 40, end_page: int = 1877, batch_size: int = 50):
    """批量提取整本PDF

    Args:
        start_page: 起始页（跳过封面、目录等）
        end_page: 结束页
        batch_size: 每批处理页数
    """
    extractor = KoreanTripitakaExtractor(PDF_PATH, OUTPUT_DIR)

    # 分批处理以避免内存问题
    for batch_start in range(start_page, end_page, batch_size):
        batch_end = min(batch_start + batch_size, end_page)
        print(f"\n{'='*50}")
        print(f"处理批次: 第 {batch_start}-{batch_end} 页")
        print(f"{'='*50}")

        try:
            extractor.process_page_range(batch_start, batch_end, save_images=False)

            # 每批保存一次结果
            extractor.save_results()

            print(f"当前累计: {len(extractor.entries)} 条目, {len(extractor.variant_pairs)} 异体字对")
        except Exception as e:
            print(f"批次处理出错: {e}")
            continue

    # 最终保存
    extractor.save_results()

    print(f"\n{'='*50}")
    print("提取完成!")
    print(f"总条目数: {len(extractor.entries)}")
    print(f"总异体字对: {len(extractor.variant_pairs)}")
    print(f"{'='*50}")


def quick_test(pages: int = 100):
    """快速测试前N页"""
    extractor = KoreanTripitakaExtractor(PDF_PATH, OUTPUT_DIR)
    extractor.process_page_range(40, 40 + pages, save_images=False)
    extractor.save_results()

    print(f"\n快速测试结果 ({pages}页):")
    print(f"  条目数: {len(extractor.entries)}")
    print(f"  异体字对: {len(extractor.variant_pairs)}")

    # 显示一些有效的异体字关系
    print("\n有效条目样本:")
    for entry in extractor.entries[:20]:
        if entry.get('related_forms'):
            print(f"  [{entry['standard']}] 关联: {entry['related_forms']}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'batch':
            batch_extraction()
        elif sys.argv[1] == 'quick':
            pages = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            quick_test(pages)
        else:
            test_extraction()
    else:
        test_extraction()
