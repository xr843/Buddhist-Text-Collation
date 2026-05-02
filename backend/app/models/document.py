"""
文档和RAG相关数据模型
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class DocumentStatus(str, enum.Enum):
    """文档状态"""
    PENDING = "pending"          # 待处理
    INDEXING = "indexing"        # 索引中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


class Document(Base):
    """文档表 - 存储上传的佛经文档"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    version_label = Column(String(50))  # "大正藏T235", "乾隆藏Q0423"
    source = Column(String(200))  # "CBETA", "SAT"
    metadata_ = Column("metadata", JSON, default=dict)  # 额外元数据

    # 索引状态
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    chunks_count = Column(Integer, default=0)
    error_message = Column(Text)

    # 时间戳
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    indexed_at = Column(DateTime(timezone=True))

    # 关系
    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, name='{self.name}', version='{self.version_label}')>"


class DocumentChunk(Base):
    """文档块表 - 用于RAG检索"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 块序号
    start_position = Column(Integer)  # 在原文中的起始位置
    end_position = Column(Integer)    # 在原文中的结束位置

    # 向量嵌入ID（存储在ChromaDB中的ID）
    vector_id = Column(String(100))

    # 元数据
    metadata_ = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"


class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # MVP可为空

    title = Column(String(200), default="新对话")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title='{self.title}')>"


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # 引用的文档位置（JSON格式）
    references = Column(JSON, default=list)

    # 元数据（如token数、响应时间等）
    metadata_ = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}')>"
