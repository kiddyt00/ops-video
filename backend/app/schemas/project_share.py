"""
Project sharing schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from ..models.project_share import SharePermission


class ShareCreate(BaseModel):
    """Schema for sharing a project with a user"""
    shared_with_user_id: UUID
    permission: SharePermission = SharePermission.VIEW


class ShareResponse(BaseModel):
    """Schema for share response"""
    id: UUID
    project_id: UUID
    owner_id: UUID
    shared_with_user_id: UUID
    permission: SharePermission
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
