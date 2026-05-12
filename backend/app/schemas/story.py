"""
Story schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ..models.story import StoryStatus


class StoryCreate(BaseModel):
    """Schema for creating a story"""
    inspiration: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    worldbuilding: Optional[Dict[str, Any]] = None
    characters: Optional[List[Any]] = None
    themes: Optional[List[Any]] = None
    plot_points: Optional[List[Any]] = None
    chapter_outline: Optional[List[Any]] = None
    status: Optional[StoryStatus] = StoryStatus.draft


class StoryUpdate(BaseModel):
    """Schema for updating a story"""
    inspiration: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    worldbuilding: Optional[Dict[str, Any]] = None
    characters: Optional[List[Any]] = None
    themes: Optional[List[Any]] = None
    plot_points: Optional[List[Any]] = None
    chapter_outline: Optional[List[Any]] = None
    status: Optional[StoryStatus] = None


class StoryResponse(BaseModel):
    """Schema for story response"""
    id: UUID
    project_id: UUID
    inspiration: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    worldbuilding: Optional[Dict[str, Any]] = None
    characters: Optional[List[Any]] = None
    themes: Optional[List[Any]] = None
    plot_points: Optional[List[Any]] = None
    chapter_outline: Optional[List[Any]] = None
    status: StoryStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
