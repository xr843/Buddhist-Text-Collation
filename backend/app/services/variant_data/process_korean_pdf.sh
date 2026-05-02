#!/bin/bash
# 使用MinerU处理高丽大藏经异体字典PDF

# 激活虚拟环境
source "/home/lqsxi/projects/AI-Powered Platform for Buddhist Text Punctuation and Collation Research/backend/venv/bin/activate"

PDF_PATH="/home/lqsxi/projects/AI-Powered Platform for Buddhist Text Punctuation and Collation Research/高麗大藏經異體字典 (李圭甲).pdf"
OUTPUT_DIR="/mnt/e/mineru_output"

echo "=========================================="
echo "高丽大藏经异体字典 OCR处理"
echo "=========================================="
echo "PDF: $PDF_PATH"
echo "输出: $OUTPUT_DIR"
echo "GPU: NVIDIA RTX 4060"
echo "=========================================="

# 处理PDF (跳过封面目录，从第40页开始)
# 分批处理避免内存问题
magic-pdf -p "$PDF_PATH" -o "$OUTPUT_DIR" -m ocr -l chinese_cht -s 40 -e 1877

echo "=========================================="
echo "处理完成!"
echo "输出目录: $OUTPUT_DIR"
echo "=========================================="
