"""
Project CRUD operations
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectUpdate


class ProjectCRUD:
    """Project CRUD operations"""

    def get_all(self, db: Session, user_id: Optional[UUID] = None) -> List[Project]:
        """Get all projects, optionally filtered by user"""
        query = db.query(Project)
        if user_id is not None:
            query = query.filter(Project.user_id == user_id)
        return query.all()

    def get(self, db: Session, project_id: UUID) -> Optional[Project]:
        """Get project by ID"""
        return db.query(Project).filter(Project.id == project_id).first()

    def create(self, db: Session, *, obj_in: ProjectCreate, user_id: Optional[UUID] = None) -> Project:
        """Create a new project"""
        project = Project(
            name=obj_in.name,
            description=obj_in.description,
            settings=obj_in.settings or {},
            user_id=user_id,
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

    def delete(self, db: Session, project_id: UUID) -> bool:
        """Delete project"""
        project = self.get(db, project_id=project_id)
        if not project:
            return False

        db.delete(project)
        db.commit()
        return True

    def count_by_user(self, db: Session, user_id: UUID) -> int:
        """Count projects owned by a user"""
        return db.query(Project).filter(Project.user_id == user_id).count()


project_crud = ProjectCRUD()
