"""
版本源流推断服务

基于版本谱系数据推断版本传承关系，生成有向无环图(DAG)

推断规则：
1. 时间约束：年代晚的版本不能是年代早的版本的源头
2. 共同讹误：共同讹误越多，传承关系越近
3. 系统归属：同系版本优先考虑传承关系
4. 祖本优先：已知祖本（开宝藏、契丹藏、崇宁藏）作为起点
"""
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


# 已知祖本（各系源头）
KNOWN_ANCESTORS = {
    "开宝藏": {"year": 971, "system": "中系", "is_root": True},
    "开宝": {"year": 971, "system": "中系", "is_root": True},
    "契丹藏": {"year": 1031, "system": "北系", "is_root": True},
    "契丹": {"year": 1031, "system": "北系", "is_root": True},
    "崇宁藏": {"year": 1104, "system": "南系", "is_root": True},
    "崇寧藏": {"year": 1104, "system": "南系", "is_root": True},
    "崇寧": {"year": 1104, "system": "南系", "is_root": True},
}

# 已知传承链（用于验证和补充推断）
KNOWN_LINEAGE_CHAINS = {
    "中系": [
        ("开宝藏", "高丽初雕"),
        ("高丽初雕", "高丽再雕"),
        ("高丽再雕", "大正藏"),
        ("开宝藏", "赵城金藏"),
        ("赵城金藏", "中华藏"),
    ],
    "南系": [
        ("崇宁藏", "思溪藏"),
        ("思溪藏", "碛砂藏"),
        ("碛砂藏", "普宁藏"),
        ("碛砂藏", "嘉兴藏"),
        ("嘉兴藏", "龙藏"),
    ],
    "北系": [
        ("契丹藏", "房山石经"),
    ],
}

# 置信度阈值
CONFIDENCE_THRESHOLD = 30  # 降低阈值以显示更多可能的关系


class VersionLineageService:
    """版本源流推断服务"""

    def __init__(self):
        self.known_ancestors = KNOWN_ANCESTORS.copy()
        self.known_chains = KNOWN_LINEAGE_CHAINS.copy()

    def infer_lineage(self, phylogeny_data: Dict) -> Dict:
        """
        基于版本谱系数据推断版本源流

        Args:
            phylogeny_data: 版本谱系分析数据
                {
                    'similarity_matrix': {names, matrix, systems},
                    'shared_errors': {names, matrix, details, ...},
                    'canon_locations': {版本名: {year, system, ...}},
                    'conclusions': [...]
                }

        Returns:
            源流图数据
            {
                'nodes': [{id, name, year, system, ...}],
                'edges': [{source, target, confidence, evidence}],
                'conclusions': [分析结论]
            }
        """
        # 提取基础数据
        similarity_matrix = phylogeny_data.get('similarity_matrix', {})
        shared_errors = phylogeny_data.get('shared_errors', {})
        canon_locations = phylogeny_data.get('canon_locations', {})

        version_names = similarity_matrix.get('names', [])
        systems = similarity_matrix.get('systems', {})
        matrix = similarity_matrix.get('matrix', [])

        print(f"[版本源流] 版本数量: {len(version_names)}")
        print(f"[版本源流] canon_locations 数量: {len(canon_locations)}")

        if not version_names:
            print("[版本源流] 没有版本名称，返回空数据")
            return {'nodes': [], 'edges': [], 'conclusions': []}

        # 1. 提取年代信息
        years = self._extract_years(version_names, canon_locations)
        print(f"[版本源流] 年代识别结果: {years}")

        # 2. 推断传承边
        edges = self._infer_edges(
            version_names, matrix, shared_errors, years, systems
        )
        print(f"[版本源流] 推断出 {len(edges)} 条传承边")

        # 3. 简化图（移除传递边）
        edges = self._remove_transitive_edges(edges, version_names)

        # 4. 构建节点数据
        nodes = self._build_nodes(version_names, years, systems, canon_locations)

        # 5. 生成分析结论
        conclusions = self._generate_lineage_conclusions(nodes, edges, systems)

        return {
            'nodes': nodes,
            'edges': edges,
            'conclusions': conclusions,
        }

    def _extract_years(
        self,
        version_names: List[str],
        canon_locations: Dict
    ) -> Dict[str, int]:
        """
        提取各版本的年代信息

        优先级：
        1. canon_locations 中的年代
        2. KNOWN_ANCESTORS 中的年代
        3. 默认估算
        """
        years = {}

        for name in version_names:
            year = None

            # 从 canon_locations 获取
            if name in canon_locations:
                year = canon_locations[name].get('year')

            # 从已知祖本获取
            if year is None:
                for ancestor_key, info in self.known_ancestors.items():
                    if ancestor_key in name:
                        year = info['year']
                        break

            # 默认估算（基于关键词）
            if year is None:
                year = self._estimate_year(name)

            years[name] = year

        return years

    def _estimate_year(self, version_name: str) -> int:
        """根据关键词估算版本年代"""
        # 关键词-年代映射
        keyword_years = {
            '开宝': 971, '高丽初': 1011, '高丽再': 1236, '高麗': 1236,
            '赵城': 1148, '趙城': 1148, '金藏': 1148,
            '大正': 1924, '中华': 1994, '中華': 1994,
            '崇宁': 1104, '崇寧': 1104, '毗卢': 1148, '毘盧': 1148,
            '思溪': 1127, '碛砂': 1231, '磧砂': 1231,
            '普宁': 1280, '普寧': 1280,
            '洪武': 1372, '永乐': 1410, '永樂': 1410,
            '嘉兴': 1589, '嘉興': 1589, '龙藏': 1735, '龍藏': 1735,
            '乾隆': 1735, '频伽': 1909, '頻伽': 1909,
            '契丹': 1031, '房山': 605,
            'CBETA': 1998, '缩刻': 1880, '縮刻': 1880,
        }

        for keyword, year in keyword_years.items():
            if keyword in version_name:
                return year

        # 默认返回现代
        return 2000

    def _infer_edges(
        self,
        version_names: List[str],
        similarity_matrix: List[List[float]],
        shared_errors: Dict,
        years: Dict[str, int],
        systems: Dict[str, str]
    ) -> List[Dict]:
        """
        推断版本传承边

        基于多因素计算传承置信度：
        - 相似度
        - 共同讹误
        - 系统一致性
        - 祖本关系
        """
        edges = []
        n = len(version_names)

        # 获取共同讹误数据
        # 注意：shared_errors.matrix 只包含校本，不包含底本
        # 而 similarity_matrix 包含所有版本（底本+校本）
        error_matrix = shared_errors.get('matrix', [])
        error_names = shared_errors.get('names', [])
        error_details = shared_errors.get('details', {})

        # 构建名称到索引的映射（用于共同讹误矩阵）
        error_name_to_idx = {name: idx for idx, name in enumerate(error_names)}

        print(f"[版本源流] similarity_matrix 版本数: {n}")
        print(f"[版本源流] error_matrix 版本数: {len(error_names)}")
        print(f"[版本源流] error_matrix 尺寸: {len(error_matrix)}x{len(error_matrix[0]) if error_matrix else 0}")

        for i in range(n):
            for j in range(i + 1, n):
                v1, v2 = version_names[i], version_names[j]
                year1 = years.get(v1, 2000)
                year2 = years.get(v2, 2000)

                # 确定方向（年代早→晚）
                if year1 < year2:
                    source, target = v1, v2
                    source_idx, target_idx = i, j
                elif year1 > year2:
                    source, target = v2, v1
                    source_idx, target_idx = j, i
                else:
                    # 年代相同，按名称顺序（仍然尝试创建关联）
                    source, target = v1, v2
                    source_idx, target_idx = i, j

                # 计算传承置信度
                similarity = similarity_matrix[i][j] if similarity_matrix else 0

                # 通过版本名称查找在 error_matrix 中的正确索引
                # 注意：error_matrix 只包含校本，不包含底本
                error_idx_i = error_name_to_idx.get(v1)
                error_idx_j = error_name_to_idx.get(v2)
                if error_idx_i is not None and error_idx_j is not None and error_matrix:
                    if error_idx_i < len(error_matrix) and error_idx_j < len(error_matrix[error_idx_i]):
                        error_count = error_matrix[error_idx_i][error_idx_j]
                    else:
                        error_count = 0
                else:
                    error_count = 0

                system_v1 = systems.get(v1, '未知')
                system_v2 = systems.get(v2, '未知')
                system_match = (system_v1 == system_v2 and system_v1 != '未知')

                confidence, evidence = self._calculate_lineage_confidence(
                    source, target, similarity, error_count, system_match
                )

                if confidence >= CONFIDENCE_THRESHOLD:
                    # 检查是否为已知传承关系
                    is_known = self._is_known_lineage(source, target)
                    if is_known:
                        confidence = max(confidence, 90)
                        evidence.append("已知传承")

                    edges.append({
                        'source': source,
                        'target': target,
                        'confidence': confidence,
                        'evidence': evidence,
                        'similarity': round(similarity * 100, 1),
                        'shared_errors': error_count,
                        'is_known': is_known,
                    })

        # 按置信度排序
        edges.sort(key=lambda x: x['confidence'], reverse=True)

        return edges

    def _calculate_lineage_confidence(
        self,
        source: str,
        target: str,
        similarity: float,
        error_count: int,
        system_match: bool
    ) -> Tuple[int, List[str]]:
        """
        综合多因素计算传承置信度

        返回: (置信度分数 0-100, 证据列表)
        """
        score = 0
        evidence = []

        # 因素1：相似度（权重30%）
        if similarity > 0.95:
            score += 30
            evidence.append(f"高度相似({similarity*100:.1f}%)")
        elif similarity > 0.90:
            score += 20
            evidence.append(f"相似({similarity*100:.1f}%)")
        elif similarity > 0.85:
            score += 10

        # 因素2：共同讹误（权重40%）
        if error_count > 10:
            score += 40
            evidence.append(f"共同讹误{error_count}处")
        elif error_count > 5:
            score += 25
            evidence.append(f"共同讹误{error_count}处")
        elif error_count > 2:
            score += 15
            evidence.append(f"共同讹误{error_count}处")
        elif error_count > 0:
            score += 5

        # 因素3：系统一致（权重20%）
        if system_match:
            score += 20
            evidence.append("同系")

        # 因素4：祖本关系（权重10%）
        is_ancestor = any(key in source for key in self.known_ancestors.keys())
        if is_ancestor:
            score += 10
            evidence.append("祖本")

        return score, evidence

    def _is_known_lineage(self, source: str, target: str) -> bool:
        """检查是否为已知传承关系"""
        for system, chains in self.known_chains.items():
            for src, tgt in chains:
                if src in source and tgt in target:
                    return True
        return False

    def _remove_transitive_edges(
        self,
        edges: List[Dict],
        version_names: List[str]
    ) -> List[Dict]:
        """
        移除传递边以简化图

        如果 A→B 和 B→C 都存在，且 A→C 也存在，则移除 A→C
        保留更直接的传承路径
        """
        if len(edges) <= 2:
            return edges

        # 构建邻接表
        adjacency = defaultdict(set)
        for edge in edges:
            adjacency[edge['source']].add(edge['target'])

        # 找出可传递到达的边
        transitive_edges = set()

        for edge in edges:
            source, target = edge['source'], edge['target']

            # 检查是否存在中间节点
            for mid in adjacency[source]:
                if mid != target and target in adjacency[mid]:
                    # source → mid → target 存在，source → target 是传递边
                    transitive_edges.add((source, target))
                    break

        # 移除传递边（但保留已知传承和高置信度的边）
        filtered_edges = []
        for edge in edges:
            key = (edge['source'], edge['target'])
            if key in transitive_edges:
                # 如果是已知传承或置信度很高，仍然保留
                if edge.get('is_known') or edge['confidence'] >= 80:
                    filtered_edges.append(edge)
            else:
                filtered_edges.append(edge)

        return filtered_edges

    def _build_nodes(
        self,
        version_names: List[str],
        years: Dict[str, int],
        systems: Dict[str, str],
        canon_locations: Dict
    ) -> List[Dict]:
        """构建节点数据"""
        nodes = []

        for name in version_names:
            year = years.get(name, 2000)
            system = systems.get(name, '未知')

            node = {
                'id': name,
                'name': name,
                'year': year,
                'system': system,
            }

            # 添加位置信息
            if name in canon_locations:
                loc = canon_locations[name]
                node['city'] = loc.get('city', '')
                node['period'] = loc.get('period', '')
                node['lat'] = loc.get('lat')
                node['lng'] = loc.get('lng')

            # 标记祖本
            is_ancestor = any(key in name for key in self.known_ancestors.keys())
            node['is_ancestor'] = is_ancestor

            nodes.append(node)

        # 按年代排序
        nodes.sort(key=lambda x: x['year'])

        return nodes

    def _generate_lineage_conclusions(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        systems: Dict[str, str]
    ) -> List[str]:
        """生成源流分析结论"""
        conclusions = []

        # 按系统分组
        system_nodes = defaultdict(list)
        for node in nodes:
            system_nodes[node['system']].append(node)

        # 构建传承链
        for system, sys_nodes in system_nodes.items():
            if len(sys_nodes) < 2:
                continue

            # 按年代排序
            sorted_nodes = sorted(sys_nodes, key=lambda x: x['year'])

            # 找出该系统的传承边
            sys_edges = [e for e in edges
                        if systems.get(e['source']) == system
                        and systems.get(e['target']) == system]

            if sys_edges:
                # 构建传承链描述
                chain_parts = []
                for node in sorted_nodes:
                    chain_parts.append(f"{node['name']}({node['year']})")

                chain_str = " → ".join(chain_parts)
                conclusions.append(f"【{system}传承链】{chain_str}")

                # 找出主要证据
                max_edge = max(sys_edges, key=lambda x: x['confidence'])
                if max_edge['evidence']:
                    evidence_str = "、".join(max_edge['evidence'])
                    conclusions.append(f"  证据：{evidence_str}")

        # 跨系关联分析
        cross_system_edges = [e for e in edges
                            if systems.get(e['source']) != systems.get(e['target'])]
        if cross_system_edges:
            for edge in cross_system_edges[:3]:  # 最多展示3条
                src_sys = systems.get(edge['source'], '未知')
                tgt_sys = systems.get(edge['target'], '未知')
                conclusions.append(
                    f"【跨系关联】{edge['source']} ({src_sys}) → {edge['target']} ({tgt_sys})"
                )

        return conclusions

    def manual_adjust(
        self,
        lineage_data: Dict,
        operation: Dict
    ) -> Dict:
        """
        支持用户手动调整推断结果

        Args:
            lineage_data: 当前源流数据
            operation: 调整操作
                {
                    'action': 'add' | 'remove',
                    'source': str,
                    'target': str,
                    'evidence': str (可选，仅 add 时使用)
                }

        Returns:
            调整后的源流数据
        """
        edges = lineage_data.get('edges', [])
        action = operation.get('action')
        source = operation.get('source')
        target = operation.get('target')

        if action == 'add':
            # 添加新边
            new_edge = {
                'source': source,
                'target': target,
                'confidence': 100,  # 用户添加的视为确定
                'evidence': [operation.get('evidence', '用户添加')],
                'is_manual': True,
            }
            edges.append(new_edge)

        elif action == 'remove':
            # 删除边
            edges = [e for e in edges
                    if not (e['source'] == source and e['target'] == target)]

        lineage_data['edges'] = edges
        return lineage_data


# 全局实例
lineage_service = VersionLineageService()
