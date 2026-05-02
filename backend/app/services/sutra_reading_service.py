"""
经论注释对读服务 - 使用 DILA 映射数据实现精确对齐

支持经论：
- T30n1579 《瑜伽师地论》
- T42n1828 《瑜伽论记》（遁伦集撰）
- T43n1829 《瑜伽师地论略纂》（窥基撰）

数据来源：
- DILA 瑜伽师地论数据库 (https://ybh.dila.edu.tw)
- 使用 DILA 的科判对应数据实现精确的经论-注疏对齐

数据加载优先级：
1. 预处理的 JSON 文件（推荐，性能好）
2. 原始 HTML 文件（回退方案）
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DilaSegment:
    """DILA 格式的文本段落"""
    node_id: str                     # 节点 ID，如 T1579D08_001
    head: str                        # 科判标题，如 "H1 自性"
    text: str                        # 段落文本内容
    page: str                        # 页码引用，如 0279a26
    path: str = ""                   # 层级路径
    commentary_links: Dict[str, str] = field(default_factory=dict)  # 对应的注疏节点（从底本角度）
    base_refs: List[str] = field(default_factory=list)  # 引用的底本节点（从注疏角度）


@dataclass
class SutraInfo:
    """经论基本信息"""
    id: str                          # 典籍ID（如 T30n1579）
    title: str                       # 标题
    author: str                      # 作者/译者
    total_juans: int                 # 总卷数
    description: str = ""            # 简介


class SutraReadingService:
    """经论对读服务 - 基于 DILA 映射数据"""

    # 支持的典籍配置
    SUPPORTED_SUTRAS = {
        'T30n1579': {
            'title': '瑜伽师地论',
            'author': '弥勒菩萨说 唐玄奘译',
            'total_juans': 100,
            'dila_work': 'T1579',
            'description': '印度大乘佛教瑜伽行派根本论典'
        },
        'T42n1828': {
            'title': '瑜伽论记',
            'author': '释遁伦集撰',
            'total_juans': 48,
            'dila_work': 'T1828',
            'description': '《瑜伽师地论》注疏，汇集诸家解释'
        },
        'T43n1829': {
            'title': '瑜伽师地论略纂',
            'author': '窥基撰',
            'total_juans': 16,
            'dila_work': 'T1829',
            'description': '窥基大师所撰《瑜伽师地论》注疏'
        }
    }

    # DILA work ID 到我们的 sutra_id 的映射
    DILA_TO_SUTRA = {
        'T1579': 'T30n1579',
        'T1828': 'T42n1828',
        'T1829': 'T43n1829',
    }

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化服务

        Args:
            data_dir: DILA 数据目录（包含 html 和 json 子目录）
        """
        # 计算项目根目录
        # 本地开发: /path/to/project/backend/app/services/xxx.py -> 4层到project
        # Docker: /app/app/services/xxx.py -> 需要到 /app
        project_root = Path(__file__).parent.parent.parent.parent

        # Docker 环境检测：如果计算出的路径不存在 data/dila，尝试 /app
        docker_data_path = Path('/app/data/dila')
        if docker_data_path.exists():
            dila_base = docker_data_path
        else:
            dila_base = project_root / 'data' / 'dila'

        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = dila_base / 'html'

        # JSON 数据目录
        self.json_dir = dila_base / 'json'

        # 缓存
        self._cache: Dict[str, List[DilaSegment]] = {}
        self._json_cache: Dict[str, Dict] = {}  # 缓存整个JSON文件
        self._alignment_index: Optional[Dict] = None  # 对齐索引

        # 尝试加载预处理的JSON数据
        self._load_json_data()

    def _load_json_data(self):
        """加载预处理的JSON数据"""
        if not self.json_dir.exists():
            logger.info("JSON数据目录不存在，将使用HTML解析")
            return

        # 加载对齐索引
        index_file = self.json_dir / "alignment_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self._alignment_index = json.load(f)
                logger.info(f"已加载对齐索引: {len(self._alignment_index)} 条")
            except Exception as e:
                logger.error(f"加载对齐索引失败: {e}")

        # 预加载各典籍JSON（启动时加载，提升运行时性能）
        for work_id in ['T1579', 'T1828', 'T1829']:
            json_file = self.json_dir / f"{work_id}.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        self._json_cache[work_id] = json.load(f)
                    logger.info(f"已加载 {work_id} JSON数据")
                except Exception as e:
                    logger.error(f"加载 {work_id} JSON失败: {e}")

    def _get_segments_from_json(self, work_id: str, juan_num: int) -> Optional[List[DilaSegment]]:
        """从JSON缓存获取段落数据"""
        if work_id not in self._json_cache:
            return None

        work_data = self._json_cache[work_id]
        juan_key = str(juan_num)

        if 'juans' not in work_data or juan_key not in work_data['juans']:
            return None

        juan_data = work_data['juans'][juan_key]
        segments = []

        for seg_data in juan_data.get('segments', []):
            segment = DilaSegment(
                node_id=seg_data.get('node_id', ''),
                head=seg_data.get('head', ''),
                text=seg_data.get('text', ''),
                page=seg_data.get('page', ''),
                path=seg_data.get('path', ''),
                commentary_links=seg_data.get('commentary_links', {}),
                base_refs=seg_data.get('base_refs', [])
            )
            segments.append(segment)

        return segments

    def get_available_sutras(self) -> List[SutraInfo]:
        """获取可用的经论列表"""
        result = []
        for sutra_id, config in self.SUPPORTED_SUTRAS.items():
            # 检查是否有 DILA HTML 数据
            dila_work = config.get('dila_work', '')
            html_file = self.data_dir / f'{dila_work}_juan1.html'
            if html_file.exists():
                result.append(SutraInfo(
                    id=sutra_id,
                    title=config['title'],
                    author=config['author'],
                    total_juans=config['total_juans'],
                    description=config['description']
                ))
        return result

    def _parse_dila_html(self, work_id: str, juan_num: int) -> List[DilaSegment]:
        """
        获取段落数据 - 优先使用预处理JSON，回退到HTML解析

        Args:
            work_id: DILA 典籍 ID（如 T1579）
            juan_num: 卷号

        Returns:
            段落列表
        """
        cache_key = f"{work_id}_{juan_num}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 优先从JSON缓存获取
        json_segments = self._get_segments_from_json(work_id, juan_num)
        if json_segments is not None:
            self._cache[cache_key] = json_segments
            return json_segments

        # 回退到HTML解析
        return self._parse_dila_html_fallback(work_id, juan_num)

    def _parse_dila_html_fallback(self, work_id: str, juan_num: int) -> List[DilaSegment]:
        """
        从HTML文件解析段落（回退方案）

        Args:
            work_id: DILA 典籍 ID（如 T1579）
            juan_num: 卷号

        Returns:
            解析出的段落列表
        """
        from bs4 import BeautifulSoup

        cache_key = f"{work_id}_{juan_num}"

        file_path = self.data_dir / f'{work_id}_juan{juan_num}.html'
        if not file_path.exists():
            logger.warning(f"DILA HTML 文件不存在: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, {e}")
            return []

        soup = BeautifulSoup(content, 'html.parser')
        segments = []

        # 找到所有 ybhDiv（科判区块）
        ybh_divs = soup.find_all('div', class_='ybhDiv')

        if ybh_divs:
            # 有科判标记，按科判解析
            for div in ybh_divs:
                node_id = div.get('id', '')
                if not node_id:
                    continue

                # 解析 ID 格式: T1579D08_001
                match = re.match(r'([A-Z]\d+)D(\d+)_(\d+)', node_id)
                if not match:
                    continue

                div_work_id = match.group(1)
                if div_work_id != work_id:
                    continue

                # 获取科判标题
                head_text = ""
                path = ""
                head_div = div.find('div', class_='YBh_head', recursive=False)
                if head_div:
                    head_span = head_div.find('span', class_='head_text')
                    if head_span:
                        head_text = head_span.get_text(strip=True)
                        path = head_span.get('path', '')
                    else:
                        # 直接从 YBh_head 获取第一个文本
                        for child in head_div.children:
                            if isinstance(child, str):
                                text = child.strip()
                                if text:
                                    head_text = text
                                    break
                            elif hasattr(child, 'name') and child.name not in ['a', 'span']:
                                text = child.get_text(strip=True)
                                if text:
                                    head_text = text
                                    break

                # 获取段落文本
                text_parts = []
                for p in div.find_all('p', recursive=False):
                    p_text = p.get_text(strip=True)
                    if p_text:
                        text_parts.append(p_text)

                # 也获取偈颂文本
                for lg in div.find_all('div', class_='lg', recursive=False):
                    lg_text = lg.get_text(strip=True)
                    if lg_text:
                        text_parts.append(lg_text)

                text = '\n'.join(text_parts)

                # 清除文本中的页码引用标记
                text = re.sub(r'\[T\d+,\s*p?\d+[a-c]?\d*\]', '', text)
                text = re.sub(r'\[\d+[a-c]\d+\]', '', text)
                text = re.sub(r'\s+', ' ', text).strip()

                # 获取页码引用
                page_ref = ""
                first_ref = div.find('a', class_='ref')
                if first_ref:
                    ref_id = first_ref.get('id', '')
                    if ref_id:
                        page_ref = ref_id

                # 获取链接到的其他节点
                commentary_links = {}
                base_refs = []

                for link in div.find_all('a', class_='link2oth'):
                    link_id = link.get('id', '')
                    if link_id:
                        link_match = re.match(r'([A-Z]\d+)D\d+_\d+', link_id)
                        if link_match:
                            link_work_id = link_match.group(1)
                            if link_work_id == 'T1579':
                                base_refs.append(link_id)
                            elif link_work_id in self.DILA_TO_SUTRA:
                                sutra_id = self.DILA_TO_SUTRA[link_work_id]
                                commentary_links[sutra_id] = link_id

                segment = DilaSegment(
                    node_id=node_id,
                    head=head_text,
                    text=text,
                    page=page_ref,
                    path=path,
                    commentary_links=commentary_links,
                    base_refs=base_refs
                )
                segments.append(segment)
        else:
            # 没有科判标记，回退到解析普通段落
            # 查找 juan_text 容器
            juan_text = soup.find('div', class_='juan_text')
            if juan_text:
                # 获取卷标题
                jhead = juan_text.find('div', class_='jhead')
                jhead.get_text(strip=True) if jhead else f"卷第{juan_num}"

                # 获取所有段落
                all_paragraphs = juan_text.find_all('p', class_='normal')

                for idx, p in enumerate(all_paragraphs):
                    p_text = p.get_text(strip=True)
                    if not p_text:
                        continue

                    # 清除页码引用标记
                    p_text = re.sub(r'\[T\d+,\s*p?\d+[a-c]?\d*\]', '', p_text)
                    p_text = re.sub(r'\[\d+[a-c]\d+\]', '', p_text)
                    p_text = re.sub(r'\s+', ' ', p_text).strip()

                    if not p_text:
                        continue

                    # 获取页码引用
                    page_ref = ""
                    prev_ref = p.find_previous('a', class_='ref')
                    if prev_ref:
                        ref_id = prev_ref.get('id', '')
                        if ref_id:
                            page_ref = ref_id

                    segment = DilaSegment(
                        node_id=f"{work_id}_juan{juan_num}_p{idx+1}",
                        head="",  # 无科判时没有标题
                        text=p_text,
                        page=page_ref,
                        path="",
                        commentary_links={},
                        base_refs=[]
                    )
                    segments.append(segment)

                logger.info(f"解析 {work_id} 卷{juan_num}（无科判模式）: {len(segments)} 个段落")

        self._cache[cache_key] = segments
        logger.info(f"解析 {work_id} 卷{juan_num}: {len(segments)} 个段落")

        return segments

    def get_juan_content(self, sutra_id: str, juan_num: int) -> Optional[Dict[str, Any]]:
        """
        获取指定经论的指定卷内容

        Args:
            sutra_id: 经论ID
            juan_num: 卷号

        Returns:
            卷内容字典
        """
        if sutra_id not in self.SUPPORTED_SUTRAS:
            return None

        config = self.SUPPORTED_SUTRAS[sutra_id]
        dila_work = config.get('dila_work', '')

        segments = self._parse_dila_html(dila_work, juan_num)
        if not segments:
            return None

        return {
            'sutra_id': sutra_id,
            'juan_num': juan_num,
            'title': f"{config['title']} 卷第{juan_num}",
            'segments': [
                {
                    'id': seg.node_id,
                    'text': seg.text,
                    'page': seg.page,
                    'line_start': '',
                    'line_end': '',
                    'div_type': '',
                    'div_title': seg.head,
                    'refs': list(seg.commentary_links.values())
                }
                for seg in segments if seg.text  # 只返回有文本的段落
            ]
        }

    def get_parallel_reading(
        self,
        base_sutra_id: str,
        commentary_ids: List[str],
        juan_num: int,
        segment_index: int = 0,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        获取对读数据 - 使用 DILA 精确映射

        基于 DILA 的科判对应关系，实现经论与注疏的精确对齐。
        每个底本段落都有明确的注疏节点链接。

        Args:
            base_sutra_id: 底本经论ID
            commentary_ids: 注疏ID列表
            juan_num: 卷号
            segment_index: 起始段落索引
            page_size: 每页段落数

        Returns:
            对读数据
        """
        result = {
            'base': None,
            'commentaries': [],
            'total_segments': 0,
            'current_index': segment_index,
            'page_size': page_size,
            'page_range': None,
            'alignment_method': 'dila_mapping'  # 标记使用 DILA 映射
        }

        # 获取底本配置
        if base_sutra_id not in self.SUPPORTED_SUTRAS:
            return result

        base_config = self.SUPPORTED_SUTRAS[base_sutra_id]
        base_dila_work = base_config.get('dila_work', '')

        # 解析底本 DILA HTML
        base_segments = self._parse_dila_html(base_dila_work, juan_num)
        if not base_segments:
            return result

        # 只保留有文本的段落
        base_segments = [seg for seg in base_segments if seg.text]
        total = len(base_segments)
        result['total_segments'] = total

        # 分页获取底本段落
        start = segment_index
        end = min(start + page_size, total)
        selected_base = base_segments[start:end]

        # 收集页码范围
        page_codes = set()
        for seg in selected_base:
            if seg.page:
                page_code = seg.page[:4] if len(seg.page) >= 4 else seg.page
                page_codes.add(page_code)
        result['page_range'] = sorted(list(page_codes))

        # 构建底本响应
        result['base'] = {
            'sutra_id': base_sutra_id,
            'juan_num': juan_num,
            'title': f"{base_config['title']} 卷第{juan_num}",
            'segments': [
                {
                    'id': seg.node_id,
                    'text': seg.text,
                    'page': seg.page,
                    'line_start': '',
                    'line_end': '',
                    'div_type': '',
                    'div_title': seg.head,
                    'refs': list(seg.commentary_links.keys())
                }
                for seg in selected_base
            ]
        }

        # 构建底本节点集合（用于精确匹配）
        base_node_ids = {seg.node_id for seg in base_segments}

        # 收集所有需要的注疏节点
        for comm_sutra_id in commentary_ids:
            if comm_sutra_id not in self.SUPPORTED_SUTRAS:
                continue

            comm_config = self.SUPPORTED_SUTRAS[comm_sutra_id]
            comm_dila_work = comm_config.get('dila_work', '')
            comm_total_juans = comm_config.get('total_juans', 16)

            # DILA 已有科判数据的卷数限制
            dila_available_juans = {
                'T1828': 24,  # 瑜伽论记 DILA 已完成 24 卷科判
                'T1829': 16,  # 略纂完整 16 卷
            }
            max_juan = dila_available_juans.get(comm_dila_work, comm_total_juans)

            # 收集注疏的完整内容
            all_comm_segments = []
            juans_used = set()

            # 查找与当前底本卷相关的注疏卷
            # 策略：精确匹配底本节点ID，只显示引用了当前底本卷具体节点的注疏
            relevant_juans = set()
            for comm_juan in range(1, max_juan + 1):
                comm_segments = self._parse_dila_html(comm_dila_work, comm_juan)
                if not comm_segments:
                    continue

                # 检查该卷是否有引用当前底本卷的具体节点
                for comm_seg in comm_segments:
                    for ref in comm_seg.base_refs:
                        if ref in base_node_ids:
                            relevant_juans.add(comm_juan)
                            break
                    if comm_juan in relevant_juans:
                        break

            # 如果没有找到精确匹配的卷，按卷号比例对应
            # 《瑜伽论记》48卷注释100卷底本，约2:1
            # 《略纂》16卷注释100卷底本，约6:1
            if not relevant_juans:
                if comm_dila_work == 'T1828':
                    # 瑜伽论记：底本卷N -> 论记卷(N*48/100)
                    mapped_juan = max(1, min(max_juan, (juan_num * 48) // 100 + 1))
                    relevant_juans.add(mapped_juan)
                elif comm_dila_work == 'T1829':
                    # 略纂：底本卷N -> 略纂卷(N*16/100)
                    mapped_juan = max(1, min(max_juan, (juan_num * 16) // 100 + 1))
                    relevant_juans.add(mapped_juan)
                elif juan_num <= max_juan:
                    relevant_juans.add(juan_num)

            # 获取相关注疏卷中与当前底本卷对应的段落
            for comm_juan in sorted(relevant_juans):
                comm_segments = self._parse_dila_html(comm_dila_work, comm_juan)
                if not comm_segments:
                    continue

                # 对于底本卷1，包含注疏的序言部分（开头没有底本引用的段落）
                include_preface = (juan_num == 1 and comm_juan == 1)
                first_ref_found = False

                for comm_seg in comm_segments:
                    if not comm_seg.text:
                        continue

                    # 查找对应的底本引用（精确匹配）
                    base_ref = None
                    for ref in comm_seg.base_refs:
                        if ref in base_node_ids:
                            base_ref = ref
                            break

                    # 添加段落的条件：
                    # 1. 有底本引用
                    # 2. 或者是底本卷1时，包含注疏卷1的序言（开头连续无引用的段落）
                    if base_ref:
                        first_ref_found = True
                        juans_used.add(comm_juan)
                        all_comm_segments.append({
                            'id': comm_seg.node_id,
                            'text': comm_seg.text,
                            'page': comm_seg.page,
                            'line_start': '',
                            'line_end': '',
                            'div_type': '',
                            'div_title': comm_seg.head,
                            'refs': comm_seg.base_refs,
                            'base_ref': base_ref
                        })
                    elif include_preface and not first_ref_found:
                        # 序言部分：开头连续没有引用的段落
                        juans_used.add(comm_juan)
                        all_comm_segments.append({
                            'id': comm_seg.node_id,
                            'text': comm_seg.text,
                            'page': comm_seg.page,
                            'line_start': '',
                            'line_end': '',
                            'div_type': '',
                            'div_title': comm_seg.head,
                            'refs': [],
                            'base_ref': None
                        })

            # 构建注疏标题（显示来源卷号）
            if juans_used:
                juans_str = ', '.join([str(j) for j in sorted(juans_used)])
                comm_title = f"{comm_config['title']}（卷{juans_str}）"
            else:
                comm_title = f"{comm_config['title']}（暂无对应）"

            result['commentaries'].append({
                'sutra_id': comm_sutra_id,
                'juan_num': juan_num,
                'title': comm_title,
                'segments': all_comm_segments
            })

        return result

    def get_structure(self, sutra_id: str) -> Optional[Dict[str, Any]]:
        """
        获取经论的目录结构

        Args:
            sutra_id: 经论ID

        Returns:
            目录结构
        """
        if sutra_id not in self.SUPPORTED_SUTRAS:
            return None

        config = self.SUPPORTED_SUTRAS[sutra_id]

        # 简单返回卷列表
        juans = []
        for i in range(1, config.get('total_juans', 100) + 1):
            juans.append({
                'juan_num': i,
                'title': f'卷第{i}'
            })

        return {
            'sutra_id': sutra_id,
            'title': config.get('title', ''),
            'author': config.get('author', ''),
            'juans': juans
        }

    def search_text(
        self,
        sutra_id: str,
        query: str,
        juan_num: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        在经论中搜索文本

        Args:
            sutra_id: 经论ID
            query: 搜索词
            juan_num: 可选，限定卷号

        Returns:
            搜索结果列表
        """
        results = []
        if sutra_id not in self.SUPPORTED_SUTRAS:
            return results

        config = self.SUPPORTED_SUTRAS[sutra_id]

        if juan_num:
            juan_range = [juan_num]
        else:
            # 只搜索前几卷（避免太慢）
            juan_range = range(1, min(6, config.get('total_juans', 100) + 1))

        for jn in juan_range:
            content = self.get_juan_content(sutra_id, jn)
            if content:
                for seg in content['segments']:
                    if query in seg['text']:
                        # 高亮匹配文本
                        highlighted = seg['text'].replace(
                            query,
                            f'<mark>{query}</mark>'
                        )
                        results.append({
                            'sutra_id': sutra_id,
                            'juan_num': jn,
                            'segment_id': seg['id'],
                            'text': seg['text'],
                            'highlighted': highlighted,
                            'page': seg['page']
                        })

        return results


# 创建全局实例
sutra_reading_service = SutraReadingService()
