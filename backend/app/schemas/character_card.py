"""
Character Card schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CharacterCardBase(BaseModel):
    """Base character card schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    front_view_url: Optional[str] = Field(None, max_length=500)
    side_view_url: Optional[str] = Field(None, max_length=500)
    back_view_url: Optional[str] = Field(None, max_length=500)
    reference_images: Optional[List[Any]] = None
    traits: Optional[Dict[str, Any]] = None
    is_active: bool = True


class CharacterCardCreate(CharacterCardBase):
    """Schema for creating a character card"""
    pass


class CharacterCardUpdate(BaseModel):
    """Schema for updating a character card"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    front_view_url: Optional[str] = Field(None, max_length=500)
    side_view_url: Optional[str] = Field(None, max_length=500)
    back_view_url: Optional[str] = Field(None, max_length=500)
    reference_images: Optional[List[Any]] = None
    traits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CharacterCardResponse(CharacterCardBase):
    """Schema for character card response"""
    id: UUID
    project_id: UUID
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
