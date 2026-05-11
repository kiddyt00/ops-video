"""
Project model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import ForeignKey
from .guid_type import GUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Project(BaseModel):
    """Project model - represents a video creation project"""

    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    settings = Column(JSON, nullable=True, default=dict)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    variant_groups = relationship(
        "VariantGroup", back_populates="project", cascade="all, delete-orphan"
    )
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    shares = relationship("ProjectShare", back_populates="project", cascade="all, delete-orphan")
    character_cards = relationship("CharacterCard", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"
