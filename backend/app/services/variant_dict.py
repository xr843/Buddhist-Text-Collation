"""
佛典异体字词典 - 统一增强版 v4.0

用于识别两个字符是否为异体字关系，减少"假差异"。

数据来源：
1. OpenCC (BYVoid/OpenCC) - 繁简异体字
   - TSCharacters.txt: 繁体→简体
   - STCharacters.txt: 简体→繁体
   - TWVariants.txt: 台湾异体字
   - HKVariants.txt: 香港异体字
   - JPVariants.txt: 日本新字体

2. CBETA 外字数据库 (cbeta-org/cbeta_gaiji)
   - 佛典缺字与标准字映射
   - 5000+ 对异体字关系

3. 台湾教育部异体字字典 (kcwu/moedict-variants)
   - 正字与异体字映射

4. 佛典专用异体字（手动维护）
   - 梵音译字异体
   - 佛教术语专用字

5. Unicode Unihan 数据库 (unicode.org)
   - kZVariant: 字形异体
   - kSemanticVariant: 语义异体
   - kTraditionalVariant/kSimplifiedVariant: 繁简变体

6. CHISE/IDS 汉字结构数据 (cjkvi/cjkvi-ids)
   - 基于部件结构推导的异体关系

使用方法：
    from variant_dict import is_variant, get_standard_form, classify_difference

    is_variant("為", "爲")  # True
    get_standard_form("爲")  # "為"
    classify_difference("眾", "紫")  # "error" (讹误)
"""

# ============================================================
# 导入统一异体字数据
# ============================================================

try:
    from app.services.variant_data.variant_groups_unified import VARIANT_GROUPS
except ImportError:
    # 开发环境可能路径不同
    try:
        from variant_data.variant_groups_unified import VARIANT_GROUPS
    except ImportError:
        VARIANT_GROUPS = []
        print("[警告] 无法导入统一异体字数据")

# ============================================================
# 构建查询数据结构
# ============================================================

# 标准形式映射：异体字 -> 标准字
_STANDARD_MAP: dict = {}

# 异体字组映射：任意字 -> 组ID
_GROUP_MAP: dict = {}


def _build_maps():
    """构建查询映射"""
    for group_id, group in enumerate(VARIANT_GROUPS):
        if not group:
            continue
        standard = group[0]  # 第一个为标准形式
        for char in group:
            if char:
                _STANDARD_MAP[char] = standard
                _GROUP_MAP[char] = group_id


_build_maps()

# ============================================================
# 公开 API
# ============================================================


def is_variant(char1: str, char2: str) -> bool:
    """
    判断两个字符是否为异体字关系

    Args:
        char1: 字符1
        char2: 字符2

    Returns:
        True 如果是异体字关系，False 否则
    """
    if not char1 or not char2:
        return False

    if char1 == char2:
        return True

    # 检查是否在同一组
    group1 = _GROUP_MAP.get(char1)
    group2 = _GROUP_MAP.get(char2)

    if group1 is not None and group2 is not None:
        return group1 == group2

    return False


def get_standard_form(char: str) -> str:
    """
    获取字符的标准形式

    Args:
        char: 输入字符

    Returns:
        标准形式，如果不在词典中则返回原字符
    """
    if not char:
        return char
    return _STANDARD_MAP.get(char, char)


def get_variant_group(char: str) -> tuple:
    """
    获取字符所属的异体字组

    Args:
        char: 输入字符

    Returns:
        异体字组元组，如果不在词典中则返回 None
    """
    group_id = _GROUP_MAP.get(char)
    if group_id is not None and group_id < len(VARIANT_GROUPS):
        return VARIANT_GROUPS[group_id]
    return None


def classify_difference(char1: str, char2: str) -> str:
    """
    对两个不同字符的差异进行分类

    Args:
        char1: 版本1的字符
        char2: 版本2的字符

    Returns:
        分类结果：
        - "identical": 完全相同
        - "variant": 异体字（同字异形）
        - "error": 讹误（非异体字的文字差异）
    """
    if not char1 or not char2:
        return "error"

    if char1 == char2:
        return "identical"

    if is_variant(char1, char2):
        return "variant"

    return "error"


# ============================================================
# 统计信息
# ============================================================


def get_dict_stats() -> dict:
    """获取词典统计信息"""
    total_groups = len(VARIANT_GROUPS)
    total_chars = len(_STANDARD_MAP)

    return {
        "total_groups": total_groups,
        "total_chars": total_chars,
        "version": "4.0.0",
        "description": "佛典异体字词典统一版（OpenCC + CBETA + 教育部 + 佛典专用 + Unihan + CHISE）",
        "sources": [
            "OpenCC (繁简/台湾/香港/日本异体字)",
            "CBETA 外字数据库",
            "台湾教育部异体字字典",
            "佛典专用异体字",
            "Unicode Unihan 数据库",
            "CHISE/IDS 汉字结构数据"
        ]
    }


if __name__ == "__main__":
    # 测试
    stats = get_dict_stats()
    print("异体字词典统计:")
    print(f"  - 总组数: {stats['total_groups']}")
    print(f"  - 总字符数: {stats['total_chars']}")
    print(f"  - 版本: {stats['version']}")
    print("  - 数据来源:")
    for src in stats['sources']:
        print(f"      · {src}")
    print()

    test_pairs = [
        ("為", "爲"),    # 应该是 variant
        ("眾", "紫"),    # 应该是 error
        ("佛", "仏"),    # 应该是 variant
        ("說", "説"),    # 应该是 variant
        ("經", "経"),    # 应该是 variant
        ("薩", "萨"),    # 应该是 variant
        ("涅", "湼"),    # 应该是 variant
        ("葱", "蔥"),    # CBETA: 应该是 variant
        ("菓", "果"),    # CBETA: 应该是 variant
        ("呪", "咒"),    # CBETA: 应该是 variant
        ("弃", "棄"),    # CBETA: 应该是 variant
        ("陀", "馱"),    # 佛典专用: 应该是 variant
    ]

    print("测试结果:")
    for c1, c2 in test_pairs:
        result = classify_difference(c1, c2)
        expected = "error" if (c1 == "眾" and c2 == "紫") else "variant"
        status = "✓" if result == expected else "✗"
        print(f"  {status} {c1} vs {c2}: {result}")
