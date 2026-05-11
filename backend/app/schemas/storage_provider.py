"""
Storage Provider schemas
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StorageProviderCreate(BaseModel):
    """Schema for creating a storage provider"""
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: str = Field(..., min_length=1, max_length=50)
    access_key: str = Field(..., min_length=1)
    secret_key: str = Field(..., min_length=1)
    bucket: str = Field(..., min_length=1)
    endpoint: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=100)
    path_prefix: Optional[str] = ""
    extra_config: Optional[Dict[str, Any]] = None


class StorageProviderUpdate(BaseModel):
    """Schema for updating a storage provider"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    provider_type: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    bucket: Optional[str] = None
    endpoint: Optional[str] = Field(None, max_length=500)
    region: Optional[str] = Field(None, max_length=100)
    path_prefix: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


class StorageProviderResponse(BaseModel):
    """Schema for storage provider response"""
    id: UUID
    name: str
    provider_type: str
    access_key: str
    secret_key: str
    bucket: str
    endpoint: Optional[str] = None
    region: Optional[str] = None
    path_prefix: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None
    is_active: bool
    is_default: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StorageTestResult(BaseModel):
    """Schema for storage connection test result"""
    success: bool
    message: str
    latency_ms: Optional[float] = None
    provider_name: Optional[str] = None
    bucket: Optional[str] = None
