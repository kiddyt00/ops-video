"""
Workflow API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import asyncio

from ...db.session import get_db
from ...services.workflow_service import WorkflowService
from ...services.traceability_service import TraceabilityService
from ...schemas.task import TaskResponse

router = APIRouter()


@router.get("/{project_id}/status")
def get_workflow_status(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get workflow status for a project"""
    workflow = WorkflowService(db)
    stages_dict = workflow.get_project_stages(project_id)

    # Transform dict {stage_name: {details}} → list [{stage, status, ...}] for frontend
    stages_list = []
    for stage_name, stage_data in stages_dict.items():
        has_completed = stage_data["completed_tasks"] > 0
        has_running = not has_completed and stage_data["total_tasks"] > 0
        status = "completed" if has_completed else ("running" if has_running else "pending")
        stages_list.append({
            "stage": stage_name,
            "status": status,
            "total_tasks": stage_data["total_tasks"],
            "completed_tasks": stage_data["completed_tasks"],
            "selected_files": stage_data["selected_files"],
            "can_proceed": stage_data["can_proceed"],
        })

    return {
        "project_id": str(project_id),
        "stages": stages_list,
        "current_stage": workflow.get_current_stage(project_id).value if workflow.get_current_stage(project_id) else None,
    }


@router.get("/{project_id}/history")
def get_workflow_history(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get complete workflow execution history"""
    workflow = WorkflowService(db)
    history = workflow.get_workflow_history(project_id)

    return {
        "project_id": str(project_id),
        "history": history,
    }


from ...schemas.task import TaskResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional


class WorkflowAdvanceRequest(BaseModel):
    generator_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    execute: bool = True


class WorkflowAdvanceToStageRequest(BaseModel):
    parameters: Optional[Dict[str, Any]] = None
    execute: bool = True


@router.post("/{project_id}/advance", response_model=TaskResponse)
async def advance_workflow(
    project_id: UUID,
    request: Optional[WorkflowAdvanceRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Advance workflow to next stage

    This will:
    1. Validate prerequisites are met
    2. Create task for next stage
    3. If execute=True, run the generation immediately
    4. Return task info
    """
    workflow = WorkflowService(db)

    request = request or WorkflowAdvanceRequest()
    try:
        task = await workflow.advance_stage(
            project_id=project_id,
            generator_type=request.generator_type,
            parameters=request.parameters,
            execute=request.execute,
        )
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/advance/{target_stage}", response_model=TaskResponse)
async def advance_to_stage(
    project_id: UUID,
    target_stage: str,
    request: Optional[WorkflowAdvanceToStageRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Advance workflow to a specific stage

    target_stage: script, storyboard, image, audio, video
    """
    from ...models.task import TaskStage

    stage_map = {
        "script": TaskStage.SCRIPT,
        "storyboard": TaskStage.STORYBOARD,
        "image": TaskStage.IMAGE,
        "audio": TaskStage.AUDIO,
        "video": TaskStage.VIDEO,
    }

    if target_stage not in stage_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage: {target_stage}. Valid stages: {list(stage_map.keys())}"
        )

    workflow = WorkflowService(db)
    request = request or WorkflowAdvanceToStageRequest()

    try:
        task = await workflow.advance_stage(
            project_id=project_id,
            target_stage=stage_map[target_stage],
            parameters=request.parameters,
            execute=request.execute,
        )
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/rollback/{target_stage}", response_model=TaskResponse)
async def rollback_to_stage(
    project_id: UUID,
    target_stage: str,
    file_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Rollback to a previous stage

    This creates a new task based on the historical task parameters
    """
    from ...models.task import TaskStage

    stage_map = {
        "script": TaskStage.SCRIPT,
        "storyboard": TaskStage.STORYBOARD,
        "image": TaskStage.IMAGE,
        "audio": TaskStage.AUDIO,
        "video": TaskStage.VIDEO,
    }

    if target_stage not in stage_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage: {target_stage}"
        )

    workflow = WorkflowService(db)

    try:
        task = await workflow.rollback_stage(
            project_id=project_id,
            target_stage=stage_map[target_stage],
            file_id=file_id,
        )
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/variants/{variant_group_id}/compare")
def compare_variants(
    variant_group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get variant comparison data for a variant group"""
    workflow = WorkflowService(db)

    try:
        comparison = workflow.get_variant_comparison(variant_group_id)
        return comparison
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/variants/{variant_group_id}/files/{file_id}/compare")
def compare_two_files(
    variant_group_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Compare two files within the same variant group"""
    from ...db.file_crud import variant_group_crud, file_crud

    variant_group = variant_group_crud.get(db, variant_group_id=variant_group_id)
    if not variant_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant group not found"
        )

    # Get another file from the same group for comparison
    files = file_crud.get_all(db)
    group_files = [f for f in files if f.variant_group_id == variant_group_id and f.id != file_id]

    if not group_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No other files in variant group to compare"
        )

    # Compare with the first other file (or selected file)
    compare_with_id = variant_group.selected_file_id or group_files[0].id

    traceability = TraceabilityService(db)
    comparison = traceability.compare_files(file_id, compare_with_id)

    return comparison


@router.get("/files/{file_id}/lineage")
def get_file_lineage(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Get complete generation lineage for a file"""
    traceability = TraceabilityService(db)
    lineage = traceability.get_generation_lineage(file_id)

    return {
        "file_id": str(file_id),
        "lineage": lineage,
    }


@router.get("/files/{file_id}/versions")
def get_file_versions(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all versions of a file"""
    traceability = TraceabilityService(db)
    versions = traceability.get_file_versions(file_id)

    return {
        "file_id": str(file_id),
        "versions": versions,
    }


@router.post("/{project_id}/rollback-regenerate")
async def rollback_and_regenerate(
    project_id: UUID,
    source_file_id: UUID,
    generator_type: str,
    new_parameters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Rollback to a historical file and regenerate with modified parameters

    This is useful for:
    - Trying different seeds/prompts while keeping other parameters
    - Regenerating downstream stages with updated upstream content
    """
    traceability = TraceabilityService(db)

    try:
        task, variant_group = await traceability.rollback_and_regenerate(
            project_id=project_id,
            source_file_id=source_file_id,
            generator_type=generator_type,
            new_parameters=new_parameters,
        )

        return {
            "task_id": str(task.id),
            "variant_group_id": str(variant_group.id),
            "status": "pending",
            "message": "Regeneration task created",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
