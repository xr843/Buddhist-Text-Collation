"""
知识库和对话相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 文档相关 ====================

class DocumentStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """创建文档请求"""
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    version_label: Optional[str] = Field(None, max_length=50)
    source: Optional[str] = Field(None, max_length=200)
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    project_id: int
    name: str
    version_label: Optional[str]
    source: Optional[str]
    status: DocumentStatus
    chunks_count: int
    uploaded_at: datetime
    indexed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    success: bool = True
    documents: List[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool = True
    document_id: int
    name: str
    chunks_count: int
    indexing_status: str
    message: Optional[str] = None


# ==================== 对话相关 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    session_id: Optional[int] = None  # 不提供则创建新会话
    message: str = Field(..., min_length=1, max_length=2000)
    n_contexts: int = Field(default=5, ge=1, le=20)


class Reference(BaseModel):
    """引用信息"""
    document_id: int
    document_name: Optional[str] = None
    version_label: Optional[str]
    source: Optional[str]
    excerpt: str
    position: Optional[Dict[str, int]] = None


class ChatResponse(BaseModel):
    """对话响应"""
    success: bool = True
    session_id: int
    message_id: int
    content: str
    references: List[Reference]
    created_at: datetime


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    id: int
    role: str
    content: str
    references: List[Reference]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    success: bool = True
    session_id: int
    title: str
    messages: List[ChatMessageResponse]


class ChatSessionResponse(BaseModel):
    """对话会话响应"""
    id: int
    project_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """对话会话列表响应"""
    success: bool = True
    sessions: List[ChatSessionResponse]
    total: int


# ==================== 项目知识库统计 ====================

class KnowledgeBaseStats(BaseModel):
    """知识库统计"""
    project_id: int
    documents_count: int
    chunks_count: int
    sessions_count: int
    messages_count: int


class KnowledgeBaseStatsResponse(BaseModel):
    """知识库统计响应"""
    success: bool = True
    stats: KnowledgeBaseStats


# ==================== 通用响应 ====================

class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    detail: Optional[str] = None
