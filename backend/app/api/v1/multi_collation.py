"""
一底多校API路由 - 含异文汇校表和版本谱系分析
支持项目持久化存储（保存/加载/列表/删除/追加校本）

此模块已重构为子模块结构，详见 multi_collation/ 目录：
- multi_collation/models.py: Pydantic 模型定义
- multi_collation/variant_table.py: 异文汇校表生成
- multi_collation/phylogeny_utils.py: 版本谱系分析工具
- multi_collation/compare_routes.py: 一底多校对比核心路由
- multi_collation/project_routes.py: 项目管理路由
- multi_collation/collation_routes.py: 校本管理路由
- multi_collation/decision_routes.py: 校勘判取路由
- multi_collation/__init__.py: 模块组装与路由合并

此文件保留以保持向后兼容性。
"""

# 从重构后的子模块导入所有内容
from app.api.v1.multi_collation import (
    router,
    # 工具函数
    generate_variant_table,
    enrich_phylogeny_with_locations,
    calculate_phylogeny_analysis,
    # 模型
    ProjectUpdateRequest,
    ProjectListResponse,
    CollationDecisionItem,
    SaveDecisionsRequest,
    GenerateDefinitiveTextRequest,
    RemoveCollationsRequest,
    CanonLocationItem,
    UpdateCanonLocationsRequest,
)

# 为了保持向后兼容，也导出内部函数的别名
_enrich_phylogeny_with_locations = enrich_phylogeny_with_locations

__all__ = [
    'router',
    'generate_variant_table',
    'enrich_phylogeny_with_locations',
    '_enrich_phylogeny_with_locations',
    'calculate_phylogeny_analysis',
    'ProjectUpdateRequest',
    'ProjectListResponse',
    'CollationDecisionItem',
    'SaveDecisionsRequest',
    'GenerateDefinitiveTextRequest',
    'RemoveCollationsRequest',
    'CanonLocationItem',
    'UpdateCanonLocationsRequest',
]
