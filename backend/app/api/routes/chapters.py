"""
Chapter API routes — derived from Story chapter_outline
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.session import get_db
from ...db.story_crud import story_crud
from ...schemas.story import StoryResponse

router = APIRouter()


@router.get("", response_model=List[dict])
def list_chapters(project_id: UUID, db: Session = Depends(get_db)):
    """List chapters from the project's story chapter_outline"""
    story = story_crud.get_by_project(db, project_id)
    if not story or not story.chapter_outline:
        return []
    return story.chapter_outline


@router.get("/{chapter_id}", response_model=dict)
def get_chapter(project_id: UUID, chapter_id: str, db: Session = Depends(get_db)):
    """Get a specific chapter by index from story chapter_outline"""
    story = story_crud.get_by_project(db, project_id)
    if not story or not story.chapter_outline:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        idx = int(chapter_id)
        if 0 <= idx < len(story.chapter_outline):
            return story.chapter_outline[idx]
    except ValueError:
        pass
    raise HTTPException(status_code=404, detail="Chapter not found")
