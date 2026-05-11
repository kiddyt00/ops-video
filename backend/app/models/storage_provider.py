"""Storage Provider model - cloud storage configuration"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from .guid_type import GUID
from .base import BaseModel


class StorageProvider(BaseModel):
    __tablename__ = "storage_providers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)
    access_key = Column(String(500), nullable=False)
    secret_key = Column(String(500), nullable=False)
    bucket = Column(String(100), nullable=False)
    region = Column(String(50), nullable=True)
    endpoint = Column(String(200), nullable=True)
    cdn_url = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_encrypted = Column(Boolean, default=False, nullable=False)
    last_test_status = Column(String(20), nullable=True)
    last_test_at = Column(DateTime, nullable=True)
    last_test_latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<StorageProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"
