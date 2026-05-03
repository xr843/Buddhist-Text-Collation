"""
经论注疏对读API

提供《瑜伽师地论》与《瑜伽论记》《瑜伽师地论略纂》的对读功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.sutra_reading_service import sutra_reading_service

router = APIRouter(prefix="/sutra-reading", tags=["经论注疏对读"])


class SutraInfoResponse(BaseModel):
    """经论信息响应"""
    id: str
    title: str
    author: str
    total_juans: int
    description: str


class TextSegmentResponse(BaseModel):
    """文本片段响应"""
    id: str
    text: str
    page: str
    line_start: str
    line_end: str
    div_type: str
    div_title: str
    refs: List[str]
    base_ref: Optional[str] = None  # 注疏段落对应的底本节点ID


class JuanContentResponse(BaseModel):
    """卷内容响应"""
    sutra_id: str
    juan_num: int
    title: str
    segments: List[TextSegmentResponse]


class ParallelReadingResponse(BaseModel):
    """对读响应"""
    base: Optional[JuanContentResponse]
    commentaries: List[JuanContentResponse]
    total_segments: int
    current_index: int
    page_size: int


class JuanInfo(BaseModel):
    """卷信息"""
    juan_num: int
    title: str


class StructureResponse(BaseModel):
    """目录结构响应"""
    sutra_id: str
    title: str
    author: str
    juans: List[JuanInfo]


class SearchResult(BaseModel):
    """搜索结果"""
    sutra_id: str
    juan_num: int
    segment_id: str
    text: str
    highlighted: str
    page: str


@router.get("/sutras", response_model=List[SutraInfoResponse])
async def get_available_sutras():
    """
    获取可用的经论列表

    Returns:
        可用经论的列表，包含ID、标题、作者等信息
    """
    sutras = sutra_reading_service.get_available_sutras()
    return [
        SutraInfoResponse(
            id=s.id,
            title=s.title,
            author=s.author,
            total_juans=s.total_juans,
            description=s.description
        )
        for s in sutras
    ]


@router.get("/sutras/{sutra_id}/structure", response_model=StructureResponse)
async def get_sutra_structure(sutra_id: str):
    """
    获取经论的目录结构

    Args:
        sutra_id: 经论ID（如 T30n1579）

    Returns:
        目录结构，包含卷列表
    """
    structure = sutra_reading_service.get_structure(sutra_id)
    if structure is None:
        raise HTTPException(status_code=404, detail=f"经论 {sutra_id} 不存在或未加载")

    return StructureResponse(**structure)


@router.get("/sutras/{sutra_id}/juan/{juan_num}", response_model=JuanContentResponse)
async def get_juan_content(sutra_id: str, juan_num: int):
    """
    获取指定经论的指定卷内容

    Args:
        sutra_id: 经论ID
        juan_num: 卷号

    Returns:
        卷内容，包含所有段落
    """
    content = sutra_reading_service.get_juan_content(sutra_id, juan_num)
    if content is None:
        raise HTTPException(
            status_code=404,
            detail=f"经论 {sutra_id} 卷{juan_num} 不存在或解析失败"
        )

    return JuanContentResponse(**content)


@router.get("/parallel", response_model=ParallelReadingResponse)
async def get_parallel_reading(
    base_id: str = Query(..., description="底本经论ID，如 T30n1579"),
    commentary_ids: str = Query(..., description="注疏ID，逗号分隔，如 T42n1828,T43n1829"),
    juan_num: int = Query(..., description="卷号"),
    segment_index: int = Query(0, description="起始段落索引"),
    page_size: int = Query(10, description="每页段落数")
):
    """
    获取经论与注疏的对读数据

    Args:
        base_id: 底本经论ID
        commentary_ids: 注疏ID列表，逗号分隔
        juan_num: 卷号
        segment_index: 起始段落索引
        page_size: 每页段落数

    Returns:
        对读数据，包含底本和注疏的段落内容
    """
    comm_ids = [id.strip() for id in commentary_ids.split(',') if id.strip()]

    result = sutra_reading_service.get_parallel_reading(
        base_sutra_id=base_id,
        commentary_ids=comm_ids,
        juan_num=juan_num,
        segment_index=segment_index,
        page_size=page_size
    )

    return ParallelReadingResponse(**result)


@router.get("/search", response_model=List[SearchResult])
async def search_sutra_text(
    sutra_id: str = Query(..., description="经论ID"),
    query: str = Query(..., description="搜索词"),
    juan_num: Optional[int] = Query(None, description="可选，限定卷号")
):
    """
    在经论中搜索文本

    Args:
        sutra_id: 经论ID
        query: 搜索词
        juan_num: 可选，限定卷号

    Returns:
        搜索结果列表
    """
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="搜索词至少需要2个字符")

    results = sutra_reading_service.search_text(sutra_id, query, juan_num)
    return [SearchResult(**r) for r in results]


@router.get("/presets")
async def get_reading_presets():
    """
    获取预设的对读组合

    Returns:
        预设列表，每个预设包含底本和注疏的组合
    """
    return [
        {
            "id": "yogacarabhumi",
            "name": "《瑜伽师地论》三家对读",
            "description": "基于 DILA 瑜伽师地论数据库的精确对应关系。《瑜伽师地论》100卷，《瑜伽论记》24卷（DILA已完成科判），《略纂》16卷。",
            "base_id": "T30n1579",
            "commentary_ids": ["T42n1828", "T43n1829"],
            "available_juans": list(range(1, 101)),  # 《瑜伽师地论》全100卷
            "data_source": "DILA 瑜伽师地论数据库 (https://ybh.dila.edu.tw)"
        }
    ]
