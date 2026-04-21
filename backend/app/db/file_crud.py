"""
VariantGroup and File CRUD operations
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.file import File, FileType, VariantGroup
from ..schemas.file import FileCreate, VariantGroupCreate, VariantSelect


class VariantGroupCRUD:
    """VariantGroup CRUD operations"""

    def get_all(self, db: Session, project_id: Optional[UUID] = None) -> List[VariantGroup]:
        """Get all variant groups"""
        query = db.query(VariantGroup)
        if project_id:
            query = query.filter(VariantGroup.project_id == project_id)
        return query.all()

    def get(self, db: Session, variant_group_id: UUID) -> Optional[VariantGroup]:
        """Get variant group by ID"""
        return db.query(VariantGroup).filter(
            VariantGroup.id == variant_group_id
        ).first()

    def create(
        self, db: Session, *, obj_in: VariantGroupCreate
    ) -> VariantGroup:
        """Create a new variant group"""
        variant_group = VariantGroup(
            project_id=obj_in.project_id,
            task_id=obj_in.task_id,
            stage=obj_in.stage,
            parameters=obj_in.parameters or {},
        )
        db.add(variant_group)
        db.commit()
        db.refresh(variant_group)
        return variant_group

    def select_variant(
        self, db: Session, *, variant_group_id: UUID, file_id: UUID
    ) -> Optional[VariantGroup]:
        """Select a variant from the group"""
        variant_group = self.get(db, variant_group_id=variant_group_id)
        if not variant_group:
            return None

        # Verify file belongs to this variant group
        file = db.query(File).filter(
            File.id == file_id,
            File.variant_group_id == variant_group_id
        ).first()

        if not file:
            return None

        # Unselect previous selection
        if variant_group.selected_file_id:
            prev_file = db.query(File).filter(
                File.id == variant_group.selected_file_id
            ).first()
            if prev_file:
                prev_file.is_selected = False
                prev_file.selected_at = None

        # Select new file
        variant_group.selected_file_id = file_id
        file.is_selected = True
        file.selected_at = datetime.utcnow()

        db.add(variant_group)
        db.add(file)
        db.commit()
        db.refresh(variant_group)

        return variant_group

    def delete(self, db: Session, variant_group_id: UUID) -> bool:
        """Delete variant group"""
        variant_group = self.get(db, variant_group_id=variant_group_id)
        if not variant_group:
            return False

        db.delete(variant_group)
        db.commit()
        return True


class FileCRUD:
    """File CRUD operations"""

    def get_all(self, db: Session, project_id: Optional[UUID] = None) -> List[File]:
        """Get all files"""
        query = db.query(File)
        if project_id:
            query = query.filter(File.project_id == project_id)
        return query.all()

    def get(self, db: Session, file_id: UUID) -> Optional[File]:
        """Get file by ID"""
        return db.query(File).filter(File.id == file_id).first()

    def create(self, db: Session, *, obj_in: FileCreate) -> File:
        """Create a new file"""
        file = File(
            project_id=obj_in.project_id,
            variant_group_id=obj_in.variant_group_id,
            task_id=obj_in.task_id,
            file_path=obj_in.file_path,
            file_type=obj_in.file_type,
            file_size=obj_in.file_size,
            generation_params=obj_in.generation_params or {},
            extra_info=obj_in.extra_info or {},
            version=obj_in.version,
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        return file

    def update(self, db: Session, *, file_id: UUID, obj_in: dict) -> Optional[File]:
        """Update file"""
        file = self.get(db, file_id=file_id)
        if not file:
            return None

        for field, value in obj_in.items():
            setattr(file, field, value)

        db.add(file)
        db.commit()
        db.refresh(file)
        return file

    def delete(self, db: Session, file_id: UUID) -> bool:
        """Delete file"""
        file = self.get(db, file_id=file_id)
        if not file:
            return False

        db.delete(file)
        db.commit()
        return True


variant_group_crud = VariantGroupCRUD()
file_crud = FileCRUD()
