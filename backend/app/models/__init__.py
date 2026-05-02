"""
数据模型包
"""
from .user import User
from .project import Project, ProjectStatus, ProjectType
from .text import Text, TextRole, TextSource
from .collation import Difference, CollationNote, DifferenceType, DifferenceStatus
from .document import Document, DocumentChunk, DocumentStatus, ChatSession, ChatMessage
from .task import PunctuationTask

__all__ = [
    "User",
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
]
