"""
协作API请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ==================== 项目相关 ====================

class ProjectCreate(BaseModel):
    """创建项目请求"""
    title: str = Field(..., min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=2000, description="项目描述")
    project_type: str = Field(default="multi_collation", description="项目类型")
    visibility: str = Field(default="private", description="可见性: private/shared/public")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="项目标题")
    description: Optional[str] = Field(None, max_length=2000, description="项目描述")
    status: Optional[str] = Field(None, description="状态: draft/in_progress/completed")
    visibility: Optional[str] = Field(None, description="可见性: private/shared/public")


class ProjectDataUpdate(BaseModel):
    """更新项目数据请求"""
    data: Dict[str, Any] = Field(default_factory=dict, description="项目数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="项目元数据")
    merge: bool = Field(default=True, description="是否合并数据")


class ProjectSummary(BaseModel):
    """项目摘要"""
    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    project_type: Optional[str] = None
    owner_id: int
    my_role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectDetail(BaseModel):
    """项目详情"""
    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    project_type: Optional[str] = None
    owner_id: int
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    members: List[Dict[str, Any]] = Field(default_factory=list)
    my_role: Optional[str] = None


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    success: bool = True
    total: int
    items: List[ProjectSummary]


# ==================== 成员相关 ====================

class MemberAdd(BaseModel):
    """添加成员请求"""
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名（二选一）")
    email: Optional[str] = Field(None, description="邮箱（二选一）")
    role: str = Field(default="viewer", description="角色: viewer/editor/admin")


class MemberUpdate(BaseModel):
    """更新成员角色请求"""
    role: str = Field(..., description="新角色: viewer/editor/admin")


class MemberResponse(BaseModel):
    """成员信息"""
    id: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None


class MemberListResponse(BaseModel):
    """成员列表响应"""
    success: bool = True
    members: List[MemberResponse]


# ==================== 评论相关 ====================

class CommentCreate(BaseModel):
    """添加评论请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")
    variant_index: Optional[int] = Field(None, ge=0, description="关联的异文序号")
    parent_id: Optional[int] = Field(None, description="回复的评论ID")


class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="评论内容")


class CommentResponse(BaseModel):
    """评论信息"""
    id: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    content: str
    variant_index: Optional[int] = None
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CommentListResponse(BaseModel):
    """评论列表响应"""
    success: bool = True
    comments: List[CommentResponse]


# ==================== 编辑历史相关 ====================

class HistoryEntry(BaseModel):
    """编辑历史条目"""
    id: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class HistoryListResponse(BaseModel):
    """编辑历史响应"""
    success: bool = True
    history: List[HistoryEntry]


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    success: bool = True
    message: str
