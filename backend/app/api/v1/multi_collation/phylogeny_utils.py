"""
版本谱系分析工具函数
从 multi_collation.py 中提取
"""
from typing import List, Dict, Any, Optional

from app.services.phylogeny_service import phylogeny_service
from app.services.canon_locations import CanonLocationService


def enrich_phylogeny_with_locations(
    phylogeny_data: Dict[str, Any],
    canon_locations_override: Optional[Dict[str, Any]] = None,
    base_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    丰富谱系数据的地理位置信息

    Args:
        phylogeny_data: 谱系分析数据
        canon_locations_override: 用户手工补充的地理位置信息
        base_name: 底本名称

    Returns:
        带有地理位置信息的谱系数据
    """
    # 兼容历史项目：早期版本把底本在 similarity_matrix.names[0] 写死为 "底本"
    try:
        bn = (base_name or "").strip()
        if bn and bn != "底本":
            sm = phylogeny_data.get("similarity_matrix", {}) if isinstance(phylogeny_data, dict) else {}
            names = sm.get("names", [])
            if isinstance(names, list) and names and names[0] == "底本":
                names[0] = bn
                sm["names"] = names
                systems = sm.get("systems")
                if isinstance(systems, dict) and "底本" in systems and bn not in systems:
                    systems[bn] = systems.pop("底本")
                phylogeny_data["similarity_matrix"] = sm

            tree = phylogeny_data.get("tree")
            if isinstance(tree, dict) and tree.get("name") == "底本":
                tree["name"] = bn
                phylogeny_data["tree"] = tree
    except Exception:
        pass

    enriched = CanonLocationService.enrich_phylogeny_data_with_locations(phylogeny_data)
    merged = dict(enriched.get("canon_locations", {}) or {})
    if canon_locations_override:
        # 兼容历史 override：用户可能保存了 key="底本"
        try:
            bn = (base_name or "").strip()
            if bn and bn != "底本" and "底本" in canon_locations_override and bn not in canon_locations_override:
                canon_locations_override = dict(canon_locations_override)
                canon_locations_override[bn] = canon_locations_override.get("底本")
        except Exception:
            pass
        merged.update(canon_locations_override)
    enriched["canon_locations"] = merged
    return enriched


def calculate_phylogeny_analysis(
    base_text: str,
    base_name: str,
    collation_results: List[Dict],
    collation_texts: Optional[Dict[str, str]] = None,
    custom_systems: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    使用专业版本谱系分析服务进行完整分析

    Args:
        base_text: 底本文本
        base_name: 底本名称
        collation_results: 各校本的对比结果
        collation_texts: 各校本文本 {校本名: 文本内容}（可选）
        custom_systems: 用户自定义版本系统归属（可选）

    Returns:
        完整的版本谱系分析结果，包含：
        - similarity_matrix: 完整相似度矩阵（所有版本两两对比）
        - shared_errors: 共同讹误分析
        - tree: UPGMA 谱系树
        - conclusions: 分析结论
    """
    return phylogeny_service.analyze_phylogeny(
        base_text=base_text,
        base_name=base_name,
        collation_results=collation_results,
        collation_texts=collation_texts,
        custom_systems=custom_systems,
    )
