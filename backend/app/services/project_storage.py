"""
项目存储服务 - 基于 JSON 文件的轻量级持久化

支持三类项目的存储：
1. 多版本对勘 (multi_collation)
2. 两版本对勘 (two_version)
3. 标点版本对比 (punctuation)

单用户使用，无需数据库和用户系统。
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from enum import Enum



class ProjectType(str, Enum):
    """项目类型"""
    MULTI_COLLATION = "multi_collation"     # 多版本对勘
    TWO_VERSION = "two_version"             # 两版本对勘
    PUNCTUATION = "punctuation"             # 标点版本对比
    SUTRA_COMMENTARY = "sutra_commentary"   # 经论-注疏关联


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"                 # 草稿（上传了文件但未开始对勘）
    IN_PROGRESS = "in_progress"     # 进行中
    COMPLETED = "completed"         # 已完成


class ProjectStorageService:
    """项目存储服务"""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化存储服务

        Args:
            base_dir: 项目存储根目录，默认为 backend/data/projects
        """
        if base_dir is None:
            # 默认存储在 backend/data/projects
            base_dir = Path(__file__).parent.parent.parent / "data" / "projects"

        self.base_dir = base_dir
        self._ensure_directories()

    def _atomic_write_json(self, path: Path, data: Any) -> None:
        """
        原子写入 JSON，避免写入中断导致文件损坏。

        策略：同目录写入临时文件 → flush+fsync → os.replace 原子替换。
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")

        payload = json.dumps(data, ensure_ascii=False, indent=2)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)

    def _ensure_directories(self):
        """确保存储目录存在"""
        for project_type in ProjectType:
            (self.base_dir / project_type.value).mkdir(parents=True, exist_ok=True)

    def _get_project_dir(self, project_type: ProjectType) -> Path:
        """获取项目类型对应的目录"""
        return self.base_dir / project_type.value

    def _get_project_path(self, project_type: ProjectType, project_id: str) -> Path:
        """获取项目文件路径"""
        return self._get_project_dir(project_type) / f"{project_id}.json"

    def _generate_project_id(self) -> str:
        """生成项目ID：日期_UUID前8位"""
        date_str = datetime.now().strftime("%Y%m%d")
        short_uuid = uuid.uuid4().hex[:8]
        return f"proj_{date_str}_{short_uuid}"

    # ==================== 通用 CRUD 操作 ====================

    def create_project(
        self,
        project_type: ProjectType,
        title: str,
        description: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建新项目

        Args:
            project_type: 项目类型
            title: 项目标题
            description: 项目描述（可选）
            data: 项目数据（如对勘结果）
            metadata: 项目元数据（如底本名、校本列表等）

        Returns:
            创建的项目信息
        """
        project_id = self._generate_project_id()
        now = datetime.now().isoformat()

        project = {
            "id": project_id,
            "type": project_type.value,
            "title": title,
            "description": description or "",
            "status": ProjectStatus.IN_PROGRESS.value,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
            "data": data or {},
        }

        # 保存到文件
        project_path = self._get_project_path(project_type, project_id)
        self._atomic_write_json(project_path, project)

        print(f"[项目存储] 创建项目: {project_id} ({title})")
        return project

    def get_project(self, project_type: ProjectType, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目详情

        Args:
            project_type: 项目类型
            project_id: 项目ID

        Returns:
            项目信息，不存在则返回 None
        """
        project_path = self._get_project_path(project_type, project_id)

        if not project_path.exists():
            return None

        with open(project_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_project(
        self,
        project_type: ProjectType,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        merge_data: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        更新项目

        Args:
            project_type: 项目类型
            project_id: 项目ID
            title: 新标题（可选）
            description: 新描述（可选）
            status: 新状态（可选）
            data: 新数据（可选）
            metadata: 新元数据（可选）
            merge_data: 是否合并数据（True=合并，False=覆盖）

        Returns:
            更新后的项目信息
        """
        project = self.get_project(project_type, project_id)
        if not project:
            return None

        # 更新字段
        if title is not None:
            project["title"] = title
        if description is not None:
            project["description"] = description
        if status is not None:
            project["status"] = status.value

        if metadata is not None:
            if merge_data:
                project["metadata"].update(metadata)
            else:
                project["metadata"] = metadata

        if data is not None:
            if merge_data:
                project["data"].update(data)
            else:
                project["data"] = data

        project["updated_at"] = datetime.now().isoformat()

        # 保存
        project_path = self._get_project_path(project_type, project_id)
        self._atomic_write_json(project_path, project)

        print(f"[项目存储] 更新项目: {project_id}")
        return project

    def update_project_data(
        self,
        project_type: ProjectType,
        project_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        更新项目数据（合并模式）

        专门用于更新 data 字段，保留其他字段不变。

        Args:
            project_type: 项目类型
            project_id: 项目ID
            data: 要更新的数据

        Returns:
            更新后的项目信息
        """
        project = self.get_project(project_type, project_id)
        if not project:
            return None

        # 合并 data 字段
        if "data" not in project:
            project["data"] = {}
        project["data"].update(data)

        project["updated_at"] = datetime.now().isoformat()

        # 保存
        project_path = self._get_project_path(project_type, project_id)
        self._atomic_write_json(project_path, project)

        print(f"[项目存储] 更新项目数据: {project_id}")
        return project

    def delete_project(self, project_type: ProjectType, project_id: str) -> bool:
        """
        删除项目

        Args:
            project_type: 项目类型
            project_id: 项目ID

        Returns:
            是否删除成功

        Raises:
            OSError: 文件删除失败时抛出异常（包含详细错误信息）
        """
        project_path = self._get_project_path(project_type, project_id)

        if not project_path.exists():
            return False

        try:
            project_path.unlink()
            print(f"[项目存储] 删除项目: {project_id}")
            return True
        except OSError as e:
            print(f"[项目存储] 删除项目失败: {project_id}, 错误: {e}")
            raise OSError(f"删除项目文件失败: {e.strerror}") from e

    def list_projects(
        self,
        project_type: ProjectType,
        status: Optional[ProjectStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取项目列表

        Args:
            project_type: 项目类型
            status: 筛选状态（可选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            {
                "total": 总数,
                "items": [项目摘要列表]
            }
        """
        project_dir = self._get_project_dir(project_type)
        projects = []

        # 读取所有项目文件
        for project_file in project_dir.glob("*.json"):
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    project = json.load(f)

                # 筛选状态
                if status and project.get("status") != status.value:
                    continue

                # 返回摘要信息（不含完整 data）
                summary = {
                    "id": project["id"],
                    "title": project["title"],
                    "description": project.get("description", ""),
                    "status": project["status"],
                    "created_at": project["created_at"],
                    "updated_at": project["updated_at"],
                    "metadata": project.get("metadata", {}),
                }
                projects.append(summary)
            except Exception as e:
                print(f"[项目存储] 读取项目文件失败: {project_file}, 错误: {e}")
                continue

        # 按更新时间倒序排列
        projects.sort(key=lambda x: x["updated_at"], reverse=True)

        total = len(projects)
        items = projects[offset:offset + limit]

        return {
            "total": total,
            "items": items,
        }

    # ==================== 多版本对勘专用方法 ====================

    def save_multi_collation(
        self,
        title: str,
        base_info: Dict[str, Any],
        collation_results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        variant_table: Dict[str, Any],
        phylogeny: Dict[str, Any],
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        保存多版本对勘结果

        Args:
            title: 项目标题
            base_info: 底本信息 {name, file, char_count, text}
            collation_results: 各校本对比结果列表
            summary: 汇总统计
            variant_table: 异文汇校表
            phylogeny: 版本谱系
            project_id: 项目ID（更新时传入）

        Returns:
            项目信息
        """
        # 统计“差异总数”（按校本逐一累加的差异条目数），用于与“异文位点数”区分展示
        diff_total = 0
        try:
            rows = summary.get("stats_table", {}).get("rows", []) if isinstance(summary, dict) else []
            diff_total = sum(int(r.get("total", 0) or 0) for r in rows if isinstance(r, dict))
        except Exception:
            diff_total = 0

        metadata = {
            "base_name": base_info.get("name", ""),
            "base_file": base_info.get("file", ""),
            "base_char_count": base_info.get("char_count", 0),
            "collation_count": len(collation_results),
            "collation_names": [c.get("collation_name", "") for c in collation_results],
            "variant_count": variant_table.get("total", 0),
            "diff_total": diff_total,
        }

        data = {
            "base": base_info,
            "collations": collation_results,
            "summary": summary,
            "variant_table": variant_table,
            "phylogeny": phylogeny,
        }

        if project_id:
            # 更新现有项目时，保留判取结果/地理信息等用户补充数据
            existing = self.get_project(ProjectType.MULTI_COLLATION, project_id)
            if existing:
                existing_data = existing.get("data", {}) or {}
                if "decisions" in existing_data:
                    data["decisions"] = existing_data.get("decisions")
                if "canon_locations_override" in existing_data:
                    data["canon_locations_override"] = existing_data.get("canon_locations_override")

            # 更新现有项目
            return self.update_project(
                ProjectType.MULTI_COLLATION,
                project_id,
                title=title,
                data=data,
                metadata=metadata,
                merge_data=False,
            )
        else:
            # 创建新项目
            return self.create_project(
                ProjectType.MULTI_COLLATION,
                title=title,
                data=data,
                metadata=metadata,
            )

    def add_collation_to_project(
        self,
        project_id: str,
        new_collation: Dict[str, Any],
        new_variant_table: Dict[str, Any],
        new_summary: Dict[str, Any],
        new_phylogeny: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        向已有项目追加校本

        Args:
            project_id: 项目ID
            new_collation: 新校本的对比结果
            new_variant_table: 更新后的异文汇校表
            new_summary: 更新后的汇总统计
            new_phylogeny: 更新后的版本谱系

        Returns:
            更新后的项目信息
        """
        if new_collation is None:
            raise ValueError("new_collation 不能为空（如需批量覆盖，请使用 update_project 直接写入 collations）")

        project = self.get_project(ProjectType.MULTI_COLLATION, project_id)
        if not project:
            return None

        # 追加校本
        collations = project["data"].get("collations", [])
        collations.append(new_collation)

        # 更新元数据
        metadata = project.get("metadata", {})
        metadata["collation_count"] = len(collations)
        metadata["collation_names"] = [c.get("collation_name", "") for c in collations]
        metadata["variant_count"] = new_variant_table.get("total", 0)
        try:
            rows = new_summary.get("stats_table", {}).get("rows", []) if isinstance(new_summary, dict) else []
            metadata["diff_total"] = sum(int(r.get("total", 0) or 0) for r in rows if isinstance(r, dict))
        except Exception:
            metadata["diff_total"] = metadata.get("diff_total", 0)

        # 更新数据
        data = {
            "base": project["data"]["base"],
            "collations": collations,
            "summary": new_summary,
            "variant_table": new_variant_table,
            "phylogeny": new_phylogeny,
        }
        existing_data = project.get("data", {}) or {}
        if "decisions" in existing_data:
            data["decisions"] = existing_data.get("decisions")
        if "canon_locations_override" in existing_data:
            data["canon_locations_override"] = existing_data.get("canon_locations_override")

        return self.update_project(
            ProjectType.MULTI_COLLATION,
            project_id,
            data=data,
            metadata=metadata,
            merge_data=False,
        )

    # ==================== 两版本对勘专用方法 ====================

    def save_two_version_collation(
        self,
        title: str,
        base_info: Dict[str, Any],
        collation_info: Dict[str, Any],
        result: Dict[str, Any],
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        保存两版本对勘结果

        Args:
            title: 项目标题
            base_info: 底本信息 {name, text, char_count}
            collation_info: 校本信息 {name, text, char_count}
            result: 对勘结果
            project_id: 项目ID（更新时传入）

        Returns:
            项目信息
        """
        metadata = {
            "base_name": base_info.get("name", ""),
            "collation_name": collation_info.get("name", ""),
            "base_char_count": base_info.get("char_count", 0),
            "collation_char_count": collation_info.get("char_count", 0),
            "similarity": result.get("similarity", 0),
            "total_differences": result.get("statistics", {}).get("total_differences", 0),
        }

        data = {
            "base": base_info,
            "collation": collation_info,
            "result": result,
        }

        if project_id:
            return self.update_project(
                ProjectType.TWO_VERSION,
                project_id,
                title=title,
                data=data,
                metadata=metadata,
                merge_data=False,
            )
        else:
            return self.create_project(
                ProjectType.TWO_VERSION,
                title=title,
                data=data,
                metadata=metadata,
            )

    # ==================== 标点版本对比专用方法 ====================

    def save_punctuation_comparison(
        self,
        title: str,
        version1_info: Dict[str, Any],
        version2_info: Dict[str, Any],
        result: Dict[str, Any],
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        保存标点版本对比结果

        Args:
            title: 项目标题
            version1_info: 版本1信息 {name, text, char_count}
            version2_info: 版本2信息 {name, text, char_count}
            result: 对比结果
            project_id: 项目ID（更新时传入）

        Returns:
            项目信息
        """
        metadata = {
            "version1_name": version1_info.get("name", "版本A"),
            "version2_name": version2_info.get("name", "版本B"),
            "version1_char_count": version1_info.get("char_count", 0),
            "version2_char_count": version2_info.get("char_count", 0),
            "total_differences": result.get("statistics", {}).get("total_differences", 0),
        }

        data = {
            "version1": version1_info,
            "version2": version2_info,
            "result": result,
        }

        if project_id:
            return self.update_project(
                ProjectType.PUNCTUATION,
                project_id,
                title=title,
                data=data,
                metadata=metadata,
                merge_data=False,
            )
        else:
            return self.create_project(
                ProjectType.PUNCTUATION,
                title=title,
                data=data,
                metadata=metadata,
            )


# 创建全局实例
project_storage = ProjectStorageService()
