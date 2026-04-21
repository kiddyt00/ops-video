"""
Generic CRUD operations
"""
from typing import Generic, Type, TypeVar, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from .base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class CRUDBase(Generic[ModelType]):
    """Base class for CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.get(self.model, id)

    def get_all(self, db: Session) -> List[ModelType]:
        """Get all records"""
        return db.query(self.model).all()

    def create(self, db: Session, *, obj_in: dict) -> ModelType:
        """Create a new record"""
        obj_in_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        obj = self.model(**obj_in_data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(
        self, db: Session, *, id: UUID, obj_in: dict
    ) -> Optional[ModelType]:
        """Update a record"""
        obj = self.get(db, id=id)
        if not obj:
            return None

        obj_in_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        for field, value in obj_in_data.items():
            setattr(obj, field, value)

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, *, id: UUID) -> bool:
        """Delete a record"""
        obj = self.get(db, id=id)
        if not obj:
            return False

        db.delete(obj)
        db.commit()
        return True
