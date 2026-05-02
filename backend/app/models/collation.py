"""
校勘数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class DifferenceType(str, enum.Enum):
    """差异类型"""
    PUNCTUATION = "punctuation"  # 句读不同
    ADDITION = "addition"  # 增字
    DELETION = "deletion"  # 删字
    SUBSTITUTION = "substitution"  # 改字
    VARIANT = "variant"  # 异体字
    HOMOPHONE = "homophone"  # 通假字
    TABOO = "taboo"  # 避讳字
    STYLE = "style"  # 用字习惯差异


class DifferenceStatus(str, enum.Enum):
    """差异处理状态"""
    PENDING = "pending"  # 待处理
    IN_REVIEW = "in_review"  # 审核中
    RESOLVED = "resolved"  # 已解决
    IGNORED = "ignored"  # 已忽略


class Difference(Base):
    """差异记录模型"""
    __tablename__ = "differences"

    id = Column(Integer, primary_key=True, index=True)

    # 关联项目
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # 差异位置信息
    base_text_id = Column(Integer, ForeignKey("texts.id", ondelete="CASCADE"))
    collation_text_id = Column(Integer, ForeignKey("texts.id", ondelete="CASCADE"))

    position_start = Column(Integer, nullable=False)  # 差异起始位置
    position_end = Column(Integer, nullable=False)  # 差异结束位置

    # 差异内容
    base_content = Column(Text)  # 底本内容
    collation_content = Column(Text)  # 校本内容
    context_before = Column(String(100))  # 前文上下文
    context_after = Column(String(100))  # 后文上下文

    # 差异分类
    difference_type = Column(Enum(DifferenceType), nullable=False)
    status = Column(Enum(DifferenceStatus), default=DifferenceStatus.PENDING)

    # AI建议（JSONB存储）
    ai_suggestion = Column(JSON, default={})
    # 例如: {
    #     "suggested_type": "variant",
    #     "confidence": 0.85,
    #     "explanation": "這是異體字的差異",
    #     "references": ["說文解字", "康熙字典"]
    # }

    # 人工标注
    manual_annotation = Column(Text)  # 人工备注
    is_significant = Column(Boolean, default=True)  # 是否重要差异

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    collation_notes = relationship("CollationNote", back_populates="difference", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Difference(id={self.id}, type='{self.difference_type}', status='{self.status}')>"


class CollationNote(Base):
    """校勘记模型"""
    __tablename__ = "collation_notes"

    id = Column(Integer, primary_key=True, index=True)

    # 关联项目和差异
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    difference_id = Column(Integer, ForeignKey("differences.id", ondelete="CASCADE"))

    # 校勘记内容（富文本）
    content = Column(Text, nullable=False)  # 富文本HTML或Markdown
    content_format = Column(String(20), default="html")  # html或markdown

    # 校勘者信息
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    author_name = Column(String(100))  # 冗余字段，避免用户删除后丢失信息

    # 校勘决策
    decision = Column(Text)  # 校勘结论
    references = Column(JSON, default=[])  # 引用文献
    # 例如: [
    #     {"title": "大正藏校勘记", "page": "123"},
    #     {"title": "佛教大辞典", "entry": "金刚经"}
    # ]

    # 标签
    tags = Column(JSON, default=[])  # 标签列表，如["异体字", "重要"]

    # 版本控制
    version = Column(Integer, default=1)  # 版本号
    parent_note_id = Column(Integer, ForeignKey("collation_notes.id"))  # 父版本

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="collation_notes")
    difference = relationship("Difference", back_populates="collation_notes")

    def __repr__(self):
        return f"<CollationNote(id={self.id}, project_id={self.project_id})>"
