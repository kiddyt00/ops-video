"""AI Model schemas"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AIModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    provider: str = Field(..., min_length=1, max_length=50)
    model_name: str = Field(..., min_length=1, max_length=100)
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    is_enabled: bool = True
    config: Dict[str, Any] = {}


class AIModelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class AIModelResponse(BaseModel):
    id: UUID
    name: str
    category: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    is_enabled: bool
    is_builtin: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelTestRequest(BaseModel):
    prompt: Optional[str] = "Hello, this is a test."


class ModelTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[float] = None
    result: Optional[str] = None
