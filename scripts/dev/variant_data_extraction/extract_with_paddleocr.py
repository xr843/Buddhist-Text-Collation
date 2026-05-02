"""
高丽大藏经异体字典 OCR提取脚本 - 使用PaddleOCR-Pytorch

直接加载本地下载的MinerU OCR模型，避免magic-pdf的bug
"""

import fitz  # PyMuPDF
import torch
import numpy as np
import re
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from PIL import Image
import io
import warnings
warnings.filterwarnings('ignore')

# 路径配置
PDF_PATH = "/home/lqsxi/projects/AI-Powered Platform for Buddhist Text Punctuation and Collation Research/高麗大藏經異體字典 (李圭甲).pdf"
OUTPUT_DIR = "/home/lqsxi/projects/AI-Powered Platform for Buddhist Text Punctuation and Collation Research/backend/app/services/variant_data/korean_tripitaka"
MODEL_DIR = "/mnt/e/mineru_models/models/OCR/paddleocr_torch"


class PaddleOCRExtractor:
    """使用PaddleOCR-Pytorch提取异体字"""

    def __init__(self, pdf_path: str, output_dir: str, model_dir: str, use_gpu: bool = True):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir = Path(model_dir)

        # 检查GPU
        self.device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'
        print(f"使用设备: {self.device}")

        # 初始化OCR
        self._init_ocr()

        # 存储结果
        self.variant_pairs: List[Tuple[str, str]] = []
        self.entries: List[Dict] = []

    def _init_ocr(self):
        """初始化PaddleOCR模型"""
        from paddleocr import PaddleOCR

        # PaddleOCR使用GPU（如果可用）
        use_gpu = self.device == 'cuda'

        print(f"初始化PaddleOCR (use_gpu={use_gpu}, lang=ch)...")

        # 使用繁体中文模型，高精度模式
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='chinese_cht',  # 繁体中文
            use_gpu=use_gpu,
            show_log=False
        )
        self.use_paddleocr = True
        print("PaddleOCR初始化成功!")

    def extract_page_image(self, doc: fitz.Document, page_num: int, dpi: int = 200) -> np.ndarray:
        """提取PDF页面为numpy数组"""
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)

        # 转换为numpy数组
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return np.array(img)

    def ocr_image(self, img: np.ndarray) -> List[Tuple[str, float]]:
        """OCR识别图像"""
        # PaddleOCR标准接口
        result = self.ocr.ocr(img, cls=True)
        if result and result[0]:
            return [(line[1][0], line[1][1]) for line in result[0]]
        return []

    def parse_ocr_result(self, ocr_results: List[Tuple[str, float]]) -> List[Dict]:
        """解析OCR结果，提取正字和异体字"""
        entries = []
        current_entry = None

        # 常用虚词（排除这些）
        common_words = set('之也的是為于於在有不以與及或者所則而已乎矣焉哉'
                          '上下左右中內外前後東西南北大小多少高低長短'
                          '一二三四五六七八九十百千萬億'
                          '曰云言謂稱作正又亦音反切同從聲義'
                          '今古新舊本原首尾始終')

        for text, conf in ocr_results:
            text = text.strip()
            if not text:
                continue

            # 匹配正字条目：[字] 或 【字】格式
            standard_match = re.match(r'[\\[【](.{1,2})[\\]】]', text)
            if standard_match:
                char = standard_match.group(1)
                if len(char) == 1 and self._is_cjk_char(char):
                    if current_entry and current_entry.get('variants'):
                        entries.append(current_entry)
                    current_entry = {
                        'standard': char,
                        'variants': set(),
                        'related_forms': [],
                        'raw_text': [text]
                    }
                    continue

            if current_entry:
                current_entry['raw_text'].append(text)

                # 模式匹配提取异体字
                # 模式1: "正作X"
                for match in re.finditer(r'正作([^\\s,，、。]+)', text):
                    for c in match.group(1):
                        if self._is_cjk_char(c) and c != current_entry['standard']:
                            current_entry['related_forms'].append(('正作', c))

                # 模式2: "又作X"、"亦作X"
                for match in re.finditer(r'[又亦]作([^\\s,，、。]+)', text):
                    for c in match.group(1):
                        if self._is_cjk_char(c) and c != current_entry['standard']:
                            current_entry['variants'].add(c)
                            current_entry['related_forms'].append(('又作', c))

                # 模式3: "同X"
                for match in re.finditer(r'同([^\\s,，、。上下]+)', text):
                    for c in match.group(1):
                        if self._is_cjk_char(c) and c != current_entry['standard'] and c not in common_words:
                            current_entry['variants'].add(c)
                            current_entry['related_forms'].append(('同', c))

                # 模式4: 高置信度单字
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
        return (0x4E00 <= code <= 0x9FFF or
                0x3400 <= code <= 0x4DBF or
                0x20000 <= code <= 0x2A6DF or
                0x2A700 <= code <= 0x2B73F or
                0x2B740 <= code <= 0x2B81F or
                0x2B820 <= code <= 0x2CEAF or
                0x2CEB0 <= code <= 0x2EBEF or
                0x30000 <= code <= 0x3134F)

    def process_page_range(self, start_page: int, end_page: int, save_progress: bool = True):
        """处理指定范围的页面"""
        print(f"打开PDF: {self.pdf_path}")
        doc = fitz.open(self.pdf_path)
        total_pages = len(doc)
        print(f"PDF总页数: {total_pages}")

        end_page = min(end_page, total_pages)

        for page_num in range(start_page, end_page):
            if (page_num - start_page) % 10 == 0:
                print(f"\n处理第 {page_num + 1}/{total_pages} 页 ({page_num - start_page + 1}/{end_page - start_page})...")

            try:
                # 提取页面图像
                img = self.extract_page_image(doc, page_num)

                # OCR识别
                ocr_results = self.ocr_image(img)

                # 解析结果
                entries = self.parse_ocr_result(ocr_results)

                for entry in entries:
                    self.entries.append(entry)
                    for variant in entry['variants']:
                        self.variant_pairs.append((entry['standard'], variant))

                # 每100页保存一次进度
                if save_progress and (page_num + 1) % 100 == 0:
                    self.save_results(suffix=f"_page{page_num + 1}")
                    print(f"  进度保存: {len(self.entries)} 条目, {len(self.variant_pairs)} 异体字对")

            except Exception as e:
                print(f"  页面 {page_num + 1} 处理错误: {e}")
                continue

        doc.close()

    def save_results(self, suffix: str = ""):
        """保存提取结果"""
        # 保存完整条目
        entries_path = self.output_dir / f"entries{suffix}.json"
        with open(entries_path, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

        # 保存正字-异体字对
        pairs_path = self.output_dir / f"variant_pairs{suffix}.txt"
        with open(pairs_path, 'w', encoding='utf-8') as f:
            for std, var in self.variant_pairs:
                f.write(f"{std}\t{var}\n")

        print(f"\n保存结果到: {self.output_dir}")
        print(f"  - 条目文件: {entries_path.name}")
        print(f"  - 异体字对: {pairs_path.name}")
        print(f"  - 总条目数: {len(self.entries)}")
        print(f"  - 总异体字对: {len(self.variant_pairs)}")


def quick_test(pages: int = 50):
    """快速测试"""
    extractor = PaddleOCRExtractor(PDF_PATH, OUTPUT_DIR, MODEL_DIR)
    # 从第40页开始（跳过封面目录）
    extractor.process_page_range(40, 40 + pages)
    extractor.save_results()

    print(f"\n快速测试结果 ({pages}页):")
    print(f"  条目数: {len(extractor.entries)}")
    print(f"  异体字对: {len(extractor.variant_pairs)}")

    if extractor.entries:
        print("\n样本条目:")
        for entry in extractor.entries[:10]:
            print(f"  [{entry['standard']}] -> {entry['variants'][:5]}")


def batch_extraction(start_page: int = 40, end_page: int = 1877):
    """批量提取整本PDF"""
    extractor = PaddleOCRExtractor(PDF_PATH, OUTPUT_DIR, MODEL_DIR)

    print(f"\n{'='*60}")
    print(f"开始批量提取: 第 {start_page}-{end_page} 页")
    print(f"{'='*60}")

    extractor.process_page_range(start_page, end_page, save_progress=True)
    extractor.save_results()

    print(f"\n{'='*60}")
    print("提取完成!")
    print(f"总条目数: {len(extractor.entries)}")
    print(f"总异体字对: {len(extractor.variant_pairs)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'batch':
            batch_extraction()
        elif sys.argv[1] == 'quick':
            pages = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            quick_test(pages)
        else:
            print("用法: python extract_with_paddleocr.py [quick|batch] [pages]")
    else:
        quick_test(50)
