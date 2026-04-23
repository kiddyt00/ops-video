"""
User management API routes (admin)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...db.session import get_db
from ...db.user_crud import user_crud
from ...schemas.user import UserResponse
from ...models.user import User, UserRole
from ...api.deps_auth import get_current_active_user


router = APIRouter()


def _require_admin(current_user: User):
    """Verify user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


@router.get("", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all users (admin only)"""
    _require_admin(current_user)
    users = user_crud.get_all(db)
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)"""
    _require_admin(current_user)
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user (admin only)"""
    _require_admin(current_user)
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    # Only allow updating role and is_active from admin panel
    if "role" in user_update:
        user.role = UserRole(user_update["role"])
    if "is_active" in user_update:
        user.is_active = user_update["is_active"]
    db.commit()
    db.refresh(user)
    return user
