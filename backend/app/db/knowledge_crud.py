"""CRUD operations for Knowledge base."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.knowledge import Knowledge
from datetime import datetime, timezone


class KnowledgeCRUD:
    def create(self, db: Session, *, name: str, category: str, content: str,
               description: Optional[str] = None, built_in: bool = False) -> Knowledge:
        existing = db.query(Knowledge).filter(Knowledge.name == name).first()
        if existing:
            raise ValueError(f"知识库名称 '{name}' 已存在")
        kb = Knowledge(
            name=name, category=category, content=content,
            description=description, built_in=built_in,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    def get(self, db: Session, kb_id: str) -> Optional[Knowledge]:
        return db.query(Knowledge).filter(Knowledge.id == kb_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Knowledge]:
        return db.query(Knowledge).filter(Knowledge.name == name).first()

    def list(self, db: Session, category: Optional[str] = None,
             skip: int = 0, limit: int = 100) -> List[Knowledge]:
        q = db.query(Knowledge)
        if category:
            q = q.filter(Knowledge.category == category)
        return q.offset(skip).limit(limit).all()

    def update(self, db: Session, kb_id: str, **kwargs) -> Optional[Knowledge]:
        kb = self.get(db, kb_id)
        if not kb:
            return None
        for key, value in kwargs.items():
            if hasattr(kb, key) and key not in ('id', 'created_at', 'built_in'):
                setattr(kb, key, value)
        kb.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(kb)
        return kb

    def delete(self, db: Session, kb_id: str) -> bool:
        kb = self.get(db, kb_id)
        if not kb:
            return False
        if kb.built_in:
            raise ValueError("系统内置知识库不可删除")
        db.delete(kb)
        db.commit()
        return True


knowledge_crud = KnowledgeCRUD()
