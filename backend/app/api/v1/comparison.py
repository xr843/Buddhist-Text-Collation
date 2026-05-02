"""
文本对比API路由 - MVP版本
支持项目持久化存储（两版本对勘、标点版本对比）

此模块已重构为子模块结构，详见 comparison/ 目录：
- comparison/models.py: Pydantic模型定义
- comparison/compare_routes.py: 基础对比路由
- comparison/file_compare_routes.py: 文件上传对比路由
- comparison/export_routes.py: 导出功能路由
- comparison/two_version_routes.py: 两版本对勘项目管理路由
- comparison/punctuation_routes.py: 标点版本对比项目管理路由
- comparison/definitive_generator.py: 标点定本生成工具
- comparison/__init__.py: 模块组装与路由合并

此文件保留以保持向后兼容性。
"""

# 从重构后的子模块导入所有内容
from app.api.v1.comparison import (
    router,
    # 模型
    ProjectUpdateRequest,
    ComparisonRequest,
    ComparisonResponse,
    PunctuationComparisonRequest,
    PunctuationDecisionItem,
    PunctuationDecisionsRequest,
    ExportCollationNotesRequest,
    # 工具函数
    generate_punctuation_definitive_text,
    find_actual_position,
    find_punct_around_position,
    PUNCT_MARKS,
)

# 为了保持向后兼容，保留内部函数的别名
_generate_punctuation_definitive_text = generate_punctuation_definitive_text

__all__ = [
    'router',
    # 模型
    'ProjectUpdateRequest',
    'ComparisonRequest',
    'ComparisonResponse',
    'PunctuationComparisonRequest',
    'PunctuationDecisionItem',
    'PunctuationDecisionsRequest',
    'ExportCollationNotesRequest',
    # 工具函数
    'generate_punctuation_definitive_text',
    '_generate_punctuation_definitive_text',
    'find_actual_position',
    'find_punct_around_position',
    'PUNCT_MARKS',
]
