"""
Story Generator Service
Expands inspirations into full story outlines and chapter breakdowns.
"""
import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from ...providers.llm_provider import llm_provider, LLMProvider
from ...config import settings, STORAGE_DIRS
from ...core.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# JSON Schema definitions
# ---------------------------------------------------------------------------

STORY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["logline", "synopsis", "worldbuilding", "characters", "themes", "plot_points"],
    "properties": {
        "logline": {
            "type": "string",
            "description": "A one-sentence summary of the story",
        },
        "synopsis": {
            "type": "string",
            "description": "A detailed paragraph summarising the full story",
        },
        "worldbuilding": {
            "type": "object",
            "required": ["setting", "time_period", "rules"],
            "properties": {
                "setting": {"type": "string"},
                "time_period": {"type": "string"},
                "rules": {"type": "string"},
            },
        },
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "role", "description"],
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "description": {"type": "string"},
                    "arc": {"type": "string"},
                },
            },
        },
        "themes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "plot_points": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["act", "description"],
                "properties": {
                    "act": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
    },
}

CHAPTER_OUTLINE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["chapters"],
    "properties": {
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "chapter_number",
                    "title",
                    "summary",
                    "key_scenes",
                    "characters",
                    "duration",
                ],
                "properties": {
                    "chapter_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_scenes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "characters": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "duration": {
                        "type": "number",
                        "description": "Estimated duration in minutes",
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_story_prompt(inspiration: str, **kwargs) -> str:
    """Build the prompt for expanding an inspiration into a full story outline."""
    genre = kwargs.get("genre", "")
    tone = kwargs.get("tone", "")
    target_length = kwargs.get("target_length", "")
    golden_finger = kwargs.get("golden_finger", "")
    protagonist = kwargs.get("protagonist", "")
    relationship = kwargs.get("relationship", "")
    worldbuilding_hints = kwargs.get("worldbuilding_hints", "")
    extra = kwargs.get("extra_context", "")

    prompt = f"""你是一位专业的中文故事开发者。请将以下灵感扩展为完整的故事大纲。所有输出必须使用中文。

灵感：{inspiration}
"""
    if genre:
        prompt += f"类型：{genre}\n"
    if tone:
        prompt += f"基调：{tone}\n"
    if target_length:
        prompt += f"目标篇幅：{target_length}\n"
    if golden_finger:
        prompt += f"主角金手指：{golden_finger}\n"
    if protagonist:
        prompt += f"主角设定：{protagonist}\n"
    if relationship:
        prompt += f"人物关系：{relationship}\n"
    if worldbuilding_hints:
        prompt += f"世界观提示：{worldbuilding_hints}\n"
    if extra:
        prompt += f"补充信息：{extra}\n"

    prompt += """
返回以下结构的 JSON 对象（所有字段内容必须使用中文）：
{
  "logline": "一句话概括整个故事",
  "synopsis": "详细的故事梗概（300-500字）",
  "title_suggestions": ["备选书名1", "备选书名2"],
  "target_audience": "目标读者群",
  "style_tags": ["风格标签1", "风格标签2"],
  "word_count_estimate": 50000,
  "worldbuilding": {
    "setting": "故事发生的世界背景",
    "time_period": "故事发生的时代",
    "rules": "这个世界的基本规则和力量体系"
  },
  "world_map_hints": "世界地理概述",
  "power_system": {
    "name": "力量体系名称",
    "stages": ["境界1", "境界2", "境界3"],
    "description": "力量体系简述"
  },
  "golden_finger_detail": "主角金手指的详细设定和限制",
  "characters": [
    {
      "name": "角色姓名",
      "role": "角色定位（如：主角/反派/导师/伙伴）",
      "description": "角色外貌和性格描述",
      "arc": "角色成长弧线简述",
      "abilities": "角色能力或特长"
    }
  ],
  "themes": ["故事主题1", "故事主题2"],
  "plot_points": [
    {"act": "开篇", "description": "开篇设定和冲突引入"},
    {"act": "发展", "description": "主要冲突展开和升级"},
    {"act": "转折", "description": "重大转折或意外事件"},
    {"act": "高潮", "description": "最终对决或关键抉择"},
    {"act": "结局", "description": "故事收束和新平衡"}
  ],
  "prologue_preview": "故事开篇楔子（100-200字吸引读者的段落）"
}"""

    prompt += "\n请只返回有效的 JSON，不要包含 markdown 或解释。"
    return prompt


def _build_chapter_prompt(story_data: Dict[str, Any], chapter_count: int) -> str:
    """Build the prompt for dividing a story into chapter outlines."""
    story_json = json.dumps(story_data, indent=2, ensure_ascii=False)

    prompt = f"""你是一位专业的叙事结构师。请将以下故事大纲拆分为恰好 {chapter_count} 个章节。所有输出必须使用中文。

故事大纲：
{story_json}

返回以下结构的 JSON 对象（所有字段内容必须使用中文）：
{{
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "章节标题",
      "summary": "本章简短概要",
      "key_scenes": ["场景1描述", "场景2描述"],
      "characters": ["本章出现的角色姓名"],
      "duration": 5.0
    }}
  ]
}}

要求：
1. 每个章节必须有清晰的叙事目的
2. 将情节点均匀分布到各章节
3. key_scenes 应该是描述性的场景概要
4. characters 列出角色姓名（不需要完整描述）
5. duration 是预估的阅读/观看时间（分钟）
6. 总章节数必须恰好为 {chapter_count}
7. 所有章节标题和内容必须使用中文

请只返回有效的 JSON，不要包含 markdown 或解释。"""
    return prompt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_result(raw_text: str) -> Dict[str, Any]:
    """Parse JSON from LLM output, handling markdown code blocks and stray text."""
    text = raw_text.strip()

    # Strip markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Try parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to find the outermost JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse JSON from LLM output:\n{raw_text[:500]}")


def _validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Basic schema validation. Returns a list of error messages (empty = valid)."""
    errors: List[str] = []

    if schema.get("type") == "object":
        if not isinstance(data, dict):
            errors.append(f"Expected object, got {type(data).__name__}")
            return errors

        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append(f"Missing required field: {key}")

        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")
                if expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"Field '{key}' should be an object")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{key}' should be an array")
                elif expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{key}' should be a string")
                elif expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Field '{key}' should be an integer")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{key}' should be a number")

                # Recurse into nested objects/arrays
                if expected_type == "object" and isinstance(value, dict):
                    nested = prop_schema.get("properties", {})
                    nested_required = prop_schema.get("required", [])
                    for rk in nested_required:
                        if rk not in value:
                            errors.append(f"Missing required field '{key}.{rk}'")
                    for nk, nv in value.items():
                        if nk in nested:
                            ns = nested[nk].get("type")
                            if ns == "array" and not isinstance(nv, list):
                                errors.append(f"Field '{key}.{nk}' should be an array")
                            elif ns == "string" and not isinstance(nv, str):
                                errors.append(f"Field '{key}.{nk}' should be a string")
                            elif ns == "object" and not isinstance(nv, dict):
                                errors.append(f"Field '{key}.{nk}' should be an object")

                if expected_type == "array" and isinstance(value, list):
                    items_schema = prop_schema.get("items", {})
                    item_type = items_schema.get("type")
                    for idx, item in enumerate(value):
                        if item_type == "object" and not isinstance(item, dict):
                            errors.append(f"Field '{key}[{idx}]' should be an object")
                        elif item_type == "string" and not isinstance(item, str):
                            errors.append(f"Field '{key}[{idx}]' should be a string")
                        elif item_type == "integer" and not isinstance(item, int):
                            errors.append(f"Field '{key}[{idx}]' should be an integer")
                        elif item_type == "number" and not isinstance(item, (int, float)):
                            errors.append(f"Field '{key}[{idx}]' should be a number")
                        # Validate required fields in array items
                        if item_type == "object" and isinstance(item, dict):
                            item_required = items_schema.get("required", [])
                            for irk in item_required:
                                if irk not in item:
                                    errors.append(f"Missing required field '{key}[{idx}].{irk}'")

    return errors


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class StoryGeneratorService:
    """Service for generating story outlines and chapter breakdowns using LLM."""

    def __init__(self, llm: Optional[LLMProvider] = None, db: Optional['Session'] = None):
        self.llm = llm or llm_provider
        self.db = db

    # --- Story generation ------------------------------------------------

    async def generate_story(
        self,
        inspiration: str,
        project_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Expand an inspiration into a complete story outline.

        Returns a dict containing:
            logline, synopsis, worldbuilding, characters, themes, plot_points

        Also saves the result to the storage directory for the project.
        """
        system_prompt = (
            "你是一位专业的故事开发者和叙事设计师。"
            "你的任务是将简短的灵感扩展为丰富、结构化的故事大纲。"
            "请始终返回符合要求格式的有效 JSON。"
        )

        # Use template-based prompt from PromptService when db is available
        if self.db:
            try:
                from ..services.prompt_service import get_rendered_prompt
                context = {
                    "inspiration": inspiration,
                    "genre": kwargs.get("genre", ""),
                    "tone": kwargs.get("tone", ""),
                    "target_length": kwargs.get("target_length", ""),
                    "protagonist": kwargs.get("protagonist", ""),
                    "golden_finger": kwargs.get("golden_finger", ""),
                    "relationship": kwargs.get("relationship", ""),
                    "worldbuilding_hints": kwargs.get("worldbuilding_hints", ""),
                }
                prompt = get_rendered_prompt(self.db, "story-generation", context)
                logger.info("Using prompt template 'story-generation' | project=%s", project_id)
            except Exception as e:
                logger.warning("Failed to use prompt template, falling back: %s", e)
                prompt = _build_story_prompt(inspiration, **kwargs)
        else:
            prompt = _build_story_prompt(inspiration, **kwargs)

        logger.info(
            "Generating story outline | project=%s | inspiration=%s",
            project_id,
            inspiration[:80],
        )

        result = await self.llm.generate(
            parameters={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": kwargs.get("temperature", 0.8),
                "max_tokens": kwargs.get("max_tokens", 4000),
                "response_format": {"type": "json_object"},
            },
        )

        # Read the generated content
        if not result.file_paths:
            raise ValueError("LLM generation produced no output file")

        raw_text = result.file_paths[0].read_text(encoding="utf-8")
        story_data = _parse_json_result(raw_text)

        # Schema validation
        validation_errors = _validate_schema(story_data, STORY_SCHEMA)
        if validation_errors:
            logger.warning(
                "Story schema validation warnings | project=%s | errors=%s",
                project_id,
                validation_errors,
            )

        # Save the structured JSON alongside the raw text
        output_dir = STORAGE_DIRS["scripts"]
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / f"story_{project_id}.json"
        json_path.write_text(
            json.dumps(story_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Story outline saved | path=%s", json_path)

        return story_data

    # --- Chapter outline generation --------------------------------------

    async def generate_chapter_outline(
        self,
        story_data: Dict[str, Any],
        chapter_count: Optional[int] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Divide a story outline into chapter-level outlines.

        Returns a dict with a 'chapters' list where each chapter has:
            chapter_number, title, summary, key_scenes, characters, duration
        """
        if chapter_count is None:
            # Default based on story length / plot points
            plot_points = story_data.get("plot_points", [])
            chapter_count = max(len(plot_points) * 2, 6)

        system_prompt = (
            "你是一位专业的叙事结构师。"
            "请将故事大纲拆分为节奏良好的章节大纲。"
            "请始终返回符合要求格式的有效 JSON。"
            "所有内容请使用中文输出。"
        )

        # Use template-based prompt from PromptService when db is available
        if self.db:
            try:
                from ..services.prompt_service import get_rendered_prompt
                from ..services.knowledge_service import build_continuity_context
                from ..db.relation_crud import relation_crud
                story_json = json.dumps(story_data, indent=2, ensure_ascii=False)
                continuity = build_continuity_context(self.db, project_id) if project_id else "（无前情提要）"
                # Build relations context
                relations_text = "（无关系信息）"
                if project_id:
                    relations = relation_crud.list_by_project(self.db, project_id)
                    if relations:
                        lines = ["角色关系图："]
                        for r in relations[:20]:
                            lines.append(f"- {r.character_name} {r.relation_type} {r.target_name}")
                        relations_text = "\n".join(lines)
                context = {
                    "chapter_count": str(chapter_count),
                    "story_data_json": story_json,
                    "continuity_context": continuity,
                    "relations_context": relations_text,
                }
                prompt = get_rendered_prompt(self.db, "chapter-outline", context)
                logger.info("Using prompt template 'chapter-outline' | chapter_count=%d", chapter_count)
            except Exception as e:
                logger.warning("Failed to use prompt template, falling back: %s", e)
                prompt = _build_chapter_prompt(story_data, chapter_count)
        else:
            prompt = _build_chapter_prompt(story_data, chapter_count)

        logger.info(
            "Generating chapter outline | chapter_count=%d",
            chapter_count,
        )

        result = await self.llm.generate(
            parameters={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": 0.7,
                "max_tokens": 4000,
                "response_format": {"type": "json_object"},
            },
        )

        if not result.file_paths:
            raise ValueError("LLM generation produced no output file")

        raw_text = result.file_paths[0].read_text(encoding="utf-8")
        outline_data = _parse_json_result(raw_text)

        # Schema validation
        validation_errors = _validate_schema(outline_data, CHAPTER_OUTLINE_SCHEMA)
        if validation_errors:
            logger.warning(
                "Chapter outline schema validation warnings | errors=%s",
                validation_errors,
            )

        return outline_data

    # --- Chapter body generation -------------------------------------------

    async def generate_chapter_body(
        self,
        project_id: str,
        chapter_number: int,
        title: str,
        summary: str,
        story_data: Dict[str, Any],
        previous_bodies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Expand a single chapter outline into full narrative prose.

        Args:
            project_id: Project UUID string.
            chapter_number: Chapter number (1-based).
            title: Chapter title.
            summary: Chapter summary from outline.
            story_data: Full story context (synopsis, worldbuilding, characters, etc.).
            previous_bodies: Last N previous chapter bodies for continuity.

        Returns:
            Dict with chapter_number, title, body_text, word_count.
        """
        import json as _json

        past_context = ""
        if previous_bodies:
            past_summaries = []
            for i, body in enumerate(previous_bodies):
                snippet = body[:300] + "..." if len(body) > 300 else body
                past_summaries.append(f"第{chapter_number - len(previous_bodies) + i}章摘要：{snippet}")
            past_context = "前情提要（请保持情节连贯性）：\n" + "\n".join(past_summaries)

        system_prompt = (
            "你是一位专业的网络小说作家，擅长将章节大纲展开为生动的叙事正文。"
            "请根据章节大纲和故事设定，写出该章的完整叙事内容。"
            "所有内容请使用中文输出，文笔流畅、有画面感。"
        )

        story_context = _json.dumps({
            "synopsis": story_data.get("synopsis", ""),
            "worldbuilding": story_data.get("worldbuilding", {}),
            "themes": story_data.get("themes", []),
            "plot_points": story_data.get("plot_points", []),
            "style_tags": story_data.get("style_tags", []),
        }, indent=2, ensure_ascii=False)

        # Try template-based prompt
        if self.db:
            try:
                from ..services.prompt_service import get_rendered_prompt
                from ..services.knowledge_service import build_continuity_context
                continuity = build_continuity_context(self.db, project_id)
                context = {
                    "chapter_number": str(chapter_number),
                    "title": title,
                    "summary": summary,
                    "story_context": story_context,
                    "continuity_context": continuity,
                    "past_context": past_context,
                }
                prompt = get_rendered_prompt(self.db, "chapter-body-generation", context)
                logger.info("Using prompt template 'chapter-body-generation' | ch=%d", chapter_number)
            except Exception as e:
                logger.warning("Failed to use prompt template for chapter body, falling back: %s", e)
                prompt = self._build_chapter_body_prompt(
                    chapter_number, title, summary, story_context, past_context
                )
        else:
            prompt = self._build_chapter_body_prompt(
                chapter_number, title, summary, story_context, past_context
            )

        logger.info("Generating chapter body | ch=%d | title=%s", chapter_number, title)

        result = await self.llm.generate(
            parameters={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": 0.85,
                "max_tokens": 6000,
                "response_format": {"type": "json_object"},
            },
        )

        if not result.file_paths:
            raise ValueError("LLM generation produced no output file")

        raw_text = result.file_paths[0].read_text(encoding="utf-8")
        body_data = _parse_json_result(raw_text)

        # Validate required fields
        if "body_text" not in body_data:
            raise ValueError("Chapter body generation missing 'body_text' field")

        return {
            "chapter_number": chapter_number,
            "title": title,
            "body_text": body_data.get("body_text", ""),
            "word_count": body_data.get("word_count", len(body_data.get("body_text", ""))),
        }

    @staticmethod
    def _build_chapter_body_prompt(
        chapter_number: int,
        title: str,
        summary: str,
        story_context: str,
        past_context: str,
    ) -> str:
        """Build fallback prompt for chapter body generation."""
        prompt = f"""你是一位专业的网络小说作家。请将以下章节大纲展开为完整的叙事正文。

【故事设定】
{story_context}

【本章信息】
章节号：第{chapter_number}章
章节标题：{title}
章节概要：{summary}

"""
        if past_context:
            prompt += f"""{past_context}

"""
        prompt += """请写出本章的完整叙事正文。要求：
1. 文笔生动，有画面感和节奏感
2. 包含场景描写、人物对话、心理活动
3. 保持与前文的情节连贯性
4. 篇幅在 1500-3000 字之间
5. 结尾要有悬念或转折引导下一章

返回以下结构的 JSON 对象：
{
  "chapter_number": """ + str(chapter_number) + """,
  "title": \"""" + title + """\",
  "body_text": "本章完整正文内容...",
  "word_count": 2500
}

请只返回有效的 JSON，不要包含 markdown 或解释。"""
        return prompt
