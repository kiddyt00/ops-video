"""
Analytics schemas for Phase 14: Data Analysis & Reporting
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class VideoStatistics(BaseModel):
    """Video file statistics"""
    duration: float = 0.0  # in seconds
    duration_formatted: str = "00:00"
    frame_count: int = 0
    frame_rate: float = 0.0
    resolution: str = "0x0"
    file_size: int = 0
    file_size_formatted: str = "0 B"
    codec: str = "unknown"
    has_audio: bool = False

    model_config = ConfigDict(from_attributes=True)


class TaskStatistics(BaseModel):
    """Task execution statistics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    average_duration: float = 0.0  # in seconds

    model_config = ConfigDict(from_attributes=True)


class StageStatistics(BaseModel):
    """Per-stage statistics"""
    stage: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0  # percentage

    model_config = ConfigDict(from_attributes=True)


class FileStatistics(BaseModel):
    """File statistics"""
    total_files: int = 0
    total_size: int = 0  # in bytes
    total_size_formatted: str = "0 B"
    by_type: Dict[str, int] = {}  # file_type -> count

    model_config = ConfigDict(from_attributes=True)


class ProjectStatistics(BaseModel):
    """Project-level statistics"""
    project_id: UUID
    task_stats: TaskStatistics
    file_stats: FileStatistics
    video_stats: Optional[VideoStatistics] = None
    stage_stats: List[StageStatistics] = []
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardMetric(BaseModel):
    """Dashboard metric card"""
    title: str
    value: str
    change: Optional[str] = None
    trend: Optional[str] = None  # "up", "down", "neutral"


class DashboardResponse(BaseModel):
    """Dashboard data response"""
    project_id: UUID
    project_name: str
    metrics: List[DashboardMetric]
    statistics: ProjectStatistics
    recent_tasks: List[Dict[str, Any]] = []
    files_by_type: Dict[str, int] = {}

    model_config = ConfigDict(from_attributes=True)


class ExportReport(BaseModel):
    """Export report structure"""
    project_id: UUID
    project_name: str
    exported_at: datetime
    version: str = "1.0.0"
    statistics: ProjectStatistics
    tasks: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []
    variants: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)
