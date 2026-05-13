"""CRUD for character state snapshots."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from ..models.relation import CharacterState


class CharacterStateCRUD:
    def create(self, db: Session, *, project_id: str, character_name: str,
               chapter_number: int, status: str = "alive", location: Optional[str] = None,
               faction: Optional[str] = None, summary: Optional[str] = None) -> CharacterState:
        s = CharacterState(
            project_id=project_id, character_name=character_name,
            chapter_number=chapter_number, status=status, location=location,
            faction=faction, summary=summary,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    def get_latest(self, db: Session, project_id: str, character_name: str) -> Optional[CharacterState]:
        return db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.character_name == character_name,
        ).order_by(desc(CharacterState.chapter_number)).first()

    def get_all_latest(self, db: Session, project_id: str) -> List[CharacterState]:
        subq = db.query(
            CharacterState.character_name,
            func.max(CharacterState.chapter_number).label("max_chapter"),
        ).filter(
            CharacterState.project_id == project_id,
        ).group_by(CharacterState.character_name).subquery()

        return db.query(CharacterState).join(
            subq,
            and_(
                CharacterState.character_name == subq.c.character_name,
                CharacterState.chapter_number == subq.c.max_chapter,
                CharacterState.project_id == project_id,
            ),
        ).all()

    def list_by_chapter(self, db: Session, project_id: str, chapter_number: int) -> List[CharacterState]:
        return db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.chapter_number == chapter_number,
        ).all()

    def get_history(self, db: Session, project_id: str, character_name: str) -> List[CharacterState]:
        return db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.character_name == character_name,
        ).order_by(CharacterState.chapter_number).all()


character_state_crud = CharacterStateCRUD()
