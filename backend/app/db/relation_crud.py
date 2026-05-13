"""CRUD for character relations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.relation import Relation


class RelationCRUD:
    def create(self, db: Session, *, project_id: str, source_type: str, source_name: str,
               relation_type: str, target_type: str, target_name: str,
               properties: Optional[dict] = None) -> Relation:
        r = Relation(
            project_id=project_id, source_type=source_type, source_name=source_name,
            relation_type=relation_type, target_type=target_type, target_name=target_name,
            properties=properties,
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return r

    def list_by_project(self, db: Session, project_id: str) -> List[Relation]:
        return db.query(Relation).filter(Relation.project_id == project_id).all()

    def list_by_character(self, db: Session, project_id: str, character_name: str) -> List[Relation]:
        return db.query(Relation).filter(
            Relation.project_id == project_id,
            (Relation.source_name == character_name) | (Relation.target_name == character_name),
        ).all()

    def delete(self, db: Session, relation_id: str) -> bool:
        r = db.query(Relation).filter(Relation.id == relation_id).first()
        if not r:
            return False
        db.delete(r)
        db.commit()
        return True


relation_crud = RelationCRUD()
