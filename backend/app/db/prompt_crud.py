"""CRUD for prompt templates."""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.prompt import Prompt
from datetime import datetime, timezone


class PromptCRUD:
    def create(self, db: Session, *, name: str, template: str,
               description: Optional[str] = None, built_in: bool = False) -> Prompt:
        existing = db.query(Prompt).filter(Prompt.name == name).first()
        if existing:
            raise ValueError(f"提示词模板 '{name}' 已存在")
        p = Prompt(name=name, template=template, description=description, built_in=built_in)
        db.add(p)
        db.commit()
        db.refresh(p)
        return p

    def get(self, db: Session, prompt_id: str) -> Optional[Prompt]:
        return db.query(Prompt).filter(Prompt.id == prompt_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Prompt]:
        return db.query(Prompt).filter(Prompt.name == name).first()

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> List[Prompt]:
        return db.query(Prompt).offset(skip).limit(limit).all()

    def update(self, db: Session, prompt_id: str, **kwargs) -> Optional[Prompt]:
        p = self.get(db, prompt_id)
        if not p:
            return None
        for key, value in kwargs.items():
            if hasattr(p, key) and key not in ('id', 'created_at', 'built_in'):
                setattr(p, key, value)
        p.version += 1
        p.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(p)
        return p

    def delete(self, db: Session, prompt_id: str) -> bool:
        p = self.get(db, prompt_id)
        if not p:
            return False
        if p.built_in:
            raise ValueError("系统内置提示词模板不可删除")
        db.delete(p)
        db.commit()
        return True


prompt_crud = PromptCRUD()
