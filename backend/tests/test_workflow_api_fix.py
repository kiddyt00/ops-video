"""
Test that workflow advance endpoints read generator_type from request body.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.api.routes.workflow import WorkflowAdvanceRequest, advance_workflow
from app.models.task import TaskStage, TaskStatus


@pytest.mark.asyncio
async def test_advance_workflow_reads_generator_type_from_body():
    """When request body contains generator_type='storyboard', the service
    should create a storyboard task, not default to script."""
    project_id = uuid4()
    mock_db = MagicMock()

    created_task = MagicMock()
    created_task.id = uuid4()
    created_task.project_id = project_id
    created_task.status = TaskStatus.COMPLETED
    created_task.stage = TaskStage.STORYBOARD
    created_task.generator_type = "storyboard"

    with patch("app.api.routes.workflow.WorkflowService") as MockService:
        mock_service = MagicMock()
        mock_service.advance_stage = AsyncMock(return_value=created_task)
        MockService.return_value = mock_service

        request = WorkflowAdvanceRequest(
            generator_type="storyboard",
            parameters={"panel_count": 6},
            execute=True,
        )

        result = await advance_workflow(
            project_id=project_id,
            request=request,
            db=mock_db,
        )

        # Verify advance_stage was called with the correct generator_type
        mock_service.advance_stage.assert_awaited_once_with(
            project_id=project_id,
            generator_type="storyboard",
            parameters={"panel_count": 6},
            execute=True,
            chapter_id=None,
        )
        assert result.status == TaskStatus.COMPLETED
        assert result.stage == TaskStage.STORYBOARD


@pytest.mark.asyncio
async def test_advance_workflow_defaults_to_none_when_no_generator_type():
    """When request body omits generator_type, it should be passed as None
    so the service can auto-determine the stage."""
    project_id = uuid4()
    mock_db = MagicMock()

    with patch("app.api.routes.workflow.WorkflowService") as MockService:
        mock_service = MagicMock()
        mock_service.advance_stage = AsyncMock(side_effect=Exception("test"))
        MockService.return_value = mock_service

        request = WorkflowAdvanceRequest()

        try:
            await advance_workflow(
                project_id=project_id,
                request=request,
                db=mock_db,
            )
        except Exception:
            pass

        mock_service.advance_stage.assert_awaited_once_with(
            project_id=project_id,
            generator_type=None,
            parameters=None,
            execute=True,
            chapter_id=None,
        )
