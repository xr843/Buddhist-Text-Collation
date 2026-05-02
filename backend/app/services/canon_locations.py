"""
藏经刻印地坐标数据库
基于历史文献记载的藏经刻印地点
"""
from typing import Dict, Optional, List


# 藏经刻印地坐标数据（经纬度）
CANON_LOCATIONS: Dict[str, Dict] = {
    # ===== 中系（开宝藏系）=====
    '开宝藏': {
        'lat': 30.5728, 'lng': 104.0668,
        'city': '四川成都（益州）',
        'province': '四川',
        'system': '中系',
        'period': '北宋',
        'year': 971,
        'description': '北宋开宝藏，刻于成都，中系之祖'
    },
    '高丽藏': {
        'lat': 37.8816, 'lng': 126.5558,
        'city': '韩国开城',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1011,
        'description': '高丽大藏经，依《开宝藏》刻成'
    },
    '高麗藏': {  # 繁体
        'lat': 37.8816, 'lng': 126.5558,
        'city': '韩国开城',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1011
    },
    '高丽初雕': {
        'lat': 37.8816, 'lng': 126.5558,
        'city': '韩国开城',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1011,
        'description': '高丽大藏经初雕本（1011-1087）'
    },
    '高麗初雕': {  # 繁体
        'lat': 37.8816, 'lng': 126.5558,
        'city': '韩国开城',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1011
    },
    '高丽再雕': {
        'lat': 35.2284, 'lng': 128.6811,
        'city': '韩国庆尚南道（海印寺）',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1236,
        'description': '高丽大藏经再雕本（1236-1251），现存海印寺'
    },
    '高麗再雕': {  # 繁体
        'lat': 35.2284, 'lng': 128.6811,
        'city': '韩国庆尚南道（海印寺）',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1236
    },
    '高麗再雕增上寺版': {  # 日本增上寺传本
        'lat': 35.2284, 'lng': 128.6811,
        'city': '韩国庆尚南道（海印寺）',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1236,
        'description': '高丽再雕本，日本增上寺传本'
    },
    '增上寺版': {  # 简称
        'lat': 35.2284, 'lng': 128.6811,
        'city': '韩国庆尚南道（海印寺）',
        'province': '海外',
        'system': '中系',
        'period': '高丽',
        'year': 1236
    },
    '赵城金藏': {
        'lat': 36.2557, 'lng': 111.7020,
        'city': '山西赵城',
        'province': '山西',
        'system': '中系',
        'period': '金',
        'year': 1148,
        'description': '金代刻藏，保存《开宝藏》原貌'
    },
    '趙城金藏': {  # 繁体
        'lat': 36.2557, 'lng': 111.7020,
        'city': '山西赵城',
        'province': '山西',
        'system': '中系',
        'period': '金',
        'year': 1148
    },
    '大正藏': {
        'lat': 35.6762, 'lng': 139.6503,
        'city': '日本东京',
        'province': '海外',
        'system': '中系',
        'period': '近代',
        'year': 1924,
        'description': '日本大正新修大藏经，以《高丽藏》为底本'
    },
    '中华藏': {
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '中系',
        'period': '现代',
        'year': 1994,
        'description': '中华大藏经（汉文部分），北京中华书局'
    },
    '中華藏': {  # 繁体
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '中系',
        'period': '现代',
        'year': 1994
    },

    # ===== 南系（福建/江浙民间募刻）=====
    '崇宁藏': {
        'lat': 26.0745, 'lng': 119.2965,
        'city': '福建福州东禅寺',
        'province': '福建',
        'system': '南系',
        'period': '北宋',
        'year': 1104,
        'description': '北宋崇宁年间刻于福州，南系之始'
    },
    '崇寧藏': {  # 繁体
        'lat': 26.0745, 'lng': 119.2965,
        'city': '福建福州东禅寺',
        'province': '福建',
        'system': '南系',
        'period': '北宋',
        'year': 1104
    },
    '崇寧': {  # 简称（用于匹配【南系●崇寧】）
        'lat': 26.0745, 'lng': 119.2965,
        'city': '福建福州',
        'province': '福建',
        'system': '南系',
        'period': '北宋',
        'year': 1104
    },
    '福州藏': {  # 别称
        'lat': 26.0745, 'lng': 119.2965,
        'city': '福建福州',
        'province': '福建',
        'system': '南系',
        'period': '北宋',
        'year': 1104
    },
    '毗卢藏': {
        'lat': 26.0745, 'lng': 119.2965,
        'city': '福建福州开元寺',
        'province': '福建',
        'system': '南系',
        'period': '南宋',
        'year': 1148,
        'description': '福州系藏经'
    },
    '毘盧藏': {  # 异体
        'lat': 26.0745, 'lng': 119.2965,
        'city': '福建福州开元寺',
        'province': '福建',
        'system': '南系',
        'period': '南宋',
        'year': 1148
    },
    '思溪藏': {
        'lat': 30.8703, 'lng': 120.0933,
        'city': '浙江湖州思溪',
        'province': '浙江',
        'system': '南系',
        'period': '南宋',
        'year': 1127,
        'description': '湖州系藏经，南系重要支派'
    },
    '碛砂藏': {
        'lat': 31.2989, 'lng': 120.5853,
        'city': '江苏苏州碛砂',
        'province': '江苏',
        'system': '南系',
        'period': '南宋',
        'year': 1231,
        'description': '苏杭系藏经，刻于平江府碛砂延圣院'
    },
    '磧砂藏': {  # 繁体
        'lat': 31.2989, 'lng': 120.5853,
        'city': '江苏苏州碛砂',
        'province': '江苏',
        'system': '南系',
        'period': '南宋',
        'year': 1231
    },
    '普宁藏': {
        'lat': 30.2741, 'lng': 120.1551,
        'city': '浙江杭州',
        'province': '浙江',
        'system': '南系',
        'period': '南宋',
        'year': 1280,
        'description': '杭州刻藏'
    },
    '普寧藏': {  # 繁体
        'lat': 30.2741, 'lng': 120.1551,
        'city': '浙江杭州',
        'province': '浙江',
        'system': '南系',
        'period': '南宋',
        'year': 1280
    },
    '洪武南藏': {
        'lat': 32.0584, 'lng': 118.7965,
        'city': '江苏南京',
        'province': '江苏',
        'system': '南系',
        'period': '明',
        'year': 1372,
        'description': '明初刻于南京'
    },
    '永乐南藏': {
        'lat': 32.0584, 'lng': 118.7965,
        'city': '江苏南京',
        'province': '江苏',
        'system': '南系',
        'period': '明',
        'year': 1410,
        'description': '永乐年间刻于南京'
    },
    '永樂南藏': {  # 繁体
        'lat': 32.0584, 'lng': 118.7965,
        'city': '江苏南京',
        'province': '江苏',
        'system': '南系',
        'period': '明',
        'year': 1410
    },
    '永乐北藏': {
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '南系',
        'period': '明',
        'year': 1421
    },
    '永樂北藏': {  # 繁体
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '南系',
        'period': '明',
        'year': 1421
    },
    '嘉兴藏': {
        'lat': 30.7467, 'lng': 120.7550,
        'city': '浙江嘉兴楞严寺',
        'province': '浙江',
        'system': '南系',
        'period': '明',
        'year': 1589,
        'description': '明代方册藏'
    },
    '嘉興藏': {  # 繁体
        'lat': 30.7467, 'lng': 120.7550,
        'city': '浙江嘉兴楞严寺',
        'province': '浙江',
        'system': '南系',
        'period': '明',
        'year': 1589
    },
    '龙藏': {
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '南系',
        'period': '清',
        'year': 1735,
        'description': '清乾隆藏，官刻藏经'
    },
    '龍藏': {  # 繁体
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '南系',
        'period': '清',
        'year': 1735
    },
    '乾隆藏': {
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '南系',
        'period': '清',
        'year': 1735
    },
    '频伽藏': {
        'lat': 31.2304, 'lng': 121.4737,
        'city': '上海',
        'province': '上海',
        'system': '南系',
        'period': '近代',
        'year': 1909,
        'description': '上海频伽精舍刻'
    },
    '頻伽藏': {  # 繁体
        'lat': 31.2304, 'lng': 121.4737,
        'city': '上海',
        'province': '上海',
        'system': '南系',
        'period': '近代',
        'year': 1909
    },
    '频伽': {  # 简称（用于匹配【南系●频伽】）
        'lat': 31.2304, 'lng': 121.4737,
        'city': '上海',
        'province': '上海',
        'system': '南系',
        'period': '近代',
        'year': 1909
    },
    '频伽精舍': {  # 全称
        'lat': 31.2304, 'lng': 121.4737,
        'city': '上海',
        'province': '上海',
        'system': '南系',
        'period': '近代',
        'year': 1909
    },
    '频伽精舍校勘大藏经': {  # 完整名称
        'lat': 31.2304, 'lng': 121.4737,
        'city': '上海',
        'province': '上海',
        'system': '南系',
        'period': '近代',
        'year': 1909
    },
    '缩刻藏': {
        'lat': 35.6762, 'lng': 139.6503,
        'city': '日本东京',
        'province': '海外',
        'system': '中系',
        'period': '近代',
        'year': 1880,
        'description': '日本缩刷藏经，缩印自《高丽藏》'
    },
    '縮刻藏': {  # 繁体
        'lat': 35.6762, 'lng': 139.6503,
        'city': '日本东京',
        'province': '海外',
        'system': '中系',
        'period': '近代',
        'year': 1880
    },
    '卍字正藏': {
        'lat': 35.0116, 'lng': 135.7681,
        'city': '日本京都',
        'province': '海外',
        'system': '南系',
        'period': '近代',
        'year': 1902,
        'description': '日本京都藏经书院刊行'
    },
    '卍正藏': {  # 简称
        'lat': 35.0116, 'lng': 135.7681,
        'city': '日本京都',
        'province': '海外',
        'system': '南系',
        'period': '近代',
        'year': 1902
    },
    '卍字续藏': {
        'lat': 35.0116, 'lng': 135.7681,
        'city': '日本京都',
        'province': '海外',
        'system': '南系',
        'period': '近代',
        'year': 1905,
        'description': '日本京都藏经书院续刊'
    },
    '卍续藏': {  # 简称
        'lat': 35.0116, 'lng': 135.7681,
        'city': '日本京都',
        'province': '海外',
        'system': '南系',
        'period': '近代',
        'year': 1905
    },

    # ===== 北系（契丹藏系）=====
    '契丹藏': {
        'lat': 41.8057, 'lng': 123.4315,
        'city': '辽宁沈阳（辽中京）',
        'province': '辽宁',
        'system': '北系',
        'period': '辽',
        'year': 1031,
        'description': '辽代独立编纂，北系之祖'
    },
    '房山石经': {
        'lat': 39.7489, 'lng': 115.9928,
        'city': '北京房山云居寺',
        'province': '北京',
        'system': '北系',
        'period': '隋唐辽',
        'year': 605,
        'description': '始刻于隋，辽代部分属北系'
    },
    '房山石經': {  # 繁体
        'lat': 39.7489, 'lng': 115.9928,
        'city': '北京房山云居寺',
        'province': '北京',
        'system': '北系',
        'period': '隋唐辽',
        'year': 605
    },
    '房山石經北京華夏版': {
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '北系',
        'period': '现代',
        'year': 2000,
        'description': '房山石经北京华夏出版社版'
    },
    '北京華夏版': {  # 简称
        'lat': 39.9042, 'lng': 116.4074,
        'city': '北京',
        'province': '北京',
        'system': '北系',
        'period': '现代',
        'year': 2000
    },

    # ===== 未知系（现代整理本）=====
    '玄奘法師譯撰全集金陵版': {
        'lat': 32.0584, 'lng': 118.7965,
        'city': '江苏南京',
        'province': '江苏',
        'system': '未知',
        'period': '现代',
        'year': 2000,
        'description': '玄奘法师译撰全集，金陵刻经处版'
    },
    '金陵版': {  # 简称
        'lat': 32.0584, 'lng': 118.7965,
        'city': '江苏南京',
        'province': '江苏',
        'system': '未知',
        'period': '现代',
        'year': 2000
    },
    'CBETA': {
        'lat': 25.0330, 'lng': 121.5654,
        'city': '台湾台北',
        'province': '台湾',
        'system': '未知',
        'period': '现代',
        'year': 1998,
        'description': '中华电子佛典协会(CBETA)电子藏经'
    },
}


class CanonLocationService:
    """藏经地理位置服务"""

    @staticmethod
    def get_canon_location(canon_name: str) -> Optional[Dict]:
        """
        获取藏经的地理位置信息

        Args:
            canon_name: 藏经名称（完整名或关键词）

        Returns:
            位置信息字典，如果未找到则返回None
        """
        # 直接匹配
        if canon_name in CANON_LOCATIONS:
            return CANON_LOCATIONS[canon_name]

        # 模糊匹配（查找包含关键词的藏经）
        for canon_key, location in CANON_LOCATIONS.items():
            if canon_key in canon_name or canon_name in canon_key:
                return location

        return None

    @staticmethod
    def get_all_locations() -> Dict[str, Dict]:
        """获取所有藏经位置"""
        return CANON_LOCATIONS

    @staticmethod
    def get_locations_by_system(system: str) -> Dict[str, Dict]:
        """按系统筛选藏经位置"""
        return {
            name: loc for name, loc in CANON_LOCATIONS.items()
            if loc.get('system') == system
        }

    @staticmethod
    def get_locations_by_province(province: str) -> Dict[str, Dict]:
        """按省份筛选藏经位置"""
        return {
            name: loc for name, loc in CANON_LOCATIONS.items()
            if loc.get('province') == province
        }

    @staticmethod
    def extract_canon_name(full_version_name: str) -> Optional[str]:
        """
        从完整版本名中提取藏经核心名称

        Example:
            "【中系●高麗藏國圖版】" -> "高麗藏"
            "《瑜伽師地論》思溪藏版" -> "思溪藏"
        """
        # 按长度降序排列，优先匹配更具体的名称
        sorted_canons = sorted(CANON_LOCATIONS.keys(), key=len, reverse=True)

        for canon_name in sorted_canons:
            if canon_name in full_version_name:
                return canon_name

        return None

    @staticmethod
    def enrich_phylogeny_data_with_locations(
        phylogeny_data: Dict
    ) -> Dict:
        """
        为谱系分析数据添加地理位置信息

        Args:
            phylogeny_data: 谱系分析数据
                {
                    'similarity_matrix': {
                        'names': [...],
                        'matrix': [...],
                        'systems': {...}
                    },
                    ...
                }

        Returns:
            增强后的数据，添加了 canon_locations 字段
        """
        similarity_matrix = phylogeny_data.get('similarity_matrix', {})
        names = similarity_matrix.get('names', [])

        # 为每个版本查找地理位置
        canon_locations = {}
        for name in names:
            canon_name = CanonLocationService.extract_canon_name(name)
            if canon_name:
                location = CanonLocationService.get_canon_location(canon_name)
                if location:
                    canon_locations[name] = location

        # 添加到数据中
        enriched_data = phylogeny_data.copy()
        enriched_data['canon_locations'] = canon_locations

        return enriched_data

    @staticmethod
    def calculate_geographic_distance(loc1: Dict, loc2: Dict) -> float:
        """
        计算两个地点之间的地理距离（公里）
        使用Haversine公式

        Args:
            loc1, loc2: 包含lat和lng的字典

        Returns:
            距离（公里）
        """
        from math import radians, sin, cos, sqrt, atan2

        # 地球半径（公里）
        R = 6371.0

        lat1 = radians(loc1['lat'])
        lon1 = radians(loc1['lng'])
        lat2 = radians(loc2['lat'])
        lon2 = radians(loc2['lng'])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance

    @staticmethod
    def analyze_geographic_clustering(
        version_names: List[str],
        similarity_matrix: List[List[float]],
        threshold: float = 0.9
    ) -> Dict:
        """
        分析地理聚类现象

        检测：相似度高的版本是否地理位置也接近

        Returns:
            {
                'geographic_clusters': [...],
                'similarity_distance_correlation': float
            }
        """
        clusters = []

        for i, name1 in enumerate(version_names):
            for j, name2 in enumerate(version_names):
                if i >= j:
                    continue

                similarity = similarity_matrix[i][j]
                if similarity < threshold:
                    continue

                # 获取地理位置
                loc1 = CanonLocationService.get_canon_location(
                    CanonLocationService.extract_canon_name(name1)
                )
                loc2 = CanonLocationService.get_canon_location(
                    CanonLocationService.extract_canon_name(name2)
                )

                if loc1 and loc2:
                    distance = CanonLocationService.calculate_geographic_distance(loc1, loc2)
                    clusters.append({
                        'version1': name1,
                        'version2': name2,
                        'similarity': similarity,
                        'distance_km': round(distance, 1),
                        'same_province': loc1.get('province') == loc2.get('province')
                    })

        return {
            'geographic_clusters': clusters,
            'total_pairs': len(clusters)
        }
