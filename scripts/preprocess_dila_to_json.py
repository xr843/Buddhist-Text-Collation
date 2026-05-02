#!/usr/bin/env python3
"""
预处理 DILA HTML 为结构化 JSON

将下载的 DILA HTML 文件解析并保存为 JSON 格式，
避免每次请求都解析 HTML，提升性能。

输入: data/dila/html/*.html
输出: data/dila/json/*.json
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent
HTML_DIR = PROJECT_ROOT / "data" / "dila" / "html"
JSON_DIR = PROJECT_ROOT / "data" / "dila" / "json"

# 典籍配置
WORKS = {
    "T1579": {"title": "瑜伽师地论", "total_juans": 100},
    "T1828": {"title": "瑜伽论记", "total_juans": 48},
    "T1829": {"title": "瑜伽师地论略纂", "total_juans": 16},
}

# DILA work ID 到 sutra_id 的映射
DILA_TO_SUTRA = {
    'T1579': 'T30n1579',
    'T1828': 'T42n1828',
    'T1829': 'T43n1829',
}


@dataclass
class Segment:
    """文本段落"""
    node_id: str                     # 节点 ID，如 T1579D08_001
    head: str                        # 科判标题
    text: str                        # 段落文本
    page: str                        # 页码引用
    path: str = ""                   # 层级路径
    commentary_links: Dict[str, str] = field(default_factory=dict)
    base_refs: List[str] = field(default_factory=list)


def clean_text(text: str) -> str:
    """清理文本，去除页码标记"""
    text = re.sub(r'\[T\d+,\s*p?\d+[a-c]?\d*\]', '', text)
    text = re.sub(r'\[\d+[a-c]\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_html(html_path: Path, work_id: str) -> List[Dict[str, Any]]:
    """解析单个 HTML 文件"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {html_path}, {e}")
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

            for lg in div.find_all('div', class_='lg', recursive=False):
                lg_text = lg.get_text(strip=True)
                if lg_text:
                    text_parts.append(lg_text)

            text = '\n'.join(text_parts)
            text = clean_text(text)

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
                        elif link_work_id in DILA_TO_SUTRA:
                            sutra_id = DILA_TO_SUTRA[link_work_id]
                            commentary_links[sutra_id] = link_id

            if text:  # 只保留有文本的段落
                segments.append({
                    'node_id': node_id,
                    'head': head_text,
                    'text': text,
                    'page': page_ref,
                    'path': path,
                    'commentary_links': commentary_links,
                    'base_refs': base_refs
                })
    else:
        # 没有科判标记，解析普通段落
        juan_text = soup.find('div', class_='juan_text')
        if juan_text:
            all_paragraphs = juan_text.find_all('p', class_='normal')
            juan_num = html_path.stem.split('_juan')[1] if '_juan' in html_path.stem else '1'

            for idx, p in enumerate(all_paragraphs):
                p_text = p.get_text(strip=True)
                if not p_text:
                    continue

                p_text = clean_text(p_text)
                if not p_text:
                    continue

                page_ref = ""
                prev_ref = p.find_previous('a', class_='ref')
                if prev_ref:
                    ref_id = prev_ref.get('id', '')
                    if ref_id:
                        page_ref = ref_id

                segments.append({
                    'node_id': f"{work_id}_juan{juan_num}_p{idx+1}",
                    'head': "",
                    'text': p_text,
                    'page': page_ref,
                    'path': "",
                    'commentary_links': {},
                    'base_refs': []
                })

    return segments


def process_work(work_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """处理单个典籍的所有卷"""
    logger.info(f"处理 {work_id} ({config['title']})...")

    work_data = {
        'work_id': work_id,
        'sutra_id': DILA_TO_SUTRA.get(work_id, work_id),
        'title': config['title'],
        'total_juans': config['total_juans'],
        'juans': {}
    }

    processed = 0
    for juan_num in range(1, config['total_juans'] + 1):
        html_file = HTML_DIR / f"{work_id}_juan{juan_num}.html"
        if not html_file.exists():
            logger.warning(f"  卷{juan_num} HTML不存在，跳过")
            continue

        segments = parse_html(html_file, work_id)
        if segments:
            work_data['juans'][str(juan_num)] = {
                'juan_num': juan_num,
                'segment_count': len(segments),
                'segments': segments
            }
            processed += 1
            logger.info(f"  卷{juan_num}: {len(segments)} 个段落")

    logger.info(f"  完成: {processed}/{config['total_juans']} 卷")
    return work_data


def build_alignment_index(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建对齐索引 - 从底本节点ID到注疏节点ID的映射

    结构: {
        "T1579D01_001": {
            "T42n1828": ["T1828D01_001", "T1828D01_002"],
            "T43n1829": ["T1829D01_001"]
        }
    }
    """
    logger.info("构建对齐索引...")

    alignment_index = {}

    # 遍历所有注疏
    for work_id in ['T1828', 'T1829']:
        if work_id not in all_data:
            continue

        sutra_id = DILA_TO_SUTRA[work_id]
        work_data = all_data[work_id]

        for juan_num, juan_data in work_data['juans'].items():
            for seg in juan_data['segments']:
                # 这个注疏段落引用了哪些底本节点
                for base_ref in seg.get('base_refs', []):
                    if base_ref not in alignment_index:
                        alignment_index[base_ref] = {}
                    if sutra_id not in alignment_index[base_ref]:
                        alignment_index[base_ref][sutra_id] = []
                    alignment_index[base_ref][sutra_id].append({
                        'node_id': seg['node_id'],
                        'juan': int(juan_num)
                    })

    logger.info(f"  索引条目数: {len(alignment_index)}")
    return alignment_index


def main():
    """主函数"""
    print("=" * 60)
    print("DILA HTML → JSON 预处理工具")
    print("=" * 60)

    # 检查输入目录
    if not HTML_DIR.exists():
        logger.error(f"HTML目录不存在: {HTML_DIR}")
        logger.error("请先运行 download_dila_complete.py 下载数据")
        return

    # 创建输出目录
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    # 处理所有典籍
    all_data = {}
    for work_id, config in WORKS.items():
        work_data = process_work(work_id, config)
        all_data[work_id] = work_data

        # 保存单个典籍的JSON
        output_file = JSON_DIR / f"{work_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(work_data, f, ensure_ascii=False, indent=2)
        logger.info(f"  保存: {output_file}")

    # 构建并保存对齐索引
    alignment_index = build_alignment_index(all_data)
    index_file = JSON_DIR / "alignment_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(alignment_index, f, ensure_ascii=False, indent=2)
    logger.info(f"保存对齐索引: {index_file}")

    # 保存元数据
    metadata = {
        'works': {k: {'sutra_id': DILA_TO_SUTRA[k], 'title': v['title'], 'total_juans': v['total_juans']}
                  for k, v in WORKS.items()},
        'total_segments': sum(
            sum(j['segment_count'] for j in w['juans'].values())
            for w in all_data.values()
        ),
        'alignment_entries': len(alignment_index)
    }
    meta_file = JSON_DIR / "metadata.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("预处理完成!")
    print(f"输出目录: {JSON_DIR}")
    print(f"总段落数: {metadata['total_segments']}")
    print(f"对齐索引: {metadata['alignment_entries']} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
