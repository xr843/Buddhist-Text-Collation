"""
对比API - Pydantic模型定义
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List


class ProjectUpdateRequest(BaseModel):
    """项目更新请求"""
    title: Optional[str] = None
    description: Optional[str] = None


class ComparisonRequest(BaseModel):
    """对比请求"""
    text1: str = Field(..., min_length=1, max_length=5000, description="第一个文本版本")
    text2: str = Field(..., min_length=1, max_length=5000, description="第二个文本版本")
    version1_name: str = Field("版本A", max_length=50, description="版本1名称")
    version2_name: str = Field("版本B", max_length=50, description="版本2名称")

    @validator("text1", "text2")
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("文本不能为空")
        return v.strip()


class ComparisonResponse(BaseModel):
    """对比响应"""
    success: bool = Field(..., description="是否成功")
    version1_name: str = Field(..., description="版本1名称")
    version2_name: str = Field(..., description="版本2名称")
    differences: list = Field(..., description="差异列表")
    statistics: dict = Field(..., description="统计信息")
    similarity: float = Field(..., description="相似度(0-1)")


class PunctuationComparisonRequest(BaseModel):
    """标点对比请求"""
    text1: str = Field(..., min_length=1, max_length=5000, description="第一个文本版本（带标点）")
    text2: str = Field(..., min_length=1, max_length=5000, description="第二个文本版本（带标点）")
    version1_name: str = Field("版本A", max_length=50, description="版本1名称")
    version2_name: str = Field("版本B", max_length=50, description="版本2名称")


class PunctuationDecisionItem(BaseModel):
    """单个标点判取项"""
    diffId: int = Field(..., description="差异ID")
    position: int = Field(..., description="位置")
    selectedVersion: str = Field(..., description="采用的版本: version1 或 version2")
    selectedPunct: str = Field(..., description="采用的标点")
    note: Optional[str] = Field(None, description="备注")


class PunctuationDecisionsRequest(BaseModel):
    """保存标点判取请求"""
    decisions: Dict[str, Dict[str, Any]] = Field(..., description="判取结果字典，key为diffId")


class ExportCollationNotesRequest(BaseModel):
    """导出校勘记请求"""
    text1: str = Field(..., min_length=1, description="底本文本")
    text2: str = Field(..., min_length=1, description="校本文本")
    version1_name: str = Field("底本", max_length=50, description="底本名称")
    version2_name: str = Field("校本", max_length=50, description="校本名称")
    format: str = Field("txt", description="导出格式: txt, tei-xml, json, csv")
    include_context: bool = Field(True, description="是否包含上下文")
    title: str = Field("校勘记", max_length=100, description="标题")
