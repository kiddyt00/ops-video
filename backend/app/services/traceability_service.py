"""
Traceability Service - Version control and rollback
"""
from uuid import UUID
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.file import File, VariantGroup
from ..models.task import Task, TaskStatus
from ..db.file_crud import file_crud, variant_group_crud
from ..db.task_crud import task_crud


class TraceabilityService:
    """
    Service for tracking and managing version history

    Features:
    - Version comparison (diff generation params)
    - Rollback to historical versions
    - Complete audit trail
    """

    def __init__(self, db: Session):
        self.db = db

    def get_file_versions(self, file_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all versions of a file (including child files derived from it)

        Returns version tree with parent-child relationships
        """
        file = file_crud.get(self.db, file_id=file_id)
        if not file:
            return []

        versions = []

        # Get parent chain (ancestors)
        current = file
        ancestors = []
        while current.parent_file_id:
            parent = file_crud.get(self.db, file_id=current.parent_file_id)
            if parent:
                ancestors.append(self._file_to_dict(parent))
                current = parent
            else:
                break

        # Get child files (descendants)
        descendants = self.db.query(File).filter(
            File.parent_file_id == file_id
        ).all()

        versions = {
            "current": self._file_to_dict(file),
            "ancestors": ancestors,
            "descendants": [self._file_to_dict(d) for d in descendants],
        }

        return versions

    def compare_files(self, file_id_1: UUID, file_id_2: UUID) -> Dict[str, Any]:
        """
        Compare two files and return their differences

        Returns:
            Dict containing:
            - params_diff: Differences in generation parameters
            - metadata_diff: Differences in metadata
            - files: Basic info of both files
        """
        file1 = file_crud.get(self.db, file_id=file_id_1)
        file2 = file_crud.get(self.db, file_id=file_id_2)

        if not file1 or not file2:
            return {"error": "One or both files not found"}

        # Compare generation parameters
        params_diff = self._compare_dicts(
            file1.generation_params,
            file2.generation_params
        )

        # Compare extra_info
        metadata_diff = self._compare_dicts(
            file1.extra_info,
            file2.extra_info
        )

        return {
            "file_1": {
                "id": str(file1.id),
                "file_path": file1.file_path,
                "file_type": file1.file_type.value,
                "version": file1.version,
                "created_at": file1.created_at.isoformat(),
            },
            "file_2": {
                "id": str(file2.id),
                "file_path": file2.file_path,
                "file_type": file2.file_type.value,
                "version": file2.version,
                "created_at": file2.created_at.isoformat(),
            },
            "params_diff": params_diff,
            "metadata_diff": metadata_diff,
        }

    def _compare_dicts(
        self,
        dict1: Dict[str, Any],
        dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two dictionaries and return differences"""
        all_keys = set(dict1.keys()) | set(dict2.keys())

        diff = {
            "only_in_first": [],
            "only_in_second": [],
            "different_values": {},
            "same_values": {},
        }

        for key in all_keys:
            in_1 = key in dict1
            in_2 = key in dict2

            if in_1 and not in_2:
                diff["only_in_first"].append(key)
            elif in_2 and not in_1:
                diff["only_in_second"].append(key)
            elif dict1[key] != dict2[key]:
                diff["different_values"][key] = {
                    "value_1": dict1[key],
                    "value_2": dict2[key],
                }
            else:
                diff["same_values"][key] = dict1[key]

        return diff

    async def rollback_and_regenerate(
        self,
        project_id: UUID,
        source_file_id: UUID,
        generator_type: str,
        new_parameters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Task, VariantGroup]:
        """
        Rollback to a historical file and regenerate with new/modified parameters

        Args:
            project_id: Project ID
            source_file_id: Historical file to use as base
            generator_type: Generator type for regeneration
            new_parameters: Optional new/modified parameters

        Returns:
            Tuple of (new_task, new_variant_group)
        """
        source_file = file_crud.get(self.db, file_id=source_file_id)
        if not source_file:
            raise ValueError(f"File {source_file_id} not found")

        # Find or create task for this stage
        stage_map = {
            "script": "script",
            "storyboard": "storyboard",
            "image": "image",
            "tts": "audio",
        }

        stage = stage_map.get(generator_type, generator_type)

        # Merge parameters
        merged_params = dict(source_file.generation_params)
        if new_parameters:
            merged_params.update(new_parameters)

        # Create new task
        task = task_crud.create(
            self.db,
            obj_in={
                "project_id": project_id,
                "stage": stage,
                "generator_type": generator_type,
                "parameters": merged_params,
                "parent_task_id": source_file.task_id,
            }
        )

        # Create variant group
        variant_group = variant_group_crud.create(
            self.db,
            obj_in={
                "project_id": project_id,
                "task_id": task.id,
                "stage": stage,
                "parameters": merged_params,
            }
        )

        return task, variant_group

    def get_generation_lineage(self, file_id: UUID) -> List[Dict[str, Any]]:
        """
        Get complete generation lineage for a file

        Traces back through all parent files and tasks to show
        the complete generation history
        """
        lineage = []
        current_file = file_crud.get(self.db, file_id=file_id)

        while current_file:
            # Get task info
            task = None
            if current_file.task_id:
                task = task_crud.get(self.db, task_id=current_file.task_id)

            # Get variant group info
            variant_group = None
            if current_file.variant_group_id:
                variant_group = variant_group_crud.get(
                    self.db,
                    variant_group_id=current_file.variant_group_id
                )

            lineage.append({
                "file": {
                    "id": str(current_file.id),
                    "file_path": current_file.file_path,
                    "file_type": current_file.file_type.value,
                    "generation_params": current_file.generation_params,
                    "version": current_file.version,
                    "created_at": current_file.created_at.isoformat(),
                },
                "task": {
                    "id": str(task.id),
                    "stage": task.stage.value,
                    "generator_type": task.generator_type,
                    "status": task.status.value,
                } if task else None,
                "variant_group": {
                    "id": str(variant_group.id),
                    "selected": variant_group.selected_file_id == current_file.id,
                } if variant_group else None,
            })

            # Move to parent
            if current_file.parent_file_id:
                current_file = file_crud.get(
                    self.db,
                    file_id=current_file.parent_file_id
                )
            else:
                break

        return lineage

    def _file_to_dict(self, file: File) -> Dict[str, Any]:
        """Convert File model to dictionary"""
        return {
            "id": str(file.id),
            "file_path": file.file_path,
            "file_type": file.file_type.value,
            "version": file.version,
            "generation_params": file.generation_params,
            "extra_info": file.extra_info,
            "is_selected": file.is_selected,
            "selected_at": file.selected_at.isoformat() if file.selected_at else None,
            "parent_file_id": str(file.parent_file_id) if file.parent_file_id else None,
            "created_at": file.created_at.isoformat(),
            "updated_at": file.updated_at.isoformat(),
        }


traceability_service = TraceabilityService
