"""
File schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class FileType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    OTHER = "other"


class FileBase(BaseModel):
    """Base file schema"""
    file_type: FileType
    generation_params: Dict[str, Any] = {}
    extra_info: Dict[str, Any] = {}

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    # Alias for backward compatibility
    metadata: Dict[str, Any] = Field(default={}, alias="extra_info")


class FileCreate(FileBase):
    """Schema for creating a file"""
    project_id: UUID
    file_path: str
    variant_group_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    file_size: Optional[int] = None
    version: str = "1.0.0"


class FileUpdate(BaseModel):
    """Schema for updating a file"""
    generation_params: Optional[Dict[str, Any]] = None
    extra_info: Optional[Dict[str, Any]] = None
    is_selected: Optional[bool] = None


class FileResponse(FileBase):
    """Schema for file response"""
    id: UUID
    project_id: UUID
    variant_group_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    file_path: str
    file_size: Optional[int] = None
    version: str
    parent_file_id: Optional[UUID] = None
    is_selected: bool
    selected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VariantGroupBase(BaseModel):
    """Base variant group schema"""
    stage: str
    parameters: Dict[str, Any] = {}


class VariantGroupCreate(VariantGroupBase):
    """Schema for creating a variant group"""
    project_id: UUID
    task_id: UUID


class VariantGroupResponse(VariantGroupBase):
    """Schema for variant group response"""
    id: UUID
    project_id: UUID
    task_id: UUID
    selected_file_id: Optional[UUID] = None
    files: List[FileResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VariantSelect(BaseModel):
    """Schema for selecting a variant"""
    file_id: UUID
    proceed_to_next: bool = True
