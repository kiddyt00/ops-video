"""
Parameter preset API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.session import get_db
from ...db.preset_crud import preset_crud
from ...schemas.parameter_preset import PresetCreate, PresetUpdate, PresetResponse
from ...models.user import User
from ...api.deps_auth import get_current_active_user, get_optional_user

router = APIRouter()


@router.post("", response_model=PresetResponse, status_code=status.HTTP_201_CREATED)
def create_preset(
    preset_in: PresetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new parameter preset"""
    return preset_crud.create(db, obj_in=preset_in, user_id=current_user.id)


@router.get("", response_model=List[PresetResponse])
def list_presets(
    generator_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List user's presets, optionally filtered by generator type"""
    return preset_crud.get_all(db, user_id=current_user.id, generator_type=generator_type)


@router.get("/{preset_id}", response_model=PresetResponse)
def get_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a preset by ID"""
    preset = preset_crud.get(db, preset_id=preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        )
    return preset


@router.put("/{preset_id}", response_model=PresetResponse)
def update_preset(
    preset_id: UUID,
    preset_in: PresetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a preset"""
    preset = preset_crud.get(db, preset_id=preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        )
    if preset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the preset owner",
        )
    updated = preset_crud.update(db, preset_id=preset_id, obj_in=preset_in)
    return updated


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a preset"""
    preset = preset_crud.get(db, preset_id=preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        )
    if preset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the preset owner",
        )
    success = preset_crud.delete(db, preset_id=preset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset {preset_id} not found",
        )
