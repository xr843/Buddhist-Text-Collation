"""
动态规划对齐模块
从 collation_service.py 中提取
"""
from typing import List, Dict, Callable

from .char_diff import compute_char_diff
from .sentence_aligner import compute_similarity


def dp_align_segment(
    sentences1: List[str],
    sentences2: List[str],
    offset1: int,
    offset2: int,
    similarity_func: Callable[[str, str], float] = None
) -> List[Dict]:
    """
    使用动态规划对齐一个分段的句子

    Args:
        sentences1: 分段的版本1句子
        sentences2: 分段的版本2句子
        offset1: 在原句子列表中的起始索引（版本1）
        offset2: 在原句子列表中的起始索引（版本2）
        similarity_func: 相似度计算函数（可选，默认使用 compute_similarity）

    Returns:
        对齐后的句子组列表
    """
    if similarity_func is None:
        similarity_func = compute_similarity

    m, n = len(sentences1), len(sentences2)

    # 空分段直接返回
    if m == 0 and n == 0:
        return []

    # 只有一边有句子
    if m == 0:
        return [
            {
                "id": 0,  # 后续统一分配ID
                "type": "insert",
                "sentence1": "",
                "sentence2": sentences2[j],
                "has_diff": True,
                "char_diff": None,
                "index1": None,
                "index2": offset2 + j,
            }
            for j in range(n)
        ]

    if n == 0:
        return [
            {
                "id": 0,
                "type": "delete",
                "sentence1": sentences1[i],
                "sentence2": "",
                "has_diff": True,
                "char_diff": None,
                "index1": offset1 + i,
                "index2": None,
            }
            for i in range(m)
        ]

    # 动态规划
    # dp[i][j] = 对齐前i个句子1和前j个句子2的最大相似度得分
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]
    # path[i][j] = 到达(i,j)的路径类型: 'match'/'delete'/'insert'/'skip'
    path = [[None] * (n + 1) for _ in range(m + 1)]

    # 初始化：空对空的得分是0
    # 初始化第一行和第一列（表示一边为空的情况）
    for i in range(1, m + 1):
        dp[i][0] = dp[i - 1][0] - 0.5  # 删除惩罚
        path[i][0] = "delete"

    for j in range(1, n + 1):
        dp[0][j] = dp[0][j - 1] - 0.5  # 插入惩罚
        path[0][j] = "insert"

    # 填充DP表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # 计算句子相似度作为匹配分数
            sim = similarity_func(sentences1[i - 1], sentences2[j - 1])

            # 三种选择：
            # 1. 匹配（一对一）
            match_score = dp[i - 1][j - 1] + sim
            # 2. 删除句子1[i]（句子1[i]不匹配任何句子2）
            delete_score = dp[i - 1][j] - 0.5
            # 3. 插入句子2[j]（句子2[j]不匹配任何句子1）
            insert_score = dp[i][j - 1] - 0.5

            # 选择得分最高的
            if match_score >= delete_score and match_score >= insert_score:
                dp[i][j] = match_score
                path[i][j] = "match"
            elif delete_score >= insert_score:
                dp[i][j] = delete_score
                path[i][j] = "delete"
            else:
                dp[i][j] = insert_score
                path[i][j] = "insert"

    # 回溯得到对齐路径
    aligned = []
    i, j = m, n
    max_iterations = m + n + 10  # 防止无限循环
    iterations = 0

    while i > 0 or j > 0:
        iterations += 1
        if iterations > max_iterations:
            print(f"[警告] 回溯超过最大迭代次数，强制退出。i={i}, j={j}")
            break

        # 边界检查
        if i == 0 and j == 0:
            break

        current_path = path[i][j] if (i <= m and j <= n) else None

        if current_path == "match" and i > 0 and j > 0:
            # 一对一匹配
            sim = similarity_func(sentences1[i - 1], sentences2[j - 1])
            char_diff = compute_char_diff(
                sentences1[i - 1], sentences2[j - 1]
            )

            aligned.append(
                {
                    "id": 0,
                    "type": "equal" if sim >= 0.99 else "replace",
                    "sentence1": sentences1[i - 1],
                    "sentence2": sentences2[j - 1],
                    "has_diff": sim < 0.99,
                    "char_diff": char_diff,
                    "index1": offset1 + i - 1,
                    "index2": offset2 + j - 1,
                }
            )
            i -= 1
            j -= 1

        elif current_path == "delete" and i > 0:
            # 删除（句子1独有）
            aligned.append(
                {
                    "id": 0,
                    "type": "delete",
                    "sentence1": sentences1[i - 1],
                    "sentence2": "",
                    "has_diff": True,
                    "char_diff": None,
                    "index1": offset1 + i - 1,
                    "index2": None,
                }
            )
            i -= 1

        elif current_path == "insert" and j > 0:
            # 插入（句子2独有）
            aligned.append(
                {
                    "id": 0,
                    "type": "insert",
                    "sentence1": "",
                    "sentence2": sentences2[j - 1],
                    "has_diff": True,
                    "char_diff": None,
                    "index1": None,
                    "index2": offset2 + j - 1,
                }
            )
            j -= 1

        else:
            # 路径未定义或边界异常，尝试回退
            print(f"[警告] 异常路径: path[{i}][{j}]={current_path}")
            if i > 0 and j > 0:
                # 默认匹配
                aligned.append(
                    {
                        "id": 0,
                        "type": "replace",
                        "sentence1": sentences1[i - 1],
                        "sentence2": sentences2[j - 1],
                        "has_diff": True,
                        "char_diff": compute_char_diff(
                            sentences1[i - 1], sentences2[j - 1]
                        ),
                        "index1": offset1 + i - 1,
                        "index2": offset2 + j - 1,
                    }
                )
                i -= 1
                j -= 1
            elif i > 0:
                aligned.append(
                    {
                        "id": 0,
                        "type": "delete",
                        "sentence1": sentences1[i - 1],
                        "sentence2": "",
                        "has_diff": True,
                        "char_diff": None,
                        "index1": offset1 + i - 1,
                        "index2": None,
                    }
                )
                i -= 1
            elif j > 0:
                aligned.append(
                    {
                        "id": 0,
                        "type": "insert",
                        "sentence1": "",
                        "sentence2": sentences2[j - 1],
                        "has_diff": True,
                        "char_diff": None,
                        "index1": None,
                        "index2": offset2 + j - 1,
                    }
                )
                j -= 1
            else:
                break

    # 反转（回溯是从后往前）
    aligned.reverse()
    return aligned


def align_sentences(
    text1: str,
    text2: str,
    split_sentences_func: Callable[[str], List[str]],
    find_anchors_func: Callable[[List[str], List[str], float], List[tuple]]
) -> List[Dict]:
    """
    对齐两个文本的句子（锚点对齐 + 动态规划全局最优）

    Args:
        text1: 版本1文本
        text2: 版本2文本
        split_sentences_func: 分句函数
        find_anchors_func: 查找锚点函数

    Returns:
        对齐后的句子组列表
    """
    # 1. 分句
    sentences1 = split_sentences_func(text1)
    sentences2 = split_sentences_func(text2)

    print(f"[句子对齐] 版本1: {len(sentences1)}句, 版本2: {len(sentences2)}句")

    # 2. 查找锚点句子（高置信度匹配，相似度>0.85）
    # 注意：使用纯文本相似度，标点不同的句子也能成为锚点
    anchors = find_anchors_func(
        sentences1, sentences2, 0.85
    )
    print(f"[句子对齐] 找到 {len(anchors)} 个锚点")

    # 3. 基于锚点分段，分别进行动态规划对齐
    aligned_groups = []
    prev_i1, prev_i2 = 0, 0

    for anchor_i1, anchor_i2, anchor_sim in anchors:
        # 对齐锚点之前的分段
        if anchor_i1 > prev_i1 or anchor_i2 > prev_i2:
            segment_aligned = dp_align_segment(
                sentences1[prev_i1:anchor_i1],
                sentences2[prev_i2:anchor_i2],
                prev_i1,
                prev_i2,
            )
            aligned_groups.extend(segment_aligned)

        # 添加锚点本身（完美匹配）
        char_diff = compute_char_diff(
            sentences1[anchor_i1], sentences2[anchor_i2]
        )
        aligned_groups.append(
            {
                "id": len(aligned_groups) + 1,
                "type": "equal" if anchor_sim >= 0.99 else "replace",
                "sentence1": sentences1[anchor_i1],
                "sentence2": sentences2[anchor_i2],
                "has_diff": anchor_sim < 0.99,
                "char_diff": char_diff,
                "index1": anchor_i1,
                "index2": anchor_i2,
            }
        )

        prev_i1 = anchor_i1 + 1
        prev_i2 = anchor_i2 + 1

    # 4. 处理最后一段（锚点之后的部分）
    if prev_i1 < len(sentences1) or prev_i2 < len(sentences2):
        segment_aligned = dp_align_segment(
            sentences1[prev_i1:], sentences2[prev_i2:], prev_i1, prev_i2
        )
        aligned_groups.extend(segment_aligned)

    # 5. 重新分配连续的ID（从1开始）
    for idx, group in enumerate(aligned_groups):
        group["id"] = idx + 1

    print(f"[句子对齐] 生成 {len(aligned_groups)} 个对齐组")

    # 调试：打印前5个ID
    if len(aligned_groups) > 0:
        sample_ids = [g["id"] for g in aligned_groups[:5]]
        print(f"[句子对齐] 前5个对齐组的ID: {sample_ids}")

    return aligned_groups
