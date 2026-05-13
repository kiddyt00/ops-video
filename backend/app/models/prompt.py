"""Prompt template model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from .guid_type import GUID
from .declarative import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text(), nullable=True)
    template = Column(Text(), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    built_in = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Prompt {self.name} v{self.version}>"
