"""
Variant API routes
"""
from uuid import UUID
from fastapi import APIRouter

router = APIRouter()


@router.get("/{variant_group_id}")
def get_variant_group(variant_group_id: UUID):
    """Get variant group by ID"""
    pass


@router.post("/{variant_group_id}/select")
def select_variant(variant_group_id: UUID):
    """Select a variant from the group"""
    pass
