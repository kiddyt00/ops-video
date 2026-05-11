"""Character Card model - project-level character consistency"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class CharacterCard(BaseModel):
    __tablename__ = "character_cards"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    front_image_url = Column(String(500), nullable=True)
    side_image_url = Column(String(500), nullable=True)
    back_image_url = Column(String(500), nullable=True)
    front_image_path = Column(String(500), nullable=True)
    side_image_path = Column(String(500), nullable=True)
    back_image_path = Column(String(500), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    project = relationship("Project", back_populates="character_cards")

    def __repr__(self):
        return f"<CharacterCard(id={self.id}, name='{self.name}')>"
