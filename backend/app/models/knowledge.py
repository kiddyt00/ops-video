"""
Knowledge model - stores knowledge base entries for the system
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime
from .guid_type import GUID
from .declarative import Base


class Knowledge(Base):
    """Knowledge base entry"""

    __tablename__ = "knowledge"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    built_in = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<Knowledge(id={self.id}, name='{self.name}', category='{self.category}')>"
