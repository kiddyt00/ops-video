"""
Chapter API routes — full CRUD backed by Chapter model.

Chapters can be:
1. Auto-created from story chapter_outline via POST /projects/{id}/chapters/sync
2. Manually created/updated/deleted
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.session import get_db
from ...db.chapter_crud import chapter_crud
from ...db.story_crud import story_crud

router = APIRouter()


def _to_response(chapter) -> dict:
    return {
        "id": str(chapter.id),
        "project_id": str(chapter.project_id),
        "chapter_number": chapter.chapter_number,
        "name": chapter.name,
        "description": chapter.description or None,
        "body_text": chapter.body_text or None,
        "status": chapter.status,
        "current_stage": chapter.current_stage,
        "video_file_id": str(chapter.video_file_id) if chapter.video_file_id else None,
        "thumbnail_url": chapter.thumbnail_url,
        "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
        "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None,
    }


@router.get("", response_model=List[dict])
def list_chapters(project_id: UUID, db: Session = Depends(get_db)):
    """List all chapters for a project."""
    chapters = chapter_crud.get_by_project(db, project_id)
    return [_to_response(c) for c in chapters]


@router.get("/{chapter_id}", response_model=dict)
def get_chapter(project_id: UUID, chapter_id: UUID, db: Session = Depends(get_db)):
    """Get a single chapter."""
    chapter = chapter_crud.get(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return _to_response(chapter)


@router.post("/sync", response_model=List[dict])
def sync_chapters_from_story(project_id: UUID, db: Session = Depends(get_db)):
    """Auto-create chapters from story chapter_outline."""
    story = story_crud.get_by_project(db, project_id)
    if not story or not story.chapter_outline:
        raise HTTPException(status_code=400, detail="Story has no chapter outline")

    chapters = chapter_crud.get_by_project(db, project_id)
    if chapters:
        return [_to_response(c) for c in chapters]

    created = chapter_crud.batch_create_from_outline(db, project_id, story.chapter_outline)
    return [_to_response(c) for c in created]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_chapter(
    project_id: UUID,
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new chapter manually."""
    chapters = chapter_crud.get_by_project(db, project_id)
    next_num = max((c.chapter_number for c in chapters), default=0) + 1
    chapter = chapter_crud.create_from_outline(
        db, project_id=project_id, chapter_number=next_num, name=name, description=description,
    )
    return _to_response(chapter)


@router.put("/{chapter_id}/body", response_model=dict)
def update_chapter_body(
    project_id: UUID,
    chapter_id: UUID,
    body_text: str,
    db: Session = Depends(get_db),
):
    """Update a chapter's body text."""
    chapter = chapter_crud.update_body_text(db, chapter_id, body_text)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return _to_response(chapter)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(project_id: UUID, chapter_id: UUID, db: Session = Depends(get_db)):
    """Soft delete a chapter."""
    success = chapter_crud.soft_delete(db, chapter_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chapter not found")
