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

    def batch_create_from_outline(
        self,
        db: Session,
        project_id: UUID,
        outline_items: List[dict],
    ) -> List[Chapter]:
        """Create chapters from story chapter_outline data."""
        created = []
        for item in outline_items:
            chapter = self.create_from_outline(
                db,
                project_id=project_id,
                chapter_number=item.get("chapter_number", len(created) + 1),
                name=item.get("title", item.get("name", f"第{len(created)+1}章")),
                description=item.get("summary", item.get("description")),
            )
            created.append(chapter)
        return created


chapter_crud = ChapterCRUD()
