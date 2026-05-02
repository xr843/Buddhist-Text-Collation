"""
高丽大藏经异体字典 文本提取脚本

直接从PDF提取内嵌文字（无需OCR），解析异体字关系
"""

import fitz  # PyMuPDF
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set

# 路径配置（请通过环境变量覆盖；本仓库不再分发原始 PDF）
import os
PDF_PATH = os.environ.get("PDF_PATH", "/path/to/your_variants_dictionary.pdf")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./korean_tripitaka_output")


class KoreanTripitakaTextExtractor:
    """高丽大藏经异体字典文本提取器"""

    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.entries: List[Dict] = []
        self.variant_pairs: List[Tuple[str, str]] = []

    def extract_text(self, start_page: int = 0, end_page: int = None) -> str:
        """提取PDF文本"""
        doc = fitz.open(self.pdf_path)
        if end_page is None:
            end_page = len(doc)

        all_text = []
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            text = page.get_text()
            all_text.append(text)

        doc.close()
        return "\n".join(all_text)

    def parse_entries(self, text: str) -> List[Dict]:
        """解析文本，提取正字和异体字"""
        entries = []

        # 匹配条目模式: [字+数字] 如 [亦48]
        entry_pattern = re.compile(r'\[([一-龥㐀-䶵\u4e00-\u9fff])(\d+)\]')

        # 按条目分割
        parts = entry_pattern.split(text)

        # parts格式: [前文, 字1, 数字1, 内容1, 字2, 数字2, 内容2, ...]
        i = 1
        while i < len(parts) - 2:
            standard_char = parts[i]
            entry_num = parts[i + 1]
            content = parts[i + 2] if i + 2 < len(parts) else ""

            # 提取异体字: 单字+反引号 格式
            variant_pattern = re.compile(r'^([一-龥㐀-䶵\u4e00-\u9fff])`', re.MULTILINE)
            variants = set(variant_pattern.findall(content))

            # 排除正字本身
            variants.discard(standard_char)

            if variants:
                entry = {
                    'standard': standard_char,
                    'entry_num': int(entry_num),
                    'variants': list(variants),
                    'content_preview': content[:200].replace('\n', ' ')
                }
                entries.append(entry)

                for var in variants:
                    self.variant_pairs.append((standard_char, var))

            i += 3

        return entries

    def process(self, start_page: int = 40, end_page: int = None):
        """处理PDF"""
        print(f"打开PDF: {self.pdf_path}")
        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)
        doc.close()

        if end_page is None:
            end_page = total_pages

        print(f"PDF总页数: {total_pages}")
        print(f"处理范围: 第 {start_page + 1} - {end_page} 页")

        # 提取文本
        print("提取文本...")
        text = self.extract_text(start_page, end_page)
        print(f"提取到 {len(text)} 字符")

        # 解析条目
        print("解析异体字条目...")
        self.entries = self.parse_entries(text)
        print(f"解析到 {len(self.entries)} 个条目")
        print(f"提取到 {len(self.variant_pairs)} 个异体字对")

    def save_results(self):
        """保存结果"""
        # 保存条目JSON
        entries_path = self.output_dir / "entries_text.json"
        with open(entries_path, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

        # 保存异体字对
        pairs_path = self.output_dir / "variant_pairs_text.txt"
        with open(pairs_path, 'w', encoding='utf-8') as f:
            for std, var in self.variant_pairs:
                f.write(f"{std}\t{var}\n")

        # 保存统计
        stats = {
            'total_entries': len(self.entries),
            'total_pairs': len(self.variant_pairs),
            'unique_standards': len(set(e['standard'] for e in self.entries)),
            'unique_variants': len(set(var for _, var in self.variant_pairs))
        }
        stats_path = self.output_dir / "stats_text.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"\n保存结果到: {self.output_dir}")
        print(f"  - 条目文件: {entries_path.name}")
        print(f"  - 异体字对: {pairs_path.name}")
        print(f"  - 统计信息: {stats_path.name}")
        print(f"\n统计:")
        print(f"  - 总条目数: {stats['total_entries']}")
        print(f"  - 总异体字对: {stats['total_pairs']}")
        print(f"  - 唯一正字: {stats['unique_standards']}")
        print(f"  - 唯一异体字: {stats['unique_variants']}")

    def show_samples(self, n: int = 10):
        """显示样本"""
        print(f"\n样本条目 (前{n}个):")
        for entry in self.entries[:n]:
            print(f"  [{entry['standard']}{entry['entry_num']}] 异体字: {entry['variants']}")


def quick_test(pages: int = 100):
    """快速测试"""
    extractor = KoreanTripitakaTextExtractor(PDF_PATH, OUTPUT_DIR)
    extractor.process(start_page=40, end_page=40 + pages)
    extractor.save_results()
    extractor.show_samples()


def full_extraction():
    """完整提取"""
    extractor = KoreanTripitakaTextExtractor(PDF_PATH, OUTPUT_DIR)
    extractor.process(start_page=40, end_page=None)  # 跳过前40页（封面目录）
    extractor.save_results()
    extractor.show_samples(20)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'full':
        full_extraction()
    else:
        pages = int(sys.argv[1]) if len(sys.argv) > 1 else 100
        quick_test(pages)
