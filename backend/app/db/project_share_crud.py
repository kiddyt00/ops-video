"""
Project share CRUD operations
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.project_share import ProjectShare, SharePermission


class ProjectShareCRUD:
    """Project share CRUD operations"""

    def create(
        self, db: Session, *, project_id: UUID, owner_id: UUID,
        shared_with_user_id: UUID, permission: SharePermission = SharePermission.VIEW
    ) -> Optional[ProjectShare]:
        """Share a project with a user"""
        # Check if already shared
        existing = self.get_by_project_and_user(db, project_id=project_id, shared_with_user_id=shared_with_user_id)
        if existing:
            return None

        share = ProjectShare(
            project_id=project_id,
            owner_id=owner_id,
            shared_with_user_id=shared_with_user_id,
            permission=permission,
        )
        db.add(share)
        db.commit()
        db.refresh(share)
        return share

    def get(self, db: Session, share_id: UUID) -> Optional[ProjectShare]:
        """Get share by ID"""
        return db.query(ProjectShare).filter(ProjectShare.id == share_id).first()

    def get_by_project_and_user(
        self, db: Session, *, project_id: UUID, shared_with_user_id: UUID
    ) -> Optional[ProjectShare]:
        """Get share by project and user"""
        return db.query(ProjectShare).filter(
            ProjectShare.project_id == project_id,
            ProjectShare.shared_with_user_id == shared_with_user_id,
        ).first()

    def list_by_project(self, db: Session, *, project_id: UUID) -> List[ProjectShare]:
        """List all shares for a project"""
        return db.query(ProjectShare).filter(ProjectShare.project_id == project_id).all()

    def list_shared_with_user(self, db: Session, *, user_id: UUID) -> List[ProjectShare]:
        """List all projects shared with a user"""
        return db.query(ProjectShare).filter(ProjectShare.shared_with_user_id == user_id).all()

    def list_shared_by_user(self, db: Session, *, user_id: UUID) -> List[ProjectShare]:
        """List all projects shared by a user"""
        return db.query(ProjectShare).filter(ProjectShare.owner_id == user_id).all()

    def delete(self, db: Session, *, project_id: UUID, shared_with_user_id: UUID) -> bool:
        """Remove a share"""
        share = self.get_by_project_and_user(db, project_id=project_id, shared_with_user_id=shared_with_user_id)
        if not share:
            return False
        db.delete(share)
        db.commit()
        return True


project_share_crud = ProjectShareCRUD()
