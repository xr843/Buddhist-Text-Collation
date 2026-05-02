"""
标点定本生成工具

包含：
- 标点定本生成核心算法
"""
from typing import List, Dict


# 定义标点符号集合
PUNCT_MARKS = set('。，、；：？！""''（）《》【】「」『』．·…—─-－﹣:;,?!.、')


def find_actual_position(text: str, clean_pos: int) -> int:
    """将纯文本位置转换为实际字符位置"""
    clean_count = 0
    for i, char in enumerate(text):
        if clean_count == clean_pos:
            return i
        if char not in PUNCT_MARKS:
            clean_count += 1
    return len(text)


def find_punct_around_position(chars: List[str], actual_pos: int, search_range: int = 3) -> int:
    """在指定位置附近查找标点"""
    # 先检查位置后面
    for offset in range(search_range + 1):
        pos = actual_pos + offset
        if 0 <= pos < len(chars) and chars[pos] in PUNCT_MARKS:
            return pos
    # 再检查位置前面
    for offset in range(1, search_range + 1):
        pos = actual_pos - offset
        if 0 <= pos < len(chars) and chars[pos] in PUNCT_MARKS:
            return pos
    return -1


def generate_punctuation_definitive_text(
    base_text: str,
    other_text: str,
    differences: List[Dict],
    decisions: Dict[str, Dict],
    version1_name: str,
    version2_name: str,
) -> Dict:
    """
    生成标点定本的核心算法

    算法思路：
    1. 以版本1文本为基础
    2. 按位置从后往前应用判取（避免位置偏移）
    3. 对于每个判取为version2的差异，执行相应的标点操作

    Args:
        base_text: 版本1文本（基准）
        other_text: 版本2文本
        differences: 标点差异列表
        decisions: 判取结果字典
        version1_name: 版本1名称
        version2_name: 版本2名称

    Returns:
        包含定本文本、改易记和统计信息的字典
    """
    # 将文本转为字符列表
    result_chars = list(base_text)
    change_notes = []

    # 统计
    stats = {
        "total_decisions": len(decisions),
        "applied_count": 0,
        "version1_adopted": 0,
        "version2_adopted": 0,
        "skipped_count": 0,
    }

    # 按位置倒序排列判取结果（从后往前应用，避免位置偏移）
    sorted_decisions = sorted(
        decisions.items(),
        key=lambda x: int(x[1].get('position', 0)),
        reverse=True
    )

    for diff_id_str, decision in sorted_decisions:
        diff_id = int(diff_id_str)
        selected_version = decision.get('selectedVersion', 'version1')

        # 如果采用版本1，无需修改
        if selected_version == 'version1':
            stats["version1_adopted"] += 1
            continue

        # 采用版本2：需要修改标点
        stats["version2_adopted"] += 1

        # 找到对应的差异
        diff = next((d for d in differences if d.get('id') == diff_id), None)
        if not diff:
            stats["skipped_count"] += 1
            continue

        position = diff.get('position_v1', diff.get('position', 0))
        diff_type = diff.get('diff_type', '')
        punct1 = diff.get('version1_punct', '')
        punct2 = diff.get('version2_punct', '')
        context = diff.get('context', '')

        # 转换为实际位置
        actual_pos = find_actual_position(''.join(result_chars), position)

        try:
            if diff_type == '新增标点':
                # version1无标点，version2有标点 → 在指定位置后插入标点
                insert_pos = actual_pos + 1
                if insert_pos <= len(result_chars):
                    result_chars.insert(insert_pos, punct2)
                    stats["applied_count"] += 1
                    change_notes.append({
                        "position": position,
                        "context": context,
                        "originalPunct": punct1 if punct1 and punct1 != '无' else '∅',
                        "changedPunct": punct2,
                        "changeType": "新增",
                        "note": decision.get('note', ''),
                    })

            elif diff_type == '删除标点':
                # version1有标点，version2无标点 → 删除标点
                punct_pos = find_punct_around_position(result_chars, actual_pos)
                if punct_pos >= 0:
                    deleted_punct = result_chars[punct_pos]
                    del result_chars[punct_pos]
                    stats["applied_count"] += 1
                    change_notes.append({
                        "position": position,
                        "context": context,
                        "originalPunct": deleted_punct,
                        "changedPunct": '∅',
                        "changeType": "删除",
                        "note": decision.get('note', ''),
                    })

            elif diff_type == '替换标点':
                # 替换标点
                punct_pos = find_punct_around_position(result_chars, actual_pos)
                if punct_pos >= 0:
                    old_punct = result_chars[punct_pos]
                    result_chars[punct_pos] = punct2
                    stats["applied_count"] += 1
                    change_notes.append({
                        "position": position,
                        "context": context,
                        "originalPunct": old_punct,
                        "changedPunct": punct2,
                        "changeType": "替换",
                        "note": decision.get('note', ''),
                    })
            else:
                stats["skipped_count"] += 1

        except Exception as e:
            print(f"[生成定本] 处理差异 {diff_id} 时出错: {e}")
            stats["skipped_count"] += 1

    # 按位置正序排列改易记
    change_notes.sort(key=lambda x: x['position'])

    return {
        "text": ''.join(result_chars),
        "notes": change_notes,
        "statistics": stats,
        "version1_name": version1_name,
        "version2_name": version2_name,
    }
