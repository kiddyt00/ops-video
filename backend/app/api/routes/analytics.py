"""
Analytics API routes for Phase 14: Data Analysis & Reporting

Endpoints:
- GET /api/v1/analytics/projects/{project_id}/stats - Project statistics
- GET /api/v1/analytics/projects/{project_id}/report - Export JSON report
- GET /api/v1/analytics/projects/{project_id}/dashboard - Dashboard data
- GET /api/v1/analytics/projects/{project_id}/videos - Video statistics
"""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json

from ...db.session import get_db
from ...db.project_crud import project_crud
from ...db.task_crud import task_crud
from ...db.file_crud import file_crud
from ...models.task import Task, TaskStatus, TaskStage
from ...models.file import File, FileType, VariantGroup
from ...schemas.analytics import (
    ProjectStatistics,
    TaskStatistics,
    FileStatistics,
    VideoStatistics,
    StageStatistics,
    DashboardResponse,
    DashboardMetric,
    ExportReport,
)
from ...services.video_analyzer import VideoAnalyzer, analyze_video
from ...config import settings

router = APIRouter()


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def _calculate_task_stats(tasks: List[Task]) -> TaskStatistics:
    """Calculate task statistics"""
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    running = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)

    # Calculate average duration for completed tasks
    durations = []
    for task in tasks:
        if task.status == TaskStatus.COMPLETED and task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            durations.append(duration)

    avg_duration = sum(durations) / len(durations) if durations else 0.0

    return TaskStatistics(
        total_tasks=total,
        completed_tasks=completed,
        failed_tasks=failed,
        pending_tasks=pending,
        running_tasks=running,
        average_duration=round(avg_duration, 2),
    )


def _calculate_file_stats(files: List[File]) -> FileStatistics:
    """Calculate file statistics"""
    total_files = len(files)
    total_size = sum(f.file_size or 0 for f in files)

    by_type: Dict[str, int] = {}
    for file in files:
        file_type = file.file_type.value
        by_type[file_type] = by_type.get(file_type, 0) + 1

    return FileStatistics(
        total_files=total_files,
        total_size=total_size,
        total_size_formatted=_format_file_size(total_size),
        by_type=by_type,
    )


def _calculate_stage_stats(tasks: List[Task]) -> List[StageStatistics]:
    """Calculate per-stage statistics"""
    stage_data: Dict[str, Dict[str, int]] = {}

    for task in tasks:
        stage = task.stage.value
        if stage not in stage_data:
            stage_data[stage] = {"total": 0, "completed": 0, "failed": 0}

        stage_data[stage]["total"] += 1
        if task.status == TaskStatus.COMPLETED:
            stage_data[stage]["completed"] += 1
        elif task.status == TaskStatus.FAILED:
            stage_data[stage]["failed"] += 1

    result = []
    for stage, data in stage_data.items():
        success_rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0.0
        result.append(
            StageStatistics(
                stage=stage,
                total_tasks=data["total"],
                completed_tasks=data["completed"],
                failed_tasks=data["failed"],
                success_rate=round(success_rate, 1),
            )
        )

    return result


def _aggregate_video_stats(files: List[File]) -> Optional[VideoStatistics]:
    """Aggregate video statistics from all video files"""
    video_files = [f for f in files if f.file_type == FileType.VIDEO]

    if not video_files:
        return None

    total_duration = 0.0
    total_frames = 0
    total_size = 0
    resolutions = []
    codecs = []

    for video_file in video_files:
        extra_info = video_file.extra_info or {}
        video_stats = extra_info.get("video_stats", {})

        duration = video_stats.get("duration", 0.0)
        total_duration += duration
        total_frames += video_stats.get("frame_count", 0)
        total_size += video_file.file_size or 0

        resolution = video_stats.get("resolution", "")
        if resolution:
            resolutions.append(resolution)

        codec = video_stats.get("codec", "")
        if codec:
            codecs.append(codec)

    # Calculate average frame rate
    avg_frame_rate = 0.0
    if total_duration > 0:
        avg_frame_rate = total_frames / total_duration

    # Most common resolution
    most_common_resolution = max(set(resolutions), key=resolutions.count) if resolutions else "0x0"

    # Most common codec
    most_common_codec = max(set(codecs), key=codecs.count) if codecs else "unknown"

    # Check if any video has audio
    has_audio = any(
        (f.extra_info or {}).get("video_stats", {}).get("has_audio", False)
        for f in video_files
    )

    return VideoStatistics(
        duration=round(total_duration, 3),
        duration_formatted=_format_duration(total_duration),
        frame_count=total_frames,
        frame_rate=round(avg_frame_rate, 2),
        resolution=most_common_resolution,
        file_size=total_size,
        file_size_formatted=_format_file_size(total_size),
        codec=most_common_codec,
        has_audio=has_audio,
    )


def _format_duration(duration_seconds: float) -> str:
    """Format duration as HH:MM:SS.mmm"""
    from datetime import timedelta
    td = timedelta(seconds=duration_seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int((duration_seconds % 1) * 1000)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    else:
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _get_recent_tasks(tasks: List[Task], limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent tasks for dashboard"""
    sorted_tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    result = []
    for task in sorted_tasks:
        result.append({
            "id": str(task.id),
            "stage": task.stage.value,
            "status": task.status.value,
            "generator_type": task.generator_type,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
        })

    return result


@router.get("/projects/{project_id}/stats", response_model=ProjectStatistics)
def get_project_stats(project_id: UUID, db: Session = Depends(get_db)):
    """Get project statistics"""
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    tasks = task_crud.get_all(db, project_id=project_id)
    files = file_crud.get_all(db, project_id=project_id)

    task_stats = _calculate_task_stats(tasks)
    file_stats = _calculate_file_stats(files)
    stage_stats = _calculate_stage_stats(tasks)
    video_stats = _aggregate_video_stats(files)

    # Determine last activity
    last_activity = None
    if tasks:
        task_dates = [t.updated_at for t in tasks if t.updated_at]
        file_dates = [f.updated_at for f in files if f.updated_at]
        all_dates = task_dates + file_dates
        if all_dates:
            last_activity = max(all_dates)

    return ProjectStatistics(
        project_id=project_id,
        task_stats=task_stats,
        file_stats=file_stats,
        video_stats=video_stats,
        stage_stats=stage_stats,
        created_at=project.created_at,
        updated_at=project.updated_at,
        last_activity=last_activity,
    )


@router.get("/projects/{project_id}/dashboard", response_model=DashboardResponse)
def get_dashboard_data(project_id: UUID, db: Session = Depends(get_db)):
    """Get dashboard data for project"""
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    tasks = task_crud.get_all(db, project_id=project_id)
    files = file_crud.get_all(db, project_id=project_id)

    task_stats = _calculate_task_stats(tasks)
    file_stats = _calculate_file_stats(files)
    stage_stats = _calculate_stage_stats(tasks)
    video_stats = _aggregate_video_stats(files)

    # Build metrics
    metrics: List[DashboardMetric] = [
        DashboardMetric(
            title="总任务数",
            value=str(task_stats.total_tasks),
            trend="neutral",
        ),
        DashboardMetric(
            title="完成率",
            value=f"{(task_stats.completed_tasks / task_stats.total_tasks * 100) if task_stats.total_tasks > 0 else 0:.1f}%",
            trend="up" if task_stats.completed_tasks > task_stats.failed_tasks else "down",
        ),
        DashboardMetric(
            title="总文件数",
            value=str(file_stats.total_files),
            trend="neutral",
        ),
        DashboardMetric(
            title="总存储",
            value=file_stats.total_size_formatted,
            trend="neutral",
        ),
    ]

    # Add video-specific metrics if available
    if video_stats:
        metrics.extend([
            DashboardMetric(
                title="视频总时长",
                value=video_stats.duration_formatted,
                trend="neutral",
            ),
            DashboardMetric(
                title="总帧数",
                value=f"{video_stats.frame_count:,}",
                trend="neutral",
            ),
        ])

    # Get recent tasks
    recent_tasks = _get_recent_tasks(tasks)

    return DashboardResponse(
        project_id=project_id,
        project_name=project.name,
        metrics=metrics,
        statistics=ProjectStatistics(
            project_id=project_id,
            task_stats=task_stats,
            file_stats=file_stats,
            video_stats=video_stats,
            stage_stats=stage_stats,
            created_at=project.created_at,
            updated_at=project.updated_at,
            last_activity=None,
        ),
        recent_tasks=recent_tasks,
        files_by_type=file_stats.by_type,
    )


@router.get("/projects/{project_id}/report")
def export_report(project_id: UUID, db: Session = Depends(get_db)):
    """Export project report as JSON"""
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    tasks = task_crud.get_all(db, project_id=project_id)
    files = file_crud.get_all(db, project_id=project_id)
    variant_groups = db.query(VariantGroup).filter(
        VariantGroup.project_id == project_id
    ).all()

    task_stats = _calculate_task_stats(tasks)
    file_stats = _calculate_file_stats(files)
    stage_stats = _calculate_stage_stats(tasks)
    video_stats = _aggregate_video_stats(files)

    # Build task list
    task_list = []
    for task in tasks:
        task_list.append({
            "id": str(task.id),
            "stage": task.stage.value,
            "status": task.status.value,
            "generator_type": task.generator_type,
            "parameters": task.parameters,
            "output_file_ids": [str(fid) for fid in task.output_file_ids],
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
        })

    # Build file list
    file_list = []
    for file in files:
        file_list.append({
            "id": str(file.id),
            "file_path": file.file_path,
            "file_type": file.file_type.value,
            "file_size": file.file_size,
            "generation_params": file.generation_params,
            "extra_info": file.extra_info,
            "is_selected": file.is_selected,
            "created_at": file.created_at.isoformat(),
        })

    # Build variant list
    variant_list = []
    for vg in variant_groups:
        variant_list.append({
            "id": str(vg.id),
            "stage": vg.stage,
            "parameters": vg.parameters,
            "selected_file_id": str(vg.selected_file_id) if vg.selected_file_id else None,
            "created_at": vg.created_at.isoformat(),
        })

    report = ExportReport(
        project_id=project_id,
        project_name=project.name,
        exported_at=datetime.utcnow(),
        statistics=ProjectStatistics(
            project_id=project_id,
            task_stats=task_stats,
            file_stats=file_stats,
            video_stats=video_stats,
            stage_stats=stage_stats,
            created_at=project.created_at,
            updated_at=project.updated_at,
            last_activity=None,
        ),
        tasks=task_list,
        files=file_list,
        variants=variant_list,
    )

    # Return as JSON response with download header
    response = JSONResponse(
        content=json.loads(report.model_dump_json()),
        headers={
            "Content-Disposition": f'attachment; filename="report_{project_id}.json"'
        },
    )
    return response


@router.get("/projects/{project_id}/videos")
def get_video_statistics(project_id: UUID, db: Session = Depends(get_db)):
    """Get detailed video statistics for all video files"""
    project = project_crud.get(db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    files = file_crud.get_all(db, project_id=project_id)
    video_files = [f for f in files if f.file_type == FileType.VIDEO]

    video_stats_list = []
    for video_file in video_files:
        extra_info = video_file.extra_info or {}
        stats = extra_info.get("video_stats", {})

        video_stats_list.append({
            "file_id": str(video_file.id),
            "file_path": video_file.file_path,
            "file_size": video_file.file_size,
            "file_size_formatted": _format_file_size(video_file.file_size or 0),
            **stats,
        })

    return {
        "project_id": str(project_id),
        "total_videos": len(video_files),
        "videos": video_stats_list,
    }


@router.post("/files/{file_id}/analyze")
def analyze_file_endpoint(file_id: UUID, db: Session = Depends(get_db)):
    """Analyze a video file and update its metadata"""
    file = file_crud.get(db, file_id=file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found",
        )

    if file.file_type != FileType.VIDEO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a video",
        )

    # Construct full path
    file_path = settings.storage_path / file.file_path

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found on disk: {file.file_path}",
        )

    # Analyze video
    video_info = analyze_video(str(file_path))

    if video_info:
        # Update file with video stats
        extra_info = file.extra_info or {}
        extra_info["video_stats"] = video_info
        file_crud.update(db, file_id=file_id, obj_in={"extra_info": extra_info})

        return {
            "file_id": str(file_id),
            "video_stats": video_info,
            "message": "Video analysis completed",
        }
    else:
        return {
            "file_id": str(file_id),
            "message": "Video analysis failed or not supported",
        }
