"""
DILA 瑜伽师地论数据库映射解析器

从 DILA HTML 数据中提取经论与注疏的精确对应关系。

DILA 数据格式说明：
- 每个科判节点有唯一 ID，格式如 T1579D08_001（典籍ID + 层级 + 序号）
- 每个节点通过 link2oth 类链接到对应的注疏节点
- 节点嵌套表示科判层级（A1 > B1 > C1 ...）

支持的典籍：
- T1579: 瑜伽师地论（底本）
- T1828: 瑜伽论记
- T1829: 瑜伽师地论略纂
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DilaNode:
    """DILA 科判节点"""
    id: str                          # 节点 ID，如 T1579D08_001
    work_id: str                     # 典籍 ID，如 T1579
    level: str                       # 层级代码，如 D08
    seq: str                         # 序号，如 001
    head_text: str                   # 科判标题，如 "H1 自性"
    path: str                        # 层级路径
    text: str = ""                   # 段落文本内容
    page_ref: str = ""               # 页码引用，如 0279a26
    links: List[str] = field(default_factory=list)  # 链接到的其他节点


@dataclass
class MappingEntry:
    """对应关系条目"""
    base_node_id: str                # 底本节点 ID
    base_head: str                   # 底本科判标题
    base_text: str                   # 底本文本
    base_page: str                   # 底本页码
    commentary_nodes: Dict[str, str] = field(default_factory=dict)  # 注疏节点 {work_id: node_id}


class DilaMappingParser:
    """DILA 映射数据解析器"""

    # 典籍配置
    WORK_CONFIG = {
        'T1579': {'name': '瑜伽师地论', 'type': 'base'},
        'T1828': {'name': '瑜伽论记', 'type': 'commentary', 'link_text': '論記'},
        'T1829': {'name': '瑜伽师地论略纂', 'type': 'commentary', 'link_text': '略纂'},
        'T1580': {'name': '瑜伽师地论释', 'type': 'commentary', 'link_text': '論釋'},
    }

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化解析器

        Args:
            data_dir: DILA HTML 数据目录
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = project_root / 'data' / 'dila' / 'html'

        self._mapping_cache: Dict[int, List[MappingEntry]] = {}

    def parse_html_file(self, file_path: Path) -> List[DilaNode]:
        """
        解析单个 HTML 文件

        Args:
            file_path: HTML 文件路径

        Returns:
            解析出的节点列表
        """
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        nodes = []

        # 找到所有 ybhDiv（科判区块）
        for div in soup.find_all('div', class_='ybhDiv'):
            node_id = div.get('id', '')
            if not node_id:
                continue

            # 解析 ID 格式: T1579D08_001
            match = re.match(r'([A-Z]\d+)D(\d+)_(\d+)', node_id)
            if not match:
                continue

            work_id, level, seq = match.groups()

            # 获取科判标题
            head_div = div.find('div', class_='YBh_head')
            head_text = ""
            path = ""
            if head_div:
                head_span = head_div.find('span', class_='head_text')
                if head_span:
                    head_text = head_span.get_text(strip=True)
                    path = head_span.get('path', '')
                else:
                    # 直接从 YBh_head 获取文本（排除链接）
                    for child in head_div.children:
                        if isinstance(child, str):
                            head_text += child.strip()
                        elif child.name == 'span' and 'class' not in child.attrs:
                            head_text += child.get_text(strip=True)
                    head_text = head_text.strip()

            # 获取段落文本
            text_parts = []
            for p in div.find_all('p', recursive=False):
                p_text = p.get_text(strip=True)
                if p_text:
                    text_parts.append(p_text)
            text = '\n'.join(text_parts)

            # 获取页码引用
            page_ref = ""
            first_ref = div.find('a', class_='ref')
            if first_ref:
                page_ref = first_ref.get('id', '')

            # 获取链接到的其他节点
            links = []
            for link in div.find_all('a', class_='link2oth'):
                link_id = link.get('id', '')
                if link_id:
                    links.append(link_id)

            node = DilaNode(
                id=node_id,
                work_id=work_id,
                level=f"D{level}",
                seq=seq,
                head_text=head_text,
                path=path,
                text=text,
                page_ref=page_ref,
                links=links
            )
            nodes.append(node)

        return nodes

    def build_mapping(self, juan_num: int) -> List[MappingEntry]:
        """
        构建指定卷的对应关系映射

        Args:
            juan_num: 卷号

        Returns:
            对应关系列表
        """
        if juan_num in self._mapping_cache:
            return self._mapping_cache[juan_num]

        # 解析底本 HTML
        base_file = self.data_dir / f'T1579_juan{juan_num}.html'
        base_nodes = self.parse_html_file(base_file)

        if not base_nodes:
            logger.warning(f"未找到底本数据: 卷{juan_num}")
            return []

        # 构建映射
        mappings = []
        for node in base_nodes:
            if node.work_id != 'T1579':
                continue

            # 提取注疏链接
            commentary_nodes = {}
            for link_id in node.links:
                # 解析链接 ID
                match = re.match(r'([A-Z]\d+)D\d+_\d+', link_id)
                if match:
                    link_work_id = match.group(1)
                    if link_work_id in self.WORK_CONFIG:
                        commentary_nodes[link_work_id] = link_id

            entry = MappingEntry(
                base_node_id=node.id,
                base_head=node.head_text,
                base_text=node.text,
                base_page=node.page_ref,
                commentary_nodes=commentary_nodes
            )
            mappings.append(entry)

        self._mapping_cache[juan_num] = mappings
        logger.info(f"卷{juan_num}: 解析了 {len(mappings)} 个节点，"
                   f"有注疏链接的节点: {sum(1 for m in mappings if m.commentary_nodes)}")

        return mappings

    def get_commentary_mapping(
        self,
        juan_num: int,
        base_node_id: str,
        commentary_work_id: str
    ) -> Optional[str]:
        """
        获取底本节点对应的注疏节点 ID

        Args:
            juan_num: 卷号
            base_node_id: 底本节点 ID
            commentary_work_id: 注疏典籍 ID

        Returns:
            注疏节点 ID，或 None
        """
        mappings = self.build_mapping(juan_num)
        for entry in mappings:
            if entry.base_node_id == base_node_id:
                return entry.commentary_nodes.get(commentary_work_id)
        return None

    def get_aligned_segments(
        self,
        juan_num: int,
        start_index: int = 0,
        count: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        获取对齐的段落数据

        Args:
            juan_num: 卷号
            start_index: 起始索引
            count: 获取数量

        Returns:
            包含底本和注疏对齐数据的字典
        """
        mappings = self.build_mapping(juan_num)

        if not mappings:
            return {'base': [], 'commentaries': {}}

        # 切片获取指定范围
        end_index = min(start_index + count, len(mappings))
        selected = mappings[start_index:end_index]

        result = {
            'base': [],
            'commentaries': {
                'T1828': [],
                'T1829': []
            },
            'total': len(mappings),
            'start_index': start_index,
            'count': len(selected)
        }

        for entry in selected:
            # 底本数据
            result['base'].append({
                'node_id': entry.base_node_id,
                'head': entry.base_head,
                'text': entry.base_text,
                'page': entry.base_page
            })

            # 注疏对应数据
            for work_id in ['T1828', 'T1829']:
                comm_node_id = entry.commentary_nodes.get(work_id, '')
                result['commentaries'][work_id].append({
                    'node_id': comm_node_id,
                    'base_ref': entry.base_node_id
                })

        return result

    def export_mapping_json(self, juan_num: int, output_path: Optional[Path] = None) -> str:
        """
        导出映射数据为 JSON

        Args:
            juan_num: 卷号
            output_path: 输出路径（可选）

        Returns:
            JSON 字符串
        """
        mappings = self.build_mapping(juan_num)
        data = [asdict(m) for m in mappings]
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"已导出映射数据到: {output_path}")

        return json_str


# 创建全局实例
dila_mapping_parser = DilaMappingParser()


if __name__ == '__main__':
    # 测试解析
    parser = DilaMappingParser()

    # 解析第1卷
    mappings = parser.build_mapping(1)

    print("\n=== 卷1 映射数据样例 ===")
    for i, entry in enumerate(mappings[:10]):
        print(f"\n{i+1}. {entry.base_node_id}")
        print(f"   标题: {entry.base_head}")
        print(f"   页码: {entry.base_page}")
        print(f"   注疏: {entry.commentary_nodes}")
        if entry.base_text:
            print(f"   文本: {entry.base_text[:50]}...")
