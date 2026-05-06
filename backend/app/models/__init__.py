"""
数据模型包
"""
from .user import User, UserRole
from .project import Project, ProjectStatus, ProjectType
from .text import Text, TextRole, TextSource
from .collation import Difference, CollationNote, DifferenceType, DifferenceStatus
from .document import Document, DocumentChunk, DocumentStatus, ChatSession, ChatMessage
from .task import PunctuationTask
from .collaboration import (
    CollabProject,
    CollabProjectType,
    CollabProjectStatus,
    ProjectVisibility,
    ProjectMember,
    MemberRole,
    Comment,
    EditHistory,
    EditAction,
)

__all__ = [
    "User",
    "UserRole",
    "Project",
    "ProjectStatus",
    "ProjectType",
    "Text",
    "TextRole",
    "TextSource",
    "Difference",
    "CollationNote",
    "DifferenceType",
    "DifferenceStatus",
    # RAG相关
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "ChatSession",
    "ChatMessage",
    # 标点任务
    "PunctuationTask",
    # 协作
    "CollabProject",
    "CollabProjectType",
    "CollabProjectStatus",
    "ProjectVisibility",
    "ProjectMember",
    "MemberRole",
    "Comment",
    "EditHistory",
    "EditAction",
]
