"""
数据库项目服务 - 协作项目的CRUD操作
支持权限检查和编辑历史记录
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from ..models.collaboration import (
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
from ..models.user import User


class ProjectDBService:
    """数据库项目服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== 项目 CRUD ====================

    async def create_project(
        self,
        owner_id: int,
        title: str,
        project_type: CollabProjectType = CollabProjectType.MULTI_COLLATION,
        description: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        visibility: ProjectVisibility = ProjectVisibility.PRIVATE,
    ) -> CollabProject:
        """
        创建新项目

        Args:
            owner_id: 所有者用户ID
            title: 项目标题
            project_type: 项目类型
            description: 项目描述
            data: 项目核心数据
            metadata: 项目元数据
            visibility: 可见性

        Returns:
            创建的项目对象
        """
        project = CollabProject(
            owner_id=owner_id,
            title=title,
            project_type=project_type,
            description=description or "",
            status=CollabProjectStatus.IN_PROGRESS,
            visibility=visibility,
            data=data or {},
            project_meta=metadata or {},
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # 记录创建历史
        await self._add_history(
            project.id, owner_id, EditAction.CREATE,
            {"title": title, "project_type": project_type.value}
        )

        return project

    async def get_project(self, project_id: str) -> Optional[CollabProject]:
        """
        获取项目详情

        Args:
            project_id: 项目ID

        Returns:
            项目对象或None
        """
        result = await self.db.execute(
            select(CollabProject).where(CollabProject.id == project_id)
        )
        return result.scalar_one_or_none()

    async def update_project(
        self,
        project_id: str,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[CollabProjectStatus] = None,
        visibility: Optional[ProjectVisibility] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        merge_data: bool = True,
    ) -> Optional[CollabProject]:
        """
        更新项目

        Args:
            project_id: 项目ID
            user_id: 操作用户ID
            title: 新标题
            description: 新描述
            status: 新状态
            visibility: 新可见性
            data: 新数据
            metadata: 新元数据
            merge_data: 是否合并数据（True=合并，False=覆盖）

        Returns:
            更新后的项目对象
        """
        project = await self.get_project(project_id)
        if not project:
            return None

        changes = {}

        if title is not None:
            changes["title"] = {"old": project.title, "new": title}
            project.title = title

        if description is not None:
            project.description = description

        if status is not None:
            changes["status"] = {"old": project.status.value if project.status else None, "new": status.value}
            project.status = status

        if visibility is not None:
            changes["visibility"] = {"old": project.visibility.value if project.visibility else None, "new": visibility.value}
            project.visibility = visibility

        if metadata is not None:
            if merge_data:
                current_metadata = project.project_meta or {}
                current_metadata.update(metadata)
                project.project_meta = current_metadata
            else:
                project.project_meta = metadata

        if data is not None:
            if merge_data:
                current_data = project.data or {}
                current_data.update(data)
                project.data = current_data
            else:
                project.data = data

        project.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(project)

        # 记录更新历史
        if changes:
            await self._add_history(project_id, user_id, EditAction.UPDATE, changes)

        return project

    async def delete_project(self, project_id: str) -> bool:
        """
        删除项目

        Args:
            project_id: 项目ID

        Returns:
            是否删除成功
        """
        project = await self.get_project(project_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.commit()
        return True

    async def list_projects(
        self,
        user_id: Optional[int] = None,
        project_type: Optional[CollabProjectType] = None,
        status: Optional[CollabProjectStatus] = None,
        visibility: Optional[ProjectVisibility] = None,
        include_shared: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取项目列表

        Args:
            user_id: 用户ID（获取该用户可访问的项目）
            project_type: 筛选项目类型
            status: 筛选状态
            visibility: 筛选可见性
            include_shared: 是否包含共享给该用户的项目
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            {
                "total": 总数,
                "items": [项目摘要列表]
            }
        """
        # 构建查询条件
        conditions = []

        if user_id:
            if include_shared:
                # 用户拥有的项目 OR 用户是成员的项目 OR 公开/共享项目
                member_subquery = (
                    select(ProjectMember.project_id)
                    .where(ProjectMember.user_id == user_id)
                )
                conditions.append(
                    or_(
                        CollabProject.owner_id == user_id,
                        CollabProject.id.in_(member_subquery),
                        CollabProject.visibility.in_([
                            ProjectVisibility.SHARED,
                            ProjectVisibility.PUBLIC
                        ])
                    )
                )
            else:
                # 只返回用户拥有的项目
                conditions.append(CollabProject.owner_id == user_id)

        if project_type:
            conditions.append(CollabProject.project_type == project_type)

        if status:
            conditions.append(CollabProject.status == status)

        if visibility:
            conditions.append(CollabProject.visibility == visibility)

        # 查询总数
        count_query = select(func.count(CollabProject.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询列表
        query = select(CollabProject)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(desc(CollabProject.updated_at)).offset(offset).limit(limit)

        result = await self.db.execute(query)
        projects = result.scalars().all()

        # 转换为摘要格式
        items = []
        for project in projects:
            items.append({
                "id": project.id,
                "title": project.title,
                "description": project.description or "",
                "status": project.status.value if project.status else None,
                "visibility": project.visibility.value if project.visibility else None,
                "project_type": project.project_type.value if project.project_type else None,
                "owner_id": project.owner_id,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "metadata": project.project_meta or {},
            })

        return {
            "total": total,
            "items": items,
        }

    async def list_user_owned_projects(
        self,
        user_id: int,
        project_type: Optional[CollabProjectType] = None,
        status: Optional[CollabProjectStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """获取用户拥有的项目列表"""
        return await self.list_projects(
            user_id=user_id,
            project_type=project_type,
            status=status,
            include_shared=False,
            limit=limit,
            offset=offset,
        )

    async def list_shared_with_user(
        self,
        user_id: int,
        project_type: Optional[CollabProjectType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """获取共享给用户的项目列表（不包括自己拥有的）"""
        # 查找用户是成员的项目（排除自己拥有的）
        member_subquery = (
            select(ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
        )

        conditions = [
            CollabProject.id.in_(member_subquery),
            CollabProject.owner_id != user_id,
        ]

        if project_type:
            conditions.append(CollabProject.project_type == project_type)

        # 查询总数
        count_query = select(func.count(CollabProject.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 查询列表
        query = (
            select(CollabProject)
            .where(and_(*conditions))
            .order_by(desc(CollabProject.updated_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        projects = result.scalars().all()

        items = []
        for project in projects:
            # 获取用户在该项目的角色
            member_result = await self.db.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id == user_id
                )
            )
            member = member_result.scalar_one_or_none()

            items.append({
                "id": project.id,
                "title": project.title,
                "description": project.description or "",
                "status": project.status.value if project.status else None,
                "visibility": project.visibility.value if project.visibility else None,
                "project_type": project.project_type.value if project.project_type else None,
                "owner_id": project.owner_id,
                "my_role": member.role.value if member else None,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "metadata": project.project_meta or {},
            })

        return {
            "total": total,
            "items": items,
        }

    # ==================== 项目成员管理 ====================

    async def add_member(
        self,
        project_id: str,
        user_id: int,
        role: MemberRole,
        invited_by: int,
    ) -> Optional[ProjectMember]:
        """
        添加项目成员

        Args:
            project_id: 项目ID
            user_id: 用户ID
            role: 角色
            invited_by: 邀请者ID

        Returns:
            成员对象
        """
        # 检查是否已是成员
        existing = await self.db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
        if existing.scalar_one_or_none():
            return None

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
        )

        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def update_member_role(
        self,
        project_id: str,
        user_id: int,
        new_role: MemberRole,
    ) -> Optional[ProjectMember]:
        """更新成员角色"""
        result = await self.db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return None

        member.role = new_role
        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def remove_member(
        self,
        project_id: str,
        user_id: int,
    ) -> bool:
        """移除项目成员"""
        result = await self.db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False

        await self.db.delete(member)
        await self.db.commit()
        return True

    async def list_members(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目成员列表"""
        result = await self.db.execute(
            select(ProjectMember, User)
            .join(User, ProjectMember.user_id == User.id)
            .where(ProjectMember.project_id == project_id)
        )
        rows = result.all()

        members = []
        for member, user in rows:
            members.append({
                "id": member.id,
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": member.role.value,
                "created_at": member.created_at.isoformat() if member.created_at else None,
            })

        return members

    # ==================== 评论管理 ====================

    async def add_comment(
        self,
        project_id: str,
        user_id: int,
        content: str,
        variant_index: Optional[int] = None,
        parent_id: Optional[int] = None,
    ) -> Comment:
        """添加评论"""
        comment = Comment(
            project_id=project_id,
            user_id=user_id,
            content=content,
            variant_index=variant_index,
            parent_id=parent_id,
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def update_comment(
        self,
        comment_id: int,
        content: str,
    ) -> Optional[Comment]:
        """更新评论"""
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            return None

        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def delete_comment(self, comment_id: int) -> bool:
        """删除评论"""
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            return False

        await self.db.delete(comment)
        await self.db.commit()
        return True

    async def list_comments(
        self,
        project_id: str,
        variant_index: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """获取项目评论列表"""
        conditions = [Comment.project_id == project_id]

        if variant_index is not None:
            conditions.append(Comment.variant_index == variant_index)

        result = await self.db.execute(
            select(Comment, User)
            .join(User, Comment.user_id == User.id)
            .where(and_(*conditions))
            .order_by(Comment.created_at)
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()

        comments = []
        for comment, user in rows:
            comments.append({
                "id": comment.id,
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "content": comment.content,
                "variant_index": comment.variant_index,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            })

        return comments

    # ==================== 编辑历史 ====================

    async def _add_history(
        self,
        project_id: str,
        user_id: int,
        action: EditAction,
        details: Dict[str, Any],
    ):
        """添加编辑历史记录"""
        history = EditHistory(
            project_id=project_id,
            user_id=user_id,
            action=action,
            details=details,
        )
        self.db.add(history)
        await self.db.commit()

    async def record_decision(
        self,
        project_id: str,
        user_id: int,
        variant_index: int,
        decision_data: Dict[str, Any],
    ):
        """记录判取操作"""
        await self._add_history(
            project_id, user_id, EditAction.DECISION,
            {"variant_index": variant_index, "decision": decision_data}
        )

    async def list_history(
        self,
        project_id: str,
        action: Optional[EditAction] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """获取项目编辑历史"""
        conditions = [EditHistory.project_id == project_id]

        if action:
            conditions.append(EditHistory.action == action)

        result = await self.db.execute(
            select(EditHistory, User)
            .join(User, EditHistory.user_id == User.id)
            .where(and_(*conditions))
            .order_by(desc(EditHistory.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()

        history = []
        for entry, user in rows:
            history.append({
                "id": entry.id,
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "action": entry.action.value,
                "details": entry.details,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            })

        return history

    # ==================== 多版本对勘专用方法 ====================

    async def save_multi_collation(
        self,
        owner_id: int,
        title: str,
        base_info: Dict[str, Any],
        collation_results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        variant_table: Dict[str, Any],
        phylogeny: Dict[str, Any],
        project_id: Optional[str] = None,
    ) -> CollabProject:
        """
        保存多版本对勘结果

        Args:
            owner_id: 所有者ID
            title: 项目标题
            base_info: 底本信息
            collation_results: 校本对比结果列表
            summary: 汇总统计
            variant_table: 异文汇校表
            phylogeny: 版本谱系
            project_id: 项目ID（更新时传入）

        Returns:
            项目对象
        """
        # 计算差异总数
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
            # 更新现有项目
            existing = await self.get_project(project_id)
            if existing:
                existing_data = existing.data or {}
                if "decisions" in existing_data:
                    data["decisions"] = existing_data.get("decisions")
                if "canon_locations_override" in existing_data:
                    data["canon_locations_override"] = existing_data.get("canon_locations_override")

                return await self.update_project(
                    project_id,
                    owner_id,
                    title=title,
                    data=data,
                    metadata=metadata,
                    merge_data=False,
                )

        # 创建新项目
        return await self.create_project(
            owner_id=owner_id,
            title=title,
            project_type=CollabProjectType.MULTI_COLLATION,
            data=data,
            metadata=metadata,
        )


def get_project_service(db: AsyncSession) -> ProjectDBService:
    """获取项目服务实例"""
    return ProjectDBService(db)
