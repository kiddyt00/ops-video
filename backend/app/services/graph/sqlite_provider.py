"""SQLite graph provider - wraps existing relation_crud + character_state_crud."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...db.relation_crud import relation_crud
from ...db.character_state_crud import character_state_crud
from ...services.knowledge_service import build_continuity_context
from . import GraphProvider, RelationData, CharacterStateData


class SQLiteGraphProvider(GraphProvider):
    async def get_relations(self, project_id: str) -> List[RelationData]:
        db = SessionLocal()
        try:
            rels = relation_crud.list_by_project(db, project_id)
            return [
                RelationData(r.project_id, r.source_type, r.source_name,
                             r.relation_type, r.target_type, r.target_name, r.properties)
                for r in rels
            ]
        finally:
            db.close()

    async def create_relation(self, project_id: str, source_type: str, source_name: str,
                              relation_type: str, target_type: str, target_name: str,
                              properties: Optional[dict] = None) -> RelationData:
        db = SessionLocal()
        try:
            r = relation_crud.create(db, project_id=project_id, source_type=source_type,
                                     source_name=source_name, relation_type=relation_type,
                                     target_type=target_type, target_name=target_name,
                                     properties=properties)
            return RelationData(r.project_id, r.source_type, r.source_name,
                                r.relation_type, r.target_type, r.target_name, r.properties)
        finally:
            db.close()

    async def get_latest_character_state(self, project_id: str, character_name: str) -> Optional[CharacterStateData]:
        db = SessionLocal()
        try:
            s = character_state_crud.get_latest(db, project_id, character_name)
            if not s:
                return None
            return CharacterStateData(s.project_id, s.character_name, s.chapter_number,
                                      s.status, s.location, s.faction, s.summary)
        finally:
            db.close()

    async def save_character_state(self, project_id: str, character_name: str,
                                   chapter_number: int, status: str = "alive",
                                   location: Optional[str] = None,
                                   faction: Optional[str] = None,
                                   summary: Optional[str] = None) -> CharacterStateData:
        db = SessionLocal()
        try:
            s = character_state_crud.create(db, project_id=project_id,
                                            character_name=character_name,
                                            chapter_number=chapter_number, status=status,
                                            location=location, faction=faction, summary=summary)
            return CharacterStateData(s.project_id, s.character_name, s.chapter_number,
                                      s.status, s.location, s.faction, s.summary)
        finally:
            db.close()

    async def get_continuity_context(self, project_id: str) -> str:
        db = SessionLocal()
        try:
            return build_continuity_context(db, project_id)
        finally:
            db.close()
