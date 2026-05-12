"""Storage Provider model - cloud storage configuration"""
import uuid
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON
from .guid_type import GUID
from .base import BaseModel


class StorageProviderType(str, Enum):
    """Supported cloud storage provider types"""
    OSS = "aliyun_oss"       # Aliyun Object Storage Service
    S3 = "aws_s3"             # Amazon S3
    S3_COMPATIBLE = "s3_compatible"  # S3-compatible (MinIO, etc.)
    COS = "tencent_cos"       # Tencent Cloud Object Storage


class StorageProvider(BaseModel):
    """Cloud storage provider configuration (OSS/S3/COS)"""

    __tablename__ = "storage_providers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=False)  # aliyun_oss, aws_s3, tencent_cos
    access_key = Column(String(500), nullable=False)
    secret_key = Column(String(500), nullable=False)
    bucket = Column(String(255), nullable=False)
    endpoint = Column(String(500), nullable=True)
    region = Column(String(100), nullable=True)
    path_prefix = Column(String(500), nullable=True)
    extra_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    is_default = Column(Boolean, nullable=False, default=False)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(50), nullable=True)
    last_test_error = Column(Text, nullable=True)

    def __repr__(self):
        return f"<StorageProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"
