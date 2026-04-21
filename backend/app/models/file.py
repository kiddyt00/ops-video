"""
File and VariantGroup models
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, ForeignKey, Enum as SQLEnum,
    DateTime, JSON, Boolean, BigInteger, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class FileType(str, Enum):
    """File type enumeration"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    OTHER = "other"


class File(BaseModel):
    """File model - represents a generated file"""

    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    variant_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("variant_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    file_path = Column(Text, nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=True)

    # Generation parameters (prompt, seed, model, etc.)
    generation_params = Column(JSON, nullable=False, default=dict)

    # Additional metadata
    metadata = Column(JSON, nullable=False, default=dict)

    # Version control
    version = Column(String(50), nullable=False, default="1.0.0")
    parent_file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Selection status
    is_selected = Column(Boolean, default=False, nullable=False, index=True)
    selected_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="files")
    variant_group = relationship("VariantGroup", back_populates="files")
    task = relationship("Task", backref="files")
    parent_file = relationship(
        "File",
        remote_side=[id],
        backref="child_files",
        foreign_keys=[parent_file_id]
    )

    def __repr__(self):
        return f"<File(id={self.id}, file_type='{self.file_type}', path='{self.file_path}')>"


class VariantGroup(BaseModel):
    """VariantGroup model - groups multiple variants of the same generation"""

    __tablename__ = "variant_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stage = Column(String(50), nullable=False, index=True)
    selected_file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    parameters = Column(JSON, nullable=False, default=dict)

    # Relationships
    project = relationship("Project", back_populates="variant_groups")
    task = relationship("Task", back_populates="variant_groups")
    files = relationship("File", back_populates="variant_group")
    selected_file = relationship(
        "File",
        foreign_keys=[selected_file_id],
        backref="selected_in_groups"
    )

    def __repr__(self):
        return f"<VariantGroup(id={self.id}, stage='{self.stage}')>"
