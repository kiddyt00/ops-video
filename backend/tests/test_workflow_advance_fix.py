"""
Tests for workflow_service.py advance_stage fixes:
- Bug 1: generator_type should determine target_stage when target_stage is None
- Bug 2: execute=True should update task status to failed on error
"""
import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.workflow_service import WorkflowService, WorkflowError
from app.models.task import TaskStage, TaskStatus


class TestAdvanceStageGeneratorTypeMapping:
    """Bug 1: generator_type should be used to derive target_stage"""

    def test_generator_type_maps_to_correct_stage(self):
        """When target_stage is None and generator_type is provided,
        the service should derive target_stage from generator_type."""
        ws = WorkflowService(MagicMock())
        reverse_map = ws._GENERATOR_TO_STAGE
        assert reverse_map["script"] == TaskStage.SCRIPT
        assert reverse_map["storyboard"] == TaskStage.STORYBOARD
        assert reverse_map["image"] == TaskStage.IMAGE
        assert reverse_map["tts"] == TaskStage.AUDIO
        assert reverse_map["video_composer"] == TaskStage.VIDEO

    @pytest.mark.asyncio
    async def test_advance_with_storyboard_generator_type(self):
        """Passing generator_type='storyboard' should create a storyboard task, not script."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_db.query.return_value.first.return_value = None  # no variant groups

        with patch("app.services.workflow_service.project_crud") as mock_project_crud, \
             patch("app.services.workflow_service.task_crud") as mock_task_crud, \
             patch("app.services.workflow_service.variant_group_crud") as mock_vg_crud:

            mock_project_crud.get.return_value = mock_project

            # Make can_advance_to pass by returning True for storyboard
            created_task = MagicMock()
            created_task.id = uuid4()
            created_task.project_id = mock_project.id
            created_task.status = TaskStatus.PENDING
            mock_task_crud.create.return_value = created_task

            ws = WorkflowService(mock_db)

            # Patch can_advance_to to always return True
            with patch.object(ws, "can_advance_to", return_value=True), \
                 patch.object(ws, "get_project_stages", return_value={
                     "script": {"selected_files": [{"file_id": "1", "task_id": str(uuid4())}],
                                "completed_tasks": 1, "total_tasks": 1, "can_proceed": True},
                     "storyboard": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "image": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "audio": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "video": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                 }):
                task = await ws.advance_stage(
                    project_id=mock_project.id,
                    generator_type="storyboard",
                    execute=False,
                )

                # Verify the task was created with stage=storyboard
                task_create = mock_task_crud.create.call_args.kwargs["obj_in"]
                assert task_create.stage == TaskStage.STORYBOARD
                assert task_create.generator_type == "storyboard"

    @pytest.mark.asyncio
    async def test_advance_with_unknown_generator_type_raises(self):
        """Unknown generator_type should raise WorkflowError."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = uuid4()

        with patch("app.services.workflow_service.project_crud") as mock_project_crud:
            mock_project_crud.get.return_value = mock_project
            ws = WorkflowService(mock_db)

            with pytest.raises(WorkflowError, match="Unknown generator_type"):
                await ws.advance_stage(
                    project_id=mock_project.id,
                    generator_type="nonexistent_generator",
                    execute=False,
                )


class TestAdvanceStageExecuteErrorHandling:
    """Bug 2: execute=True should set task status to failed on generation error."""

    @pytest.mark.asyncio
    async def test_execute_script_failure_sets_failed_status(self):
        """If _execute_script_generation raises, task should be set to failed."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = uuid4()

        created_task = MagicMock()
        created_task.id = uuid4()
        created_task.project_id = mock_project.id
        created_task.status = TaskStatus.PENDING

        with patch("app.services.workflow_service.project_crud") as mock_project_crud, \
             patch("app.services.workflow_service.task_crud") as mock_task_crud, \
             patch("app.services.workflow_service.variant_group_crud") as mock_vg_crud:

            mock_project_crud.get.return_value = mock_project
            mock_task_crud.create.return_value = created_task

            ws = WorkflowService(mock_db)

            with patch.object(ws, "can_advance_to", return_value=True), \
                 patch.object(ws, "get_project_stages", return_value={
                     "script": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "storyboard": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "image": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "audio": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "video": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                 }), \
                 patch.object(ws, "_execute_script_generation", new_callable=AsyncMock,
                              side_effect=WorkflowError("Script generation failed: no topic")):

                with pytest.raises(WorkflowError, match="Script generation failed"):
                    await ws.advance_stage(
                        project_id=mock_project.id,
                        execute=True,
                    )

                # Verify task status was updated to FAILED
                mock_task_crud.update_status.assert_called_once()
                call_kwargs = mock_task_crud.update_status.call_args
                status_update = call_kwargs.kwargs["obj_in"]
                assert status_update.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_storyboard_failure_sets_failed_status(self):
        """If _execute_storyboard_generation raises, task should be set to failed."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = uuid4()

        created_task = MagicMock()
        created_task.id = uuid4()
        created_task.project_id = mock_project.id

        with patch("app.services.workflow_service.project_crud") as mock_project_crud, \
             patch("app.services.workflow_service.task_crud") as mock_task_crud, \
             patch("app.services.workflow_service.variant_group_crud") as mock_vg_crud:

            mock_project_crud.get.return_value = mock_project
            mock_task_crud.create.return_value = created_task

            ws = WorkflowService(mock_db)

            with patch.object(ws, "can_advance_to", return_value=True), \
                 patch.object(ws, "get_project_stages", return_value={
                     "script": {"selected_files": [{"file_id": "1", "task_id": str(uuid4())}],
                                "completed_tasks": 1, "total_tasks": 1, "can_proceed": True},
                     "storyboard": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "image": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "audio": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                     "video": {"selected_files": [], "completed_tasks": 0, "total_tasks": 0, "can_proceed": False},
                 }), \
                 patch.object(ws, "_execute_storyboard_generation", new_callable=AsyncMock,
                              side_effect=WorkflowError("Storyboard generation failed")):

                with pytest.raises(WorkflowError, match="Storyboard generation failed"):
                    await ws.advance_stage(
                        project_id=mock_project.id,
                        generator_type="storyboard",
                        execute=True,
                    )

                mock_task_crud.update_status.assert_called_once()
                status_update = mock_task_crud.update_status.call_args.kwargs["obj_in"]
                assert status_update.status == TaskStatus.FAILED
