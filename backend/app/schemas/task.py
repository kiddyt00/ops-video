"""
Task schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TaskStage(str, Enum):
    INSPIRATION = "inspiration"
    STORY = "story"
    CHAPTER_OUTLINE = "chapter_outline"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskBase(BaseModel):
    """Base task schema"""
    stage: TaskStage
    generator_type: str
    parameters: Dict[str, Any] = {}


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    project_id: UUID
    parent_task_ids: List[UUID] = []


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    parameters: Optional[Dict[str, Any]] = None


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status"""
    status: TaskStatus
    reason: Optional[str] = None


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: UUID
    project_id: UUID
    status: TaskStatus
    parent_task_id: Optional[UUID] = None
    output_file_ids: List[UUID] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskStatusLogResponse(BaseModel):
    """Schema for task status log response"""
    id: UUID
    task_id: UUID
    from_status: Optional[TaskStatus] = None
    to_status: TaskStatus
    reason: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
