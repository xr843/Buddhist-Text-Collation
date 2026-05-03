"""
本地SQLite数据持久化模型
用于个人使用场景，无需用户系统
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Project(Base):
    """校勘项目表"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='项目标题')
    project_type = Column(String(50), nullable=False, comment='项目类型: two_version, multi_collation')

    # 基础文本信息
    base_text = Column(Text, comment='底本文本')
    base_name = Column(String(200), comment='底本名称')

    # 校本信息（JSON存储）
    collation_texts_json = Column(JSON, comment='校本列表: [{name, text, source}, ...]')

    # 对勘结果（JSON存储）
    results_json = Column(JSON, comment='对勘结果')

    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    last_modified = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='最后修改时间')
    status = Column(String(20), default='draft', comment='状态: draft, completed, archived')
    notes = Column(Text, comment='项目备注')

    # 统计信息
    total_differences = Column(Integer, default=0, comment='异文总数')
    avg_similarity = Column(Float, comment='平均相似度')

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', type='{self.project_type}')>"


class PhylogenyAnalysis(Base):
    """版本谱系分析表"""
    __tablename__ = 'phylogeny_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='分析标题')

    # 分析数据（JSON存储）
    similarity_matrix_json = Column(JSON, comment='相似度矩阵')
    shared_errors_json = Column(JSON, comment='共同异文数据')
    phylogeny_tree_json = Column(JSON, comment='谱系树数据')
    conclusions_json = Column(JSON, comment='分析结论')

    # 版本信息
    base_name = Column(String(200), comment='底本名称')
    version_count = Column(Integer, default=0, comment='版本数量')

    # 元数据
    created_at = Column(DateTime, default=datetime.now)
    notes = Column(Text, comment='分析备注')

    # 关联的校勘项目（可选）
    related_project_id = Column(Integer, comment='关联的校勘项目ID')

    def __repr__(self):
        return f"<PhylogenyAnalysis(id={self.id}, title='{self.title}', versions={self.version_count})>"


class ExportHistory(Base):
    """导出历史表"""
    __tablename__ = 'export_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    export_type = Column(String(50), nullable=False, comment='导出类型: csv, word, tei_xml, markdown')
    source_type = Column(String(50), comment='来源类型: project, phylogeny')
    source_id = Column(Integer, comment='来源ID')

    file_path = Column(String(500), comment='导出文件路径')
    file_size = Column(Integer, comment='文件大小（字节）')

    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ExportHistory(id={self.id}, type='{self.export_type}')>"


class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, comment='设置键')
    value = Column(Text, comment='设置值')
    description = Column(String(500), comment='设置说明')

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<SystemSettings(key='{self.key}')>"
