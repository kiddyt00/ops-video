"""
Project CRUD operations
"""
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectUpdate


class ProjectCRUD:
    """Project CRUD operations"""

    def get_all(self, db: Session, user_id: Optional[UUID] = None, include_deleted: bool = False) -> List[Project]:
        """Get all projects, optionally filtered by user"""
        query = db.query(Project)
        if not include_deleted:
            query = query.filter(Project.is_deleted == False)
        if user_id is not None:
            query = query.filter(Project.user_id == user_id)
        return query.all()

    def get(self, db: Session, project_id: UUID, include_deleted: bool = False) -> Optional[Project]:
        """Get project by ID"""
        query = db.query(Project).filter(Project.id == project_id)
        if not include_deleted:
            query = query.filter(Project.is_deleted == False)
        return query.first()

    def create(self, db: Session, *, obj_in: ProjectCreate, user_id: Optional[UUID] = None) -> Project:
        """Create a new project"""
        project = Project(
            name=obj_in.name,
            description=obj_in.description,
            settings=obj_in.settings or {},
            user_id=user_id,
            is_deleted=False,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def update(
        self, db: Session, *, project_id: UUID, obj_in: ProjectUpdate
    ) -> Optional[Project]:
        """Update project"""
        project = self.get(db, project_id=project_id)
        if not project:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def soft_delete(self, db: Session, project_id: UUID) -> bool:
        """Soft delete project (move to recycle bin)"""
        project = self.get(db, project_id=project_id)
        if not project:
            return False

        project.is_deleted = True
        project.deleted_at = datetime.utcnow()
        db.commit()
        return True

    def restore(self, db: Session, project_id: UUID) -> bool:
        """Restore a soft-deleted project"""
        project = self.get(db, project_id=project_id, include_deleted=True)
        if not project or not project.is_deleted:
            return False

        project.is_deleted = False
        project.deleted_at = None
        db.commit()
        return True

    def permanent_delete(self, db: Session, project_id: UUID) -> bool:
        """Permanently delete a soft-deleted project"""
        project = self.get(db, project_id=project_id, include_deleted=True)
        if not project:
            return False

        db.delete(project)
        db.commit()
        return True

    def get_deleted(self, db: Session, user_id: Optional[UUID] = None) -> List[Project]:
        """Get soft-deleted projects (recycle bin)"""
        query = db.query(Project).filter(Project.is_deleted == True)
        if user_id is not None:
            query = query.filter(Project.user_id == user_id)
        return query.all()

    def count_by_user(self, db: Session, user_id: UUID) -> int:
        """Count projects owned by a user (excluding deleted)"""
        return db.query(Project).filter(
            Project.user_id == user_id,
            Project.is_deleted == False
        ).count()


project_crud = ProjectCRUD()
