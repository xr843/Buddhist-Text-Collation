#!/usr/bin/env python3
"""
下载 DILA 瑜伽师地论数据库的完整数据

数据来源: https://ybh.dila.edu.tw
API: /juans/html?work={work}&juan={juan}

包含:
- T1579 瑜伽师地论 (100卷)
- T1828 瑜伽论记 (48卷)
- T1829 瑜伽师地论略纂 (16卷)
"""

import os
import time
import requests
from pathlib import Path

# 配置
BASE_URL = "https://ybh.dila.edu.tw/juans/html"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "dila" / "html"

# 需要下载的经典及其卷数
WORKS = {
    "T1579": 100,  # 瑜伽师地论 100卷
    "T1828": 48,   # 瑜伽论记 48卷
    "T1829": 16,   # 瑜伽师地论略纂 16卷
}

def download_juan(work: str, juan: int, output_dir: Path) -> bool:
    """下载单卷数据"""
    # 构建URL - juan参数需要3位数字
    url = f"{BASE_URL}?work={work}&juan={juan:03d}"
    output_file = output_dir / f"{work}_juan{juan}.html"

    # 如果文件已存在且不为空，跳过
    if output_file.exists() and output_file.stat().st_size > 1000:
        print(f"  跳过 {work} 卷{juan} (已存在)")
        return True

    try:
        print(f"  下载 {work} 卷{juan}...", end=" ", flush=True)
        response = requests.get(url, timeout=60)

        if response.status_code == 200 and len(response.text) > 100:
            # 检查是否是有效的HTML内容
            if '<div class="juan_text"' in response.text or '<body id=' in response.text:
                output_file.write_text(response.text, encoding="utf-8")
                print(f"成功 ({len(response.text)} 字节)")
                return True
            else:
                print(f"失败 (无效内容)")
                return False
        else:
            print(f"失败 (状态码: {response.status_code})")
            return False

    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("DILA 瑜伽师地论数据库完整下载工具")
    print("=" * 60)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {OUTPUT_DIR}")
    print()

    total_success = 0
    total_failed = 0

    for work, total_juans in WORKS.items():
        print(f"\n下载 {work} ({total_juans}卷):")
        print("-" * 40)

        for juan in range(1, total_juans + 1):
            if download_juan(work, juan, OUTPUT_DIR):
                total_success += 1
            else:
                total_failed += 1

            # 添加延迟避免请求过快
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"下载完成!")
    print(f"成功: {total_success} 卷")
    print(f"失败: {total_failed} 卷")
    print("=" * 60)


if __name__ == "__main__":
    main()
