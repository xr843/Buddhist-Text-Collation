"""
CNS 11643 工具模块

提供 CNS 编码转换和字符属性查询功能。

数据来源：台湾 CNS 11643 中文标准交换码全字库
官方网站：https://www.cns11643.gov.tw

功能：
1. CNS 编码 ↔ Unicode 字符转换
2. 字符属性查询：部首、笔画、注音、拼音
3. 按部首/笔画筛选字符

使用方法：
    from cns_utils import (
        cns_to_char, char_to_cns,
        get_radical, get_strokes, get_pinyin,
        find_chars_by_radical
    )

    # 编码转换
    char = cns_to_char('1-4421')  # '一'
    cns = char_to_cns('一')       # ['1-4421']

    # 属性查询
    get_radical('漢')   # '水'
    get_strokes('漢')   # 14
    get_pinyin('漢')    # ['han4']
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from collections import defaultdict

# ============================================================
# 数据加载
# ============================================================

_DATA_DIR = Path(__file__).parent / 'variant_data' / 'cns11643'

# 延迟加载的数据
_cns_to_unicode: Optional[dict] = None
_unicode_to_cns: Optional[dict] = None
_char_attrs: Optional[dict] = None
_radical_index: Optional[dict] = None  # 部首 -> 字符列表


def _load_cns_unicode():
    """加载 CNS-Unicode 映射数据"""
    global _cns_to_unicode, _unicode_to_cns

    if _cns_to_unicode is not None:
        return

    json_path = _DATA_DIR / 'cns_unicode.json'
    if not json_path.exists():
        print(f"[警告] CNS-Unicode 数据文件不存在: {json_path}")
        _cns_to_unicode = {}
        _unicode_to_cns = {}
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        _cns_to_unicode = data.get('cns_to_unicode', {})
        _unicode_to_cns = data.get('unicode_to_cns', {})


def _load_char_attrs():
    """加载字符属性数据"""
    global _char_attrs, _radical_index

    if _char_attrs is not None:
        return

    json_path = _DATA_DIR / 'char_attrs.json'
    if not json_path.exists():
        print(f"[警告] 字符属性数据文件不存在: {json_path}")
        _char_attrs = {}
        _radical_index = {}
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        _char_attrs = json.load(f)

    # 构建部首索引
    _radical_index = defaultdict(list)
    for char, attrs in _char_attrs.items():
        if 'radical' in attrs:
            _radical_index[attrs['radical']].append(char)


# ============================================================
# CNS 编码转换 API
# ============================================================


def cns_to_char(cns_code: str) -> str:
    """
    将 CNS 编码转换为 Unicode 字符

    Args:
        cns_code: CNS 编码，如 '1-4421'

    Returns:
        对应的 Unicode 字符，如 '一'
        如果编码无效则返回空字符串
    """
    _load_cns_unicode()

    if cns_code not in _cns_to_unicode:
        return ''

    try:
        unicode_hex = _cns_to_unicode[cns_code]
        return chr(int(unicode_hex, 16))
    except (ValueError, OverflowError):
        return ''


def char_to_cns(char: str) -> List[str]:
    """
    将 Unicode 字符转换为 CNS 编码

    Args:
        char: Unicode 字符，如 '一'

    Returns:
        CNS 编码列表（一个字符可能有多个 CNS 编码）
        如果字符不在 CNS 中则返回空列表
    """
    _load_cns_unicode()

    if not char or len(char) != 1:
        return []

    unicode_hex = f'{ord(char):X}'
    return _unicode_to_cns.get(unicode_hex, [])


def is_cns_char(char: str) -> bool:
    """
    判断字符是否在 CNS 11643 中

    Args:
        char: Unicode 字符

    Returns:
        True 如果字符在 CNS 中，否则 False
    """
    return len(char_to_cns(char)) > 0


# ============================================================
# 字符属性查询 API
# ============================================================


def get_radical(char: str) -> str:
    """
    获取字符的部首

    Args:
        char: Unicode 字符

    Returns:
        部首字符，如 '水'
        如果无数据则返回空字符串
    """
    _load_char_attrs()

    if not char or len(char) != 1:
        return ''

    attrs = _char_attrs.get(char, {})
    return attrs.get('radical', '')


def get_radical_index(char: str) -> int:
    """
    获取字符的部首序号（康熙部首序号，1-214）

    Args:
        char: Unicode 字符

    Returns:
        部首序号，如 85（水部）
        如果无数据则返回 0
    """
    _load_char_attrs()

    if not char or len(char) != 1:
        return 0

    attrs = _char_attrs.get(char, {})
    return attrs.get('radical_index', 0)


def get_strokes(char: str) -> int:
    """
    获取字符的笔画数

    Args:
        char: Unicode 字符

    Returns:
        笔画数
        如果无数据则返回 0
    """
    _load_char_attrs()

    if not char or len(char) != 1:
        return 0

    attrs = _char_attrs.get(char, {})
    return attrs.get('strokes', 0)


def get_zhuyin(char: str) -> List[str]:
    """
    获取字符的注音（可能有多个读音）

    Args:
        char: Unicode 字符

    Returns:
        注音列表，如 ['ㄏㄢˋ']
        如果无数据则返回空列表
    """
    _load_char_attrs()

    if not char or len(char) != 1:
        return []

    attrs = _char_attrs.get(char, {})
    return attrs.get('zhuyin', [])


def get_pinyin(char: str) -> List[str]:
    """
    获取字符的拼音（可能有多个读音）

    Args:
        char: Unicode 字符

    Returns:
        拼音列表，如 ['han4']
        如果无数据则返回空列表
    """
    _load_char_attrs()

    if not char or len(char) != 1:
        return []

    attrs = _char_attrs.get(char, {})
    return attrs.get('pinyin', [])


def get_char_info(char: str) -> Dict:
    """
    获取字符的完整属性信息

    Args:
        char: Unicode 字符

    Returns:
        包含所有属性的字典，如：
        {
            'char': '漢',
            'radical': '水',
            'radical_index': 85,
            'strokes': 14,
            'zhuyin': ['ㄏㄢˋ'],
            'pinyin': ['han4'],
            'cns_codes': ['1-5765']
        }
    """
    _load_char_attrs()
    _load_cns_unicode()

    if not char or len(char) != 1:
        return {}

    attrs = _char_attrs.get(char, {})
    result = {'char': char}
    result.update(attrs)
    result['cns_codes'] = char_to_cns(char)

    return result


# ============================================================
# 字符查找 API
# ============================================================


def find_chars_by_radical(radical: str, stroke_range: tuple = None) -> List[str]:
    """
    按部首查找字符

    Args:
        radical: 部首字符，如 '水'
        stroke_range: 可选的笔画范围，如 (10, 15) 表示 10-15 画

    Returns:
        符合条件的字符列表
    """
    _load_char_attrs()

    if not radical:
        return []

    chars = _radical_index.get(radical, [])

    if stroke_range:
        min_strokes, max_strokes = stroke_range
        chars = [
            c for c in chars
            if min_strokes <= _char_attrs.get(c, {}).get('strokes', 0) <= max_strokes
        ]

    return sorted(chars)


def find_chars_by_strokes(strokes: int, radical: str = None) -> List[str]:
    """
    按笔画数查找字符

    Args:
        strokes: 笔画数
        radical: 可选的部首筛选

    Returns:
        符合条件的字符列表
    """
    _load_char_attrs()

    result = []
    for char, attrs in _char_attrs.items():
        if attrs.get('strokes') == strokes:
            if radical is None or attrs.get('radical') == radical:
                result.append(char)

    return sorted(result)


def find_chars_by_pinyin(pinyin: str) -> List[str]:
    """
    按拼音查找字符

    Args:
        pinyin: 拼音，如 'han4'

    Returns:
        符合条件的字符列表
    """
    _load_char_attrs()

    result = []
    for char, attrs in _char_attrs.items():
        if pinyin in attrs.get('pinyin', []):
            result.append(char)

    return sorted(result)


# ============================================================
# 统计信息
# ============================================================


def get_cns_stats() -> Dict:
    """获取 CNS 数据统计信息"""
    _load_cns_unicode()
    _load_char_attrs()

    return {
        'cns_codes': len(_cns_to_unicode),
        'chars_with_attrs': len(_char_attrs),
        'radicals': len(_radical_index),
        'version': '1.0.0',
        'source': 'CNS 11643 全字库 (m80126colin/cns11643)'
    }


# ============================================================
# 测试
# ============================================================


if __name__ == '__main__':
    print("CNS 11643 工具模块测试")
    print("=" * 50)

    stats = get_cns_stats()
    print(f"\n统计信息:")
    print(f"  CNS 编码数: {stats['cns_codes']}")
    print(f"  有属性的字符: {stats['chars_with_attrs']}")
    print(f"  部首种类: {stats['radicals']}")

    print(f"\n编码转换测试:")
    test_cns = ['1-4421', '1-4422', '1-5765']
    for cns in test_cns:
        char = cns_to_char(cns)
        print(f"  {cns} -> '{char}'")

    print(f"\n字符属性测试:")
    test_chars = ['一', '漢', '佛', '經', '般', '若']
    for char in test_chars:
        info = get_char_info(char)
        if info:
            radical = info.get('radical', '?')
            strokes = info.get('strokes', 0)
            pinyin = ', '.join(info.get('pinyin', []))
            cns = ', '.join(info.get('cns_codes', []))
            print(f"  {char}: 部首={radical}, 笔画={strokes}, 拼音={pinyin}, CNS={cns}")
        else:
            print(f"  {char}: 无数据")

    print(f"\n按部首查找测试 (水部, 10-15画):")
    chars = find_chars_by_radical('水', (10, 15))
    print(f"  找到 {len(chars)} 字: {chars[:20]}...")
