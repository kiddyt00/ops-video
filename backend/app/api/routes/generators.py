"""
Generator API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import asyncio
import logging

from ...db.session import get_db
from ...db.task_crud import task_crud
from ...db.file_crud import variant_group_crud
from ...schemas.task import TaskCreate, TaskStage
from ...schemas.generator import GenerateRequest, GenerateResponse, GeneratorInfo
from ...services.workflow_service import WorkflowError

router = APIRouter()
logger = logging.getLogger(__name__)

# Generator metadata
GENERATORS = {
    "script": GeneratorInfo(
        name="Script Generator",
        type="llm",
        description="Generate manga script from topic using LLM",
        parameters={
            "topic": {"type": "string", "required": True, "description": "Story topic"},
            "style": {"type": "string", "required": False, "default": "comic"},
            "duration": {"type": "string", "required": False, "default": "1-3 minutes"},
            "variant_count": {"type": "integer", "required": False, "default": 4},
        },
    ),
    "storyboard": GeneratorInfo(
        name="Storyboard Generator",
        type="llm",
        description="Generate storyboard from script using LLM",
        parameters={
            "script_file_id": {"type": "string", "required": True, "description": "Selected script file ID"},
            "panel_count": {"type": "integer", "required": False, "default": 6},
            "variant_count": {"type": "integer", "required": False, "default": 4},
        },
    ),
    "image": GeneratorInfo(
        name="Image Generator",
        type="wanx",
        description="Generate manga-style images using 通义万相 (DashScope Wanx)",
        parameters={
            "prompt": {"type": "string", "required": True, "description": "Image prompt"},
            "negative_prompt": {"type": "string", "required": False, "default": ""},
            "storyboard_file_id": {"type": "string", "required": True, "description": "Selected storyboard panel file ID"},
            "variant_count": {"type": "integer", "required": False, "default": 4},
            "seed": {"type": "integer", "required": False, "default": -1},
            "steps": {"type": "integer", "required": False, "default": 20},
            "cfg_scale": {"type": "number", "required": False, "default": 7.0},
            "width": {"type": "integer", "required": False, "default": 512},
            "height": {"type": "integer", "required": False, "default": 768},
        },
    ),
    "tts": GeneratorInfo(
        name="TTS Generator",
        type="tts",
        description="Generate narration audio using edge-tts",
        parameters={
            "text": {"type": "string", "required": True, "description": "Text to synthesize"},
            "voice": {"type": "string", "required": False, "default": "zh-CN-XiaoxiaoNeural"},
            "rate": {"type": "string", "required": False, "default": "+0%"},
        },
    ),
    "bgm": GeneratorInfo(
        name="BGM Generator",
        type="bgm",
        description="Generate background music",
        parameters={
            "duration": {"type": "number", "required": False, "default": 30.0},
            "bpm": {"type": "integer", "required": False, "default": 80},
            "mood": {"type": "string", "required": False, "default": "ambient"},
        },
    ),
    "video_composer": GeneratorInfo(
        name="Video Composer",
        type="video",
        description="Compose final video from images, audio, and storyboard timing",
        parameters={
            "panels": {"type": "array", "required": True, "description": "Panel data with image paths, audio, and durations"},
            "resolution": {"type": "array", "required": False, "default": [1080, 1920]},
            "fps": {"type": "integer", "required": False, "default": 24},
        },
    ),
}


@router.get("", response_model=List[GeneratorInfo])
def list_generators():
    """List available generators"""
    return list(GENERATORS.values())


@router.get("/{generator_type}", response_model=GeneratorInfo)
def get_generator(generator_type: str):
    """Get generator info by type"""
    if generator_type not in GENERATORS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generator '{generator_type}' not found",
        )
    return GENERATORS[generator_type]


@router.post("/{generator_type}/generate", response_model=GenerateResponse)
async def generate(
    generator_type: str,
    request: GenerateRequest,
    db: Session = Depends(get_db),
):
    """Execute generation — creates task and runs the corresponding service."""
    if generator_type not in GENERATORS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generator '{generator_type}' not found",
        )

    # Map generator type to task stage
    stage_map = {
        "script": TaskStage.SCRIPT,
        "storyboard": TaskStage.STORYBOARD,
        "image": TaskStage.IMAGE,
        "tts": TaskStage.AUDIO,
        "bgm": TaskStage.AUDIO,
        "video_composer": TaskStage.VIDEO,
    }

    stage = stage_map.get(generator_type)
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid generator type: {generator_type}",
        )

    # Create task
    task = task_crud.create(
        db,
        obj_in=TaskCreate(
            project_id=UUID(request.project_id),
            stage=stage,
            generator_type=generator_type,
            parameters=request.parameters,
        ),
    )

    # Execute generation based on type
    result = await _dispatch_generation(db, generator_type, task, request.parameters)

    return GenerateResponse(
        task_id=str(task.id),
        variant_group_id=result.get("variant_group_id", ""),
        status="completed" if result.get("success") else "failed",
        message=f"Generation {'completed' if result.get('success') else 'failed'} for {generator_type}",
    )


async def _dispatch_generation(
    db: Session,
    generator_type: str,
    task,
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """Dispatch to the appropriate generator service and return result."""
    try:
        if generator_type == "script":
            return await _generate_script(db, task, parameters)
        elif generator_type == "storyboard":
            return await _generate_storyboard(db, task, parameters)
        elif generator_type == "image":
            return await _generate_image(db, task, parameters)
        elif generator_type == "tts":
            return await _generate_tts(db, task, parameters)
        elif generator_type == "bgm":
            return _generate_bgm(db, task, parameters)
        elif generator_type == "video_composer":
            return _generate_video(db, task, parameters)
        return {"success": False, "error": "Unknown generator type"}
    except WorkflowError as e:
        logger.error("dispatch_generation WorkflowError: generator_type=%s, %s", generator_type, str(e), exc_info=True)
        return {"success": False, "error": str(e)}
    except (ValueError, TypeError) as e:
        logger.error("dispatch_generation invalid input: generator_type=%s, %s", generator_type, str(e), exc_info=True)
        return {"success": False, "error": f"Invalid parameters: {e}"}
    except Exception as e:
        logger.error("dispatch_generation unexpected error: generator_type=%s, %s", generator_type, str(e), exc_info=True)
        return {"success": False, "error": f"Internal error: {e}"}


async def _generate_script(db, task, params):
    from ...services.generator_services.script_generator_service import ScriptGeneratorService
    service = ScriptGeneratorService(db)
    success = await service.generate(
        project_id=task.project_id,
        task_id=task.id,
        topic=params.get("topic", ""),
        style=params.get("style", "comic"),
        duration=params.get("duration", "1-3 minutes"),
        variant_count=int(params.get("variant_count", 4)),
    )
    return {"success": success}


async def _generate_storyboard(db, task, params):
    from ...services.generator_services.storyboard_generator_service import StoryboardGeneratorService
    from ...providers.llm_provider import llm_provider
    script_file_id = params.get("script_file_id")
    if not script_file_id:
        return {"success": False, "error": "script_file_id required"}
    service = StoryboardGeneratorService(db)
    success = await service.generate(
        project_id=task.project_id,
        task_id=task.id,
        script_file_id=UUID(script_file_id),
        panel_count=int(params.get("panel_count", 6)),
        variant_count=int(params.get("variant_count", 4)),
    )
    return {"success": success}


async def _generate_image(db, task, params):
    from ...services.generator_services.image_generator_service import ImageGeneratorService
    storyboard_file_id = params.get("storyboard_file_id")
    prompt = params.get("prompt", "")
    if not storyboard_file_id or not prompt:
        return {"success": False, "error": "storyboard_file_id and prompt required"}
    service = ImageGeneratorService(db)
    success = await service.generate(
        project_id=task.project_id,
        task_id=task.id,
        storyboard_file_id=UUID(storyboard_file_id),
        prompt=prompt,
        negative_prompt=params.get("negative_prompt", ""),
        variant_count=int(params.get("variant_count", 4)),
        seed=int(params.get("seed", -1)),
        steps=int(params.get("steps", 20)),
        cfg_scale=float(params.get("cfg_scale", 7.0)),
        width=int(params.get("width", 512)),
        height=int(params.get("height", 768)),
    )
    return {"success": success}


async def _generate_tts(db, task, params):
    from ...services.tts_service import tts_service
    from ...schemas.file import FileCreate
    from ...models.file import FileType
    from ...config import settings
    from ...db.file_crud import file_crud

    text = params.get("text", "")
    if not text:
        return {"success": False, "error": "text required"}

    voice = params.get("voice", "zh-CN-XiaoxiaoNeural")
    audio_path = await tts_service.synthesize(text, voice=voice)
    rel_path = str(audio_path.relative_to(settings.storage_path)) if audio_path.is_absolute() else str(audio_path)
    file_record = file_crud.create(
        db,
        obj_in=FileCreate(
            project_id=task.project_id,
            task_id=task.id,
            file_path=rel_path,
            file_type=FileType.AUDIO,
            generation_params={"type": "tts", "voice": voice},
        ),
    )
    task.output_file_ids = [str(file_record.id)]
    db.add(task)
    db.commit()
    return {"success": True}


def _generate_bgm(db, task, params):
    from ...services.bgm_service import bgm_service
    from ...schemas.file import FileCreate
    from ...models.file import FileType
    from ...config import settings, STORAGE_DIRS
    from ...db.file_crud import file_crud

    duration = float(params.get("duration", 30.0))
    mood = params.get("mood", "ambient")
    bpm = int(params.get("bpm", 80))
    audio_path = bgm_service.generate(duration=duration, mood=mood, bpm=bpm)
    rel_path = str(audio_path.relative_to(settings.storage_path)) if audio_path.is_absolute() else str(audio_path)
    file_record = file_crud.create(
        db,
        obj_in=FileCreate(
            project_id=task.project_id,
            task_id=task.id,
            file_path=rel_path,
            file_type=FileType.AUDIO,
            generation_params={"type": "bgm", "mood": mood, "duration": duration, "bpm": bpm},
        ),
    )
    task.output_file_ids = [str(file_record.id)]
    db.add(task)
    db.commit()
    return {"success": True}


def _generate_video(db, task, params):
    from ...services.video_synthesis_service import video_synthesis_service
    from ...schemas.file import FileCreate
    from ...models.file import FileType
    from ...config import settings, STORAGE_DIRS
    from ...db.file_crud import file_crud

    panels = params.get("panels", [])
    if not panels:
        return {"success": False, "error": "panels required"}

    resolution = tuple(params.get("resolution", [1080, 1920]))
    fps = int(params.get("fps", 24))

    video_path = video_synthesis_service.compose(
        panels=panels,
        resolution=resolution,
        fps=fps,
    )
    rel_path = str(video_path.relative_to(settings.storage_path)) if video_path.is_absolute() else str(video_path)
    file_record = file_crud.create(
        db,
        obj_in=FileCreate(
            project_id=task.project_id,
            task_id=task.id,
            file_path=rel_path,
            file_type=FileType.VIDEO,
            generation_params={"panels": len(panels), "resolution": resolution, "fps": fps},
        ),
    )
    task.output_file_ids = [str(file_record.id)]
    db.add(task)
    db.commit()
    return {"success": True}
