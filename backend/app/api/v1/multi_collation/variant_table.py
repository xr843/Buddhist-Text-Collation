"""
异文汇校表生成模块
从 multi_collation.py 中提取
"""
import re
from typing import List, Dict, Any

from app.services.variant_dict import classify_difference


def generate_variant_table(
    base_text: str,
    base_name: str,
    collation_results: List[Dict]
) -> List[Dict]:
    """
    生成异文汇校表

    将各校本在同一位置的差异合并，生成汇校表数据

    Args:
        base_text: 底本文本（原始文本，可能包含换行符）
        base_name: 底本名称
        collation_results: 各校本的对比结果

    Returns:
        异文汇校表数据列表
    """
    # 关键修复：规范化底本文本（与 collation_service 中的处理保持一致）
    # 移除换行符、空格和零宽字符，这样 current_pos 才能正确对应
    normalized_base = base_text.replace('\n', '').replace('\r', '')
    normalized_base = re.sub(r'[\s\u3000\u00A0]+', '', normalized_base)
    # 移除零宽字符（U+200B-U+200F, U+FEFF, U+2060-U+2064）
    normalized_base = re.sub(r'[\u200B-\u200F\uFEFF\u2060-\u2064]+', '', normalized_base)

    # 用于存储按位置归类的差异
    # key: 位置(起始位置), value: {base_char, context, variants: {校本名: 字符}, categories: {校本名: 分类}}
    position_variants: Dict[Any, Dict[str, Any]] = {}

    # 预处理：构建每个校本的替换分类映射 {(from_char, to_char): category}
    def build_replace_category_map(coll_result: Dict) -> Dict[tuple, str]:
        """从 diff_details.replaced 构建替换分类映射"""
        category_map = {}
        diff_details = coll_result.get("statistics", {}).get("diff_details", {})
        replaced_list = diff_details.get("replaced", [])
        transposed_list = diff_details.get("transposed", [])

        for item in replaced_list:
            from_char = item.get("from", "")
            to_char = item.get("to", "")
            category = item.get("category", "error")  # "variant" 或 "error"
            if from_char and to_char:
                category_map[(from_char, to_char)] = category

        # 倒文归入讹误
        for item in transposed_list:
            from_char = item.get("from", "")
            to_char = item.get("to", "")
            if from_char and to_char:
                category_map[(from_char, to_char)] = "error"

        return category_map

    for coll in collation_results:
        coll_name = coll["collation_name"]
        coll_result = coll.get("result")

        # 如果 result 为 None，跳过此校本
        if not coll_result:
            continue

        segments = coll_result.get("side_by_side", {}).get("segments", [])

        # 构建该校本的替换分类映射
        replace_category_map = build_replace_category_map(coll_result)

        current_pos = 0  # 当前在规范化底本中的位置

        for seg in segments:
            seg_type = seg["type"]
            text1 = seg.get("text1", "")  # 底本文字
            text2 = seg.get("text2", "")  # 校本文字

            if seg_type == "equal":
                # 相同部分，更新位置
                current_pos += len(text1)

            elif seg_type == "replace":
                # 替换（异体字/讹误，包含倒文）
                min_len = min(len(text1), len(text2))

                # 处理共同长度部分
                for i in range(min_len):
                    char1 = text1[i]
                    char2 = text2[i]
                    if char1 == char2:
                        current_pos += 1
                        continue

                    pos = current_pos

                    # 获取上下文（前后各5字）- 使用规范化后的底本
                    ctx_start = max(0, pos - 5)
                    ctx_end = min(len(normalized_base), pos + 1 + 5)
                    context_before = normalized_base[ctx_start:pos]
                    context_after = normalized_base[pos + 1:ctx_end]

                    # 查找该替换的分类（单字符对）
                    replace_category = replace_category_map.get((char1, char2))
                    if replace_category is None:
                        replace_category = classify_difference(char1, char2)

                    if pos not in position_variants:
                        position_variants[pos] = {
                            "position": pos,
                            "base_char": char1,
                            "context_before": context_before,
                            "context_after": context_after,
                            "variants": {},
                            "categories": {},
                            "category": "replace"
                        }

                    position_variants[pos]["variants"][coll_name] = char2
                    position_variants[pos]["categories"][coll_name] = replace_category
                    current_pos += 1

                # 处理 text1 比 text2 长的情况（脱文）
                if len(text1) > len(text2):
                    for j in range(len(text2), len(text1)):
                        pos = current_pos
                        tuowen_char = text1[j]

                        ctx_start = max(0, pos - 5)
                        ctx_end = min(len(normalized_base), pos + len(tuowen_char) + 5)
                        context_before = normalized_base[ctx_start:pos]
                        context_after = normalized_base[pos + len(tuowen_char):ctx_end]

                        if pos not in position_variants:
                            position_variants[pos] = {
                                "position": pos,
                                "base_char": tuowen_char,
                                "context_before": context_before,
                                "context_after": context_after,
                                "variants": {},
                                "categories": {},
                                "category": "tuowen"
                            }

                        position_variants[pos]["variants"][coll_name] = "∅"
                        position_variants[pos]["categories"][coll_name] = "tuowen"
                        current_pos += 1

                # 处理 text2 比 text1 长的情况（衍文）
                if len(text2) > len(text1):
                    yanwen_idx = 0
                    for j in range(len(text1), len(text2)):
                        pos_key = f"ins_{current_pos}_{yanwen_idx}"
                        yanwen_char = text2[j]

                        ctx_start = max(0, current_pos - 5)
                        ctx_end = min(len(normalized_base), current_pos + 5)
                        context_before = normalized_base[ctx_start:current_pos]
                        context_after = normalized_base[current_pos:ctx_end]

                        position_variants[pos_key] = {
                            "position": current_pos,
                            "sort_key": (current_pos, yanwen_idx),
                            "base_char": "∅",
                            "context_before": context_before,
                            "context_after": context_after,
                            "variants": {coll_name: yanwen_char},
                            "categories": {coll_name: "yanwen"},
                            "category": "yanwen"
                        }
                        yanwen_idx += 1

            elif seg_type == "delete":
                # 脱文（底本有，校本无）- 逐字符记录
                for char in text1:
                    pos = current_pos

                    ctx_start = max(0, pos - 5)
                    ctx_end = min(len(normalized_base), pos + 1 + 5)
                    context_before = normalized_base[ctx_start:pos]
                    context_after = normalized_base[pos + 1:ctx_end]

                    if pos not in position_variants:
                        position_variants[pos] = {
                            "position": pos,
                            "base_char": char,
                            "context_before": context_before,
                            "context_after": context_after,
                            "variants": {},
                            "categories": {},
                            "category": "tuowen"
                        }

                    position_variants[pos]["variants"][coll_name] = "∅"
                    position_variants[pos]["categories"][coll_name] = "tuowen"
                    current_pos += 1

            elif seg_type == "insert":
                # 衍文（底本无，校本有）- 逐字符记录
                yanwen_idx = 0
                for char in text2:
                    pos_key = f"ins_{current_pos}_{yanwen_idx}"

                    ctx_start = max(0, current_pos - 5)
                    ctx_end = min(len(normalized_base), current_pos + 5)
                    context_before = normalized_base[ctx_start:current_pos]
                    context_after = normalized_base[current_pos:ctx_end]

                    position_variants[pos_key] = {
                        "position": current_pos,
                        "sort_key": (current_pos, yanwen_idx),
                        "base_char": "∅",
                        "context_before": context_before,
                        "context_after": context_after,
                        "variants": {coll_name: char},
                        "categories": {coll_name: "yanwen"},
                        "category": "yanwen"
                    }
                    yanwen_idx += 1

    # 转换为列表并排序
    variant_table = []
    all_coll_names = [c["collation_name"] for c in collation_results]

    # 自定义排序
    def get_sort_key(pos_key):
        item = position_variants[pos_key]
        if "sort_key" in item:
            return item["sort_key"]
        elif isinstance(pos_key, int):
            return (pos_key, 0)
        else:
            try:
                parts = str(pos_key).split("_")
                return (int(parts[1]), int(parts[2]))
            except:
                return (item.get("position", 0), 0)

    sorted_keys = sorted(position_variants.keys(), key=get_sort_key)

    for pos in sorted_keys:
        item = position_variants[pos]

        # 确定最终分类
        categories = item.get("categories", {})

        tuowen_count = sum(1 for c in categories.values() if c == "tuowen")
        yanwen_count = sum(1 for c in categories.values() if c == "yanwen")
        variant_count = sum(1 for c in categories.values() if c == "variant")
        error_count = sum(1 for c in categories.values() if c == "error")

        if tuowen_count > 0:
            category = "脱文"
        elif yanwen_count > 0:
            category = "衍文"
        elif variant_count > 0 and variant_count >= error_count:
            category = "异体字"
        else:
            category = "讹误"

        # 构建各校本的值列表
        coll_values = []
        for coll_name in all_coll_names:
            val = item["variants"].get(coll_name, item["base_char"])
            coll_values.append(val)

        base_char = item["base_char"]

        display_position = item["position"] + 1 if isinstance(item["position"], int) else item["position"]

        variant_table.append({
            "position": display_position,
            "context": f"...{item['context_before']}【{base_char}】{item['context_after']}...",
            "base_char": base_char,
            "coll_values": coll_values,
            "category": category
        })

    return variant_table
