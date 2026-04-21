"""
Variant API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.session import get_db
from ...db.file_crud import variant_group_crud
from ...db.project_crud import project_crud
from ...schemas.file import VariantGroupCreate, VariantGroupResponse, VariantSelect

router = APIRouter()


@router.get("", response_model=List[VariantGroupResponse])
def list_variant_groups(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List all variant groups, optionally filtered by project"""
    groups = variant_group_crud.get_all(db, project_id=project_id)
    return groups


@router.get("/{variant_group_id}", response_model=VariantGroupResponse)
def get_variant_group(
    variant_group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get variant group by ID"""
    group = variant_group_crud.get(db, variant_group_id=variant_group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VariantGroup {variant_group_id} not found"
        )
    return group


@router.post("", response_model=VariantGroupResponse, status_code=status.HTTP_201_CREATED)
def create_variant_group(
    group_in: VariantGroupCreate,
    db: Session = Depends(get_db)
):
    """Create a new variant group"""
    # Verify project exists
    project = project_crud.get(db, project_id=group_in.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {group_in.project_id} not found"
        )

    group = variant_group_crud.create(db, obj_in=group_in)
    return group


@router.post("/{variant_group_id}/select", response_model=VariantGroupResponse)
def select_variant(
    variant_group_id: UUID,
    select_in: VariantSelect,
    db: Session = Depends(get_db)
):
    """Select a variant from the group"""
    group = variant_group_crud.select_variant(
        db,
        variant_group_id=variant_group_id,
        file_id=select_in.file_id
    )

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VariantGroup {variant_group_id} or File {select_in.file_id} not found"
        )

    return group


@router.delete("/{variant_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant_group(
    variant_group_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete variant group"""
    success = variant_group_crud.delete(db, variant_group_id=variant_group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VariantGroup {variant_group_id} not found"
        )
