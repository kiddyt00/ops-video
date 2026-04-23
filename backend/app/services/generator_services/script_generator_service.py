"""
Script Generator Service
"""
import asyncio
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from pathlib import Path

from ...db.task_crud import task_crud
from ...db.file_crud import file_crud, variant_group_crud
from ...db.project_crud import project_crud
from ...providers.llm_provider import llm_provider, LLMProvider
from ...schemas.task import TaskStatusUpdate, TaskStatus
from ...schemas.file import FileCreate, FileType, VariantGroupCreate
from ...config import settings
from .mock_helpers import mock_script_result


class ScriptGeneratorService:
    """Service for generating scripts using LLM"""

    def __init__(self, db: Session, llm: Optional[LLMProvider] = None):
        self.db = db
        self.llm = llm or llm_provider

    async def generate(
        self,
        project_id: UUID,
        task_id: UUID,
        topic: str,
        style: str = "comic",
        duration: str = "1-3 minutes",
        additional_context: Optional[str] = None,
        variant_count: int = 4,
    ) -> bool:
        """
        Generate multiple script variants

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
                    stage="script",
                    parameters={
                        "topic": topic,
                        "style": style,
                        "duration": duration,
                        "variant_count": variant_count,
                    },
                ),
            )

            # Generate variants
            file_ids = []
            for i in range(variant_count):
                seed = task.parameters.get("seed", 42) + i if task.parameters.get("seed") else None

                if settings.MOCK_MODE:
                    result = mock_script_result(topic=topic, style=style, duration=duration)
                else:
                    result = await self.llm.generate_script(
                        topic=topic,
                        style=style,
                        duration=duration,
                        additional_context=additional_context,
                    )

                if result.success and result.file_paths:
                    file_path = result.file_paths[0]
                    rel_path = str(file_path.relative_to(settings.storage_path))

                    # Create file record
                    file_record = file_crud.create(
                        self.db,
                        obj_in=FileCreate(
                            project_id=project_id,
                            variant_group_id=variant_group.id,
                            task_id=task_id,
                            file_path=rel_path,
                            file_type=FileType.SCRIPT,
                            file_size=file_path.stat().st_size,
                            generation_params={
                                **result.parameters,
                                "seed": seed,
                                "variant_index": i,
                            },
                            extra_info=result.metadata if result.metadata else {},
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
