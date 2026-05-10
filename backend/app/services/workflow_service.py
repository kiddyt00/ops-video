"""
Workflow Service - Core workflow engine

Integrates all generation services:
- Script/Storyboard (LLM)
- Image (通义万相 Wanx)
- Audio (TTS via edge-tts, BGM via scipy)
- Video (FFmpeg composition)
"""
from pathlib import Path
from uuid import UUID, uuid4
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
from ..schemas.file import VariantGroupCreate
from ..config import STORAGE_DIRS, settings
from .storyboard_parser import parse_storyboard


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

    # Reverse map: generator_type -> TaskStage
    _GENERATOR_TO_STAGE: Dict[str, TaskStage] = {
        v: k for k, v in STAGE_GENERATOR_MAP.items()
    }
    # Alias audio to tts
    _GENERATOR_TO_STAGE["audio"] = TaskStage.AUDIO

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
        execute: bool = True,  # Whether to execute the generation immediately
    ) -> Task:
        """
        Advance workflow to next stage or specific stage

        Args:
            project_id: Project ID
            target_stage: Optional specific stage to advance to
            generator_type: Optional generator type override
            parameters: Optional generation parameters
            execute: Whether to execute generation immediately (for audio/video stages)

        Returns:
            Created task for the new stage
        """
        project = project_crud.get(self.db, project_id=project_id)
        if not project:
            raise WorkflowError(f"Project {project_id} not found")

        # Determine target stage
        if target_stage is None:
            # If generator_type is provided, derive target_stage from it
            if generator_type:
                target_stage = self._GENERATOR_TO_STAGE.get(generator_type)
                if target_stage is None:
                    raise WorkflowError(
                        f"Unknown generator_type: {generator_type}. "
                        f"Valid types: {list(self._GENERATOR_TO_STAGE.keys())}"
                    )
            else:
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

        # Normalize parameters
        parameters = parameters or {}

        # For audio/video stages, prepare parameters from previous stage data
        if target_stage in [TaskStage.AUDIO, TaskStage.VIDEO]:
            parameters = await self._prepare_stage_parameters(
                project_id, target_stage, parameters
            )

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
            obj_in=VariantGroupCreate(
                project_id=project_id,
                task_id=task.id,
                stage=target_stage.value,
                parameters=parameters or {},
            ),
        )

        # Execute generation for all stages if requested
        if execute:
            try:
                if target_stage in [TaskStage.AUDIO, TaskStage.VIDEO]:
                    await self._execute_generation(target_stage, task, parameters)
                elif target_stage == TaskStage.SCRIPT:
                    await self._execute_script_generation(task, parameters)
                elif target_stage == TaskStage.STORYBOARD:
                    await self._execute_storyboard_generation(task, parameters)
                elif target_stage == TaskStage.IMAGE:
                    await self._execute_image_generation(task, parameters)
            except Exception as e:
                task_crud.update_status(
                    self.db,
                    task_id=task.id,
                    obj_in=TaskStatusUpdate(
                        status=TaskStatus.FAILED,
                        reason=str(e),
                    ),
                )
                self.db.commit()
                raise

        return task

    async def _prepare_stage_parameters(
        self,
        project_id: UUID,
        target_stage: TaskStage,
        override_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare generation parameters for audio/video stages based on previous stage data.

        For AUDIO stage:
        - Extract narration text from storyboard panels
        - Collect timing/duration info

        For VIDEO stage:
        - Collect all image paths from selected images
        - Collect all audio paths (TTS, BGM, SFX)
        - Collect timing data from storyboard
        """
        stages_status = self.get_project_stages(project_id)

        if target_stage == TaskStage.AUDIO:
            # Get selected storyboard file
            storyboard_files = stages_status.get("storyboard", {}).get("selected_files", [])
            if not storyboard_files:
                return override_params

            # Load storyboard JSON to extract panel text
            storyboard_file_id = storyboard_files[0].get("file_id")
            if storyboard_file_id:
                file_record = file_crud.get(self.db, file_id=UUID(storyboard_file_id))
                if file_record:
                    import json
                    from pathlib import Path
                    storyboard_path = settings.storage_path / file_record.file_path
                    if storyboard_path.exists():
                        storyboard_data = parse_storyboard(storyboard_path.read_text())
                        panels = storyboard_data.get("panels", [])

                        # Extract text for TTS
                        texts = [p.get('text') or p.get('dialogue') or p.get('scene_description', '') for p in panels]

                        return {
                            "texts": texts,
                            "panels": panels,
                            **override_params,
                        }

        elif target_stage == TaskStage.VIDEO:
            # Collect all required data for video composition
            image_files = stages_status.get("image", {}).get("selected_files", [])
            storyboard_files = stages_status.get("storyboard", {}).get("selected_files", [])
            audio_files = stages_status.get("audio", {}).get("selected_files", [])

            panels = []

            # Get image paths
            image_paths = []
            for f in image_files:
                file_record = file_crud.get(self.db, file_id=UUID(f["file_id"]))
                if file_record:
                    image_paths.append(str(STORAGE_DIRS["images"] / file_record.file_path))

            # Get audio paths (TTS)
            tts_paths = []
            for f in audio_files:
                file_record = file_crud.get(self.db, file_id=UUID(f["file_id"]))
                if file_record and file_record.file_type == FileType.AUDIO:
                    tts_paths.append(str(STORAGE_DIRS["audio"] / file_record.file_path))

            # Get storyboard timing
            storyboard_data = {}
            if storyboard_files:
                file_record = file_crud.get(self.db, file_id=UUID(storyboard_files[0]["file_id"]))
                if file_record:
                    import json
                    from pathlib import Path
                    storyboard_path = settings.storage_path / file_record.file_path
                    if storyboard_path.exists():
                        storyboard_data = parse_storyboard(storyboard_path.read_text())

            # Build panels array for video composition
            num_panels = min(len(image_paths), len(storyboard_data.get("panels", [])))

            # Load SFX paths from audio task if available
            sfx_path_map = self._get_sfx_path_map(project_id)

            for i in range(num_panels):
                panel_data = storyboard_data["panels"][i] if i < len(storyboard_data.get("panels", [])) else {}
                panel = {
                    "image_path": image_paths[i] if i < len(image_paths) else None,
                    "audio_path": tts_paths[i] if i < len(tts_paths) else None,
                    "duration": panel_data.get("duration", 3.0),
                    "text": panel_data.get("text", ""),
                }
                if i in sfx_path_map:
                    panel["sfx_path"] = sfx_path_map[i]
                panels.append(panel)

            return {
                "panels": panels,
                "storyboard_data": storyboard_data,
                **override_params,
            }

        return override_params

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

    def _get_sfx_path_map(self, project_id: UUID) -> Dict[int, str]:
        """Load SFX file paths from the completed audio task."""
        tasks = task_crud.get_all(self.db, project_id=project_id)
        audio_tasks = [t for t in tasks if t.stage == TaskStage.AUDIO and t.status == TaskStatus.COMPLETED]
        if not audio_tasks:
            return {}

        audio_task = max(audio_tasks, key=lambda t: t.created_at)
        params = audio_task.parameters or {}
        return {int(k): v for k, v in params.get("sfx_paths", {}).items()}

    async def _execute_generation(
        self,
        target_stage: TaskStage,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """
        Execute generation for audio/video stages.

        For AUDIO stage:
        - Generate TTS for each panel's narration
        - Generate BGM

        For VIDEO stage:
        - Compose final video from images, audio, and timing
        """
        try:
            if target_stage == TaskStage.AUDIO:
                await self._execute_audio_generation(task, parameters)
            elif target_stage == TaskStage.VIDEO:
                await self._execute_video_generation(task, parameters)

            # Update task status to completed
            task_crud.update_status(
                self.db,
                task_id=task.id,
                obj_in=TaskStatusUpdate(status=TaskStatus.COMPLETED),
            )
            # Auto-select first generated file
            self._auto_select_first_file(task.id)

        except Exception as e:
            # Update task status to failed
            task_crud.update_status(
                self.db,
                task_id=task.id,
                obj_in=TaskStatusUpdate(
                    status=TaskStatus.FAILED,
                    reason=str(e),
                ),
            )
            raise

    async def _execute_audio_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute audio generation (TTS + BGM + SFX)."""
        from .tts_service import tts_service
        from .bgm_service import bgm_service
        from .sfx_service import sfx_service
        from ..schemas.file import FileCreate

        texts = parameters.get("texts", [])
        panels = parameters.get("panels", [])
        voice = parameters.get("voice", "zh-CN-XiaoxiaoNeural")
        generate_bgm = parameters.get("generate_bgm", True)
        bgm_mood = parameters.get("bgm_mood", "ambient")

        # SFX: default to one whoosh per panel, or explicit types from parameters
        sfx_types = parameters.get("sfx_types", None)
        if sfx_types is None:
            sfx_types = ["whoosh"] * len(panels) if panels else []

        # Find variant group for this task
        variant_group = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task.id
        ).first()

        file_ids = []
        sfx_path_map = {}  # panel_index -> sfx_path

        # Generate TTS for each text
        for i, text in enumerate(texts):
            if text:
                tts_path = await tts_service.synthesize(text, voice=voice)
                rel_path = str(tts_path.relative_to(settings.storage_path)) if tts_path.is_absolute() else str(tts_path)
                file_record = file_crud.create(
                    self.db,
                    obj_in=FileCreate(
                        project_id=task.project_id,
                        task_id=task.id,
                        variant_group_id=variant_group.id if variant_group else None,
                        file_path=rel_path,
                        file_type=FileType.AUDIO,
                        generation_params={"type": "tts", "panel_index": i, "voice": voice},
                    ),
                )
                file_ids.append(str(file_record.id))

        # Generate BGM
        if generate_bgm:
            total_duration = sum(p.get("duration", 3.0) for p in panels) if panels else 30.0
            bgm_path = bgm_service.generate(
                duration=total_duration,
                mood=bgm_mood,
            )
            try:
                rel_path = str(bgm_path.relative_to(settings.storage_path)) if bgm_path.is_absolute() else str(bgm_path)
            except ValueError:
                # BGM file is outside storage_path (e.g. test tmpdir); use just the filename
                rel_path = bgm_path.name
            file_record = file_crud.create(
                self.db,
                obj_in=FileCreate(
                    project_id=task.project_id,
                    task_id=task.id,
                    variant_group_id=variant_group.id if variant_group else None,
                    file_path=rel_path,
                    file_type=FileType.AUDIO,
                    generation_params={"type": "bgm", "mood": bgm_mood, "duration": total_duration},
                ),
            )
            file_ids.append(str(file_record.id))

        # Generate SFX for each panel
        for i, sfx_type in enumerate(sfx_types):
            if not sfx_type:
                continue
            panel_duration = panels[i].get("duration", 3.0) if i < len(panels) else 1.0
            sfx_path = sfx_service.generate(
                sfx_type=sfx_type,
                duration=panel_duration,
                output_filename=f"sfx_panel_{i}_{sfx_type}_{task.id}.wav",
            )
            rel_path = str(sfx_path.relative_to(settings.storage_path)) if sfx_path.is_absolute() else str(sfx_path)
            file_record = file_crud.create(
                self.db,
                obj_in=FileCreate(
                    project_id=task.project_id,
                    task_id=task.id,
                    variant_group_id=variant_group.id if variant_group else None,
                    file_path=rel_path,
                    file_type=FileType.AUDIO,
                    generation_params={"type": "sfx", "sfx_type": sfx_type, "panel_index": i},
                ),
            )
            sfx_path_map[i] = str(sfx_path)
            file_ids.append(str(file_record.id))

        # Attach SFX paths to panel data for video_composer
        for i, panel in enumerate(panels):
            if i in sfx_path_map:
                panel["sfx_path"] = sfx_path_map[i]

        # Save SFX paths to task parameters for video stage to retrieve
        task.parameters = {**task.parameters, "sfx_paths": {str(k): v for k, v in sfx_path_map.items()}}
        self.db.add(task)

        task.output_file_ids = file_ids

    async def _execute_video_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute video composition."""
        from .video_synthesis_service import video_synthesis_service
        from .bgm_service import bgm_service
        from ..schemas.file import FileCreate

        # Find variant group for this task
        variant_group = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task.id
        ).first()

        panels = parameters.get("panels", [])
        if not panels and settings.MOCK_MODE:
            import tempfile
            from PIL import Image
            tmp_img = Path(tempfile.gettempdir()) / f"mock_panel_{uuid4()}.png"
            img = Image.new("RGB", (540, 960), color=(100, 100, 150))
            img.save(tmp_img)
            panels = [{"image_path": str(tmp_img), "duration": 3.0, "text": "Mock panel"}]
        resolution = tuple(parameters.get("resolution", [1080, 1920]))
        fps = parameters.get("fps", 24)
        generate_bgm = parameters.get("generate_bgm", True)
        bgm_mood = parameters.get("bgm_mood", "ambient")

        # Generate BGM if requested
        bgm_path = None
        if generate_bgm and panels:
            total_duration = sum(p.get("duration", 3.0) for p in panels)
            bgm_path = bgm_service.generate(
                duration=total_duration,
                mood=bgm_mood,
            )

        # Compose video
        video_path = video_synthesis_service.compose(
            panels=panels,
            bgm_path=bgm_path,
            resolution=resolution,
            fps=fps,
        )

        rel_path = str(video_path.relative_to(settings.storage_path)) if video_path.is_absolute() else str(video_path)
        file_record = file_crud.create(
            self.db,
            obj_in=FileCreate(
                project_id=task.project_id,
                task_id=task.id,
                variant_group_id=variant_group.id if variant_group else None,
                file_path=rel_path,
                file_type=FileType.VIDEO,
                generation_params={"panels": len(panels), "resolution": resolution, "fps": fps},
            ),
        )
        task.output_file_ids = [str(file_record.id)]

    def _auto_select_first_file(self, task_id: UUID):
        """Auto-select the first generated file in a task's variant group."""
        variant_groups = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task_id
        ).all()

        for vg in variant_groups:
            if vg.selected_file_id is None:
                files = self.db.query(File).filter(
                    File.variant_group_id == vg.id
                ).all()
                if files:
                    vg.selected_file_id = files[0].id
                    files[0].is_selected = True
                    files[0].selected_at = datetime.utcnow()
                    self.db.add(vg)
                    self.db.add(files[0])

        self.db.flush()
        self.db.commit()

    async def _execute_script_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute script generation using ScriptGeneratorService."""
        from .generator_services.script_generator_service import ScriptGeneratorService

        topic = parameters.get("topic")
        if not topic:
            if settings.MOCK_MODE:
                topic = "Test Topic"
            else:
                raise WorkflowError("Script generation requires 'topic' parameter")

        style = parameters.get("style", "comic")
        duration = parameters.get("duration", "1-3 minutes")
        variant_count = int(parameters.get("variant_count", 4))

        service = ScriptGeneratorService(self.db)
        success = await service.generate(
            project_id=task.project_id,
            task_id=task.id,
            topic=topic,
            style=style,
            duration=duration,
            variant_count=variant_count,
        )
        if not success:
            raise WorkflowError("Script generation failed")

        # Auto-select first generated file so next stage can proceed
        self._auto_select_first_file(task.id)

    async def _execute_storyboard_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute storyboard generation using StoryboardGeneratorService."""
        from .generator_services.storyboard_generator_service import StoryboardGeneratorService

        stages_status = self.get_project_stages(task.project_id)
        script_files = stages_status.get("script", {}).get("selected_files", [])
        if not script_files:
            raise WorkflowError(
                "Storyboard generation requires a completed script stage with a selected file"
            )

        script_file_id = UUID(script_files[0]["file_id"])
        panel_count = int(parameters.get("panel_count", 6))
        variant_count = int(parameters.get("variant_count", 4))

        service = StoryboardGeneratorService(self.db)
        success = await service.generate(
            project_id=task.project_id,
            task_id=task.id,
            script_file_id=script_file_id,
            panel_count=panel_count,
            variant_count=variant_count,
        )
        if not success:
            raise WorkflowError("Storyboard generation failed")

        self._auto_select_first_file(task.id)

    async def _execute_image_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute image generation using ImageGeneratorService."""
        from .generator_services.image_generator_service import ImageGeneratorService

        stages_status = self.get_project_stages(task.project_id)
        storyboard_files = stages_status.get("storyboard", {}).get("selected_files", [])
        if not storyboard_files:
            raise WorkflowError(
                "Image generation requires a completed storyboard stage with a selected file"
            )

        storyboard_file_id = UUID(storyboard_files[0]["file_id"])
        prompt = parameters.get("prompt", "")
        if not prompt:
            # Try to infer prompt from storyboard content
            file_record = file_crud.get(self.db, file_id=storyboard_file_id)
            if file_record:
                storyboard_path = settings.storage_path / file_record.file_path
                if storyboard_path.exists():
                    import json
                    storyboard_data = parse_storyboard(storyboard_path.read_text())
                    panels = storyboard_data.get("panels", [])
                    # Build prompt from first panel description
                    if panels:
                        first_panel = panels[0]
                        prompt = first_panel.get("scene_description", first_panel.get("description", ""))
                    if not prompt:
                        prompt = str(storyboard_path.read_text()[:500])

        if not prompt:
            if settings.MOCK_MODE:
                prompt = "A test image"
            else:
                raise WorkflowError(
                    "Image generation requires 'prompt' parameter or valid storyboard content"
                )

        negative_prompt = parameters.get("negative_prompt", "")
        variant_count = int(parameters.get("variant_count", 4))
        width = int(parameters.get("width", 512))
        height = int(parameters.get("height", 768))
        steps = int(parameters.get("steps", 20))
        cfg_scale = float(parameters.get("cfg_scale", 7.0))
        seed = int(parameters.get("seed", -1))

        service = ImageGeneratorService(self.db)
        success = await service.generate(
            project_id=task.project_id,
            task_id=task.id,
            storyboard_file_id=storyboard_file_id,
            prompt=prompt,
            negative_prompt=negative_prompt,
            variant_count=variant_count,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale,
            width=width,
            height=height,
        )
        if not success:
            raise WorkflowError("Image generation failed")

        self._auto_select_first_file(task.id)

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
            parent_task_ids=[latest_task.parent_task_id] if latest_task.parent_task_id else [],
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
