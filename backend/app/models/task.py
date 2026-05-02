"""
标点任务模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PunctuationTask(Base):
    """标点处理任务表"""
    __tablename__ = "punctuation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 任务内容
    input_text = Column(Text, nullable=False)
    output_text = Column(Text)
    context = Column(String(500))

    # 处理信息
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    model_used = Column(String(50))
    confidence = Column(Float)
    processing_time = Column(Float)  # 秒
    tokens_used = Column(Integer)

    # 元数据
    task_metadata = Column(JSON)  # 存储额外信息（如分块信息、错误详情等）

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # 关系
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<PunctuationTask(id={self.id}, status='{self.status}')>"
