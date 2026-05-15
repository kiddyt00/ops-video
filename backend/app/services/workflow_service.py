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

from ..core.logging_config import get_logger

logger = get_logger(__name__)

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

    Stage order: inspiration -> story -> chapter_outline -> script -> storyboard -> image -> audio -> video
    """

    STAGE_ORDER: List[TaskStage] = [
        TaskStage.INSPIRATION,
        TaskStage.STORY,
        TaskStage.CHAPTER_OUTLINE,
        TaskStage.CHAPTER_BODY,
        TaskStage.SCRIPT,
        TaskStage.STORYBOARD,
        TaskStage.IMAGE,
        TaskStage.AUDIO,
        TaskStage.VIDEO,
    ]

    STAGE_GENERATOR_MAP: Dict[TaskStage, str] = {
        TaskStage.INSPIRATION: "inspiration",
        TaskStage.STORY: "story",
        TaskStage.CHAPTER_OUTLINE: "chapter_outline",
        TaskStage.CHAPTER_BODY: "chapter_body",
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
        if target_stage == TaskStage.INSPIRATION:
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
        execute: bool = True,
        chapter_id: Optional[UUID] = None,
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
                    target_stage = TaskStage.INSPIRATION
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
            chapter_id=chapter_id,
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
            max_retries = 2
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    if target_stage in [TaskStage.AUDIO, TaskStage.VIDEO]:
                        await self._execute_generation(target_stage, task, parameters)
                    elif target_stage == TaskStage.INSPIRATION:
                        await self._execute_inspiration_generation(task, parameters)
                    elif target_stage == TaskStage.STORY:
                        await self._execute_story_generation(task, parameters)
                    elif target_stage == TaskStage.CHAPTER_OUTLINE:
                        await self._execute_chapter_outline_generation(task, parameters)
                    elif target_stage == TaskStage.CHAPTER_BODY:
                        await self._execute_chapter_body_generation(task, parameters)
                    elif target_stage == TaskStage.SCRIPT:
                        await self._execute_script_generation(task, parameters)
                    elif target_stage == TaskStage.STORYBOARD:
                        await self._execute_storyboard_generation(task, parameters)
                    elif target_stage == TaskStage.IMAGE:
                        await self._execute_image_generation(task, parameters)

                    # Mark task as completed after successful generation
                    task_crud.update_status(
                        self.db,
                        task_id=task.id,
                        obj_in=TaskStatusUpdate(status=TaskStatus.COMPLETED),
                    )
                    self.db.commit()

                    # Upload artifacts to OSS (non-blocking)
                    await self._upload_artifacts_to_oss(task, target_stage)

                    break  # success — exit retry loop
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(
                            "Stage %s failed (attempt %d/%d), retrying in 2s: %s",
                            target_stage.value, attempt + 1, max_retries + 1, str(e)[:200]
                        )
                        import asyncio
                        await asyncio.sleep(2)
                    else:
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
            image_files = [f for f in file_crud.get_all(self.db, project_id=project_id) if f.file_type.value == 'image']
            storyboard_files = stages_status.get("storyboard", {}).get("selected_files", [])
            audio_files = [f for f in file_crud.get_all(self.db, project_id=project_id) if f.file_type.value == 'audio']

            panels = []

            # Get image paths (all images, not just selected)
            image_paths = [str(settings.storage_path / f.file_path) for f in image_files]

            # Get audio paths (TTS first, fallback to all audio)
            tts_only = [f for f in audio_files if f.generation_params and
                        isinstance(f.generation_params, dict) and
                        f.generation_params.get('type') == 'tts']
            tts_paths = [str(settings.storage_path / f.file_path) for f in (tts_only or audio_files)]

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
            num_panels = max(len(image_paths), len(storyboard_data.get("panels", []))) if storyboard_data else len(image_paths)

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
                try:
                    rel_path = str(tts_path.relative_to(settings.storage_path)) if tts_path.is_absolute() else str(tts_path)
                except ValueError:
                    rel_path = tts_path.name
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
                try:
                    rel_path = str(bgm_path.relative_to(settings.storage_path)) if bgm_path.is_absolute() else str(bgm_path)
                except ValueError:
                    rel_path = bgm_path.name
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
            try:
                rel_path = str(sfx_path.relative_to(settings.storage_path)) if sfx_path.is_absolute() else str(sfx_path)
            except ValueError:
                rel_path = sfx_path.name

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
        from .i2v_composer import i2v_composer
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
        video_path = await i2v_composer.compose(
            storyboard_panels=storyboard.get("panels", []) if (storyboard := parameters.get("storyboard_data", {})) else None,
            panels=panels,
            bgm_path=bgm_path,
            resolution=resolution,
            fps=fps,
        )

        try:
            rel_path = str(video_path.relative_to(settings.storage_path)) if video_path.is_absolute() else str(video_path)
        except ValueError:
            rel_path = video_path.name
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

    async def _execute_inspiration_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute inspiration capture using StoryGeneratorService."""
        from .generator_services.story_generator_service import StoryGeneratorService
        from ..schemas.file import FileCreate

        inspiration = parameters.get("inspiration")
        if not inspiration:
            if settings.MOCK_MODE:
                inspiration = "A lone wanderer discovers an ancient library beneath a ruined city."
            else:
                raise WorkflowError("Inspiration stage requires 'inspiration' parameter")

        # MOCK_MODE fast path — skip LLM call
        if settings.MOCK_MODE:
            from .generator_services.mock_helpers import mock_story_data
            story_data = mock_story_data(inspiration=inspiration)
        else:
            service = StoryGeneratorService(db=self.db)
            story_data = await service.generate_story(
                inspiration=inspiration,
                project_id=str(task.project_id),
                genre=parameters.get("genre", ""),
                tone=parameters.get("tone", ""),
                target_length=parameters.get("target_length", ""),
                golden_finger=parameters.get("golden_finger", ""),
                protagonist=parameters.get("protagonist", ""),
                relationship=parameters.get("relationship", ""),
                worldbuilding_hints=parameters.get("worldbuilding_hints", ""),
                extra_context=parameters.get("extra_context", ""),
            )

        # Create file record for the inspiration output
        variant_group = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task.id
        ).first()

        # The service already saves to disk; create DB record
        output_path = Path(settings.storage_path) / f"story_{task.project_id}.json"
        if output_path.exists():
            rel_path = str(output_path.relative_to(settings.storage_path))
        else:
            # Fallback: write it ourselves
            import json
            output_dir = settings.storage_path / "scripts"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"inspiration_{task.id}.json"
            output_path.write_text(json.dumps(story_data, indent=2, ensure_ascii=False), encoding="utf-8")
            rel_path = str(output_path.relative_to(settings.storage_path))

        file_record = file_crud.create(
            self.db,
            obj_in=FileCreate(
                project_id=task.project_id,
                task_id=task.id,
                variant_group_id=variant_group.id if variant_group else None,
                file_path=rel_path,
                file_type=FileType.TEXT,
                generation_params={"type": "inspiration", "inspiration": inspiration},
            ),
        )
        task.output_file_ids = [str(file_record.id)]

        # Auto-select the generated file in variant_group
        if variant_group:
            variant_group.selected_file_id = file_record.id
            self.db.add(variant_group)
            self.db.flush()

        # ── Create or update the Story DB record ────────────────────────
        from ..db.story_crud import story_crud
        from ..schemas.story import StoryCreate as StoryCreateSchema, StoryUpdate as StoryUpdateSchema
        from ..models.story import StoryStatus

        existing = story_crud.get_by_project(self.db, task.project_id)
        story_obj = StoryCreateSchema(
            inspiration=inspiration,
            logline=story_data.get("logline"),
            synopsis=story_data.get("synopsis"),
            worldbuilding=story_data.get("worldbuilding"),
            characters=story_data.get("characters"),
            themes=story_data.get("themes"),
            plot_points=story_data.get("plot_points"),
            status=StoryStatus.draft,
        )
        if existing:
            story_crud.update(self.db, existing.id, StoryUpdateSchema(**story_obj.model_dump(exclude_unset=True)))
        else:
            story_crud.create(self.db, task.project_id, story_obj)
        self.db.commit()
        # ────────────────────────────────────────────────────────────────

    async def _execute_story_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute story expansion using StoryGeneratorService."""
        from .generator_services.story_generator_service import StoryGeneratorService
        from ..schemas.file import FileCreate

        stages_status = self.get_project_stages(task.project_id)
        inspiration_files = stages_status.get("inspiration", {}).get("selected_files", [])
        if not inspiration_files:
            raise WorkflowError(
                "Story generation requires a completed inspiration stage with a selected file"
            )

        # Load inspiration data
        inspiration_file_id = UUID(inspiration_files[0]["file_id"])
        file_record = file_crud.get(self.db, file_id=inspiration_file_id)
        if not file_record:
            raise WorkflowError("Inspiration file not found")

        inspiration_path = settings.storage_path / file_record.file_path
        if not inspiration_path.exists():
            raise WorkflowError(f"Inspiration file not found on disk: {inspiration_path}")

        import json
        inspiration_data = json.loads(inspiration_path.read_text(encoding="utf-8"))
        inspiration_text = inspiration_data.get("inspiration", "")
        if not inspiration_text:
            # Try to get from parameters
            inspiration_text = parameters.get("inspiration", "")

        genre = parameters.get("genre", inspiration_data.get("genre", ""))
        tone = parameters.get("tone", inspiration_data.get("tone", ""))
        target_length = parameters.get("target_length", "")
        golden_finger = parameters.get("golden_finger", "")
        protagonist = parameters.get("protagonist", "")
        relationship = parameters.get("relationship", "")
        worldbuilding_hints = parameters.get("worldbuilding_hints", "")

        # MOCK_MODE fast path
        if settings.MOCK_MODE:
            from .generator_services.mock_helpers import mock_story_data
            story_data = mock_story_data(inspiration=inspiration_text)
        else:
            service = StoryGeneratorService(db=self.db)
            story_data = await service.generate_story(
                inspiration=inspiration_text,
                project_id=str(task.project_id),
                genre=genre,
                tone=tone,
                target_length=target_length,
                golden_finger=golden_finger,
                protagonist=protagonist,
                relationship=relationship,
                worldbuilding_hints=worldbuilding_hints,
            )

        variant_group = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task.id
        ).first()

        output_dir = settings.storage_path / "scripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"story_{task.id}.json"
        output_path.write_text(json.dumps(story_data, indent=2, ensure_ascii=False), encoding="utf-8")
        rel_path = str(output_path.relative_to(settings.storage_path))

        file_record = file_crud.create(
            self.db,
            obj_in=FileCreate(
                project_id=task.project_id,
                task_id=task.id,
                variant_group_id=variant_group.id if variant_group else None,
                file_path=rel_path,
                file_type=FileType.TEXT,
                generation_params={"type": "story"},
            ),
        )
        task.output_file_ids = [str(file_record.id)]

        self._auto_select_first_file(task.id)

        # ── Update Story DB record ──────────────────────────────────────
        from ..db.story_crud import story_crud
        from ..schemas.story import StoryCreate as StoryCreateSchema, StoryUpdate as StoryUpdateSchema

        existing = story_crud.get_by_project(self.db, task.project_id)
        story_obj = StoryCreateSchema(
            inspiration=inspiration_text,
            logline=story_data.get("logline"),
            synopsis=story_data.get("synopsis"),
            worldbuilding=story_data.get("worldbuilding"),
            characters=story_data.get("characters"),
            themes=story_data.get("themes"),
            plot_points=story_data.get("plot_points"),
            style_tags=story_data.get("style_tags"),
            title_suggestions=story_data.get("title_suggestions"),
            target_audience=story_data.get("target_audience"),
            word_count_estimate=story_data.get("word_count_estimate"),
            golden_finger_detail=story_data.get("golden_finger_detail"),
            power_system=story_data.get("power_system"),
            world_map_hints=story_data.get("world_map_hints"),
            prologue_preview=story_data.get("prologue_preview"),
        )
        if existing:
            story_crud.update(self.db, existing.id, StoryUpdateSchema(**story_obj.model_dump(exclude_unset=True)))
        else:
            story_crud.create(self.db, task.project_id, story_obj)
        self.db.commit()

        # ── Auto-create CharacterCards from story characters ──────────
        try:
            from ..db.character_card_crud import character_card_crud
            from ..schemas.character_card import CharacterCardCreate

            _IMPORTANT_ROLES = {"主角", "反派", "导师", "伙伴", "朋友", "恋人"}
            _MAX_SUPPORTING = 10
            characters = story_data.get("characters", [])
            if characters:
                existing_cards = character_card_crud.get_by_project(self.db, task.project_id)
                existing_names = {c.name for c in existing_cards}
                supporting_count = 0
                created_count = 0

                for char in characters:
                    name = char.get("name", "").strip()
                    role = char.get("role", "").strip()
                    if not name:
                        continue
                    is_important = any(r in role for r in _IMPORTANT_ROLES)
                    is_supporting = "配角" in role
                    if not is_important and not is_supporting:
                        continue
                    if is_supporting and not is_important:
                        supporting_count += 1
                        if supporting_count > _MAX_SUPPORTING:
                            continue
                    if name in existing_names:
                        continue
                    character_card_crud.create(
                        self.db, project_id=task.project_id,
                        obj_in=CharacterCardCreate(
                            name=name,
                            description=char.get("description", ""),
                            traits={"role": role, "arc": char.get("arc", "")} if char.get("arc") else {"role": role},
                        ),
                    )
                    existing_names.add(name)
                    created_count += 1

                if created_count > 0:
                    logger.info("Auto-created %d CharacterCards from story | project=%s", created_count, task.project_id)
        except Exception as e:
            logger.warning("Auto-create CharacterCards failed (non-blocking): %s", e)
        # ────────────────────────────────────────────────────────────────

    async def _execute_chapter_outline_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute chapter outline generation using StoryGeneratorService."""
        from .generator_services.story_generator_service import StoryGeneratorService
        from ..schemas.file import FileCreate

        stages_status = self.get_project_stages(task.project_id)
        story_files = stages_status.get("story", {}).get("selected_files", [])
        if not story_files:
            raise WorkflowError(
                "Chapter outline generation requires a completed story stage with a selected file"
            )

        # Load story data
        story_file_id = UUID(story_files[0]["file_id"])
        file_record = file_crud.get(self.db, file_id=story_file_id)
        if not file_record:
            raise WorkflowError("Story file not found")

        story_path = settings.storage_path / file_record.file_path
        if not story_path.exists():
            raise WorkflowError(f"Story file not found on disk: {story_path}")

        import json
        story_data = json.loads(story_path.read_text(encoding="utf-8"))

        chapter_count = parameters.get("chapter_count", None)
        if chapter_count is not None:
            chapter_count = int(chapter_count)

        # MOCK_MODE fast path
        if settings.MOCK_MODE:
            from .generator_services.mock_helpers import mock_chapter_outline_data
            outline_data = mock_chapter_outline_data(story_data, chapter_count or 6)
        else:
            from ..db.relation_crud import relation_crud
            service = StoryGeneratorService(db=self.db)
            service.project_id = task.project_id
            outline_data = await service.generate_chapter_outline(
                project_id=task.project_id,
                story_data=story_data,
                chapter_count=chapter_count,
            )

        variant_group = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task.id
        ).first()

        output_dir = settings.storage_path / "scripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"chapter_outline_{task.id}.json"
        output_path.write_text(json.dumps(outline_data, indent=2, ensure_ascii=False), encoding="utf-8")
        rel_path = str(output_path.relative_to(settings.storage_path))

        file_record = file_crud.create(
            self.db,
            obj_in=FileCreate(
                project_id=task.project_id,
                task_id=task.id,
                variant_group_id=variant_group.id if variant_group else None,
                file_path=rel_path,
                file_type=FileType.TEXT,
                generation_params={"type": "chapter_outline"},
            ),
        )
        task.output_file_ids = [str(file_record.id)]

        self._auto_select_first_file(task.id)

        # ── Update Story with chapter outline ──────────────────────────
        from ..db.story_crud import story_crud
        from ..schemas.story import StoryUpdate as StoryUpdateSchema

        existing = story_crud.get_by_project(self.db, task.project_id)
        if existing:
            story_crud.update(self.db, existing.id, StoryUpdateSchema(
                chapter_outline=outline_data.get("chapters", []),
            ))
            self.db.commit()

        # ── Sync Chapter model records from outline ────────────────────
        try:
            from ..db.chapter_crud import chapter_crud
            chapters = outline_data.get("chapters", [])
            if chapters:
                created = chapter_crud.batch_create_from_outline(
                    self.db,
                    project_id=task.project_id,
                    outline_items=chapters,
                )
                logger.info(
                    "Synced %d chapters from outline | project=%s",
                    len(created), task.project_id,
                )
        except Exception as e:
            logger.warning("Chapter model sync failed (non-blocking): %s", e)
        # ────────────────────────────────────────────────────────────────

    async def _execute_chapter_body_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute chapter body generation — expand outlines into full narrative prose."""
        from .generator_services.story_generator_service import StoryGeneratorService
        from ..schemas.file import FileCreate
        from ..db.chapter_crud import chapter_crud as _chapter_crud

        stages_status = self.get_project_stages(task.project_id)
        outline_files = stages_status.get("chapter_outline", {}).get("selected_files", [])
        if not outline_files:
            raise WorkflowError(
                "Chapter body generation requires a completed chapter_outline stage with a selected file"
            )

        # Load chapter outline data
        outline_file_id = UUID(outline_files[0]["file_id"])
        file_record = file_crud.get(self.db, file_id=outline_file_id)
        if not file_record:
            raise WorkflowError("Chapter outline file not found")

        outline_path = settings.storage_path / file_record.file_path
        if not outline_path.exists():
            raise WorkflowError(f"Chapter outline file not found on disk: {outline_path}")

        import json
        outline_data = json.loads(outline_path.read_text(encoding="utf-8"))
        chapters = outline_data.get("chapters", [])

        # Support single-chapter generation via chapter_number parameter
        target_chapter = parameters.get("chapter_number")
        if target_chapter is not None:
            target_chapter = int(target_chapter)
            chapters = [c for c in chapters if c.get("chapter_number") == target_chapter]
            if not chapters:
                raise WorkflowError(f"Chapter {target_chapter} not found in outline")

        # Load story data for full context
        from ..db.story_crud import story_crud as _story_crud
        story = _story_crud.get_by_project(self.db, task.project_id)
        story_data = {}
        if story:
            story_data = {
                "synopsis": story.synopsis,
                "worldbuilding": story.worldbuilding,
                "characters": story.characters,
                "themes": story.themes,
                "plot_points": story.plot_points,
                "style_tags": story.style_tags,
            }

        # Pre-load existing chapter bodies for continuity
        previous_bodies: list = []
        try:
            existing_chapters = _chapter_crud.get_by_project(self.db, task.project_id)
            for c in sorted(existing_chapters, key=lambda x: x.chapter_number):
                if c.body_text:
                    previous_bodies.append(c.body_text)
        except Exception:
            pass

        # Generate body text for each chapter
        body_results = []
        service = StoryGeneratorService(db=self.db)

        for ch in chapters:
            ch_num = ch.get("chapter_number", len(body_results) + 1)
            ch_title = ch.get("title", "")
            ch_summary = ch.get("summary", "")

            if settings.MOCK_MODE:
                from .generator_services.mock_helpers import mock_chapter_body_data
                body = mock_chapter_body_data(ch_num, ch_title, ch_summary)
            else:
                body = await service.generate_chapter_body(
                    project_id=task.project_id,
                    chapter_number=ch_num,
                    title=ch_title,
                    summary=ch_summary,
                    story_data=story_data,
                    previous_bodies=previous_bodies[-3:] if previous_bodies else [],
                )

            body_text = body.get("body_text", "")
            body_results.append({
                "chapter_number": ch_num,
                "title": ch_title,
                "body_text": body_text,
                "word_count": body.get("word_count", len(body_text)),
            })
            previous_bodies.append(body_text)

            # Persist body_text on Chapter model
            try:
                chapters_in_db = _chapter_crud.get_by_project(self.db, task.project_id)
                db_chapter = next((c for c in chapters_in_db if c.chapter_number == ch_num), None)
                if db_chapter:
                    _chapter_crud.update_body_text(self.db, db_chapter.id, body_text)
            except Exception as e:
                logger.warning("Failed to persist body_text for chapter %d: %s", ch_num, e)

        # Save combined result as JSON file
        variant_group = self.db.query(VariantGroup).filter(
            VariantGroup.task_id == task.id
        ).first()

        output_dir = settings.storage_path / "scripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"chapter_body_{task.id}.json"
        output_path.write_text(
            json.dumps({"chapters": body_results}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        rel_path = str(output_path.relative_to(settings.storage_path))

        file_record = file_crud.create(
            self.db,
            obj_in=FileCreate(
                project_id=task.project_id,
                task_id=task.id,
                variant_group_id=variant_group.id if variant_group else None,
                file_path=rel_path,
                file_type=FileType.TEXT,
                generation_params={"type": "chapter_body"},
            ),
        )
        task.output_file_ids = [str(file_record.id)]
        self._auto_select_first_file(task.id)

    async def _execute_script_generation(
        self,
        task: Task,
        parameters: Dict[str, Any],
    ):
        """Execute script generation using ScriptGeneratorService."""
        from .generator_services.script_generator_service import ScriptGeneratorService

        topic = parameters.get("topic")
        if not topic:
            # Auto-derive from Story DB
            from ..db.story_crud import story_crud as _story_crud
            story = _story_crud.get_by_project(self.db, task.project_id)
            if story:
                topic = story.logline or story.inspiration or None
        if not topic:
            if settings.MOCK_MODE:
                topic = "Test Topic"
            else:
                raise WorkflowError("Script generation requires 'topic' parameter")

        style = parameters.get("style", "comic")
        duration = parameters.get("duration", "1-3 minutes")
        variant_count = int(parameters.get("variant_count", 4))

        # Build full context from story + characters + continuity
        from ..services.knowledge_service import build_continuity_context
        from ..services.prompt_service import get_rendered_prompt
        from ..db.story_crud import story_crud as _story_crud
        from ..services.character_context import CharacterContextBuilder

        continuity_context = build_continuity_context(self.db, str(task.project_id))
        story = _story_crud.get_by_project(self.db, task.project_id)

        # Try using prompt template for richer generation
        try:
            ctx_builder = CharacterContextBuilder(self.db)
            char_ctx = ctx_builder.get_character_context_for_project(task.project_id)
            char_summary = char_ctx.get("context_template", "") if char_ctx else ""

            worldbuilding_str = json.dumps(story.worldbuilding, ensure_ascii=False) if story and story.worldbuilding else ""
            style_tags_str = ", ".join(story.style_tags) if story and story.style_tags else style
            synopsis_str = story.synopsis if story else ""

            # ── Inject chapter body_text as primary narrative input ──────
            chapter_body_context = ""
            if task.chapter_id:
                from ..models.chapter import Chapter as ChapterModel
                ch = self.db.query(ChapterModel).filter(ChapterModel.id == task.chapter_id).first()
                if ch and ch.body_text:
                    chapter_body_context = (
                        f"=== 本章正文（请基于此生成剧本）===\n{ch.body_text[:6000]}\n\n"
                    )
                    logger.info(
                        "Script gen using chapter body_text | ch=%d | len=%d",
                        ch.chapter_number, len(ch.body_text),
                    )
                elif ch:
                    logger.info(
                        "Script gen: chapter %d has no body_text, falling back to synopsis",
                        ch.chapter_number,
                    )
            # ──────────────────────────────────────────────────────────────

            rendered = get_rendered_prompt(self.db, "script-generation", {
                "topic": topic,
                "synopsis": synopsis_str,
                "worldbuilding": worldbuilding_str,
                "style_tags": style_tags_str,
                "characters_context": char_summary,
                "additional_context": chapter_body_context + continuity_context,
            })
            additional_context = rendered
        except Exception:
            additional_context = chapter_body_context + continuity_context

        service = ScriptGeneratorService(self.db)
        success = await service.generate(
            project_id=task.project_id,
            task_id=task.id,
            topic=topic,
            style=style,
            duration=duration,
            additional_context=additional_context,
            variant_count=variant_count,
        )
        if not success:
            raise WorkflowError("Script generation failed")

        # Extract character states from generated script (non-blocking)
        try:
            from ..services.memory_extractor import extract_from_script
            from ..models.chapter import Chapter
            chapter_number = 1
            if task.chapter_id:
                ch = self.db.query(Chapter).filter(Chapter.id == task.chapter_id).first()
                if ch:
                    chapter_number = ch.chapter_number
            stage_status = self.get_project_stages(task.project_id)
            script_files = stage_status.get("script", {}).get("selected_files", [])
            if script_files:
                import json
                script_fid = UUID(script_files[0]["file_id"])
                script_rec = file_crud.get(self.db, file_id=script_fid)
                if script_rec:
                    sp = settings.storage_path / script_rec.file_path
                    if sp.exists():
                        script_text = sp.read_text(encoding="utf-8")
                        await extract_from_script(
                            project_id=str(task.project_id),
                            content=script_text[:6000],
                            chapter_number=chapter_number,
                        )
                        logger.info("Memory extraction completed for project=%s chapter=%d", task.project_id, chapter_number)
        except Exception as e:
            logger.warning("Memory extraction failed (non-blocking): %s", e)

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

        # Build character + story context for storyboard generation
        from ..services.prompt_service import get_rendered_prompt
        from ..db.story_crud import story_crud as _story_crud
        from ..services.character_context import CharacterContextBuilder
        from ..services.knowledge_service import build_continuity_context

        continuity_context = build_continuity_context(self.db, str(task.project_id))
        story = _story_crud.get_by_project(self.db, task.project_id)

        # Load script text
        script_rec = file_crud.get(self.db, file_id=script_file_id)
        script_text = ""
        if script_rec:
            sp = settings.storage_path / script_rec.file_path
            if sp.exists():
                script_text = sp.read_text(encoding="utf-8")

        # Try using prompt template
        try:
            ctx_builder = CharacterContextBuilder(self.db)
            char_ctx = ctx_builder.get_character_context_for_project(task.project_id)
            char_summary = char_ctx.get("context_template", "") if char_ctx else ""

            worldbuilding_str = json.dumps(story.worldbuilding, ensure_ascii=False) if story and story.worldbuilding else ""
            style_tags_str = ", ".join(story.style_tags) if story and story.style_tags else ""
            synopsis_str = story.synopsis if story else ""

            rendered = get_rendered_prompt(self.db, "storyboard-generation", {
                "script": script_text,
                "synopsis": synopsis_str,
                "worldbuilding": worldbuilding_str,
                "style_tags": style_tags_str,
                "characters_context": char_summary,
                "panel_count": str(panel_count),
            })
        except Exception:
            rendered = None

        service = StoryboardGeneratorService(self.db)
        success = await service.generate(
            project_id=task.project_id,
            task_id=task.id,
            script_file_id=script_file_id,
            panel_count=panel_count,
            variant_count=variant_count,
            additional_context=rendered,
        )
        if not success:
            raise WorkflowError("Storyboard generation failed")

        # Extract character states from storyboard (non-blocking)
        try:
            from ..services.memory_extractor import extract_from_script
            from ..models.chapter import Chapter
            chapter_number = 1
            if task.chapter_id:
                ch = self.db.query(Chapter).filter(Chapter.id == task.chapter_id).first()
                if ch:
                    chapter_number = ch.chapter_number
            stage_status = self.get_project_stages(task.project_id)
            sb_files = stage_status.get("storyboard", {}).get("selected_files", [])
            if sb_files:
                sb_fid = UUID(sb_files[0]["file_id"])
                sb_rec = file_crud.get(self.db, file_id=sb_fid)
                if sb_rec:
                    sp = settings.storage_path / sb_rec.file_path
                    if sp.exists():
                        sb_text = sp.read_text(encoding="utf-8")
                        await extract_from_script(
                            project_id=str(task.project_id),
                            content=sb_text[:6000],
                            chapter_number=chapter_number,
                        )
                        logger.info("Storyboard memory extraction completed for project=%s chapter=%d", task.project_id, chapter_number)
        except Exception as e:
            logger.warning("Storyboard memory extraction failed (non-blocking): %s", e)

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
        storyboard_file_record = file_crud.get(self.db, file_id=storyboard_file_id)
        storyboard_rel_path = storyboard_file_record.file_path if storyboard_file_record else None

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

        # Enrich prompt with character context from active CharacterCards
        if storyboard_rel_path:
            from .character_context import CharacterContextBuilder
            ctx = CharacterContextBuilder(self.db)
            enriched = ctx.enrich_storyboard_prompt(
                prompt=prompt,
                storyboard_file_path=storyboard_rel_path,
                project_id=task.project_id,
            )
            if enriched != prompt:
                logger.info("Prompt enriched with character context (original %d chars -> %d chars)", len(prompt), len(enriched))
                prompt = enriched

        service = ImageGeneratorService(self.db, project_id=task.project_id)
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
                    "oss_url": f.oss_url,
                    "generation_params": f.generation_params,
                    "extra_info": f.extra_info,
                    "is_selected": f.is_selected,
                    "created_at": f.created_at.isoformat(),
                }
                for f in files
            ],
        }

    async def _upload_artifacts_to_oss(
        self,
        task: "Task",
        target_stage: "TaskStage",
    ) -> None:
        """Upload all file artifacts for a completed task to OSS (non-blocking)."""
        try:
            from ..services.artifact_uploader import upload_artifacts_batch
            from ..models.file import File

            file_records = self.db.query(File).filter(
                File.task_id == task.id
            ).all()

            if not file_records:
                return

            file_paths = [f.file_path for f in file_records if not f.oss_url]
            file_ids = [f.id for f in file_records if not f.oss_url]

            if not file_paths:
                return

            await upload_artifacts_batch(
                project_id=task.project_id,
                task_id=task.id,
                stage=target_stage.value,
                file_paths=file_paths,
                file_ids=file_ids,
            )
        except Exception as e:
            logger.warning("OSS artifact upload failed (non-blocking): %s", e)


workflow_service = WorkflowService
