#!/bin/bash
# 使用 MinerU 处理高丽大藏经异体字典 PDF
# 这是一次性的离线数据提取脚本，开源仓库不再分发原 PDF（版权关系）。
# 如需运行，请准备：
#   1) Activate your backend venv before running
#   2) Set PDF_PATH to your local copy of "高麗大藏經異體字典 (李圭甲)" 或同类异体字典 PDF
#   3) Set OUTPUT_DIR to a writable scratch directory

set -euo pipefail

PDF_PATH="${PDF_PATH:?Please export PDF_PATH=/path/to/your.pdf}"
OUTPUT_DIR="${OUTPUT_DIR:?Please export OUTPUT_DIR=/path/to/output}"

echo "=========================================="
echo "Korean Tripitaka variant-character PDF OCR"
echo "=========================================="
echo "PDF:    $PDF_PATH"
echo "Output: $OUTPUT_DIR"
echo "=========================================="

# 处理 PDF（跳过封面目录，从第 40 页开始；按需调整）
# 分批处理避免显存问题
magic-pdf -p "$PDF_PATH" -o "$OUTPUT_DIR" -m ocr -l chinese_cht -s 40 -e 1877

echo "=========================================="
echo "Done. See: $OUTPUT_DIR"
echo "=========================================="
