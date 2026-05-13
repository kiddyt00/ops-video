"""Relation and CharacterState API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.relation_crud import relation_crud
from ...db.character_state_crud import character_state_crud

router = APIRouter(tags=["relations"])


# ── Relations ──

@router.get("/api/v1/projects/{project_id}/relations")
def list_relations(project_id: str, character: Optional[str] = Query(None),
                   db: Session = Depends(get_db)):
    if character:
        rels = relation_crud.list_by_character(db, project_id, character)
    else:
        rels = relation_crud.list_by_project(db, project_id)
    return [{"id": r.id, "source_type": r.source_type, "source_name": r.source_name,
             "relation_type": r.relation_type, "target_type": r.target_type,
             "target_name": r.target_name, "properties": r.properties,
             "created_at": r.created_at.isoformat() if r.created_at else None} for r in rels]


@router.post("/api/v1/projects/{project_id}/relations", status_code=201)
def create_relation(project_id: str, data: dict, db: Session = Depends(get_db)):
    r = relation_crud.create(db, project_id=project_id,
                             source_type=data["source_type"], source_name=data["source_name"],
                             relation_type=data["relation_type"],
                             target_type=data["target_type"], target_name=data["target_name"],
                             properties=data.get("properties"))
    return {"id": r.id}


@router.delete("/api/v1/projects/{project_id}/relations/{relation_id}", status_code=204)
def delete_relation(project_id: str, relation_id: str, db: Session = Depends(get_db)):
    ok = relation_crud.delete(db, relation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="关系不存在")


# ── Character States ──

@router.get("/api/v1/projects/{project_id}/character-states")
def list_character_states(project_id: str, character: Optional[str] = Query(None),
                          chapter: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if character:
        states = character_state_crud.get_history(db, project_id, character)
    elif chapter is not None:
        states = character_state_crud.list_by_chapter(db, project_id, chapter)
    else:
        states = character_state_crud.get_all_latest(db, project_id)
    return [{"id": s.id, "character_name": s.character_name,
             "chapter_number": s.chapter_number, "status": s.status,
             "location": s.location, "faction": s.faction, "summary": s.summary,
             "created_at": s.created_at.isoformat() if s.created_at else None} for s in states]


@router.post("/api/v1/projects/{project_id}/character-states", status_code=201)
def create_character_state(project_id: str, data: dict, db: Session = Depends(get_db)):
    s = character_state_crud.create(db, project_id=project_id,
                                    character_name=data["character_name"],
                                    chapter_number=data["chapter_number"],
                                    status=data.get("status", "alive"),
                                    location=data.get("location"),
                                    faction=data.get("faction"),
                                    summary=data.get("summary"))
    return {"id": s.id}
