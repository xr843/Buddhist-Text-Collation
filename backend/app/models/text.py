"""
文本版本数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..core.database import Base


class TextRole(str, enum.Enum):
    """文本角色"""
    BASE = "base"  # 底本
    COLLATION = "collation"  # 校本
    REFERENCE = "reference"  # 参考本


class TextSource(str, enum.Enum):
    """文本来源"""
    UPLOAD = "upload"  # 用户上传
    AI_PUNCTUATION = "ai_punctuation"  # AI标点结果
    CBETA = "cbeta"  # CBETA数据库
    MANUAL = "manual"  # 手工录入


class Text(Base):
    """文本版本模型"""
    __tablename__ = "texts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)

    # 文本内容
    content = Column(Text, nullable=False)  # 完整文本内容
    content_length = Column(Integer)  # 文本长度（字符数）

    # 文本属性
    role = Column(Enum(TextRole), nullable=False, default=TextRole.BASE)
    source = Column(Enum(TextSource), nullable=False, default=TextSource.UPLOAD)

    # 版本信息
    version_name = Column(String(100))  # 版本名称，如"大正藏"、"房山石经"
    version_code = Column(String(50))  # 版本编码
    era = Column(String(50))  # 年代
    dynasty = Column(String(50))  # 朝代

    # 关联项目
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))

    # 上传者
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # 文件信息
    original_filename = Column(String(255))  # 原始文件名
    file_path = Column(String(500))  # 文件存储路径
    file_size = Column(Integer)  # 文件大小（字节）
    encoding = Column(String(20), default="utf-8")  # 文本编码

    # 元数据（JSONB存储）
    text_metadata = Column(JSON, default={})
    # 例如: {
    #     "scripture_name": "金刚经",
    #     "sutra_number": "T235",
    #     "volume": "8",
    #     "author": "鸠摩罗什译",
    #     "notes": "..."
    # }

    # 标点处理状态
    is_punctuated = Column(Boolean, default=False)  # 是否已标点
    punctuation_model = Column(String(50))  # 使用的标点模型（fast/expert）

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="texts")
    uploader = relationship("User", back_populates="texts")

    def __repr__(self):
        return f"<Text(id={self.id}, title='{self.title}', role='{self.role}')>"

    @property
    def word_count(self) -> int:
        """计算字数（中文字符数）"""
        if not self.content:
            return 0
        # 简单统计中文字符数
        return sum(1 for char in self.content if '\u4e00' <= char <= '\u9fff')
