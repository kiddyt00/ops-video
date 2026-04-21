"""
Base model with common fields
"""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declared_attr
from .session import Base


class CommonMixin:
    """Common mixin for all models"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )


class BaseModel(CommonMixin, Base):
    """Base model with common fields"""

    __abstract__ = True
