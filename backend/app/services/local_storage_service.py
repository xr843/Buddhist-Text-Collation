"""
本地SQLite数据持久化服务
提供项目、谱系分析的CRUD操作
"""
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

from app.models.local_storage import Base, Project, PhylogenyAnalysis, ExportHistory, SystemSettings

# 数据库文件路径
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "local_storage.db"

# 创建引擎（SQLite）
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # 单线程池，适合SQLite
    echo=False  # 生产环境设为False
)

# 创建所有表
Base.metadata.create_all(engine)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass


class ProjectService:
    """校勘项目服务"""

    @staticmethod
    def create_project(
        title: str,
        project_type: str,
        base_text: str = None,
        base_name: str = None,
        collation_texts: List[Dict] = None,
        results: Dict = None,
        notes: str = None
    ) -> Project:
        """创建新项目"""
        db = get_db()
        try:
            project = Project(
                title=title,
                project_type=project_type,
                base_text=base_text,
                base_name=base_name,
                collation_texts_json=collation_texts or [],
                results_json=results,
                notes=notes,
                status='draft'
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            return project
        finally:
            db.close()

    @staticmethod
    def get_project(project_id: int) -> Optional[Project]:
        """获取项目"""
        db = get_db()
        try:
            return db.query(Project).filter(Project.id == project_id).first()
        finally:
            db.close()

    @staticmethod
    def list_projects(
        project_type: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Project]:
        """列出项目"""
        db = get_db()
        try:
            query = db.query(Project)
            if project_type:
                query = query.filter(Project.project_type == project_type)
            if status:
                query = query.filter(Project.status == status)

            query = query.order_by(desc(Project.last_modified))
            return query.limit(limit).offset(offset).all()
        finally:
            db.close()

    @staticmethod
    def update_project(
        project_id: int,
        **kwargs
    ) -> Optional[Project]:
        """更新项目"""
        db = get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None

            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)

            project.last_modified = datetime.now()
            db.commit()
            db.refresh(project)
            return project
        finally:
            db.close()

    @staticmethod
    def delete_project(project_id: int) -> bool:
        """删除项目"""
        db = get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False

            db.delete(project)
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def save_results(project_id: int, results: Dict, total_differences: int = None, avg_similarity: float = None):
        """保存对勘结果"""
        db = get_db()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None

            project.results_json = results
            project.last_modified = datetime.now()
            project.status = 'completed'

            if total_differences is not None:
                project.total_differences = total_differences
            if avg_similarity is not None:
                project.avg_similarity = avg_similarity

            db.commit()
            db.refresh(project)
            return project
        finally:
            db.close()


class PhylogenyAnalysisService:
    """版本谱系分析服务"""

    @staticmethod
    def create_analysis(
        title: str,
        base_name: str,
        similarity_matrix: Dict,
        shared_errors: Dict = None,
        phylogeny_tree: Dict = None,
        conclusions: List[str] = None,
        version_count: int = 0,
        related_project_id: int = None
    ) -> PhylogenyAnalysis:
        """创建谱系分析"""
        db = get_db()
        try:
            analysis = PhylogenyAnalysis(
                title=title,
                base_name=base_name,
                similarity_matrix_json=similarity_matrix,
                shared_errors_json=shared_errors,
                phylogeny_tree_json=phylogeny_tree,
                conclusions_json=conclusions or [],
                version_count=version_count,
                related_project_id=related_project_id
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            return analysis
        finally:
            db.close()

    @staticmethod
    def get_analysis(analysis_id: int) -> Optional[PhylogenyAnalysis]:
        """获取谱系分析"""
        db = get_db()
        try:
            return db.query(PhylogenyAnalysis).filter(PhylogenyAnalysis.id == analysis_id).first()
        finally:
            db.close()

    @staticmethod
    def list_analyses(limit: int = 50, offset: int = 0) -> List[PhylogenyAnalysis]:
        """列出谱系分析"""
        db = get_db()
        try:
            return db.query(PhylogenyAnalysis).order_by(desc(PhylogenyAnalysis.created_at)).limit(limit).offset(offset).all()
        finally:
            db.close()


class ExportHistoryService:
    """导出历史服务"""

    @staticmethod
    def record_export(
        export_type: str,
        source_type: str,
        source_id: int,
        file_path: str,
        file_size: int = 0
    ) -> ExportHistory:
        """记录导出历史"""
        db = get_db()
        try:
            record = ExportHistory(
                export_type=export_type,
                source_type=source_type,
                source_id=source_id,
                file_path=file_path,
                file_size=file_size
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        finally:
            db.close()

    @staticmethod
    def list_exports(limit: int = 50) -> List[ExportHistory]:
        """列出导出历史"""
        db = get_db()
        try:
            return db.query(ExportHistory).order_by(desc(ExportHistory.created_at)).limit(limit).all()
        finally:
            db.close()


# 初始化默认设置
def init_default_settings():
    """初始化默认系统设置"""
    db = get_db()
    try:
        default_settings = [
            {
                "key": "auto_save_interval",
                "value": "300",
                "description": "自动保存间隔（秒）"
            },
            {
                "key": "max_versions_per_collation",
                "value": "31",
                "description": "多版本对勘最大版本数"
            }
        ]

        for setting in default_settings:
            existing = db.query(SystemSettings).filter(SystemSettings.key == setting["key"]).first()
            if not existing:
                db.add(SystemSettings(**setting))

        db.commit()
    finally:
        db.close()


# 启动时初始化
init_default_settings()
