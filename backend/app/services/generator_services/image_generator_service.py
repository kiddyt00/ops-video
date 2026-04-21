"""
Image Generator Service
"""
from uuid import UUID
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from pathlib import Path

from ...db.task_crud import task_crud
from ...db.file_crud import file_crud, variant_group_crud
from ...db.project_crud import project_crud
from ...providers.stable_diffusion_provider import comfyui_provider, ComfyUIProvider
from ...schemas.task import TaskStatusUpdate, TaskStatus
from ...schemas.file import FileCreate, FileType, VariantGroupCreate
from ...config import settings


class ImageGeneratorService:
    """Service for generating images using ComfyUI"""

    def __init__(self, db: Session, sd_provider: Optional[ComfyUIProvider] = None):
        self.db = db
        self.sd_provider = sd_provider or comfyui_provider

    async def generate(
        self,
        project_id: UUID,
        task_id: UUID,
        storyboard_file_id: UUID,
        prompt: str,
        negative_prompt: str = "",
        variant_count: int = 4,
        seed: int = -1,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler: str = "euler",
        width: int = 512,
        height: int = 768,
        workflow_id: str = "default",
    ) -> bool:
        """
        Generate multiple image variants from a storyboard panel

        Returns True if successful, False otherwise
        """
        task = task_crud.get(self.db, task_id=task_id)
        if not task:
            return False

        try:
            # Update task status to running
            task_crud.update_status(
                self.db,
                task_id=task_id,
                obj_in=TaskStatusUpdate(status=TaskStatus.RUNNING),
            )

            # Create variant group
            variant_group = variant_group_crud.create(
                self.db,
                obj_in=VariantGroupCreate(
                    project_id=project_id,
                    task_id=task_id,
                    stage="image",
                    parameters={
                        "storyboard_file_id": str(storyboard_file_id),
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "variant_count": variant_count,
                        "steps": steps,
                        "cfg_scale": cfg_scale,
                        "sampler": sampler,
                        "width": width,
                        "height": height,
                        "workflow_id": workflow_id,
                    },
                ),
            )

            # Generate variants with different seeds
            file_ids = []
            base_seed = seed if seed != -1 else 42

            for i in range(variant_count):
                variant_seed = base_seed + i if seed == -1 else seed + i

                result = await self.sd_provider.generate({
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "seed": variant_seed,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler": sampler,
                    "width": width,
                    "height": height,
                    "workflow_id": workflow_id,
                })

                if result.success and result.file_paths:
                    for file_path in result.file_paths:
                        rel_path = str(file_path.relative_to(settings.storage_path)) if file_path.is_absolute() else str(file_path)

                        # Create file record
                        file_record = file_crud.create(
                            self.db,
                            obj_in=FileCreate(
                                project_id=project_id,
                                variant_group_id=variant_group.id,
                                task_id=task_id,
                                file_path=rel_path,
                                file_type=FileType.IMAGE,
                                file_size=file_path.stat().st_size if isinstance(file_path, Path) and file_path.exists() else 0,
                                generation_params={
                                    "prompt": prompt,
                                    "negative_prompt": negative_prompt,
                                    "seed": variant_seed,
                                    "steps": steps,
                                    "cfg_scale": cfg_scale,
                                    "sampler": sampler,
                                    "width": width,
                                    "height": height,
                                    "variant_index": i,
                                },
                                metadata=result.metadata,
                            ),
                        )
                        file_ids.append(str(file_record.id))

            # Update task with output file IDs
            task.output_file_ids = file_ids
            self.db.add(task)

            # Update task status to completed
            task_crud.update_status(
                self.db,
                task_id=task_id,
                obj_in=TaskStatusUpdate(status=TaskStatus.COMPLETED),
            )

            return len(file_ids) > 0

        except Exception as e:
            # Update task status to failed
            task_crud.update_status(
                self.db,
                task_id=task_id,
                obj_in=TaskStatusUpdate(
                    status=TaskStatus.FAILED,
                    reason=str(e),
                ),
            )
            return False
