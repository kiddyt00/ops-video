"""
Task API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..db.session import get_db

router = APIRouter()


@router.get("")
def list_tasks(project_id: UUID, db: Session = Depends(get_db)):
    """List tasks for a project"""
    pass


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task():
    """Create a new task"""
    pass


@router.get("/{task_id}")
def get_task(task_id: UUID):
    """Get task by ID"""
    pass


@router.post("/{task_id}/run")
def run_task(task_id: UUID):
    """Execute a task"""
    pass


@router.put("/{task_id}/status")
def update_task_status(task_id: UUID):
    """Update task status"""
    pass
