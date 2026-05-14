"""
Chapter model - tracks per-chapter generation status within a project.
"""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class Chapter(BaseModel):
    """Chapter model - represents a chapter with its own generation pipeline."""

    __tablename__ = "chapters"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    current_stage = Column(String(50), nullable=True)
    video_file_id = Column(GUID(), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    project = relationship("Project", backref="chapters")
