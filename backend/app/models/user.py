"""
用户数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


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

    # 学术信息
    institution = Column(String(200))  # 所属机构
    research_field = Column(String(200))  # 研究领域
    bio = Column(Text)  # 个人简介

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # 关系
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    texts = relationship("Text", back_populates="uploader", cascade="all, delete-orphan")
    tasks = relationship("PunctuationTask", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
