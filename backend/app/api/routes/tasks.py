"""
Task API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.session import get_db
from ...db.task_crud import task_crud
from ...db.project_crud import project_crud
from ...schemas.task import TaskCreate, TaskStatusUpdate, TaskResponse, TaskStatusLogResponse
from ...models.task import Task, TaskStatus

router = APIRouter()


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List tasks, optionally filtered by project"""
    tasks = task_crud.get_all(db, project_id=project_id)
    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    # Verify project exists
    project = project_crud.get(db, project_id=task_in.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {task_in.project_id} not found"
        )

    task = task_crud.create(db, obj_in=task_in)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Get task by ID"""
    task = task_crud.get(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.post("/{task_id}/run", response_model=TaskResponse)
def run_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Execute a task - starts task execution"""
    task = task_crud.get(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    if task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be run in current status: {task.status}"
        )

    # Update status to running
    task_crud.update_status(
        db,
        task_id=task_id,
        obj_in=TaskStatusUpdate(status=TaskStatus.RUNNING, reason="Task started")
    )

    # Note: Actual execution logic will be implemented in generator services
    # For now, we just mark it as running

    return task_crud.get(db, task_id=task_id)


@router.put("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: UUID,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update task status"""
    task = task_crud.get(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    updated_task = task_crud.update_status(db, task_id=task_id, obj_in=status_in)
    return updated_task


@router.get("/{task_id}/logs", response_model=List[TaskStatusLogResponse])
def get_task_logs(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Get task status change logs"""
    logs = task_crud.get_status_logs(db, task_id=task_id)
    return logs


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete task"""
    success = task_crud.delete(db, task_id=task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
