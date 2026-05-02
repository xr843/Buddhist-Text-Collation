"""
一底多校API路由模块

此模块已重构为子模块结构：
- models.py: Pydantic 模型定义
- variant_table.py: 异文汇校表生成
- phylogeny_utils.py: 版本谱系分析工具
- compare_routes.py: 一底多校对比核心路由
- project_routes.py: 项目管理路由
- collation_routes.py: 校本管理路由（追加/移除）
- decision_routes.py: 校勘判取路由
- note_routes.py: 校勘记生成与导出路由
"""
from fastapi import APIRouter

# 导入子路由
from .compare_routes import router as compare_router
from .project_routes import router as project_router
from .collation_routes import router as collation_router
from .decision_routes import router as decision_router
from .note_routes import router as note_router

# 导入工具函数（供外部使用）
from .variant_table import generate_variant_table
from .phylogeny_utils import enrich_phylogeny_with_locations, calculate_phylogeny_analysis
from .models import (
    ProjectUpdateRequest,
    ProjectListResponse,
    CollationDecisionItem,
    SaveDecisionsRequest,
    GenerateDefinitiveTextRequest,
    RemoveCollationsRequest,
    CanonLocationItem,
    UpdateCanonLocationsRequest,
)

# 创建主路由并合并子路由
router = APIRouter()

# 合并所有子路由
router.include_router(compare_router)
router.include_router(project_router)
router.include_router(collation_router)
router.include_router(decision_router)
router.include_router(note_router)


# 导出所有公共API
__all__ = [
    'router',
    # 工具函数
    'generate_variant_table',
    'enrich_phylogeny_with_locations',
    'calculate_phylogeny_analysis',
    # 模型
    'ProjectUpdateRequest',
    'ProjectListResponse',
    'CollationDecisionItem',
    'SaveDecisionsRequest',
    'GenerateDefinitiveTextRequest',
    'RemoveCollationsRequest',
    'CanonLocationItem',
    'UpdateCanonLocationsRequest',
]
