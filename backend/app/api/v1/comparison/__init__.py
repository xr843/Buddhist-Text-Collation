"""
文本对比API路由模块

此模块已重构为子模块结构：
- models.py: Pydantic模型定义
- compare_routes.py: 基础对比路由
- file_compare_routes.py: 文件上传对比路由
- export_routes.py: 导出功能路由
- two_version_routes.py: 两版本对勘项目管理路由
- punctuation_routes.py: 标点版本对比项目管理路由
- definitive_generator.py: 标点定本生成工具
"""
from fastapi import APIRouter

# 导入子路由
from .compare_routes import router as compare_router
from .file_compare_routes import router as file_compare_router
from .export_routes import router as export_router
from .two_version_routes import router as two_version_router
from .punctuation_routes import router as punctuation_router

# 导入模型（供外部使用）
from .models import (
    ProjectUpdateRequest,
    ComparisonRequest,
    ComparisonResponse,
    PunctuationComparisonRequest,
    PunctuationDecisionItem,
    PunctuationDecisionsRequest,
    ExportCollationNotesRequest,
)

# 导入工具函数
from .definitive_generator import (
    generate_punctuation_definitive_text,
    find_actual_position,
    find_punct_around_position,
    PUNCT_MARKS,
)

# 创建主路由并合并子路由
router = APIRouter()

# 合并所有子路由
router.include_router(compare_router)
router.include_router(file_compare_router)
router.include_router(export_router)
router.include_router(two_version_router)
router.include_router(punctuation_router)


# 导出所有公共API
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
    'find_actual_position',
    'find_punct_around_position',
    'PUNCT_MARKS',
]
