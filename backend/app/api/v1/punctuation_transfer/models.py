"""
标点迁移 API 数据模型
"""
from pydantic import BaseModel, Field
from typing import List

# 文本字数上限（5万字）
MAX_TEXT_LENGTH = 50000


class TransferRequest(BaseModel):
    """标点迁移请求"""
    source_text: str = Field(
        ...,
        description="源文本（带标点）",
        min_length=1,
        max_length=MAX_TEXT_LENGTH
    )
    target_text: str = Field(
        ...,
        description="目标文本（无标点或少量标点）",
        min_length=1,
        max_length=MAX_TEXT_LENGTH
    )
    preserve_existing: bool = Field(
        default=False,
        description="是否保留目标文本中已有的标点"
    )


class TransferResponse(BaseModel):
    """标点迁移响应"""
    result_text: str = Field(..., description="迁移后的文本")
    transferred_count: int = Field(..., description="成功迁移的标点数量")
    total_punctuation_count: int = Field(..., description="源文本中的标点总数")
    alignment_score: float = Field(..., description="对齐分数（0-1）")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


class RemovePunctuationRequest(BaseModel):
    """清除标点请求"""
    text: str = Field(
        ...,
        description="待清除标点的文本",
        min_length=1,
        max_length=MAX_TEXT_LENGTH
    )


class RemovePunctuationResponse(BaseModel):
    """清除标点响应"""
    result_text: str = Field(..., description="清除标点后的文本")
    removed_count: int = Field(..., description="移除的标点数量")


class ExampleResponse(BaseModel):
    """示例文本响应"""
    source: str = Field(..., description="源文本（带标点）")
    target: str = Field(..., description="目标文本（无标点）")
