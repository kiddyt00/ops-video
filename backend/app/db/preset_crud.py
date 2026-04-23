"""
Parameter preset CRUD operations
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.parameter_preset import ParameterPreset
from ..schemas.parameter_preset import PresetCreate, PresetUpdate


class PresetCRUD:
    """Parameter preset CRUD operations"""

    def create(self, db: Session, *, obj_in: PresetCreate, user_id: Optional[UUID] = None) -> ParameterPreset:
        """Create a new preset"""
        preset = ParameterPreset(
            name=obj_in.name,
            generator_type=obj_in.generator_type,
            description=obj_in.description,
            parameters=obj_in.parameters or {},
            user_id=user_id,
        )
        db.add(preset)
        db.commit()
        db.refresh(preset)
        return preset

    def get(self, db: Session, preset_id: UUID) -> Optional[ParameterPreset]:
        """Get preset by ID"""
        return db.query(ParameterPreset).filter(ParameterPreset.id == preset_id).first()

    def get_all(
        self, db: Session, *, user_id: Optional[UUID] = None,
        generator_type: Optional[str] = None
    ) -> List[ParameterPreset]:
        """Get all presets, optionally filtered by user and generator type"""
        query = db.query(ParameterPreset)
        if user_id is not None:
            query = query.filter(ParameterPreset.user_id == user_id)
        if generator_type is not None:
            query = query.filter(ParameterPreset.generator_type == generator_type)
        return query.all()

    def update(self, db: Session, *, preset_id: UUID, obj_in: PresetUpdate) -> Optional[ParameterPreset]:
        """Update preset"""
        preset = self.get(db, preset_id=preset_id)
        if not preset:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preset, field, value)

        db.add(preset)
        db.commit()
        db.refresh(preset)
        return preset

    def delete(self, db: Session, preset_id: UUID) -> bool:
        """Delete preset"""
        preset = self.get(db, preset_id=preset_id)
        if not preset:
            return False

        db.delete(preset)
        db.commit()
        return True


preset_crud = PresetCRUD()
