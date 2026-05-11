"""
Storage Provider CRUD operations
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.storage_provider import StorageProvider
from ..schemas.storage_provider import StorageProviderCreate, StorageProviderUpdate


class StorageProviderCRUD:
    def create(self, db: Session, obj_in: StorageProviderCreate) -> StorageProvider:
        model = StorageProvider(**obj_in.model_dump())
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def get_all(self, db: Session) -> List[StorageProvider]:
        return db.query(StorageProvider).order_by(StorageProvider.created_at.desc()).all()

    def get(self, db: Session, provider_id: UUID) -> Optional[StorageProvider]:
        return db.query(StorageProvider).filter(StorageProvider.id == provider_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[StorageProvider]:
        return db.query(StorageProvider).filter(StorageProvider.name == name).first()

    def get_active(self, db: Session) -> Optional[StorageProvider]:
        return (
            db.query(StorageProvider)
            .filter(StorageProvider.is_active == True)
            .first()
        )

    def update(self, db: Session, provider_id: UUID, obj_in: StorageProviderUpdate) -> Optional[StorageProvider]:
        provider = self.get(db, provider_id)
        if not provider:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(provider, field, value)
        db.commit()
        db.refresh(provider)
        return provider

    def delete(self, db: Session, provider_id: UUID) -> bool:
        provider = self.get(db, provider_id)
        if not provider:
            return False
        db.delete(provider)
        db.commit()
        return True

    def activate(self, db: Session, provider_id: UUID) -> Optional[StorageProvider]:
        """Activate a provider and deactivate all others."""
        provider = self.get(db, provider_id)
        if not provider:
            return None
        # Deactivate all providers first
        db.query(StorageProvider).update({StorageProvider.is_active: False})
        # Activate the target provider
        provider.is_active = True
        db.commit()
        db.refresh(provider)
        return provider

    def update_test_result(
        self,
        db: Session,
        provider_id: UUID,
        success: bool,
        error: Optional[str] = None,
    ) -> Optional[StorageProvider]:
        """Update the last test result for a storage provider."""
        provider = self.get(db, provider_id)
        if not provider:
            return None
        provider.last_tested_at = datetime.utcnow()
        provider.last_test_status = "success" if success else "failed"
        provider.last_test_error = error if not success else None
        db.commit()
        db.refresh(provider)
        return provider


storage_provider_crud = StorageProviderCRUD()
