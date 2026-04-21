"""
Workflow Service - Core workflow engine
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from enum import Enum

from ..models.task import Task, TaskStage, TaskStatus
from ..models.file import File, FileType, VariantGroup
from ..models.project import Project
from ..db.task_crud import task_crud
from ..db.file_crud import file_crud, variant_group_crud
from ..db.project_crud import project_crud
from ..schemas.task import TaskCreate, TaskStatusUpdate


class WorkflowError(Exception):
    """Workflow execution error"""
    pass


class WorkflowService:
    """
    Workflow engine for managing generation pipeline

    Stage order: script -> storyboard -> image -> audio -> video
    """

    STAGE_ORDER: List[TaskStage] = [
        TaskStage.SCRIPT,
        TaskStage.STORYBOARD,
        TaskStage.IMAGE,
        TaskStage.AUDIO,
        TaskStage.VIDEO,
    ]

    STAGE_GENERATOR_MAP: Dict[TaskStage, str] = {
        TaskStage.SCRIPT: "script",
        TaskStage.STORYBOARD: "storyboard",
        TaskStage.IMAGE: "image",
        TaskStage.AUDIO: "tts",
        TaskStage.VIDEO: "video_composer",
    }

    def __init__(self, db: Session):
        self.db = db

    def get_project_stages(self, project_id: UUID) -> Dict[str, Any]:
        """Get all stages and their status for a project"""
        tasks = task_crud.get_all(self.db, project_id=project_id)

        stages = {}
        for stage in self.STAGE_ORDER:
            stage_tasks = [t for t in tasks if t.stage == stage]
            completed_tasks = [t for t in stage_tasks if t.status == TaskStatus.COMPLETED]
            selected_files = []

            for task in completed_tasks:
                variant_groups = self.db.query(VariantGroup).filter(
                    VariantGroup.task_id == task.id
                ).all()
                for vg in variant_groups:
                    if vg.selected_file_id:
                        selected_files.append({
                            "file_id": str(vg.selected_file_id),
                            "task_id": str(task.id),
                            "variant_group_id": str(vg.id),
                        })

            stages[stage.value] = {
                "total_tasks": len(stage_tasks),
                "completed_tasks": len(completed_tasks),
                "selected_files": selected_files,
                "can_proceed": len(selected_files) > 0,
            }

        return stages

    def get_current_stage(self, project_id: UUID) -> Optional[TaskStage]:
        """Get the current active stage of the project"""
        stages_status = self.get_project_stages(project_id)

        for stage in self.STAGE_ORDER:
            stage_data = stages_status[stage.value]
            if stage_data["selected_files"]:
                return stage

        return None

    def can_advance_to(self, project_id: UUID, target_stage: TaskStage) -> bool:
        """Check if workflow can advance to target stage"""
        if target_stage == TaskStage.SCRIPT:
            return True

        target_index = self.STAGE_ORDER.index(target_stage)
        for i in range(target_index):
            prev_stage = self.STAGE_ORDER[i]
            stages_status = self.get_project_stages(project_id)
            if not stages_status[prev_stage.value]["selected_files"]:
                return False

        return True

    def get_next_stage(self, current_stage: TaskStage) -> Optional[TaskStage]:
        """Get the next stage in the workflow"""
        try:
            current_index = self.STAGE_ORDER.index(current_stage)
            if current_index < len(self.STAGE_ORDER) - 1:
                return self.STAGE_ORDER[current_index + 1]
        except ValueError:
            pass
        return None

    def get_previous_stage(self, current_stage: TaskStage) -> Optional[TaskStage]:
        """Get the previous stage in the workflow"""
        try:
            current_index = self.STAGE_ORDER.index(current_stage)
            if current_index > 0:
                return self.STAGE_ORDER[current_index - 1]
        except ValueError:
            pass
        return None

    async def advance_stage(
        self,
        project_id: UUID,
        target_stage: Optional[TaskStage] = None,
        generator_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Advance workflow to next stage or specific stage

        Args:
            project_id: Project ID
            target_stage: Optional specific stage to advance to
            generator_type: Optional generator type override
            parameters: Optional generation parameters

        Returns:
            Created task for the new stage
        """
        project = project_crud.get(self.db, project_id=project_id)
        if not project:
            raise WorkflowError(f"Project {project_id} not found")

        # Determine target stage
        if target_stage is None:
            current_stage = self.get_current_stage(project_id)
            if current_stage is None:
                target_stage = TaskStage.SCRIPT
            else:
                target_stage = self.get_next_stage(current_stage)

            if target_stage is None:
                raise WorkflowError("Workflow already at final stage")

        # Validate prerequisites
        if not self.can_advance_to(project_id, target_stage):
            raise WorkflowError(
                f"Cannot advance to {target_stage.value}: "
                "prerequisite stages not completed"
            )

        # Get selected files from previous stages
        input_file_ids = self._get_input_files(project_id, target_stage)

        # Determine generator type
        if generator_type is None:
            generator_type = self.STAGE_GENERATOR_MAP.get(target_stage, target_stage.value)

        # Create task for new stage
        task_create = TaskCreate(
            project_id=project_id,
            stage=target_stage,
            generator_type=generator_type,
            parameters=parameters or {},
            parent_task_ids=[UUID(f["task_id"]) for f in input_file_ids] if input_file_ids else [],
        )

        task = task_crud.create(self.db, obj_in=task_create)

        # Create variant group
        variant_group_crud.create(
            self.db,
            obj_in={
                "project_id": project_id,
                "task_id": task.id,
                "stage": target_stage.value,
                "parameters": parameters or {},
            },
        )

        return task

    def _get_input_files(
        self,
        project_id: UUID,
        target_stage: TaskStage
    ) -> List[Dict[str, str]]:
        """Get selected input files for target stage"""
        stages_status = self.get_project_stages(project_id)
        target_index = self.STAGE_ORDER.index(target_stage)

        input_files = []

        # Collect selected files from all previous completed stages
        for i in range(target_index):
            prev_stage = self.STAGE_ORDER[i]
            stage_data = stages_status[prev_stage.value]
            input_files.extend(stage_data["selected_files"])

        return input_files

    async def rollback_stage(
        self,
        project_id: UUID,
        target_stage: TaskStage,
        file_id: Optional[UUID] = None,
    ) -> Task:
        """
        Rollback to a previous stage and optionally use a different file

        Args:
            project_id: Project ID
            target_stage: Stage to rollback to
            file_id: Optional specific file to use (for variant selection)

        Returns:
            New task for the target stage
        """
        # Verify target stage exists and has completed tasks
        tasks = task_crud.get_all(self.db, project_id=project_id)
        stage_tasks = [t for t in tasks if t.stage == target_stage and t.status == TaskStatus.COMPLETED]

        if not stage_tasks:
            raise WorkflowError(f"No completed tasks found for stage {target_stage.value}")

        # Create new task for the target stage
        latest_task = max(stage_tasks, key=lambda t: t.created_at)

        task_create = TaskCreate(
            project_id=project_id,
            stage=target_stage,
            generator_type=latest_task.generator_type,
            parameters=latest_task.parameters,
            parent_task_ids=latest_task.parent_task_id,
        )

        task = task_crud.create(self.db, obj_in=task_create)

        return task

    def get_workflow_history(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get complete workflow execution history for a project"""
        tasks = task_crud.get_all(self.db, project_id=project_id)

        history = []
        for task in sorted(tasks, key=lambda t: t.created_at):
            # Get variant groups for this task
            variant_groups = self.db.query(VariantGroup).filter(
                VariantGroup.task_id == task.id
            ).all()

            # Get files for this task
            files = self.db.query(File).filter(
                File.task_id == task.id
            ).all()

            # Get status logs
            status_logs = task.status_logs

            history.append({
                "task_id": str(task.id),
                "stage": task.stage.value,
                "generator_type": task.generator_type,
                "status": task.status.value,
                "parameters": task.parameters,
                "variant_groups": [
                    {
                        "id": str(vg.id),
                        "selected_file_id": str(vg.selected_file_id) if vg.selected_file_id else None,
                    }
                    for vg in variant_groups
                ],
                "files": [
                    {
                        "id": str(f.id),
                        "file_type": f.file_type.value,
                        "file_path": f.file_path,
                        "is_selected": f.is_selected,
                    }
                    for f in files
                ],
                "status_logs": [
                    {
                        "from_status": log.from_status.value if log.from_status else None,
                        "to_status": log.to_status.value,
                        "reason": log.reason,
                        "changed_at": log.changed_at.isoformat(),
                    }
                    for log in status_logs
                ],
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            })

        return history

    def get_variant_comparison(
        self,
        variant_group_id: UUID
    ) -> Dict[str, Any]:
        """Get variant comparison data for a variant group"""
        variant_group = variant_group_crud.get(self.db, variant_group_id=variant_group_id)

        if not variant_group:
            raise WorkflowError(f"VariantGroup {variant_group_id} not found")

        files = self.db.query(File).filter(
            File.variant_group_id == variant_group_id
        ).all()

        return {
            "variant_group_id": str(variant_group.id),
            "stage": variant_group.stage,
            "parameters": variant_group.parameters,
            "selected_file_id": str(variant_group.selected_file_id) if variant_group.selected_file_id else None,
            "variants": [
                {
                    "file_id": str(f.id),
                    "file_path": f.file_path,
                    "file_type": f.file_type.value,
                    "generation_params": f.generation_params,
                    "extra_info": f.extra_info,
                    "is_selected": f.is_selected,
                    "created_at": f.created_at.isoformat(),
                }
                for f in files
            ],
        }


workflow_service = WorkflowService
