"""
Provider routing API — expose available providers and active selection.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...services.provider_router import ProviderRouter

router = APIRouter()


@router.get("/providers", response_model=List[Dict[str, Any]])
def list_providers(
    category: str = Query("text2img", description="Provider category (text2img, llm, tts, bgm, video)"),
    db: Session = Depends(get_db),
):
    """List all available (enabled) providers for a given category.

    Used by the frontend provider selector to populate choices.
    """
    router = ProviderRouter(db)
    return router.list_available(category)


@router.get("/providers/active", response_model=Optional[Dict[str, Any]])
def get_active_provider(
    category: str = Query("text2img", description="Provider category"),
    db: Session = Depends(get_db),
):
    """Get the currently active (global) provider for a category."""
    from ...db.ai_model_crud import ai_model_crud

    active = ai_model_crud.get_active(db, category)
    if not active:
        return None
    return {
        "id": str(active.id),
        "name": active.name,
        "provider": active.provider,
        "model_name": active.model_name,
        "category": active.category,
    }
