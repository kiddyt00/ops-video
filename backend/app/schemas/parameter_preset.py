"""
Parameter preset schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PresetCreate(BaseModel):
    """Schema for creating a parameter preset"""
    name: str = Field(..., min_length=1, max_length=255)
    generator_type: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PresetUpdate(BaseModel):
    """Schema for updating a parameter preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class PresetResponse(BaseModel):
    """Schema for preset response"""
    id: UUID
    user_id: Optional[UUID] = None
    name: str
    generator_type: str
    description: Optional[str] = None
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
