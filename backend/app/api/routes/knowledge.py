"""Knowledge base API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.knowledge_crud import knowledge_crud

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("")
def list_knowledge(category: Optional[str] = Query(None), db: Session = Depends(get_db)):
    items = knowledge_crud.list(db, category=category)
    return [{"id": k.id, "name": k.name, "category": k.category,
             "description": k.description, "built_in": k.built_in,
             "created_at": k.created_at.isoformat() if k.created_at else None} for k in items]


@router.get("/{kb_id}")
def get_knowledge(kb_id: str, db: Session = Depends(get_db)):
    kb = knowledge_crud.get(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"id": kb.id, "name": kb.name, "category": kb.category,
            "content": kb.content, "description": kb.description,
            "built_in": kb.built_in,
            "created_at": kb.created_at.isoformat() if kb.created_at else None,
            "updated_at": kb.updated_at.isoformat() if kb.updated_at else None}


@router.post("", status_code=201)
def create_knowledge(data: dict, db: Session = Depends(get_db)):
    try:
        kb = knowledge_crud.create(db, name=data["name"], category=data["category"],
                                   content=data["content"], description=data.get("description"))
        return {"id": kb.id, "name": kb.name, "category": kb.category}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{kb_id}")
def update_knowledge(kb_id: str, data: dict, db: Session = Depends(get_db)):
    kb = knowledge_crud.update(db, kb_id, **data)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"id": kb.id, "name": kb.name}


@router.delete("/{kb_id}", status_code=204)
def delete_knowledge(kb_id: str, db: Session = Depends(get_db)):
    try:
        ok = knowledge_crud.delete(db, kb_id)
        if not ok:
            raise HTTPException(status_code=404, detail="知识库不存在")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
