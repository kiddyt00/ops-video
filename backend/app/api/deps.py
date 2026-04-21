"""
Dependency injection
"""
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ...db.session import get_db
from ...models.project import Project
from ...models.task import Task
from ...models.file import File
from ...models.variant import VariantGroup


def get_project(project_id: UUID, db: Session = Depends(get_db)) -> Project:
    """Get project by ID or raise 404"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


def get_task(task_id: UUID, db: Session = Depends(get_db)) -> Task:
    """Get task by ID or raise 404"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


def get_file(file_id: UUID, db: Session = Depends(get_db)) -> File:
    """Get file by ID or raise 404"""
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    return file
