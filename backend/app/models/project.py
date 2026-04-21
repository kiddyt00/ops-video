"""
Project model
"""
import uuid
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel


class Project(BaseModel):
    """Project model - represents a video creation project"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    settings = Column(JSON, nullable=True, default=dict)

    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    variant_groups = relationship(
        "VariantGroup", back_populates="project", cascade="all, delete-orphan"
    )
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"
