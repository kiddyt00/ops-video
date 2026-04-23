"""
Project API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.session import get_db
from ...db.project_crud import project_crud
from ...schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ...models.user import User
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


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """List all projects, optionally filtered by user_id"""
    filter_user_id = user_id
    # If no user_id param and user is authenticated, show their projects
    if user_id is None and current_user is not None:
        filter_user_id = current_user.id
    projects = project_crud.get_all(db, user_id=filter_user_id)
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
    """Delete project"""
    success = project_crud.delete(db, project_id=project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
