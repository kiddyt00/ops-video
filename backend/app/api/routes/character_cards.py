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
