"""
Story model for long-form story creation workflow
"""
import enum
import uuid
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class StoryStatus(str, enum.Enum):
    """Story status enum"""
    draft = "draft"
    completed = "completed"
    archived = "archived"


class Story(BaseModel):
    """Story model - represents a long-form story within a project"""

    __tablename__ = "stories"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inspiration = Column(String, nullable=True)
    logline = Column(String, nullable=True)
    synopsis = Column(String, nullable=True)
    worldbuilding = Column(JSON, nullable=True, default=dict)
    characters = Column(JSON, nullable=True, default=list)
    themes = Column(JSON, nullable=True, default=list)
    plot_points = Column(JSON, nullable=True, default=list)
    chapter_outline = Column(JSON, nullable=True, default=list)
    status = Column(
        Enum(StoryStatus, name="story_status"),
        nullable=False,
        default=StoryStatus.draft,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="stories")

    def __repr__(self):
        return f"<Story(id={self.id}, project_id={self.project_id}, status='{self.status.value}')>"
