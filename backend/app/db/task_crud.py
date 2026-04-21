"""
Task CRUD operations
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.task import Task, TaskStatus, TaskStatusLog
from ..schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate


class TaskCRUD:
    """Task CRUD operations"""

    def get_all(self, db: Session, project_id: Optional[UUID] = None) -> List[Task]:
        """Get all tasks, optionally filtered by project"""
        query = db.query(Task)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        return query.all()

    def get(self, db: Session, task_id: UUID) -> Optional[Task]:
        """Get task by ID"""
        return db.query(Task).filter(Task.id == task_id).first()

    def create(self, db: Session, *, obj_in: TaskCreate) -> Task:
        """Create a new task"""
        task = Task(
            project_id=obj_in.project_id,
            stage=obj_in.stage,
            generator_type=obj_in.generator_type,
            parameters=obj_in.parameters or {},
            parent_task_id=obj_in.parent_task_ids[0] if obj_in.parent_task_ids else None,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Log initial status
        self._log_status_change(db, task, None, TaskStatus.PENDING, "Task created")

        return task

    def update(
        self, db: Session, *, task_id: UUID, obj_in: TaskUpdate
    ) -> Optional[Task]:
        """Update task"""
        task = self.get(db, task_id=task_id)
        if not task:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update_status(
        self, db: Session, *, task_id: UUID, obj_in: TaskStatusUpdate
    ) -> Optional[Task]:
        """Update task status"""
        task = self.get(db, task_id=task_id)
        if not task:
            return None

        from_status = task.status
        to_status = obj_in.status

        task.status = to_status

        # Set timestamps based on status
        if to_status == TaskStatus.RUNNING and from_status != TaskStatus.RUNNING:
            task.started_at = datetime.utcnow()
        elif to_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            if task.completed_at is None:
                task.completed_at = datetime.utcnow()

        db.add(task)
        db.commit()
        db.refresh(task)

        # Log status change
        self._log_status_change(db, task, from_status, to_status, obj_in.reason)

        return task

    def delete(self, db: Session, task_id: UUID) -> bool:
        """Delete task"""
        task = self.get(db, task_id=task_id)
        if not task:
            return False

        db.delete(task)
        db.commit()
        return True

    def _log_status_change(
        self,
        db: Session,
        task: Task,
        from_status: Optional[TaskStatus],
        to_status: TaskStatus,
        reason: Optional[str] = None
    ):
        """Log a status change"""
        log = TaskStatusLog(
            task_id=task.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )
        db.add(log)
        db.commit()

    def get_status_logs(self, db: Session, task_id: UUID) -> List[TaskStatusLog]:
        """Get status logs for a task"""
        return db.query(TaskStatusLog).filter(
            TaskStatusLog.task_id == task_id
        ).order_by(TaskStatusLog.created_at).all()


task_crud = TaskCRUD()
