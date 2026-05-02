"""
版本谱系分析服务 - 专业级藏经版本学分析工具

功能：
1. 完整的相似度矩阵计算（所有版本两两对比）
2. 共同讹误分析（严格定义：同位置、同内容）
3. 版本系统识别与用户自定义
4. UPGMA层次聚类生成谱系树
"""
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re


# ==================== 版本系统映射 ====================
# 汉文大藏经三系分类（团队标准）
#
# 汉文刻本大藏经三大系统：
# 1. 中系 - 以《开宝藏》为祖本，包括高丽藏、赵城金藏、大正藏、中华藏等
# 2. 南系 - 起源于两宋福建/江浙民间募刻，包括崇宁藏、思溪藏、碛砂藏、嘉兴藏等
# 3. 北系 - 辽朝（契丹）独立编纂体系，以学术严谨著称，实物稀少

# 预设的版本系统映射（团队标准分类）
DEFAULT_VERSION_SYSTEM_MAP = {
    # ========== 中系 ==========
    # 以《开宝藏》为祖本的版本系统
    #
    # 开宝藏系
    "开宝": "中系",
    "蜀版": "中系",
    #
    # 高丽藏（初雕、再雕）
    "高丽": "中系",
    "高麗": "中系",
    "丽藏": "中系",
    "海印": "中系",
    "初雕": "中系",
    "再雕": "中系",
    "東國大學": "中系",
    "奎章閣": "中系",
    "高麗研究所": "中系",
    "西南師大": "中系",
    #
    # 赵城金藏
    "赵城": "中系",
    "趙城": "中系",
    "金藏": "中系",
    "赵城金藏": "中系",
    "广胜寺": "中系",
    "國圖": "中系",
    #
    # 大正藏
    "大正": "中系",
    "大正藏": "中系",
    "佛陀基金會": "中系",
    #
    # 中华藏
    "中华": "中系",
    "中華": "中系",
    "中华藏": "中系",
    "中華藏": "中系",
    "中华大藏经": "中系",
    "中華書局": "中系",
    #
    # 缩刻藏
    "缩刻": "中系",
    "縮刻": "中系",
    "弘教書院": "中系",

    # ========== 南系 ==========
    # 起源于两宋福建/江浙民间募刻的版本系统
    #
    # --- 福州系（崇宁藏/毗卢藏） ---
    "福州": "南系",
    "东禅": "南系",
    "东禅寺": "南系",
    "崇宁": "南系",
    "崇寧": "南系",
    "开元寺": "南系",
    "毗卢": "南系",
    "毘盧": "南系",
    "宮內廳": "南系",
    #
    # --- 思溪藏 ---
    "思溪": "南系",
    "圆觉": "南系",
    "资福": "南系",
    "湖州": "南系",
    "增上寺": "南系",
    #
    # --- 碛砂藏 ---
    "碛砂": "南系",
    "磧砂": "南系",
    "延圣": "南系",
    "綫裝書局": "南系",
    "线装书局": "南系",
    #
    # --- 普宁藏 ---
    "普宁": "南系",
    "普寧": "南系",
    "白云宗": "南系",
    #
    # --- 洪武南藏 ---
    "洪武": "南系",
    "洪武南": "南系",
    "川佛協": "南系",
    #
    # --- 永乐藏（南藏、北藏均属南系） ---
    "永乐": "南系",
    "永樂": "南系",
    "永乐南": "南系",
    "永乐北": "南系",
    "永樂南": "南系",
    "永樂北": "南系",
    "南藏": "南系",
    "北藏": "南系",
    "魯圖": "南系",
    #
    # --- 嘉兴藏 ---
    "嘉兴": "南系",
    "嘉興": "南系",
    "径山": "南系",
    "東京大學": "南系",
    #
    # --- 乾隆藏/龙藏 ---
    "龙藏": "南系",
    "清藏": "南系",
    "乾隆": "南系",
    "台北傳正": "南系",
    #
    # --- 频伽藏 ---
    "频伽": "南系",
    "頻伽": "南系",
    "频伽精舍": "南系",
    #
    # --- 卍字正藏 ---
    "卍续": "南系",
    "卍正": "南系",
    "卍字": "南系",
    "卍": "南系",
    "新文豐": "南系",

    # ========== 北系 ==========
    # 辽朝（契丹）独立编纂体系
    "契丹": "北系",
    "辽藏": "北系",
    "辽": "北系",
    "房山": "北系",
    "房山石经": "北系",
    "云居寺": "北系",

    # ========== 近现代藏经 ==========
    "CBETA": "近现代藏经",
    "电子": "近现代藏经",
}


class PhylogenyAnalysisService:
    """版本谱系分析服务"""

    def __init__(self):
        self.version_system_map = DEFAULT_VERSION_SYSTEM_MAP.copy()

    # ==================== 版本系统识别 ====================

    def identify_version_system(self, version_name: str) -> Optional[str]:
        """
        识别版本所属系统

        Args:
            version_name: 版本名称

        Returns:
            系统名称，如 "中系"、"南系"、"北系"，未识别则返回 None
        """
        # 遍历映射表，检查版本名是否包含关键词
        for keyword, system in self.version_system_map.items():
            if keyword in version_name:
                return system
        return None

    def update_version_system_map(self, custom_map: Dict[str, str]):
        """
        更新版本系统映射（用户自定义）

        Args:
            custom_map: 用户自定义的版本-系统映射
        """
        self.version_system_map.update(custom_map)

    def get_all_systems(self, version_names: List[str]) -> Dict[str, str]:
        """
        获取所有版本的系统归属

        Args:
            version_names: 版本名称列表

        Returns:
            {版本名: 系统名} 映射
        """
        result = {}
        for name in version_names:
            system = self.identify_version_system(name)
            result[name] = system or "未知"
        return result

    # ==================== 完整相似度矩阵计算 ====================

    def calculate_full_similarity_matrix(
        self,
        base_text: str,
        base_name: str,
        collation_results: List[Dict],
        collation_texts: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        计算完整的相似度矩阵（所有版本两两对比）

        Args:
            base_text: 底本文本
            collation_results: 各校本的对比结果（含与底本的相似度）
            collation_texts: 各校本文本 {校本名: 文本内容}

        Returns:
            完整的相似度矩阵数据
        """
        from difflib import SequenceMatcher

        base_display_name = (base_name or "").strip() or "底本"
        collation_names = [c["collation_name"] for c in collation_results]
        # 避免与校本重名导致矩阵/字典覆盖
        if base_display_name in collation_names:
            base_display_name = f"{base_display_name}（底本）"

        names = [base_display_name] + collation_names
        n = len(names)

        # 准备所有文本
        texts = {base_display_name: base_text}
        for coll in collation_results:
            coll_name = coll["collation_name"]
            if collation_texts and coll_name in collation_texts:
                texts[coll_name] = collation_texts[coll_name]
            else:
                # 从 side_by_side 数据中提取校本文本
                coll_result = coll.get("result")
                if coll_result:
                    side_by_side = coll_result.get("side_by_side", {})
                    if side_by_side and "text2" in side_by_side:
                        texts[coll_name] = side_by_side["text2"]
                    else:
                        texts[coll_name] = None
                else:
                    texts[coll_name] = None

        # 初始化矩阵
        matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        # 填充底本与各校本的相似度（已有）
        for i, coll in enumerate(collation_results):
            coll_result = coll.get("result")
            similarity = coll_result.get("similarity", 0) if coll_result else 0
            matrix[0][i + 1] = similarity
            matrix[i + 1][0] = similarity

        # 计算校本之间的真实相似度
        for i in range(len(collation_results)):
            for j in range(i + 1, len(collation_results)):
                name_i = collation_results[i]["collation_name"]
                name_j = collation_results[j]["collation_name"]

                text_i = texts.get(name_i)
                text_j = texts.get(name_j)

                if text_i and text_j:
                    # 使用 SequenceMatcher 计算真实相似度
                    matcher = SequenceMatcher(None, text_i, text_j, autojunk=False)
                    similarity = matcher.ratio()
                else:
                    # 如果没有文本，使用改进的估算方法
                    result_i = collation_results[i].get("result")
                    result_j = collation_results[j].get("result")
                    sim_i = result_i.get("similarity", 0) if result_i else 0
                    sim_j = result_j.get("similarity", 0) if result_j else 0
                    # 改进的估算：基于三角不等式
                    similarity = max(0, min(1, (sim_i + sim_j) / 2))

                matrix[i + 1][j + 1] = round(similarity, 4)
                matrix[j + 1][i + 1] = round(similarity, 4)

        # 识别版本系统
        systems = self.get_all_systems(names)

        return {
            "names": names,
            "matrix": matrix,
            "systems": systems,
        }

    # ==================== 共同讹误分析 ====================

    def _extract_variants_from_collation(
        self,
        coll_result: Dict,
        categories: List[str] = None
    ) -> Dict[int, Dict]:
        """
        从对勘结果中提取异文信息（讹误、异体字、衍脱等）

        适配 collation_service.py 的实际数据结构：
        - aligned_sentences 是 display_blocks 列表
        - 每个 block 包含 char_diff: {segments1, segments2, diff_type}
        - segment 格式: {text, type, is_punct, category}
        - category: "error"(讹误), "variant"(异体字), "tuowen"(脱文), "yanwen"(衍文)

        Args:
            coll_result: 校勘结果
            categories: 要提取的类别列表，默认 ["error"]
                       支持: "error", "variant", "tuowen", "yanwen"

        Returns:
            {全局位置: {base_char, coll_char, category, diff_type}}
        """
        if categories is None:
            categories = ["error"]

        variants = {}
        global_pos = 0  # 全局位置（基于底本文本）

        aligned = coll_result.get("aligned_sentences", [])

        for block in aligned:
            char_diff = block.get("char_diff")
            sentence1 = block.get("sentence1", "")  # 底本文本

            if char_diff:
                segments1 = char_diff.get("segments1", [])
                segments2 = char_diff.get("segments2", [])

                # ===== 处理 replace 类型（讹误、异体字） =====
                if "error" in categories or "variant" in categories:
                    target_cats = [c for c in categories if c in ("error", "variant")]
                    target_seg1 = []
                    target_seg2 = []

                    pos_in_block = 0
                    for seg in segments1:
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")
                        seg_category = seg.get("category")

                        if seg_type == "replace" and seg_category in target_cats:
                            for i, char in enumerate(seg_text):
                                target_seg1.append((global_pos + pos_in_block + i, char, seg_category))

                        if seg_type in ("equal", "delete", "replace"):
                            pos_in_block += len(seg_text)

                    for seg in segments2:
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")
                        seg_category = seg.get("category")

                        if seg_type == "replace" and seg_category in target_cats:
                            for char in seg_text:
                                target_seg2.append(char)

                    for i, (pos, base_char, category) in enumerate(target_seg1):
                        if i < len(target_seg2):
                            coll_char = target_seg2[i]
                            if base_char != coll_char:
                                variants[pos] = {
                                    "base_char": base_char,
                                    "coll_char": coll_char,
                                    "category": category,
                                    "diff_type": "replace",
                                }

                # ===== 处理 delete 类型（脱文） =====
                if "tuowen" in categories:
                    pos_in_block = 0
                    for seg in segments1:
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")
                        seg_category = seg.get("category")

                        if seg_type == "delete" and seg_category == "tuowen":
                            # 脱文：底本有，校本无
                            for i, char in enumerate(seg_text):
                                pos = global_pos + pos_in_block + i
                                variants[pos] = {
                                    "base_char": char,
                                    "coll_char": "",  # 校本无此字
                                    "category": "tuowen",
                                    "diff_type": "delete",
                                }

                        if seg_type in ("equal", "delete", "replace"):
                            pos_in_block += len(seg_text)

                # ===== 处理 insert 类型（衍文） =====
                if "yanwen" in categories:
                    # 衍文的位置用插入点之前的底本位置表示
                    pos_in_block = 0

                    for seg in segments1:
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")

                        if seg_type in ("equal", "delete", "replace"):
                            pos_in_block += len(seg_text)

                    # 遍历 segments2 找衍文
                    # 用一个简化的方法：按顺序遍历，用累计的底本位置
                    pos_tracker = 0
                    for seg in segments1:
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")
                        if seg_type in ("equal", "delete", "replace"):
                            pos_tracker += len(seg_text)

                    # 简化处理：遍历 segments2 收集衍文
                    base_pos = 0
                    for idx, seg in enumerate(segments1):
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")
                        if seg_type in ("equal", "replace"):
                            base_pos += len(seg_text)
                        elif seg_type == "delete":
                            base_pos += len(seg_text)

                    # 更简单的方法：直接遍历 segments2
                    for seg_idx, seg in enumerate(segments2):
                        seg_type = seg.get("type", "")
                        seg_text = seg.get("text", "")
                        seg_category = seg.get("category")

                        if seg_type == "insert" and seg_category == "yanwen":
                            # 衍文：校本多出的字
                            # 位置用一个特殊标记：负数或带前缀
                            for i, char in enumerate(seg_text):
                                # 用 "insert_" 前缀的位置键
                                pos_key = f"ins_{global_pos}_{seg_idx}_{i}"
                                variants[pos_key] = {
                                    "base_char": "",  # 底本无此字
                                    "coll_char": char,
                                    "category": "yanwen",
                                    "diff_type": "insert",
                                    "insert_pos": global_pos,  # 大致位置
                                }

            global_pos += len(sentence1)

        return variants

    def analyze_shared_errors(
        self,
        collation_results: List[Dict],
    ) -> Dict[str, Any]:
        """
        分析共同异文（三类：讹误、异体字、衍脱）

        共同异文是版本谱系学中判断版本亲缘关系的重要证据：
        - 共同讹误：同位置、同内容的抄写/刻印错误，强烈暗示共同来源
        - 共同异体字：同位置、同字形的异体字选择，可能暗示版本关联
        - 共同衍脱：同位置的衍文/脱文，暗示共同底本错误

        Args:
            collation_results: 各校本的对比结果

        Returns:
            共同异文分析数据，包含三类分析
        """
        names = [c["collation_name"] for c in collation_results]
        n = len(names)

        # 提取各校本的三类异文
        error_maps = {}      # {校本名: {位置: 讹误内容}}
        variant_maps = {}    # {校本名: {位置: 异体字内容}}
        yantuo_maps = {}     # {校本名: {位置: 衍脱内容}}

        for coll in collation_results:
            coll_name = coll["collation_name"]
            coll_result = coll.get("result", {})

            # 提取讹误
            errors = self._extract_variants_from_collation(coll_result, ["error"])
            error_maps[coll_name] = errors

            # 提取异体字
            variants = self._extract_variants_from_collation(coll_result, ["variant"])
            variant_maps[coll_name] = variants

            # 提取衍脱（衍文+脱文）
            yantuo = self._extract_variants_from_collation(coll_result, ["tuowen", "yanwen"])
            yantuo_maps[coll_name] = yantuo

            print(f"[共同异文] {coll_name}: 讹误={len(errors)}处, 异体字={len(variants)}处, 衍脱={len(yantuo)}处")

        # ===== 计算共同讹误 =====
        shared_error_matrix = [[0 for _ in range(n)] for _ in range(n)]
        shared_error_details = {}

        for i in range(n):
            for j in range(i + 1, n):
                name_i, name_j = names[i], names[j]
                errors_i = error_maps.get(name_i, {})
                errors_j = error_maps.get(name_j, {})

                shared = []
                for pos, err_i in errors_i.items():
                    if pos in errors_j:
                        err_j = errors_j[pos]
                        if err_i["coll_char"] == err_j["coll_char"]:
                            shared.append({
                                "position": pos,
                                "base_char": err_i["base_char"],
                                "shared_char": err_i["coll_char"],
                                "category": "error",
                            })

                count = len(shared)
                shared_error_matrix[i][j] = count
                shared_error_matrix[j][i] = count

                if count > 0:
                    shared_error_details[f"{name_i}|{name_j}"] = shared
                    print(f"[共同讹误] {name_i} vs {name_j}: {count} 处")

        # ===== 计算共同异体字 =====
        shared_variant_matrix = [[0 for _ in range(n)] for _ in range(n)]
        shared_variant_details = {}

        for i in range(n):
            for j in range(i + 1, n):
                name_i, name_j = names[i], names[j]
                variants_i = variant_maps.get(name_i, {})
                variants_j = variant_maps.get(name_j, {})

                shared = []
                for pos, var_i in variants_i.items():
                    if pos in variants_j:
                        var_j = variants_j[pos]
                        if var_i["coll_char"] == var_j["coll_char"]:
                            shared.append({
                                "position": pos,
                                "base_char": var_i["base_char"],
                                "shared_char": var_i["coll_char"],
                                "category": "variant",
                            })

                count = len(shared)
                shared_variant_matrix[i][j] = count
                shared_variant_matrix[j][i] = count

                if count > 0:
                    shared_variant_details[f"{name_i}|{name_j}"] = shared
                    print(f"[共同异体字] {name_i} vs {name_j}: {count} 处")

        # ===== 计算共同衍脱 =====
        shared_yantuo_matrix = [[0 for _ in range(n)] for _ in range(n)]
        shared_yantuo_details = {}

        for i in range(n):
            for j in range(i + 1, n):
                name_i, name_j = names[i], names[j]
                yantuo_i = yantuo_maps.get(name_i, {})
                yantuo_j = yantuo_maps.get(name_j, {})

                shared = []
                for pos, yt_i in yantuo_i.items():
                    if pos in yantuo_j:
                        yt_j = yantuo_j[pos]
                        # 共同脱文：同位置都缺少相同的字
                        # 共同衍文：同位置都多出相同的字
                        if yt_i["category"] == yt_j["category"]:
                            if yt_i["category"] == "tuowen":
                                # 共同脱文：底本字相同
                                if yt_i["base_char"] == yt_j["base_char"]:
                                    shared.append({
                                        "position": pos,
                                        "base_char": yt_i["base_char"],
                                        "shared_char": "(脱)",
                                        "category": "tuowen",
                                    })
                            elif yt_i["category"] == "yanwen":
                                # 共同衍文：校本多出的字相同
                                if yt_i["coll_char"] == yt_j["coll_char"]:
                                    shared.append({
                                        "position": pos if isinstance(pos, int) else yt_i.get("insert_pos", 0),
                                        "base_char": "(无)",
                                        "shared_char": yt_i["coll_char"],
                                        "category": "yanwen",
                                    })

                count = len(shared)
                shared_yantuo_matrix[i][j] = count
                shared_yantuo_matrix[j][i] = count

                if count > 0:
                    shared_yantuo_details[f"{name_i}|{name_j}"] = shared
                    print(f"[共同衍脱] {name_i} vs {name_j}: {count} 处")

        # ===== 合并统计 =====
        combined_matrix = [
            [shared_error_matrix[i][j] + shared_variant_matrix[i][j] + shared_yantuo_matrix[i][j]
             for j in range(n)]
            for i in range(n)
        ]

        return {
            "names": names,
            # 共同讹误
            "matrix": shared_error_matrix,
            "details": shared_error_details,
            "total_by_version": {
                name: len(error_maps.get(name, {}))
                for name in names
            },
            # 共同异体字
            "variant_matrix": shared_variant_matrix,
            "variant_details": shared_variant_details,
            "variant_total_by_version": {
                name: len(variant_maps.get(name, {}))
                for name in names
            },
            # 共同衍脱（新增）
            "yantuo_matrix": shared_yantuo_matrix,
            "yantuo_details": shared_yantuo_details,
            "yantuo_total_by_version": {
                name: len(yantuo_maps.get(name, {}))
                for name in names
            },
            # 合并统计
            "combined_matrix": combined_matrix,
            "combined_total_by_version": {
                name: len(error_maps.get(name, {})) + len(variant_maps.get(name, {})) + len(yantuo_maps.get(name, {}))
                for name in names
            },
        }

    # ==================== UPGMA 层次聚类 ====================

    def upgma_clustering(self, similarity_matrix: Dict) -> Dict:
        """
        使用 UPGMA（非加权组平均法）进行层次聚类

        Args:
            similarity_matrix: 相似度矩阵

        Returns:
            谱系树数据
        """
        names = similarity_matrix["names"]
        matrix = similarity_matrix["matrix"]
        systems = similarity_matrix.get("systems", {})
        n = len(names)

        if n <= 1:
            return {"name": names[0] if names else "空", "children": []}

        # 转换为距离矩阵（1 - 相似度）
        dist = [[1 - matrix[i][j] for j in range(n)] for i in range(n)]

        # UPGMA 聚类
        # 初始化：每个版本是一个簇
        clusters = [{
            "name": names[i],
            "members": [i],
            "height": 0,
            "system": systems.get(names[i], "未知"),
            "similarity": round(matrix[0][i] * 100, 1) if i > 0 else 100.0,
        } for i in range(n)]

        # 记录活跃簇
        active = list(range(n))

        # 聚类过程
        while len(active) > 2:  # 保留底本和一个聚类组
            # 找最小距离（排除底本与其他的直接合并）
            min_dist = float('inf')
            min_i, min_j = -1, -1

            for i in range(len(active)):
                for j in range(i + 1, len(active)):
                    idx_i, idx_j = active[i], active[j]
                    # 跳过底本（索引0）的直接合并
                    if idx_i == 0 or idx_j == 0:
                        continue

                    # 计算簇间平均距离
                    d = self._cluster_distance(clusters[idx_i], clusters[idx_j], dist)
                    if d < min_dist:
                        min_dist = d
                        min_i, min_j = i, j

            if min_i < 0:
                break

            # 合并两个簇
            idx_i, idx_j = active[min_i], active[min_j]
            new_cluster = {
                "name": f"聚类_{len(clusters)}",
                "members": clusters[idx_i]["members"] + clusters[idx_j]["members"],
                "height": min_dist,
                "children": [clusters[idx_i], clusters[idx_j]],
            }
            clusters.append(new_cluster)

            # 更新活跃簇列表
            active.append(len(clusters) - 1)
            # 删除时先删大的索引
            if min_i > min_j:
                del active[min_i]
                del active[min_j]
            else:
                del active[min_j]
                del active[min_i]

        # 构建最终树结构
        tree = self._build_tree_from_clusters(clusters, active, names[0])

        return tree

    def _cluster_distance(self, c1: Dict, c2: Dict, dist: List[List[float]]) -> float:
        """计算两个簇之间的平均距离"""
        total = 0
        count = 0
        for i in c1["members"]:
            for j in c2["members"]:
                total += dist[i][j]
                count += 1
        return total / count if count > 0 else 0

    def _build_tree_from_clusters(
        self,
        clusters: List[Dict],
        active: List[int],
        root_name: str
    ) -> Dict:
        """从聚类结果构建树"""
        # 找到根节点（底本）
        root_idx = 0
        other_clusters = [clusters[i] for i in active if i != root_idx]

        def build_subtree(cluster):
            if "children" in cluster:
                return {
                    "name": cluster.get("name", "组"),
                    "is_group": True,
                    "children": [build_subtree(c) for c in cluster["children"]],
                }
            else:
                return {
                    "name": cluster["name"],
                    "similarity": cluster.get("similarity", 0),
                    "system": cluster.get("system", "未知"),
                    "children": [],
                }

        # 构建树
        tree = {
            "name": root_name,
            "children": [build_subtree(c) for c in other_clusters],
        }

        return tree

    # ==================== 综合分析 ====================

    def analyze_phylogeny(
        self,
        base_text: str,
        base_name: str,
        collation_results: List[Dict],
        collation_texts: Optional[Dict[str, str]] = None,
        custom_systems: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        综合版本谱系分析

        Args:
            base_text: 底本文本
            base_name: 底本名称
            collation_results: 各校本的对比结果
            collation_texts: 各校本文本（可选）
            custom_systems: 用户自定义版本系统归属（可选）

        Returns:
            完整的版本谱系分析结果
        """
        # 应用用户自定义系统
        if custom_systems:
            self.update_version_system_map(custom_systems)

        # 1. 计算完整相似度矩阵
        similarity_matrix = self.calculate_full_similarity_matrix(
            base_text, base_name, collation_results, collation_texts
        )

        # 2. 分析共同讹误
        shared_errors = self.analyze_shared_errors(collation_results)

        # 3. UPGMA 聚类生成谱系树
        phylogeny_tree = self.upgma_clustering(similarity_matrix)

        # 4. 生成分析结论
        conclusions = self._generate_conclusions(
            similarity_matrix, shared_errors, phylogeny_tree
        )

        return {
            "similarity_matrix": similarity_matrix,
            "shared_errors": shared_errors,
            "tree": phylogeny_tree,
            "conclusions": conclusions,
        }

    def _generate_conclusions(
        self,
        similarity_matrix: Dict,
        shared_errors: Dict,
        tree: Dict,
    ) -> List[str]:
        """生成分析结论"""
        conclusions = []
        names = similarity_matrix["names"]
        matrix = similarity_matrix["matrix"]
        systems = similarity_matrix.get("systems", {})
        n = len(names)

        # 1. 找出最相似的版本对
        max_sim = 0
        max_pair = None
        for i in range(1, n):
            for j in range(i + 1, n):
                if matrix[i][j] > max_sim:
                    max_sim = matrix[i][j]
                    max_pair = (names[i], names[j])

        if max_pair:
            conclusions.append(
                f"最相似版本对：{max_pair[0]} 与 {max_pair[1]}，相似度 {max_sim*100:.1f}%"
            )

        # 2. 按系统分组统计
        system_groups = defaultdict(list)
        for name in names[1:]:  # 跳过底本
            system = systems.get(name, "未知")
            system_groups[system].append(name)

        for system, members in system_groups.items():
            if len(members) > 1:
                conclusions.append(
                    f"{system}：{', '.join(members)}"
                )

        # 3. 共同讹误分析
        error_matrix = shared_errors.get("matrix", [])
        error_names = shared_errors.get("names", [])
        if error_matrix and error_names:
            max_errors = 0
            max_error_pair = None
            for i in range(len(error_names)):
                for j in range(i + 1, len(error_names)):
                    if error_matrix[i][j] > max_errors:
                        max_errors = error_matrix[i][j]
                        max_error_pair = (error_names[i], error_names[j])

            if max_error_pair and max_errors > 0:
                conclusions.append(
                    f"共同讹误最多：{max_error_pair[0]} 与 {max_error_pair[1]}，共 {max_errors} 处"
                )

        return conclusions


# 全局实例
phylogeny_service = PhylogenyAnalysisService()
