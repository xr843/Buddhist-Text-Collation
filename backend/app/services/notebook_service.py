"""
研究笔记本服务 - 协作研究笔记管理
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger


class NotebookService:
    """研究笔记本服务"""

    def __init__(self):
        """初始化笔记本服务"""
        self._notebooks_db: Dict[int, Dict[str, Any]] = {}
        self._notes_db: Dict[int, Dict[str, Any]] = {}
        self._versions_db: Dict[int, List[Dict[str, Any]]] = {}
        self._notebook_id_counter = 1
        self._note_id_counter = 1

    def _get_next_notebook_id(self) -> int:
        current = self._notebook_id_counter
        self._notebook_id_counter += 1
        return current

    def _get_next_note_id(self) -> int:
        current = self._note_id_counter
        self._note_id_counter += 1
        return current

    # ==================== 笔记本管理 ====================

    def create_notebook(
            self,
            title: str,
            description: str = "",
            tags: List[str] = None
    ) -> Dict[str, Any]:
        """创建研究笔记本"""
        notebook_id = self._get_next_notebook_id()
        now = datetime.now()

        notebook = {
            "id": notebook_id,
            "title": title,
            "description": description,
            "tags": tags or [],
            "note_count": 0,
            "created_at": now,
            "updated_at": now
        }

        self._notebooks_db[notebook_id] = notebook
        logger.info(f"创建笔记本: {title} (ID: {notebook_id})")

        return notebook

    def get_notebook(self, notebook_id: int) -> Optional[Dict[str, Any]]:
        """获取笔记本详情"""
        return self._notebooks_db.get(notebook_id)

    def list_notebooks(
            self,
            tag: Optional[str] = None,
            search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取笔记本列表"""
        notebooks = list(self._notebooks_db.values())

        # 标签过滤
        if tag:
            notebooks = [n for n in notebooks if tag in n.get("tags", [])]

        # 搜索过滤
        if search:
            search_lower = search.lower()
            notebooks = [
                n for n in notebooks
                if search_lower in n["title"].lower()
                or search_lower in n.get("description", "").lower()
            ]

        # 按更新时间排序
        notebooks.sort(key=lambda x: x["updated_at"], reverse=True)

        return notebooks

    def update_notebook(
            self,
            notebook_id: int,
            title: Optional[str] = None,
            description: Optional[str] = None,
            tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """更新笔记本"""
        if notebook_id not in self._notebooks_db:
            return None

        notebook = self._notebooks_db[notebook_id]

        if title is not None:
            notebook["title"] = title
        if description is not None:
            notebook["description"] = description
        if tags is not None:
            notebook["tags"] = tags

        notebook["updated_at"] = datetime.now()

        return notebook

    def delete_notebook(self, notebook_id: int) -> bool:
        """删除笔记本及其所有笔记"""
        if notebook_id not in self._notebooks_db:
            return False

        # 删除笔记本下的所有笔记
        note_ids_to_delete = [
            nid for nid, note in self._notes_db.items()
            if note.get("notebook_id") == notebook_id
        ]
        for note_id in note_ids_to_delete:
            del self._notes_db[note_id]
            if note_id in self._versions_db:
                del self._versions_db[note_id]

        del self._notebooks_db[notebook_id]
        logger.info(f"删除笔记本: {notebook_id}")

        return True

    # ==================== 笔记管理 ====================

    def create_note(
            self,
            notebook_id: int,
            title: str,
            content: str = "",
            tags: List[str] = None,
            source_text: str = "",
            related_punctuation_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """创建笔记"""
        if notebook_id not in self._notebooks_db:
            return None

        note_id = self._get_next_note_id()
        now = datetime.now()

        note = {
            "id": note_id,
            "notebook_id": notebook_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "source_text": source_text,
            "related_punctuation_id": related_punctuation_id,
            "version": 1,
            "created_at": now,
            "updated_at": now
        }

        self._notes_db[note_id] = note

        # 保存初始版本
        self._versions_db[note_id] = [{
            "version": 1,
            "content": content,
            "title": title,
            "timestamp": now,
            "change_summary": "创建笔记"
        }]

        # 更新笔记本计数
        self._notebooks_db[notebook_id]["note_count"] += 1
        self._notebooks_db[notebook_id]["updated_at"] = now

        logger.info(f"创建笔记: {title} (ID: {note_id})")

        return note

    def get_note(self, note_id: int) -> Optional[Dict[str, Any]]:
        """获取笔记详情"""
        note = self._notes_db.get(note_id)
        if note:
            note = note.copy()
            note["version_count"] = len(self._versions_db.get(note_id, []))
        return note

    def list_notes(
            self,
            notebook_id: int,
            tag: Optional[str] = None,
            search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取笔记本下的笔记列表"""
        notes = [
            n for n in self._notes_db.values()
            if n.get("notebook_id") == notebook_id
        ]

        # 标签过滤
        if tag:
            notes = [n for n in notes if tag in n.get("tags", [])]

        # 搜索过滤
        if search:
            search_lower = search.lower()
            notes = [
                n for n in notes
                if search_lower in n["title"].lower()
                or search_lower in n.get("content", "").lower()
            ]

        # 按更新时间排序
        notes.sort(key=lambda x: x["updated_at"], reverse=True)

        return notes

    def update_note(
            self,
            note_id: int,
            title: Optional[str] = None,
            content: Optional[str] = None,
            tags: Optional[List[str]] = None,
            change_summary: str = ""
    ) -> Optional[Dict[str, Any]]:
        """更新笔记（自动保存版本）"""
        if note_id not in self._notes_db:
            return None

        note = self._notes_db[note_id]
        now = datetime.now()
        content_changed = False

        if title is not None and title != note["title"]:
            note["title"] = title
            content_changed = True
        if content is not None and content != note["content"]:
            note["content"] = content
            content_changed = True
        if tags is not None:
            note["tags"] = tags

        # 如果内容有变化，保存新版本
        if content_changed:
            note["version"] += 1
            note["updated_at"] = now

            if note_id not in self._versions_db:
                self._versions_db[note_id] = []

            self._versions_db[note_id].append({
                "version": note["version"],
                "content": note["content"],
                "title": note["title"],
                "timestamp": now,
                "change_summary": change_summary or f"版本 {note['version']}"
            })

            # 更新笔记本时间
            notebook_id = note.get("notebook_id")
            if notebook_id in self._notebooks_db:
                self._notebooks_db[notebook_id]["updated_at"] = now

        return note

    def delete_note(self, note_id: int) -> bool:
        """删除笔记"""
        if note_id not in self._notes_db:
            return False

        note = self._notes_db[note_id]
        notebook_id = note.get("notebook_id")

        # 更新笔记本计数
        if notebook_id in self._notebooks_db:
            self._notebooks_db[notebook_id]["note_count"] -= 1
            self._notebooks_db[notebook_id]["updated_at"] = datetime.now()

        del self._notes_db[note_id]
        if note_id in self._versions_db:
            del self._versions_db[note_id]

        logger.info(f"删除笔记: {note_id}")

        return True

    # ==================== 版本历史 ====================

    def get_note_versions(self, note_id: int) -> List[Dict[str, Any]]:
        """获取笔记的版本历史"""
        versions = self._versions_db.get(note_id, [])
        # 按版本号倒序
        return sorted(versions, key=lambda x: x["version"], reverse=True)

    def restore_version(self, note_id: int, version: int) -> Optional[Dict[str, Any]]:
        """恢复到指定版本"""
        if note_id not in self._notes_db:
            return None

        versions = self._versions_db.get(note_id, [])
        target_version = None
        for v in versions:
            if v["version"] == version:
                target_version = v
                break

        if not target_version:
            return None

        # 恢复内容
        return self.update_note(
            note_id,
            title=target_version["title"],
            content=target_version["content"],
            change_summary=f"恢复到版本 {version}"
        )

    # ==================== 统计 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取笔记本统计信息"""
        total_notes = len(self._notes_db)
        total_notebooks = len(self._notebooks_db)

        # 收集所有标签
        all_tags = set()
        for note in self._notes_db.values():
            all_tags.update(note.get("tags", []))
        for notebook in self._notebooks_db.values():
            all_tags.update(notebook.get("tags", []))

        return {
            "total_notebooks": total_notebooks,
            "total_notes": total_notes,
            "total_tags": len(all_tags),
            "tags": list(all_tags)
        }


# 创建全局实例
notebook_service = NotebookService()
