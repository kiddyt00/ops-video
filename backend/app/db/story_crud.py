"""
Story CRUD operations
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session

from ..models.story import Story
from ..schemas.story import StoryCreate, StoryUpdate


class StoryCRUD:
    def create(self, db: Session, project_id: UUID, obj_in: StoryCreate) -> Story:
        model = Story(**obj_in.model_dump(), project_id=project_id)
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def get_by_project(self, db: Session, project_id: UUID) -> Optional[Story]:
        return (
            db.query(Story)
            .filter(Story.project_id == project_id)
            .first()
        )

    def get(self, db: Session, story_id: UUID) -> Optional[Story]:
        return db.query(Story).filter(Story.id == story_id).first()

    def update(self, db: Session, story_id: UUID, obj_in: StoryUpdate) -> Optional[Story]:
        story = self.get(db, story_id)
        if not story:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(story, field, value)
        db.commit()
        db.refresh(story)
        return story

    def delete(self, db: Session, story_id: UUID) -> bool:
        story = self.get(db, story_id)
        if not story:
            return False
        db.delete(story)
        db.commit()
        return True


story_crud = StoryCRUD()
