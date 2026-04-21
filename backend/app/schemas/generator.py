"""
Generator schemas
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Schema for generation request"""
    project_id: str
    parameters: Dict[str, Any]
    variant_count: int = 4


class GenerateResponse(BaseModel):
    """Schema for generation response"""
    task_id: str
    variant_group_id: str
    status: str
    message: str


class GeneratorInfo(BaseModel):
    """Schema for generator info"""
    name: str
    type: str
    description: str
    parameters: Dict[str, Any]
