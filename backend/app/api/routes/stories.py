"""
Story API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from typing import Optional

from ...db.session import get_db
from ...db.story_crud import story_crud
from ...schemas.story import StoryCreate, StoryUpdate, StoryResponse

router = APIRouter()


@router.get("", response_model=Optional[StoryResponse])
def get_story(project_id: UUID, db: Session = Depends(get_db)):
    """Get the story for a project"""
    story = story_crud.get_by_project(db, project_id)
    if not story:
        return None
    return story


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(
    project_id: UUID,
    story_in: StoryCreate,
    db: Session = Depends(get_db),
):
    """Create a new story for a project"""
    # Check if story already exists for this project
    existing = story_crud.get_by_project(db, project_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A story already exists for this project. Use PUT to update.",
        )
    return story_crud.create(db, project_id=project_id, obj_in=story_in)


@router.put("", response_model=StoryResponse)
def update_story(
    project_id: UUID,
    story_in: StoryUpdate,
    db: Session = Depends(get_db),
):
    """Update the story for a project"""
    story = story_crud.get_by_project(db, project_id)
    if not story:
        return None
    story = story_crud.update(db, story.id, story_in)
    return story


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(project_id: UUID, db: Session = Depends(get_db)):
    """Delete the story for a project"""
    story = story_crud.get_by_project(db, project_id)
    if not story:
        return None
    success = story_crud.delete(db, story.id)
    if not success:
        raise HTTPException(status_code=404, detail="Story not found")
