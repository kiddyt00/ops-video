"""Chapter CRUD operations."""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.chapter import Chapter


class ChapterCRUD:
    def create_from_outline(
        self,
        db: Session,
        project_id: UUID,
        chapter_number: int,
        name: str,
        description: Optional[str] = None,
    ) -> Chapter:
        chapter = Chapter(
            project_id=project_id,
            chapter_number=chapter_number,
            name=name,
            description=description,
            status="pending",
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter

    def get_by_project(self, db: Session, project_id: UUID) -> List[Chapter]:
        return (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id, Chapter.is_deleted == False)
            .order_by(Chapter.chapter_number)
            .all()
        )

    def get(self, db: Session, chapter_id: UUID) -> Optional[Chapter]:
        return db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.is_deleted == False).first()

    def update_status(
        self,
        db: Session,
        chapter_id: UUID,
        status: str,
        current_stage: Optional[str] = None,
        video_file_id: Optional[UUID] = None,
    ) -> Optional[Chapter]:
        chapter = self.get(db, chapter_id)
        if not chapter:
            return None
        chapter.status = status
        if current_stage:
            chapter.current_stage = current_stage
        if video_file_id:
            chapter.video_file_id = video_file_id
        db.commit()
        db.refresh(chapter)
        return chapter

    def soft_delete(self, db: Session, chapter_id: UUID) -> bool:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return False
        chapter.is_deleted = True
        db.commit()
        return True

    def update_body_text(
        self,
        db: Session,
        chapter_id: UUID,
        body_text: str,
    ) -> Optional[Chapter]:
        chapter = self.get(db, chapter_id)
        if not chapter:
            return None
        chapter.body_text = body_text
        db.commit()
        db.refresh(chapter)
        return chapter

    def batch_create_from_outline(
        self,
        db: Session,
        project_id: UUID,
        outline_items: List[dict],
    ) -> List[Chapter]:
        """Create or update chapters from story chapter_outline data.

        Existing chapters are updated (name, description); only new ones
        are created. This prevents duplicates across multiple calls.
        """
        existing = self.get_by_project(db, project_id)
        existing_by_number = {c.chapter_number: c for c in existing}

        result = []
        for item in outline_items:
            num = item.get("chapter_number", len(result) + 1)
            name = item.get("title", item.get("name", f"第{num}章"))
            desc = item.get("summary", item.get("description"))

            if num in existing_by_number:
                ch = existing_by_number[num]
                ch.name = name
                if desc:
                    ch.description = desc
                db.add(ch)
                result.append(ch)
            else:
                ch = self.create_from_outline(
                    db, project_id=project_id,
                    chapter_number=num, name=name, description=desc,
                )
                result.append(ch)

        db.commit()
        return result


chapter_crud = ChapterCRUD()
