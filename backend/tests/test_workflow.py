"""
Integration tests for workflow services

Simple validation tests that don't require database.
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWorkflowServiceImport:
    """Test that services can be imported and have correct structure"""

    def test_workflow_service_import(self):
        """Test WorkflowService can be imported"""
        from app.services.workflow_service import WorkflowService, WorkflowError
        assert WorkflowService is not None
        assert WorkflowError is not None

    def test_workflow_service_stage_order(self):
        """Test STAGE_ORDER is correctly defined"""
        from app.services.workflow_service import WorkflowService
        from app.models.task import TaskStage

        assert len(WorkflowService.STAGE_ORDER) == 5
        assert WorkflowService.STAGE_ORDER[0] == TaskStage.SCRIPT
        assert WorkflowService.STAGE_ORDER[1] == TaskStage.STORYBOARD
        assert WorkflowService.STAGE_ORDER[2] == TaskStage.IMAGE
        assert WorkflowService.STAGE_ORDER[3] == TaskStage.AUDIO
        assert WorkflowService.STAGE_ORDER[4] == TaskStage.VIDEO

    def test_workflow_service_generator_map(self):
        """Test STAGE_GENERATOR_MAP is correctly defined"""
        from app.services.workflow_service import WorkflowService
        from app.models.task import TaskStage

        assert WorkflowService.STAGE_GENERATOR_MAP[TaskStage.SCRIPT] == "script"
        assert WorkflowService.STAGE_GENERATOR_MAP[TaskStage.STORYBOARD] == "storyboard"
        assert WorkflowService.STAGE_GENERATOR_MAP[TaskStage.IMAGE] == "image"

    def test_traceability_service_import(self):
        """Test TraceabilityService can be imported"""
        from app.services.traceability_service import TraceabilityService
        assert TraceabilityService is not None


class TestAPIRoutes:
    """Test API routes can be imported"""

    def test_workflow_router_import(self):
        """Test workflow router can be imported"""
        from app.api.routes.workflow import router
        assert router is not None

    def test_generators_router(self):
        """Test generators router has correct endpoints"""
        from app.api.routes.generators import GENERATORS

        assert "script" in GENERATORS
        assert "storyboard" in GENERATORS
        assert "image" in GENERATORS

        assert GENERATORS["script"].name == "Script Generator"
        assert GENERATORS["image"].type == "wanx"


class TestProviders:
    """Test providers can be imported"""

    def test_llm_provider_import(self):
        """Test LLMProvider can be imported"""
        from app.providers.llm_provider import llm_provider, LLMProvider
        assert llm_provider is not None
        assert LLMProvider is not None

    def test_base_provider_import(self):
        """Test BaseProvider can be imported"""
        from app.providers.base_provider import BaseProvider, GenerationResult
        assert BaseProvider is not None
        assert GenerationResult is not None


class TestGeneratorServices:
    """Test generator services can be imported"""

    def test_script_generator_service_import(self):
        """Test ScriptGeneratorService can be imported"""
        from app.services.generator_services import ScriptGeneratorService
        assert ScriptGeneratorService is not None

    def test_storyboard_generator_service_import(self):
        """Test StoryboardGeneratorService can be imported"""
        from app.services.generator_services import StoryboardGeneratorService
        assert StoryboardGeneratorService is not None

    def test_image_generator_service_import(self):
        """Test ImageGeneratorService can be imported"""
        from app.services.generator_services import ImageGeneratorService
        assert ImageGeneratorService is not None

    def test_tts_service_import(self):
        """Test TTSService can be imported"""
        from app.services.tts_service import TTSService
        assert TTSService is not None

    def test_bgm_service_import(self):
        """Test BGMService can be imported"""
        from app.services.bgm_service import bgm_service
        assert bgm_service is not None

    def test_sfx_service_import(self):
        """Test SFXService can be imported"""
        from app.services.sfx_service import sfx_service
        assert sfx_service is not None

    def test_video_synthesis_service_import(self):
        """Test VideoSynthesisService can be imported"""
        from app.services.video_synthesis_service import VideoSynthesisService
        assert VideoSynthesisService is not None


class TestModels:
    """Test models are correctly defined"""

    def test_task_stage_enum(self):
        """Test TaskStage enum values"""
        from app.models.task import TaskStage

        assert TaskStage.SCRIPT.value == "script"
        assert TaskStage.STORYBOARD.value == "storyboard"
        assert TaskStage.IMAGE.value == "image"
        assert TaskStage.AUDIO.value == "audio"
        assert TaskStage.VIDEO.value == "video"

    def test_task_status_enum(self):
        """Test TaskStatus enum values"""
        from app.models.task import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_file_type_enum(self):
        """Test FileType enum values"""
        from app.models.file import FileType

        assert FileType.IMAGE.value == "image"
        assert FileType.AUDIO.value == "audio"
        assert FileType.VIDEO.value == "video"
        assert FileType.SCRIPT.value == "script"
        assert FileType.STORYBOARD.value == "storyboard"


class TestMainApp:
    """Test main application"""

    def test_app_import(self):
        """Test app can be imported"""
        from app.main import app
        assert app is not None

    def test_app_title(self):
        """Test app title"""
        from app.main import app
        assert app.title == "Ops-Video"

    def test_app_routes_registered(self):
        """Test routes are registered"""
        from app.main import app

        route_paths = [r.path for r in app.routes]

        assert "/api/v1/projects" in str(route_paths)
        assert "/api/v1/tasks" in str(route_paths)
        assert "/api/v1/files" in str(route_paths)
        assert "/api/v1/variants" in str(route_paths)
        assert "/api/v1/generators" in str(route_paths)
        assert "/api/v1/workflow" in str(route_paths)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
