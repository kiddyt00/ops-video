"""
Generator API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import asyncio

from ...db.session import get_db
from ...db.task_crud import task_crud
from ...db.file_crud import variant_group_crud
from ...schemas.task import TaskCreate, TaskStage
from ...schemas.generator import GenerateRequest, GenerateResponse, GeneratorInfo

router = APIRouter()

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
        type="comfyui",
        description="Generate manga-style images using ComfyUI",
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
    """Execute generation"""
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

    # Create variant group
    variant_group = variant_group_crud.create(
        db,
        obj_in={
            "project_id": UUID(request.project_id),
            "task_id": task.id,
            "stage": generator_type,
            "parameters": request.parameters,
        },
    )

    # Start generation in background
    # The actual generation will be implemented with a task queue
    # For now, we'll return the task ID and variant group ID

    return GenerateResponse(
        task_id=str(task.id),
        variant_group_id=str(variant_group.id),
        status="pending",
        message=f"Generation started for {generator_type}",
    )
