"""
用户数据模型
"""
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class UserRole(str, enum.Enum):
    """系统用户角色"""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))

    # 用户角色
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(
        Enum(UserRole, values_callable=enum_values, native_enum=False, length=20),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )

    # 学术信息
    institution = Column(String(200))  # 所属机构
    research_field = Column(String(200))  # 研究领域
    bio = Column(Text)  # 个人简介
    avatar_url = Column(String(500))  # 头像URL

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # 关系
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    texts = relationship("Text", back_populates="uploader", cascade="all, delete-orphan")
    tasks = relationship("PunctuationTask", back_populates="user", cascade="all, delete-orphan")
    collab_projects = relationship(
        "CollabProject",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    project_memberships = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="ProjectMember.user_id",
    )
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    edit_history = relationship("EditHistory", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        """Compatibility helper used by admin and collaboration dependencies."""
        return bool(self.is_superuser or self.role == UserRole.ADMIN)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
