"""
Pydantic 模型定义
从 multi_collation.py 中提取
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProjectUpdateRequest(BaseModel):
    """项目更新请求"""
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    items: List[Dict[str, Any]]


class CollationDecisionItem(BaseModel):
    """校勘判取项"""
    position: int                          # 异文位置
    selectedVersion: str                   # 采用的版本
    selectedText: str                      # 采用的文字
    customText: Optional[str] = None       # 自定义文字
    duijiao: List[str] = []                # 对校依据
    benjiao: List[str] = []                # 本校依据
    tajiao: List[str] = []                 # 他校依据
    lijiao: List[str] = []                 # 理校依据
    note: str = ""                         # 详细说明
    uncertain: bool = False                # 是否存疑
    createdAt: str                         # 创建时间
    updatedAt: str                         # 更新时间
    commentary_matches: Optional[List[Dict[str, Any]]] = []  # 注疏匹配结果


class SaveDecisionsRequest(BaseModel):
    """保存判取结果请求"""
    decisions: Dict[str, CollationDecisionItem]  # key 为 position 字符串


class GenerateDefinitiveTextRequest(BaseModel):
    """生成定本请求"""
    include_uncertain: bool = False        # 是否包含存疑项


class RemoveCollationsRequest(BaseModel):
    """移除校本请求"""
    indices: List[int] = Field(default_factory=list, description="要移除的校本索引（0-based）")


class CanonLocationItem(BaseModel):
    """版本刻印地/流传地位置信息（可由用户补充/覆盖）"""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    city: str = Field(..., min_length=1)
    province: Optional[str] = None
    system: Optional[str] = None
    period: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=0, le=9999)
    description: Optional[str] = None


class UpdateCanonLocationsRequest(BaseModel):
    """更新项目的地理位置信息（按版本名映射）"""
    locations: Dict[str, CanonLocationItem] = Field(default_factory=dict)
