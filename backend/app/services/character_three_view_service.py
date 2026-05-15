"""
Character Three-View Service - sync character cards and generate three-view images.

Produces front/side/back view images for main characters using LLM for
angle-specific appearance descriptions and image providers for generation.
"""
import json
import logging
from uuid import UUID
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ..models.story import Story
from ..models.character_card import CharacterCard
from ..db.character_card_crud import character_card_crud
from ..schemas.character_card import CharacterCardCreate, CharacterCardUpdate

logger = logging.getLogger(__name__)

# Role keywords that qualify for three-view generation
_IMPORTANT_ROLES = {"主角", "反派", "导师", "伙伴", "朋友", "恋人", "protagonist", "antagonist", "mentor", "companion"}
_SUPPORTING_KEYWORDS = {"配角", "supporting"}
_MAX_SUPPORTING = 10


class CharacterThreeViewService:
    """Service for syncing story characters into CharacterCards and generating three-view images."""

    def __init__(self, db: Session):
        self.db = db

    async def sync_cards_from_story(self, project_id: UUID) -> Dict[str, Any]:
        """Sync main characters from Story.characters into CharacterCards.

        Filters by role: main roles always pass, supporting capped at 10, extras skipped.
        Existing cards are skipped by name.
        """
        story = (
            self.db.query(Story)
            .filter(Story.project_id == project_id)
            .order_by(Story.created_at.desc())
            .first()
        )
        if not story or not story.characters:
            return {"created": 0, "skipped": 0, "cards": []}

        existing_cards = character_card_crud.get_by_project(self.db, project_id)
        existing_names = {c.name for c in existing_cards}

        created = []
        skipped = 0
        supporting_count = 0

        for char in story.characters:
            name = char.get("name", "").strip()
            role = char.get("role", "").strip()
            description = char.get("description", "")
            arc = char.get("arc", "")

            if not name:
                continue

            # Role filtering
            is_important = any(r in role for r in _IMPORTANT_ROLES)
            is_supporting = any(r in role for r in _SUPPORTING_KEYWORDS)

            if not is_important and not is_supporting:
                continue

            # Cap supporting characters
            if is_supporting and not is_important:
                supporting_count += 1
                if supporting_count > _MAX_SUPPORTING:
                    continue

            if name in existing_names:
                skipped += 1
                continue

            card = character_card_crud.create(
                self.db,
                project_id=project_id,
                obj_in=CharacterCardCreate(
                    name=name,
                    description=description,
                    traits={"role": role, "arc": arc} if arc else {"role": role},
                ),
            )
            created.append(card)
            existing_names.add(name)

        return {
            "created": len(created),
            "skipped": skipped,
            "cards": created,
        }

    async def generate_three_view(
        self,
        project_id: UUID,
        card_id: UUID,
        style_tags: Optional[List[str]] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """Generate front/side/back three-view images for a character card.

        1. LLM generates angle-specific appearance descriptions (JSON)
           using full story context: synopsis(蓝图), worldbuilding, style, themes
        2. Image provider generates 3 images (front/side/back)
        3. Uploads to OSS via ArtifactUploader
        4. Updates CharacterCard with OSS URLs
        """
        from ..providers.llm_provider import llm_provider
        from ..services.provider_router import ProviderRouter
        from ..services.artifact_uploader import upload_artifact

        card = self.db.query(CharacterCard).filter(
            CharacterCard.id == card_id,
            CharacterCard.project_id == project_id,
        ).first()
        if not card:
            raise ValueError(f"CharacterCard {card_id} not found")

        # Get full story context
        story = (
            self.db.query(Story)
            .filter(Story.project_id == project_id)
            .order_by(Story.created_at.desc())
            .first()
        )
        worldbuilding = (story.worldbuilding or {}) if story else {}
        synopsis = story.synopsis if story else ""
        themes = story.themes if story else []
        style = style_tags or (story.style_tags if story else []) or ["写实"]
        style_str = ", ".join(style) if isinstance(style, list) else str(style)

        # Step 1: LLM generates angle descriptions with full story context
        prompt = self._build_angle_prompt(
            card, worldbuilding, style_str,
            synopsis=synopsis, themes=themes,
        )
        llm_result = await llm_provider.generate(parameters={
            "prompt": prompt,
            "system_prompt": "你是一位专业角色设计师。返回严格JSON。",
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        })

        raw_text = ""
        if llm_result.file_paths:
            raw_text = llm_result.file_paths[0].read_text(encoding="utf-8")

        angle_descriptions = self._parse_angle_json(raw_text)

        # Step 2: Generate one image per angle
        router = ProviderRouter(self.db)
        provider = router.resolve("text2img", project_id=project_id)
        urls: Dict[str, str] = {}

        for angle_key, angle_label in [("front", "正面"), ("side", "侧面"), ("back", "背面")]:
            desc = angle_descriptions.get(angle_key, card.description or "")
            image_prompt = f"{desc}, {style_str}, {angle_label}全身照, 角色设计图, 白色背景, 高清"

            try:
                img_result = await provider.generate(parameters={
                    "prompt": image_prompt,
                    "negative_prompt": "",
                    "size": "1024*1024",
                    "n": 1,
                })
                if img_result.file_paths and len(img_result.file_paths) > 0:
                    local_path = str(img_result.file_paths[0])
                    # Upload to OSS
                    oss_url = await upload_artifact(
                        project_id=project_id,
                        task_id=card_id,
                        stage="character_three_views",
                        file_path=local_path,
                    )
                    urls[f"{angle_key}_view_url"] = oss_url or local_path
            except Exception as e:
                logger.warning("Image generation failed for %s/%s: %s", card.name, angle_key, e)

        if not urls:
            raise RuntimeError(f"All three image generations failed for card {card.name}")

        # Step 3: Update character card with OSS URLs
        character_card_crud.update(
            self.db, card_id,
            CharacterCardUpdate(**urls),
        )

        logger.info("Three-view generated for %s | oss_urls=%s", card.name, urls)

        return {
            "card_id": str(card_id),
            "card_name": card.name,
            **urls,
        }

    async def generate_all_three_views(
        self,
        project_id: UUID,
        style_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate three-views for all cards that don't have them yet."""
        cards = self.db.query(CharacterCard).filter(
            CharacterCard.project_id == project_id,
            CharacterCard.is_active == True,
        ).all()

        results: Dict[str, Any] = {
            "total": len(cards),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        for card in cards:
            if card.front_view_url and card.side_view_url and card.back_view_url:
                results["skipped"] += 1
                continue
            try:
                r = await self.generate_three_view(project_id, card.id, style_tags)
                results["success"] += 1
                results["details"].append({
                    "card_id": str(card.id),
                    "name": card.name,
                    "status": "ok",
                })
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "card_id": str(card.id),
                    "name": card.name,
                    "status": "failed",
                    "error": str(e),
                })
                logger.warning("Three-view generation failed for %s: %s", card.name, e)

        return results

    def _build_angle_prompt(
        self,
        card: CharacterCard,
        worldbuilding: Dict[str, Any],
        style_str: str,
        synopsis: str = "",
        themes: Optional[List[str]] = None,
    ) -> str:
        """Build LLM prompt for generating angle-specific appearance descriptions.

        Uses full story context: worldbuilding(世界观), synopsis(蓝图/梗概),
        style(风格), themes(主题) to guide character design.
        """
        wb = worldbuilding if isinstance(worldbuilding, dict) else {}
        theme_str = "、".join(themes) if themes else ""
        synopsis_preview = synopsis[:300] + "..." if len(synopsis) > 300 else synopsis

        return f"""你是一位专业的角色设计师。请根据以下完整故事设定，为指定角色生成正/侧/背三个角度的外观描述。

=== 故事蓝图 ===
{synopsis_preview or "（无）"}

=== 世界观 ===
背景设定: {wb.get("setting", "未知")}
时代: {wb.get("time_period", "未知")}
世界规则: {wb.get("rules", "无")}

=== 风格 ===
{style_str}

{'=== 故事主题 ===' + theme_str if theme_str else ''}

=== 目标角色 ===
角色名: {card.name}
角色定位: {card.traits.get("role", "角色") if card.traits else "角色"}
角色设定: {card.description or "无"}
外貌特征: {card.traits or {}}

请根据故事的整体设定，设计符合世界观和风格的角色外观。
每个角度描述包含：
- 发型、发色
- 脸型、五官、表情特征
- 服装（正面/侧面/背面细节不同）
- 配饰、道具
- 体型特征

输出 JSON:
{{
  "front": "正面详细描述（包含全身服装、五官、发型）",
  "side": "侧面详细描述（包含侧脸轮廓、侧面服装细节）",
  "back": "背面详细描述（包含背面服装、发型背面）"
}}"""

    @staticmethod
    def _parse_angle_json(raw_text: str) -> Dict[str, str]:
        """Parse the LLM's JSON output, handling markdown fences and stray text."""
        text = raw_text.strip()
        if not text:
            return {"front": "", "side": "", "back": ""}

        # Strip markdown code fences
        import re
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    return {"front": "", "side": "", "back": ""}
            else:
                return {"front": "", "side": "", "back": ""}

        return {
            "front": data.get("front", ""),
            "side": data.get("side", ""),
            "back": data.get("back", ""),
        }
