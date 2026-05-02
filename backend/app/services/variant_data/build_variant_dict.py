"""
从 OpenCC 数据构建异体字词典

数据来源：
- TSCharacters.txt: 繁体→简体 (4113组)
- STCharacters.txt: 简体→繁体 (3980组)
- TWVariants.txt: 台湾异体字 (39组)
- HKVariants.txt: 香港异体字 (63组)
- JPVariants.txt: 日本新字体 (369组)
"""

import os
from collections import defaultdict
from pathlib import Path


def parse_opencc_file(filepath: str) -> list:
    """
    解析 OpenCC 格式的数据文件

    格式: 源字符<tab>目标字符1 目标字符2 ...
    返回: [(源字符, 目标字符1), (源字符, 目标字符2), ...]
    """
    pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) >= 2:
                source = parts[0].strip()
                targets = parts[1].strip().split()
                for target in targets:
                    target = target.strip()
                    if target and source != target:
                        pairs.append((source, target))

    return pairs


def build_variant_groups(all_pairs: list) -> list:
    """
    从字符对构建异体字组

    使用并查集(Union-Find)算法将相关的字符合并到同一组
    """
    # 并查集
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # 合并所有对
    for a, b in all_pairs:
        union(a, b)

    # 按根节点分组
    groups = defaultdict(set)
    for char in parent:
        root = find(char)
        groups[root].add(char)

    # 转换为列表，按组大小排序
    result = []
    for chars in groups.values():
        if len(chars) >= 2:  # 只保留有多个字符的组
            result.append(tuple(sorted(chars)))

    return sorted(result, key=lambda x: -len(x))


def generate_python_code(groups: list) -> str:
    """生成 Python 代码"""
    lines = []
    lines.append('"""')
    lines.append('异体字组数据 - 自动生成')
    lines.append('')
    lines.append('数据来源:')
    lines.append('- OpenCC (BYVoid/OpenCC)')
    lines.append('  - TSCharacters.txt: 繁体→简体')
    lines.append('  - STCharacters.txt: 简体→繁体')
    lines.append('  - TWVariants.txt: 台湾异体字')
    lines.append('  - HKVariants.txt: 香港异体字')
    lines.append('  - JPVariants.txt: 日本新字体')
    lines.append('')
    lines.append(f'总计: {len(groups)} 组异体字')
    lines.append('"""')
    lines.append('')
    lines.append('VARIANT_GROUPS = [')

    for group in groups:
        # 格式化为 Python 元组
        chars = ', '.join(f'"{c}"' for c in group)
        lines.append(f'    ({chars}),')

    lines.append(']')

    return '\n'.join(lines)


def main():
    # 数据文件路径
    data_dir = Path(__file__).parent

    files = [
        'TSCharacters.txt',
        'STCharacters.txt',
        'TWVariants.txt',
        'HKVariants.txt',
        'JPVariants.txt',
    ]

    # 解析所有文件
    all_pairs = []
    for filename in files:
        filepath = data_dir / filename
        if filepath.exists():
            pairs = parse_opencc_file(str(filepath))
            print(f"解析 {filename}: {len(pairs)} 对")
            all_pairs.extend(pairs)
        else:
            print(f"文件不存在: {filename}")

    print(f"\n总计: {len(all_pairs)} 对映射")

    # 构建异体字组
    groups = build_variant_groups(all_pairs)
    print(f"构建异体字组: {len(groups)} 组")

    # 统计
    total_chars = sum(len(g) for g in groups)
    print(f"涵盖字符: {total_chars} 个")

    # 显示最大的几组
    print("\n最大的异体字组 (前10):")
    for i, group in enumerate(groups[:10]):
        print(f"  {i+1}. {group}")

    # 生成 Python 代码
    code = generate_python_code(groups)

    output_file = data_dir / 'variant_groups_generated.py'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"\n已生成: {output_file}")

    return groups


if __name__ == '__main__':
    main()
