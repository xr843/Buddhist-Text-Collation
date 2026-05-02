"""
统一异体字词典构建脚本

数据来源:
1. OpenCC (4000+ 组繁简异体字)
   - TSCharacters.txt, STCharacters.txt
   - TWVariants.txt, HKVariants.txt, JPVariants.txt

2. CBETA 外字数据库 (5000+ 对异体字映射)
   - cbeta_gaiji.csv

3. 台湾教育部异体字字典 (5000+ 对异体字映射)
   - moe_variants.txt (来自 kcwu/moedict-variants)

4. 佛典专用异体字 (手动维护)

5. Unicode Unihan 数据库 (国际标准)
   - Unihan_Variants.txt
   - kZVariant: 字形异体
   - kSemanticVariant: 语义异体
   - kTraditionalVariant/kSimplifiedVariant: 繁简变体

6. CHISE/IDS 汉字结构数据 (学术级)
   - IDS.txt (cjkvi/cjkvi-ids)
   - 基于部件结构推导异体关系

使用并查集(Union-Find)算法合并所有数据源
"""

import csv
import os
import re
from collections import defaultdict
from pathlib import Path


# ============================================================
# 并查集算法
# ============================================================

class UnionFind:
    """并查集，用于合并异体字组"""

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        # 按秩合并
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

    def get_groups(self):
        """获取所有组"""
        groups = defaultdict(set)
        for char in self.parent:
            root = self.find(char)
            groups[root].add(char)
        return [tuple(sorted(chars)) for chars in groups.values() if len(chars) >= 2]


# ============================================================
# 数据解析函数
# ============================================================

def parse_opencc_file(filepath: str) -> list:
    """解析 OpenCC 格式的数据文件"""
    pairs = []
    if not os.path.exists(filepath):
        return pairs

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
                    if target and source != target and len(source) == 1 and len(target) == 1:
                        pairs.append((source, target))

    return pairs


def parse_cbeta_gaiji(filepath: str) -> list:
    """
    解析 CBETA 外字数据库

    CBETA 数据有两种记录格式：
    1. 标准格式: uni_char 有值，norm_big5_char 有值
       例: CB00001 6B35 欵 [肄-聿+欠] 款
    2. 变体格式: uni_char 为空，norm_uni_char 有值，norm_big5_char 有值
       例: CB29798     39FE 㧾 [悊-斤+勿] 總

    需要同时处理这两种格式，提取异体字映射关系
    """
    pairs = []
    if not os.path.exists(filepath):
        return pairs

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            uni_char = row.get('uni_char', '').strip()
            norm_uni_char = row.get('norm_uni_char', '').strip()
            norm_big5 = row.get('norm_big5_char', '').strip()

            # 情况1: uni_char → norm_big5_char (标准格式)
            if uni_char and norm_big5 and len(uni_char) == 1 and len(norm_big5) == 1 and uni_char != norm_big5:
                pairs.append((uni_char, norm_big5))

            # 情况2: norm_uni_char → norm_big5_char (变体格式，如 㧾 → 總)
            if norm_uni_char and norm_big5 and len(norm_uni_char) == 1 and len(norm_big5) == 1 and norm_uni_char != norm_big5:
                # 避免重复添加
                if (norm_uni_char, norm_big5) not in pairs:
                    pairs.append((norm_uni_char, norm_big5))

    return pairs


def parse_moe_variants(filepath: str) -> list:
    """解析台湾教育部异体字字典数据"""
    pairs = []
    if not os.path.exists(filepath):
        return pairs

    current_standard = None
    current_standard_char = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue

            code = parts[0]  # 如 A00001
            char_type = parts[1] if len(parts) > 1 else ''  # 正/附/空
            char = parts[3] if len(parts) > 3 else ''

            # 跳过图片路径
            if char.startswith('/'):
                char = ''

            # 正字记录
            if char_type == '正' and char and len(char) == 1:
                current_standard = code.split('-')[0]
                current_standard_char = char

            # 异体字记录（同一正字下的其他记录）
            elif current_standard and char and len(char) == 1 and char != current_standard_char:
                base_code = code.split('-')[0]
                if base_code == current_standard:
                    pairs.append((current_standard_char, char))

    return pairs


def parse_unihan_variants(filepath: str) -> list:
    """
    解析 Unicode Unihan 异体字数据

    处理字段:
    - kZVariant: 字形异体（字源相同但写法略有不同）
    - kSemanticVariant: 语义异体（含义相同但字形不同）
    - kSpecializedSemanticVariant: 特殊语义异体
    - kTraditionalVariant: 繁体变体
    - kSimplifiedVariant: 简体变体

    格式示例:
    U+3400	kSemanticVariant	U+4E18
    U+3405	kSemanticVariant	U+4E94<kMatthews
    """
    pairs = []
    if not os.path.exists(filepath):
        print(f"    警告: Unihan 文件不存在: {filepath}")
        return pairs

    # 需要处理的字段
    variant_fields = {
        'kZVariant',
        'kSemanticVariant',
        'kSpecializedSemanticVariant',
        'kTraditionalVariant',
        'kSimplifiedVariant',
    }

    # Unicode 码点转字符
    def codepoint_to_char(cp_str: str) -> str:
        """将 U+XXXX 格式转换为字符"""
        try:
            # 去除 U+ 前缀和可能的来源标记
            cp_clean = cp_str.split('<')[0].strip()
            if cp_clean.startswith('U+'):
                cp_clean = cp_clean[2:]
            code = int(cp_clean, 16)
            return chr(code)
        except (ValueError, OverflowError):
            return ''

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            source_cp = parts[0]  # U+XXXX
            field = parts[1]      # kZVariant 等
            targets_str = parts[2]  # U+YYYY U+ZZZZ ...

            if field not in variant_fields:
                continue

            source_char = codepoint_to_char(source_cp)
            if not source_char or len(source_char) != 1:
                continue

            # 目标可能有多个，用空格分隔
            targets = targets_str.split()
            for target_cp in targets:
                target_char = codepoint_to_char(target_cp)
                if target_char and len(target_char) == 1 and source_char != target_char:
                    pairs.append((source_char, target_char))

    return pairs


def parse_chise_ids(filepath: str) -> list:
    """
    解析 CHISE IDS 数据，通过相同的部件结构推导异体字关系

    IDS (Ideographic Description Sequence) 使用结构符号描述汉字部件组合:
    ⿰ 左右结构, ⿱ 上下结构, ⿲ 左中右, ⿳ 上中下
    ⿴ 全包围, ⿵ 上三包, ⿶ 下三包, ⿷ 左三包
    ⿸ 左上包, ⿹ 右上包, ⿺ 左下包, ⿻ 重叠

    格式示例:
    U+4E01	丁	⿱一亅
    U+4E09	三	⿱一二

    策略:
    1. 构建 IDS -> 字符列表 的映射
    2. 相同 IDS 结构的字符互为异体字
    """
    pairs = []
    if not os.path.exists(filepath):
        print(f"    警告: CHISE IDS 文件不存在: {filepath}")
        return pairs

    # IDS 结构到字符列表的映射
    ids_to_chars = defaultdict(set)

    # 用于标准化 IDS 的正则（移除地区变体标记如 [GJK]）
    region_pattern = re.compile(r'\[[A-Z]+\]')

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            # 格式: U+XXXX\t字符\tIDS描述
            char = parts[1].strip()

            # 只处理单字符
            if len(char) != 1:
                continue

            # IDS 描述可能有多个（不同地区变体），取第一个主要的
            ids_raw = parts[2].strip()

            # 跳过没有实际 IDS 结构的（即字符本身）
            if ids_raw == char:
                continue

            # 移除地区变体标记
            ids_normalized = region_pattern.sub('', ids_raw).strip()

            # 只取第一个 IDS（多个变体用空格或制表符分隔）
            ids_first = ids_normalized.split()[0] if ids_normalized else ''

            if ids_first and len(ids_first) > 1:
                ids_to_chars[ids_first].add(char)

    # 相同 IDS 结构的字符互为异体字
    for ids, chars in ids_to_chars.items():
        if len(chars) >= 2:
            chars_list = sorted(chars)
            # 两两配对
            for i in range(len(chars_list)):
                for j in range(i + 1, len(chars_list)):
                    pairs.append((chars_list[i], chars_list[j]))

    return pairs


# ============================================================
# 佛典专用异体字（手动维护）
# ============================================================

BUDDHIST_VARIANT_PAIRS = [
    # 佛教术语专用
    ("佛", "仏"), ("佛", "𠑵"), ("佛", "𠑸"),
    ("菩", "菐"),
    ("薩", "萨"),
    ("禪", "禅"),
    ("涅", "湼"),
    ("槃", "盤"), ("槃", "磐"),
    ("般", "𦬇"),
    ("若", "𠰥"),
    ("波", "皤"),
    ("羅", "罗"), ("羅", "囉"),
    ("密", "宻"), ("密", "祕"),
    ("陀", "陁"), ("陀", "佗"), ("陀", "馱"),
    ("彌", "弥"), ("彌", "㣊"),
    ("迦", "伽"),
    ("那", "㦤"),
    ("婆", "嚩"), ("婆", "縛"),
    ("摩", "磨"), ("摩", "麼"),
    ("尼", "泥"),

    # 佛典常见名相
    ("蘊", "薀"), ("蘊", "蕴"), ("蘊", "藴"),
    ("緣", "缘"), ("緣", "縁"),
    ("諦", "谛"),
    ("慧", "恵"), ("慧", "惠"),
    ("施", "𢼸"),
    ("覺", "覚"), ("覺", "觉"),
    ("解", "觧"),
    ("脫", "脱"),

    # 梵音译字异体
    ("嚩", "縛"),
    ("啰", "囉"),
    ("唎", "利"), ("唎", "哩"),
    ("儞", "你"), ("儞", "尼"),
    ("誐", "伽"),
    ("娑", "沙"), ("娑", "裟"),
    ("怛", "呾"), ("怛", "達"),
    ("馱", "陀"), ("馱", "駄"),

    # 经典用字异体
    ("經", "経"), ("經", "经"),
    ("論", "论"),
    ("頌", "颂"),
    ("咒", "呪"),
    ("真", "眞"),
    ("實", "実"), ("實", "实"),
    ("報", "报"),
    ("應", "応"), ("應", "应"),

    # 其他佛典常见
    ("衆", "眾"), ("衆", "众"),
    ("説", "說"), ("説", "说"),
    ("爲", "為"), ("爲", "为"),
    ("與", "与"),
    ("於", "于"),
    ("無", "无"),
    ("勝", "胜"),
    ("國", "国"),
    ("處", "処"), ("處", "处"),
    ("願", "愿"),
    ("讃", "讚"), ("讃", "赞"),
    ("塔", "墖"),
    ("廟", "庙"),
    ("藏", "蔵"),
]


# ============================================================
# 主构建函数
# ============================================================

def build_unified_dict():
    """构建统一异体字词典"""
    data_dir = Path(__file__).parent
    uf = UnionFind()

    stats = {
        'opencc_pairs': 0,
        'cbeta_pairs': 0,
        'moe_pairs': 0,
        'buddhist_pairs': 0,
        'unihan_pairs': 0,
        'chise_pairs': 0,
    }

    # 1. 解析 OpenCC 数据
    opencc_files = [
        'TSCharacters.txt',
        'STCharacters.txt',
        'TWVariants.txt',
        'HKVariants.txt',
        'JPVariants.txt',
    ]

    for filename in opencc_files:
        filepath = data_dir / filename
        pairs = parse_opencc_file(str(filepath))
        for a, b in pairs:
            uf.union(a, b)
        stats['opencc_pairs'] += len(pairs)
        print(f"  OpenCC {filename}: {len(pairs)} 对")

    # 2. 解析 CBETA 数据
    cbeta_file = data_dir / 'cbeta_gaiji.csv'
    cbeta_pairs = parse_cbeta_gaiji(str(cbeta_file))
    for a, b in cbeta_pairs:
        uf.union(a, b)
    stats['cbeta_pairs'] = len(cbeta_pairs)
    print(f"  CBETA gaiji: {len(cbeta_pairs)} 对")

    # 3. 解析教育部异体字字典数据
    moe_file = data_dir / 'moe_variants.txt'
    moe_pairs = parse_moe_variants(str(moe_file))
    for a, b in moe_pairs:
        uf.union(a, b)
    stats['moe_pairs'] = len(moe_pairs)
    print(f"  教育部异体字: {len(moe_pairs)} 对")

    # 4. 添加佛典专用异体字
    for a, b in BUDDHIST_VARIANT_PAIRS:
        uf.union(a, b)
    stats['buddhist_pairs'] = len(BUDDHIST_VARIANT_PAIRS)
    print(f"  佛典专用: {len(BUDDHIST_VARIANT_PAIRS)} 对")

    # 5. 解析 Unicode Unihan 数据
    unihan_file = data_dir / 'unihan' / 'Unihan_Variants.txt'
    unihan_pairs = parse_unihan_variants(str(unihan_file))
    for a, b in unihan_pairs:
        uf.union(a, b)
    stats['unihan_pairs'] = len(unihan_pairs)
    print(f"  Unihan 异体字: {len(unihan_pairs)} 对")

    # 6. 解析 CHISE IDS 数据
    chise_file = data_dir / 'chise' / 'IDS.txt'
    chise_pairs = parse_chise_ids(str(chise_file))
    for a, b in chise_pairs:
        uf.union(a, b)
    stats['chise_pairs'] = len(chise_pairs)
    print(f"  CHISE IDS: {len(chise_pairs)} 对")

    # 获取所有组
    groups = uf.get_groups()

    # 按组大小排序
    groups = sorted(groups, key=lambda x: -len(x))

    return groups, stats


def generate_python_code(groups: list, stats: dict) -> str:
    """生成 Python 代码"""
    total_chars = sum(len(g) for g in groups)

    lines = [
        '"""',
        '统一异体字词典 - 自动生成',
        '',
        '数据来源:',
        '1. OpenCC (BYVoid/OpenCC)',
        '   - TSCharacters.txt: 繁体→简体',
        '   - STCharacters.txt: 简体→繁体',
        '   - TWVariants.txt: 台湾异体字',
        '   - HKVariants.txt: 香港异体字',
        '   - JPVariants.txt: 日本新字体',
        '',
        '2. CBETA 外字数据库 (cbeta-org/cbeta_gaiji)',
        '   - 佛典缺字与标准字映射',
        '',
        '3. 台湾教育部异体字字典 (kcwu/moedict-variants)',
        '   - 正字与异体字映射',
        '',
        '4. 佛典专用异体字 (手动维护)',
        '',
        '5. Unicode Unihan 数据库 (unicode.org)',
        '   - kZVariant: 字形异体',
        '   - kSemanticVariant: 语义异体',
        '   - kTraditionalVariant/kSimplifiedVariant: 繁简变体',
        '',
        '6. CHISE/IDS 汉字结构数据 (cjkvi/cjkvi-ids)',
        '   - 基于部件结构推导的异体关系',
        '',
        f'统计:',
        f'  - OpenCC 映射: {stats["opencc_pairs"]} 对',
        f'  - CBETA 映射: {stats["cbeta_pairs"]} 对',
        f'  - 教育部异体字: {stats["moe_pairs"]} 对',
        f'  - 佛典专用: {stats["buddhist_pairs"]} 对',
        f'  - Unihan 异体字: {stats["unihan_pairs"]} 对',
        f'  - CHISE IDS: {stats["chise_pairs"]} 对',
        f'  - 合并后组数: {len(groups)} 组',
        f'  - 涵盖字符: {total_chars} 个',
        '"""',
        '',
        'VARIANT_GROUPS = [',
    ]

    for group in groups:
        chars = ', '.join(f'"{c}"' for c in group)
        lines.append(f'    ({chars}),')

    lines.append(']')

    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("统一异体字词典构建")
    print("=" * 60)
    print()

    print("1. 解析数据源:")
    groups, stats = build_unified_dict()

    print()
    print("2. 构建结果:")
    total_chars = sum(len(g) for g in groups)
    print(f"  - 异体字组数: {len(groups)}")
    print(f"  - 涵盖字符数: {total_chars}")

    print()
    print("3. 最大的异体字组 (前10):")
    for i, group in enumerate(groups[:10]):
        print(f"  {i+1}. ({len(group)}字) {group[:8]}{'...' if len(group) > 8 else ''}")

    # 生成代码
    code = generate_python_code(groups, stats)

    output_file = Path(__file__).parent / 'variant_groups_unified.py'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)

    print()
    print(f"4. 已生成: {output_file}")

    return groups, stats


if __name__ == '__main__':
    main()
