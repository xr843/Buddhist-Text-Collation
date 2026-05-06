"""
协作项目数据模型
用于支持多人协作的校勘项目
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import datetime

from ..core.database import Base


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class CollabProjectType(str, enum.Enum):
    """协作项目类型"""
    MULTI_COLLATION = "multi_collation"  # 多版本校勘
    TWO_VERSION = "two_version"          # 双版本对勘
    PUNCTUATION = "punctuation"          # 标点项目


class CollabProjectStatus(str, enum.Enum):
    """项目状态"""
    DRAFT = "draft"           # 草稿
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"   # 已完成


class ProjectVisibility(str, enum.Enum):
    """项目可见性"""
    PRIVATE = "private"   # 仅所有者和被共享成员可见
    SHARED = "shared"     # 所有登录用户可见（只读）
    PUBLIC = "public"     # 无需登录即可查看


class MemberRole(str, enum.Enum):
    """项目成员角色"""
    VIEWER = "viewer"     # 只读
    EDITOR = "editor"     # 可编辑
    ADMIN = "admin"       # 管理员（可管理成员）


class EditAction(str, enum.Enum):
    """编辑操作类型"""
    CREATE = "create"
    UPDATE = "update"
    DECISION = "decision"  # 判取操作
    EXPORT = "export"
    DELETE = "delete"


def generate_project_id() -> str:
    """生成项目ID: proj_YYYYMMDD_UUID"""
    date_str = datetime.now().strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:8]
    return f"proj_{date_str}_{short_uuid}"


class CollabProject(Base):
    """协作校勘项目模型"""
    __tablename__ = "collab_projects"

    id = Column(String(50), primary_key=True, default=generate_project_id)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # 所有者
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 项目类型和状态
    project_type = Column(
        Enum(CollabProjectType, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=CollabProjectType.MULTI_COLLATION,
    )
    status = Column(
        Enum(CollabProjectStatus, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=CollabProjectStatus.IN_PROGRESS,
    )
    visibility = Column(
        Enum(ProjectVisibility, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=ProjectVisibility.PRIVATE,
    )

    # 核心数据（JSONB）- 包含 base, collations, summary, variant_table, phylogeny, decisions
    data = Column(JSONB, default={})

    # 元数据（JSONB）- 包含统计信息
    # 例如: {"base_name": "大正藏", "collation_count": 5, "variant_count": 120}
    project_meta = Column(JSONB, default={})

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    owner = relationship("User", back_populates="collab_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="project", cascade="all, delete-orphan")
    history = relationship("EditHistory", back_populates="project", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("ix_collab_projects_owner_id", "owner_id"),
        Index("ix_collab_projects_status", "status"),
        Index("ix_collab_projects_visibility", "visibility"),
        Index("ix_collab_projects_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<CollabProject(id='{self.id}', title='{self.title}', type='{self.project_type}')>"


class ProjectMember(Base):
    """项目成员模型（多对多关联）"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("collab_projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum(MemberRole, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
        default=MemberRole.VIEWER,
    )

    # 邀请者
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("CollabProject", back_populates="members")
    user = relationship("User", back_populates="project_memberships", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    # 唯一约束：同一用户在同一项目中只能有一个角色
    __table_args__ = (
        Index("ix_project_members_project_user", "project_id", "user_id", unique=True),
    )

    def __repr__(self):
        return f"<ProjectMember(project='{self.project_id}', user={self.user_id}, role='{self.role}')>"


class Comment(Base):
    """评论模型"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("collab_projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 关联的异文序号（可选，用于针对特定异文的评论）
    variant_index = Column(Integer, nullable=True)

    # 评论内容
    content = Column(Text, nullable=False)

    # 回复关系（自引用）
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    project = relationship("CollabProject", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")

    # 索引
    __table_args__ = (
        Index("ix_comments_project_id", "project_id"),
        Index("ix_comments_user_id", "user_id"),
        Index("ix_comments_variant_index", "variant_index"),
        Index("ix_comments_parent_id", "parent_id"),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, project='{self.project_id}', user={self.user_id})>"


class EditHistory(Base):
    """编辑历史模型"""
    __tablename__ = "edit_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(50), ForeignKey("collab_projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 操作类型
    action = Column(
        Enum(EditAction, values_callable=enum_values, native_enum=False, length=32),
        nullable=False,
    )

    # 变更详情（JSONB）
    # 例如: {"field": "decisions", "variant_index": 5, "old_value": null, "new_value": "底本"}
    details = Column(JSONB, default={})

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("CollabProject", back_populates="history")
    user = relationship("User", back_populates="edit_history")

    # 索引
    __table_args__ = (
        Index("ix_edit_history_project_id", "project_id"),
        Index("ix_edit_history_user_id", "user_id"),
        Index("ix_edit_history_action", "action"),
        Index("ix_edit_history_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<EditHistory(id={self.id}, project='{self.project_id}', action='{self.action}')>"
