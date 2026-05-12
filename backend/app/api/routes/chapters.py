"""
Chapter API routes -- derived from Story chapter_outline
"""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.session import get_db
from ...db.story_crud import story_crud

router = APIRouter()

# Status progression mapping
STATUS_ORDER = ["pending", "running", "completed", "failed"]
DEFAULT_STATUS = "pending"


def _enrich_chapter(
    item: dict, index: int, project_id: UUID, story_updated_at: Optional[datetime]
) -> dict:
    """Map chapter_outline entry to full chapter response expected by frontend."""
    return {
        "id": str(index),  # chapter_outline uses array index as ID
        "project_id": str(project_id),
        "chapter_number": item.get("chapter_number", index + 1),
        "name": item.get("title") or item.get("name") or f"Chapter {index + 1}",
        "description": item.get("summary") or item.get("description") or None,
        "status": item.get("status", DEFAULT_STATUS),
        "thumbnail_url": item.get("thumbnail_url"),
        "video_file_id": item.get("video_file_id"),
        "current_stage": item.get("current_stage"),
        "created_at": (
            story_updated_at.isoformat()
            if story_updated_at
            else datetime.utcnow().isoformat()
        ),
        "updated_at": (
            story_updated_at.isoformat()
            if story_updated_at
            else datetime.utcnow().isoformat()
        ),
    }


@router.get("", response_model=List[dict])
def list_chapters(project_id: UUID, db: Session = Depends(get_db)):
    """List chapters from the project's story chapter_outline"""
    story = story_crud.get_by_project(db, project_id)
    if not story or not story.chapter_outline:
        return []
    return [
        _enrich_chapter(item, idx, project_id, story.updated_at)
        for idx, item in enumerate(story.chapter_outline)
    ]


@router.get("/{chapter_id}", response_model=dict)
def get_chapter(project_id: UUID, chapter_id: str, db: Session = Depends(get_db)):
    """Get a specific chapter by index from story chapter_outline"""
    story = story_crud.get_by_project(db, project_id)
    if not story or not story.chapter_outline:
        raise HTTPException(status_code=404, detail="Chapter not found")
    try:
        idx = int(chapter_id)
        if 0 <= idx < len(story.chapter_outline):
            return _enrich_chapter(
                story.chapter_outline[idx], idx, project_id, story.updated_at
            )
    except ValueError:
        pass
    raise HTTPException(status_code=404, detail="Chapter not found")
