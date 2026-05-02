"""
统一的标点符号集合与清洗工具。

目的：
- 后端多个模块（标点分析/纯文本一致性检查/标点对比）使用同一套标点集合，避免结果不一致。
"""

from __future__ import annotations


PUNCTUATION_CHARS = (
    # 句末和句内点号
    "。，、；：？！"
    # 弯引号/低引号等
    "\u201c\u201d\u2018\u2019\u201a\u201e"
    # ASCII 直引号
    "\"'"
    # 中文括号、角引号、书名号等
    "（）《》【】「」『』〈〉〔〕〖〗"
    # 半角标点
    ":;,?!"
    # 全角引号
    "＂＇"
    # 竖排引号等
    "〝〞〟｢｣"
    # 书名号式引号
    "‹›«»"
    # 佛典/古籍常见符号
    "·…—"
)

PUNCTUATION_SET = set(PUNCTUATION_CHARS)


def strip_punctuation_and_whitespace(text: str) -> str:
    """移除标点与空白字符，用于“纯文本一致性”判断。"""
    return "".join(
        c for c in text
        if c not in PUNCTUATION_SET and not c.isspace()
    )

