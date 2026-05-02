"""
校勘项目数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class ProjectStatus(str, enum.Enum):
    """项目状态"""
    DRAFT = "draft"  # 草稿
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档


class ProjectType(str, enum.Enum):
    """项目类型"""
    PUNCTUATION = "punctuation"  # 智能标点
    COMPARISON = "comparison"  # 版本对比
    COLLATION = "collation"  # 文本校勘


class Project(Base):
    """校勘项目模型"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # 项目类型和状态
    project_type = Column(Enum(ProjectType), nullable=False, default=ProjectType.COLLATION)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.DRAFT)

    # 所有者
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 项目元数据（JSONB存储）
    project_metadata = Column(JSON, default={})
    # 例如: {
    #     "base_text_era": "唐代",
    #     "scripture_name": "金刚经",
    #     "base_version": "大正藏",
    #     "collation_versions": ["房山石经", "敦煌写本"],
    #     "notes": "..."
    # }

    # 项目配置
    settings = Column(JSON, default={})
    # 例如: {
    #     "ai_model": "expert",
    #     "auto_save": true,
    #     "comparison_mode": "parallel"
    # }

    # 统计信息
    total_differences = Column(Integer, default=0)  # 总差异数
    processed_differences = Column(Integer, default=0)  # 已处理差异数

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # 关系
    owner = relationship("User", back_populates="projects")
    texts = relationship("Text", back_populates="project", cascade="all, delete-orphan")
    collation_notes = relationship("CollationNote", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', type='{self.project_type}')>"

    @property
    def progress_percentage(self) -> float:
        """计算项目进度百分比"""
        if self.total_differences == 0:
            return 0.0
        return (self.processed_differences / self.total_differences) * 100
