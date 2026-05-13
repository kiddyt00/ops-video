"""
Character Context Builder — enriches image prompts with character card info.

Maps storyboard panel characters to CharacterCard data (name, description, traits)
and injects structured character descriptions into image generation prompts
for visual consistency across scenes.
"""
import logging
from uuid import UUID
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ..db.character_card_crud import character_card_crud
from ..models.character_card import CharacterCard
from .storyboard_parser import parse_storyboard
from ..config import settings

logger = logging.getLogger(__name__)


class CharacterContextBuilder:
    """Builds character context for image prompt enrichment."""

    def __init__(self, db: Session):
        self.db = db

    def get_character_map(self, project_id: UUID) -> Dict[str, CharacterCard]:
        """Build a name -> CharacterCard lookup for all active cards in a project.

        Character names are matched case-insensitively for flexible panel matching.
        """
        cards = character_card_crud.get_by_project(self.db, project_id)
        char_map: Dict[str, CharacterCard] = {}
        for card in cards:
            if not card.is_active:
                continue
            char_map[card.name] = card
            char_map[card.name.lower()] = card
        return char_map

    def extract_character_names_from_panel(self, panel: Dict[str, Any]) -> List[str]:
        """Extract character names from a storyboard panel."""
        chars = panel.get("characters")
        if isinstance(chars, str):
            return [c.strip() for c in chars.split(",") if c.strip()]
        elif isinstance(chars, list):
            return [str(c).strip() for c in chars if c]
        return []

    def build_character_context(
        self,
        character_names: List[str],
        char_map: Dict[str, CharacterCard],
    ) -> str:
        """Build a natural-language character description context string.

        Example:
        "角色设定: 小明(17岁男生,黑色短发,校服,性格勇敢开朗); 小红(16岁女生,长辫子,红色发带)。"
        """
        parts = []
        for name in character_names:
            card = char_map.get(name) or char_map.get(name.lower())
            if not card:
                continue

            desc_parts = [card.name]
            if card.traits:
                if isinstance(card.traits, dict):
                    t = "、".join(
                        str(v) for v in card.traits.values()
                        if isinstance(v, (str, int, float))
                    )
                    if t:
                        desc_parts.append(t)
                elif isinstance(card.traits, str):
                    desc_parts.append(card.traits)
            if card.description:
                d = card.description[:80] + "..." if len(card.description) > 80 else card.description
                desc_parts.append(d)

            parts.append(": ".join(desc_parts))

        if not parts:
            return ""
        return "角色设定: " + "; ".join(parts) + "。"

    def enrich_storyboard_prompt(
        self,
        prompt: str,
        storyboard_file_path: Optional[str] = None,
        project_id: Optional[UUID] = None,
        storyboard_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Enrich an image generation prompt with character context."""
        if not project_id:
            return prompt

        if storyboard_data is None and storyboard_file_path:
            try:
                sp = settings.storage_path / storyboard_file_path
                if sp.exists():
                    storyboard_data = parse_storyboard(sp.read_text())
            except Exception:
                logger.warning("Failed to parse storyboard for character context")
                return prompt

        if not storyboard_data:
            return prompt

        char_map = self.get_character_map(project_id)
        if not char_map:
            return prompt

        panels = storyboard_data.get("panels", [])
        all_names: set = set()
        for panel in panels:
            all_names.update(self.extract_character_names_from_panel(panel))

        if not all_names:
            return prompt

        context = self.build_character_context(list(all_names), char_map)
        if not context:
            return prompt

        enriched = f"{context}\n场景: {prompt}"
        logger.info("Character context injected | chars=%s", list(all_names))
        return enriched

    def get_character_context_for_project(self, project_id: UUID) -> Dict[str, Any]:
        """Get all character context for a project (debug/API use)."""
        char_map = self.get_character_map(project_id)
        cards = character_card_crud.get_by_project(self.db, project_id)
        characters = []
        for card in cards:
            if not card.is_active:
                continue
            characters.append({
                "id": str(card.id),
                "name": card.name,
                "description": card.description,
                "traits": card.traits,
                "reference_images": {
                    "front_view": card.front_view_url,
                    "side_view": card.side_view_url,
                    "back_view": card.back_view_url,
                    "extra": card.reference_images,
                },
            })
        return {
            "project_id": str(project_id),
            "character_count": len(characters),
            "characters": characters,
            "context_template": (
                self.build_character_context([c["name"] for c in characters], char_map)
                if characters else "无角色设定"
            ),
        }
