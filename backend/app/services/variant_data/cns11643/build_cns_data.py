"""
CNS 11643 数据构建脚本

将 CNS 原始数据转换为 JSON 格式，供 cns_utils 模块使用。

数据来源：
- CNS2UNICODE_2.txt: CNS 编码到 Unicode 映射
- CNS_radical.txt: 部首数据
- CNS_stroke.txt: 笔画数据
- CNS_phonetic.txt: 注音数据
- CNS_pinyin_1.txt: 注音到拼音转换表
"""

import json
import os
from pathlib import Path
from collections import defaultdict


def load_cns_unicode_mapping(filepath: str) -> dict:
    """加载 CNS 到 Unicode 的映射"""
    cns_to_unicode = {}
    unicode_to_cns = defaultdict(list)

    if not os.path.exists(filepath):
        print(f"警告: 文件不存在 {filepath}")
        return {}, {}

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                cns_code = parts[0]
                unicode_hex = parts[1].upper()
                cns_to_unicode[cns_code] = unicode_hex
                unicode_to_cns[unicode_hex].append(cns_code)

    return cns_to_unicode, dict(unicode_to_cns)


def cns_to_char(cns_code: str, cns_to_unicode: dict) -> str:
    """将 CNS 编码转换为 Unicode 字符"""
    if cns_code not in cns_to_unicode:
        return ''
    try:
        unicode_hex = cns_to_unicode[cns_code]
        return chr(int(unicode_hex, 16))
    except (ValueError, OverflowError):
        return ''


def load_radical_data(filepath: str, cns_to_unicode: dict) -> dict:
    """加载部首数据"""
    char_radical = {}

    # 214 部首对照表（康熙部首）
    radicals = [
        '', '一', '丨', '丶', '丿', '乙', '亅', '二', '亠', '人', '儿',
        '入', '八', '冂', '冖', '冫', '几', '凵', '刀', '力', '勹',
        '匕', '匚', '匸', '十', '卜', '卩', '厂', '厶', '又', '口',
        '囗', '土', '士', '夂', '夊', '夕', '大', '女', '子', '宀',
        '寸', '小', '尢', '尸', '屮', '山', '巛', '工', '己', '巾',
        '干', '幺', '广', '廴', '廾', '弋', '弓', '彐', '彡', '彳',
        '心', '戈', '戶', '手', '支', '攴', '文', '斗', '斤', '方',
        '无', '日', '曰', '月', '木', '欠', '止', '歹', '殳', '毋',
        '比', '毛', '氏', '气', '水', '火', '爪', '父', '爻', '爿',
        '片', '牙', '牛', '犬', '玄', '玉', '瓜', '瓦', '甘', '生',
        '用', '田', '疋', '疒', '癶', '白', '皮', '皿', '目', '矛',
        '矢', '石', '示', '禸', '禾', '穴', '立', '竹', '米', '糸',
        '缶', '网', '羊', '羽', '老', '而', '耒', '耳', '聿', '肉',
        '臣', '自', '至', '臼', '舌', '舛', '舟', '艮', '色', '艸',
        '虍', '虫', '血', '行', '衣', '襾', '見', '角', '言', '谷',
        '豆', '豕', '豸', '貝', '赤', '走', '足', '身', '車', '辛',
        '辰', '辵', '邑', '酉', '釆', '里', '金', '長', '門', '阜',
        '隶', '隹', '雨', '靑', '非', '面', '革', '韋', '韭', '音',
        '頁', '風', '飛', '食', '首', '香', '馬', '骨', '高', '髟',
        '鬥', '鬯', '鬲', '鬼', '魚', '鳥', '鹵', '鹿', '麥', '麻',
        '黃', '黍', '黑', '黹', '黽', '鼎', '鼓', '鼠', '鼻', '齊',
        '齒', '龍', '龜', '龠'
    ]

    if not os.path.exists(filepath):
        return char_radical

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                cns_code = parts[0]
                try:
                    radical_idx = int(parts[1])
                    char = cns_to_char(cns_code, cns_to_unicode)
                    if char and 0 < radical_idx < len(radicals):
                        char_radical[char] = {
                            'index': radical_idx,
                            'radical': radicals[radical_idx]
                        }
                except ValueError:
                    pass

    return char_radical


def load_stroke_data(filepath: str, cns_to_unicode: dict) -> dict:
    """加载笔画数据"""
    char_stroke = {}

    if not os.path.exists(filepath):
        return char_stroke

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                cns_code = parts[0]
                try:
                    stroke_count = int(parts[1])
                    char = cns_to_char(cns_code, cns_to_unicode)
                    if char and stroke_count > 0:
                        char_stroke[char] = stroke_count
                except ValueError:
                    pass

    return char_stroke


def load_phonetic_data(filepath: str, pinyin_filepath: str, cns_to_unicode: dict) -> dict:
    """加载注音和拼音数据"""
    char_phonetic = defaultdict(lambda: {'zhuyin': [], 'pinyin': []})

    # 先加载注音到拼音的转换表
    zhuyin_to_pinyin = {}
    if os.path.exists(pinyin_filepath):
        with open(pinyin_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    zhuyin = parts[0]
                    pinyin = parts[1]  # 取第一个拼音
                    zhuyin_to_pinyin[zhuyin] = pinyin

    if not os.path.exists(filepath):
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                cns_code = parts[0]
                zhuyin = parts[1]
                char = cns_to_char(cns_code, cns_to_unicode)
                if char:
                    if zhuyin not in char_phonetic[char]['zhuyin']:
                        char_phonetic[char]['zhuyin'].append(zhuyin)
                    # 转换为拼音
                    pinyin = zhuyin_to_pinyin.get(zhuyin, '')
                    if pinyin and pinyin not in char_phonetic[char]['pinyin']:
                        char_phonetic[char]['pinyin'].append(pinyin)

    return dict(char_phonetic)


def build_all_data():
    """构建所有数据"""
    data_dir = Path(__file__).parent

    print("=" * 60)
    print("CNS 11643 数据构建")
    print("=" * 60)

    # 1. 加载 CNS-Unicode 映射（合并 BMP 和扩展区）
    print("\n1. 加载 CNS-Unicode 映射...")

    # 先加载 BMP 区域（基本多文种平面，包含常用汉字）
    cns_to_unicode, unicode_to_cns = load_cns_unicode_mapping(
        str(data_dir / 'CNS2UNICODE_BMP.txt')
    )
    print(f"   BMP 区域: {len(cns_to_unicode)} 编码")

    # 再加载扩展区（CJK 扩展 B 等）
    cns_ext, unicode_ext = load_cns_unicode_mapping(
        str(data_dir / 'CNS2UNICODE_2.txt')
    )
    cns_to_unicode.update(cns_ext)
    for u, c_list in unicode_ext.items():
        if u in unicode_to_cns:
            unicode_to_cns[u].extend(c_list)
        else:
            unicode_to_cns[u] = c_list
    print(f"   扩展区域: {len(cns_ext)} 编码")
    print(f"   合计: {len(cns_to_unicode)} 编码")

    # 2. 加载部首数据
    print("\n2. 加载部首数据...")
    char_radical = load_radical_data(
        str(data_dir / 'CNS_radical.txt'),
        cns_to_unicode
    )
    print(f"   有部首数据的字符: {len(char_radical)}")

    # 3. 加载笔画数据
    print("\n3. 加载笔画数据...")
    char_stroke = load_stroke_data(
        str(data_dir / 'CNS_stroke.txt'),
        cns_to_unicode
    )
    print(f"   有笔画数据的字符: {len(char_stroke)}")

    # 4. 加载注音/拼音数据
    print("\n4. 加载注音/拼音数据...")
    char_phonetic = load_phonetic_data(
        str(data_dir / 'CNS_phonetic.txt'),
        str(data_dir / 'CNS_pinyin_1.txt'),
        cns_to_unicode
    )
    print(f"   有注音数据的字符: {len(char_phonetic)}")

    # 5. 合并字符属性
    print("\n5. 合并字符属性...")
    char_attrs = {}
    all_chars = set(char_radical.keys()) | set(char_stroke.keys()) | set(char_phonetic.keys())

    for char in all_chars:
        attrs = {}
        if char in char_radical:
            attrs['radical'] = char_radical[char]['radical']
            attrs['radical_index'] = char_radical[char]['index']
        if char in char_stroke:
            attrs['strokes'] = char_stroke[char]
        if char in char_phonetic:
            attrs['zhuyin'] = char_phonetic[char]['zhuyin']
            attrs['pinyin'] = char_phonetic[char]['pinyin']
        if attrs:
            char_attrs[char] = attrs

    print(f"   总字符数: {len(char_attrs)}")

    # 6. 保存数据
    print("\n6. 保存数据...")

    # CNS-Unicode 映射
    with open(data_dir / 'cns_unicode.json', 'w', encoding='utf-8') as f:
        json.dump({
            'cns_to_unicode': cns_to_unicode,
            'unicode_to_cns': unicode_to_cns
        }, f, ensure_ascii=False, indent=None)
    print(f"   已保存: cns_unicode.json")

    # 字符属性
    with open(data_dir / 'char_attrs.json', 'w', encoding='utf-8') as f:
        json.dump(char_attrs, f, ensure_ascii=False, indent=None)
    print(f"   已保存: char_attrs.json")

    # 7. 统计信息
    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)
    print(f"\n统计:")
    print(f"  - CNS 编码总数: {len(cns_to_unicode)}")
    print(f"  - 字符属性总数: {len(char_attrs)}")

    # 按部首统计
    radical_counts = defaultdict(int)
    for char, attrs in char_attrs.items():
        if 'radical' in attrs:
            radical_counts[attrs['radical']] += 1

    print(f"  - 部首种类: {len(radical_counts)}")
    print(f"\n最常见的部首 (前10):")
    for radical, count in sorted(radical_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {radical}: {count} 字")

    return char_attrs


if __name__ == '__main__':
    build_all_data()
