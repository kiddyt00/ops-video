"""
Task model and related models
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, ForeignKey, Enum as SQLEnum,
    DateTime, JSON, Boolean, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class TaskStage(str, Enum):
    """Task stage enumeration"""
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task model - represents a generation task"""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stage = Column(SQLEnum(TaskStage), nullable=False, index=True)
    status = Column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    parent_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True
    )
    generator_type = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    output_file_ids = Column(JSON, nullable=False, default=list)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    parent_task = relationship(
        "Task",
        remote_side=[id],
        backref="child_tasks",
        foreign_keys=[parent_task_id]
    )
    status_logs = relationship(
        "TaskStatusLog",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    variant_groups = relationship(
        "VariantGroup",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, stage='{self.stage}', status='{self.status}')>"


class TaskStatusLog(BaseModel):
    """Task status change log"""

    __tablename__ = "task_status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_status = Column(SQLEnum(TaskStatus), nullable=True)
    to_status = Column(SQLEnum(TaskStatus), nullable=False)
    reason = Column(String(500), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="status_logs")

    def __repr__(self):
        return f"<TaskStatusLog(id={self.id}, task_id={self.task_id}, to_status='{self.to_status}')>"
