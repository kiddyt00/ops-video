"""
Character Cards API routes
"""
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.character_card_crud import character_card_crud
from ...schemas.character_card import CharacterCardCreate, CharacterCardUpdate, CharacterCardResponse
from ...services.character_context import CharacterContextBuilder
from ...services.character_three_view_service import CharacterThreeViewService
from pydantic import BaseModel
from typing import Optional, List


class SyncResult(BaseModel):
    created: int
    skipped: int
    cards: List[CharacterCardResponse]


class ThreeViewRequest(BaseModel):
    style_tags: Optional[List[str]] = None
    strict: bool = False


class ThreeViewResult(BaseModel):
    card_id: str
    card_name: Optional[str] = None
    front_view_url: Optional[str] = None
    side_view_url: Optional[str] = None
    back_view_url: Optional[str] = None


class BatchThreeViewResult(BaseModel):
    total: int
    success: int
    failed: int
    skipped: int
    details: List[dict]

router = APIRouter()


@router.get("", response_model=List[CharacterCardResponse])
def list_character_cards(project_id: UUID, db: Session = Depends(get_db)):
    """List all character cards for a project"""
    return character_card_crud.get_by_project(db, project_id)


@router.post("", response_model=CharacterCardResponse, status_code=status.HTTP_201_CREATED)
def create_character_card(
    project_id: UUID,
    card_in: CharacterCardCreate,
    db: Session = Depends(get_db),
):
    """Create a new character card for a project"""
    return character_card_crud.create(db, project_id=project_id, obj_in=card_in)


@router.get("/{card_id}", response_model=CharacterCardResponse)
def get_character_card(
    project_id: UUID,
    card_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a character card by ID"""
    card = character_card_crud.get(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Character card not found")
    if card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character card not found in this project")
    return card


@router.put("/{card_id}", response_model=CharacterCardResponse)
def update_character_card(
    project_id: UUID,
    card_id: UUID,
    card_in: CharacterCardUpdate,
    db: Session = Depends(get_db),
):
    """Update a character card"""
    card = character_card_crud.get(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Character card not found")
    if card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character card not found in this project")
    card = character_card_crud.update(db, card_id, card_in)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character_card(
    project_id: UUID,
    card_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a character card"""
    card = character_card_crud.get(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Character card not found")
    if card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character card not found in this project")
    success = character_card_crud.delete(db, card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character card not found")


@router.get("/context", response_model=dict)
def get_character_context(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """Get character context preview — shows how cards will be injected into prompts.

    Useful for debugging: preview the context template that gets prepended
    to image generation prompts.
    """
    ctx = CharacterContextBuilder(db)
    return ctx.get_character_context_for_project(project_id)


@router.post("/sync", response_model=SyncResult)
async def sync_character_cards(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """Sync main characters from Story.characters into CharacterCards.

    Filters by role: main roles always pass, supporting capped at 10.
    Existing cards are skipped by name.
    """
    svc = CharacterThreeViewService(db)
    return await svc.sync_cards_from_story(project_id)


@router.post("/{card_id}/three-view", response_model=ThreeViewResult)
async def generate_three_view(
    project_id: UUID,
    card_id: UUID,
    body: ThreeViewRequest = ThreeViewRequest(),
    db: Session = Depends(get_db),
):
    """Generate front/side/back three-view images for a character card."""
    svc = CharacterThreeViewService(db)
    try:
        result = await svc.generate_three_view(
            project_id=project_id,
            card_id=card_id,
            style_tags=body.style_tags,
            strict=body.strict,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/generate-all-three-views", response_model=BatchThreeViewResult)
async def generate_all_three_views(
    project_id: UUID,
    body: ThreeViewRequest = ThreeViewRequest(),
    db: Session = Depends(get_db),
):
    """Generate three-view images for all cards without them."""
    svc = CharacterThreeViewService(db)
    return await svc.generate_all_three_views(
        project_id=project_id,
        style_tags=body.style_tags,
    )
