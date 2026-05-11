"""
Character Card CRUD operations
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.character_card import CharacterCard
from ..schemas.character_card import CharacterCardCreate, CharacterCardUpdate


class CharacterCardCRUD:
    def create(self, db: Session, project_id: UUID, obj_in: CharacterCardCreate) -> CharacterCard:
        model = CharacterCard(**obj_in.model_dump(), project_id=project_id)
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def get_by_project(self, db: Session, project_id: UUID) -> List[CharacterCard]:
        return (
            db.query(CharacterCard)
            .filter(CharacterCard.project_id == project_id)
            .order_by(CharacterCard.created_at.desc())
            .all()
        )

    def get(self, db: Session, card_id: UUID) -> Optional[CharacterCard]:
        return db.query(CharacterCard).filter(CharacterCard.id == card_id).first()

    def update(self, db: Session, card_id: UUID, obj_in: CharacterCardUpdate) -> Optional[CharacterCard]:
        card = self.get(db, card_id)
        if not card:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)
        db.commit()
        db.refresh(card)
        return card

    def delete(self, db: Session, card_id: UUID) -> bool:
        card = self.get(db, card_id)
        if not card:
            return False
        db.delete(card)
        db.commit()
        return True


character_card_crud = CharacterCardCRUD()
