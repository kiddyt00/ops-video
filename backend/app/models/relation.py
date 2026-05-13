"""Relation and CharacterState models for story continuity tracking."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime
from .guid_type import GUID
from .declarative import Base


class Relation(Base):
    __tablename__ = "relations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(32), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_name = Column(String(255), nullable=False)
    relation_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_name = Column(String(255), nullable=False)
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<Relation {self.source_name} --{self.relation_type}--> {self.target_name}>"


class CharacterState(Base):
    __tablename__ = "character_states"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(32), nullable=False, index=True)
    character_name = Column(String(255), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="alive")
    location = Column(String(255), nullable=True)
    faction = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<CharacterState {self.character_name} ch{self.chapter_number} [{self.status}] @{self.location}>"
