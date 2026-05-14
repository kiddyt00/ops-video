"""
Project API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.session import get_db
from ...db.project_crud import project_crud
from ...db.project_share_crud import project_share_crud
from ...schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ...schemas.project_share import ShareCreate, ShareResponse
from ...models.user import User
from ...models.project_share import SharePermission
from ...api.deps_auth import get_current_active_user, get_optional_user

router = APIRouter()


@router.get("/me", response_model=List[ProjectResponse])
def get_my_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get projects owned by the current user"""
    projects = project_crud.get_all(db, user_id=current_user.id)
    return projects


@router.get("/shared-with-me", response_model=List[ProjectResponse])
def get_shared_with_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get projects shared with the current user"""
    from ...models.project import Project
    shares = project_share_crud.list_shared_with_user(db, user_id=current_user.id)
    project_ids = [s.project_id for s in shares]
    if not project_ids:
        return []
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    return projects


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    user_id: Optional[UUID] = None,
    limit: int = 12,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """List all projects, optionally filtered by user_id. Ordered by created_at desc, limited to 12.

    Admin sees all projects by default; regular user sees only their own.
    """
    filter_user_id = user_id
    if user_id is None:
        # Admin sees all; regular user sees their own
        if current_user is not None and current_user.role != "admin":
            filter_user_id = current_user.id
    projects = project_crud.get_all(db, user_id=filter_user_id)
    # Sort by created_at descending and limit
    projects = sorted(projects, key=lambda p: p.created_at, reverse=True)[:limit]
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Create a new project. If authenticated, associates with current user."""
    user_id = current_user.id if current_user else None
    project = project_crud.create(db, obj_in=project_in, user_id=user_id)
    return project


# ─── Recycle Bin (must be before /{project_id} routes) ────────────────


@router.get("/recycle-bin", response_model=List[ProjectResponse])
def list_deleted_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List soft-deleted projects (recycle bin) for current user"""
    return project_crud.get_deleted(db, user_id=current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update project"""
    project = project_crud.update(db, project_id=project_id, obj_in=project_in)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Soft delete project (move to recycle bin)"""
    success = project_crud.soft_delete(db, project_id=project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )


# ─── Project Sharing ─────────────────────────────────────────────────


@router.post("/{project_id}/restore", response_model=ProjectResponse)
def restore_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted project from recycle bin"""
    success = project_crud.restore(db, project_id=project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found or not deleted"
        )
    return project_crud.get(db, project_id=project_id)


@router.delete("/{project_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def permanently_delete_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Permanently delete a soft-deleted project"""
    success = project_crud.permanent_delete(db, project_id=project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )


# ─── Project Sharing ─────────────────────────────────────────────────


def _require_project_owner(project_id: UUID, current_user: User, db: Session):
    """Verify user owns the project"""
    project = project_crud.get(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can manage shares",
        )


@router.post("/{project_id}/share", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
def share_project(
    project_id: UUID,
    share_in: ShareCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Share a project with another user. Only project owner can share."""
    _require_project_owner(project_id, current_user, db)

    # Cannot share with yourself
    if share_in.shared_with_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share a project with yourself",
        )

    # Verify target user exists
    from ...db.user_crud import user_crud
    target_user = user_crud.get(db, user_id=share_in.shared_with_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {share_in.shared_with_user_id} not found",
        )

    share = project_share_crud.create(
        db,
        project_id=project_id,
        owner_id=current_user.id,
        shared_with_user_id=share_in.shared_with_user_id,
        permission=share_in.permission,
    )
    if not share:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project already shared with user {share_in.shared_with_user_id}",
        )
    return share


@router.get("/{project_id}/shares", response_model=List[ShareResponse])
def list_project_shares(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all shares for a project. Only project owner can view."""
    _require_project_owner(project_id, current_user, db)
    shares = project_share_crud.list_by_project(db, project_id=project_id)
    return shares


@router.delete("/{project_id}/share/{shared_with_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_project(
    project_id: UUID,
    shared_with_user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a project share. Only project owner can unshare."""
    _require_project_owner(project_id, current_user, db)
    success = project_share_crud.delete(
        db, project_id=project_id, shared_with_user_id=shared_with_user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )


@router.put("/{project_id}/share/{shared_with_user_id}", response_model=ShareResponse)
def update_share_permission(
    project_id: UUID,
    shared_with_user_id: UUID,
    share_update: ShareCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update share permission. Only project owner can change."""
    _require_project_owner(project_id, current_user, db)
    share = project_share_crud.get_by_project_and_user(
        db, project_id=project_id, shared_with_user_id=shared_with_user_id
    )
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )
    share.permission = share_update.permission
    db.commit()
    db.refresh(share)
    return share
