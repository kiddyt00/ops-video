"""Character Card model - project-level character consistency"""
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class CharacterCard(BaseModel):
    """Character reference card for visual consistency across episodes"""

    __tablename__ = "character_cards"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    front_view_url = Column(String(500), nullable=True)
    side_view_url = Column(String(500), nullable=True)
    back_view_url = Column(String(500), nullable=True)
    reference_images = Column(JSON, nullable=True)
    traits = Column(JSON, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    project = relationship("Project", back_populates="character_cards")

    def __repr__(self):
        return f"<CharacterCard(id={self.id}, name='{self.name}')>"
