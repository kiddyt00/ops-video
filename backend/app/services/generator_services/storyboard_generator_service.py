"""
Storyboard Generator Service
"""
import json
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


class StoryboardGeneratorService:
    """Service for generating storyboards from scripts using LLM"""

    def __init__(self, db: Session, llm: Optional[LLMProvider] = None):
        self.db = db
        self.llm = llm or llm_provider

    async def generate(
        self,
        project_id: UUID,
        task_id: UUID,
        script_file_id: UUID,
        panel_count: int = 6,
        variant_count: int = 4,
    ) -> bool:
        """
        Generate multiple storyboard variants from a script

        Returns True if successful, False otherwise
        """
        task = task_crud.get(self.db, task_id=task_id)
        if not task:
            return False

        # Get the selected script file
        script_file = file_crud.get(self.db, file_id=script_file_id)
        if not script_file:
            return False

        # Read script content
        script_path = settings.storage_path / script_file.file_path
        script_content = script_path.read_text(encoding="utf-8")

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
                    stage="storyboard",
                    parameters={
                        "script_file_id": str(script_file_id),
                        "panel_count": panel_count,
                        "variant_count": variant_count,
                    },
                ),
            )

            # Generate variants
            file_ids = []
            for i in range(variant_count):
                result = await self.llm.generate_storyboard(
                    script=script_content,
                    panel_count=panel_count,
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
                            file_type=FileType.STORYBOARD,
                            file_size=file_path.stat().st_size if file_path.exists() else 0,
                            generation_params={
                                **result.parameters,
                                "variant_index": i,
                            },
                            extra_info=result.metadata,
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
