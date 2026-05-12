"""
Story Generator Service
Expands inspirations into full story outlines and chapter breakdowns.
"""
import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

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

    prompt = f"""你是一位专业的故事开发者。请将以下灵感扩展为完整的故事大纲。

灵感：{inspiration}
"""
    if genre:
        prompt += f"Genre: {genre}\n"
    if tone:
        prompt += f"Tone: {tone}\n"
    if target_length:
        prompt += f"Target length: {target_length}\n"
    if golden_finger:
        prompt += f"Protagonist's special ability / golden finger: {golden_finger}\n"
    if protagonist:
        prompt += f"Protagonist profile: {protagonist}\n"
    if relationship:
        prompt += f"Character relationships: {relationship}\n"
    if worldbuilding_hints:
        prompt += f"Worldbuilding hints: {worldbuilding_hints}\n"
    if extra:
        prompt += f"Additional context: {extra}\n"

    prompt += """
Return a JSON object with the following structure:
{
  "logline": "A one-sentence summary of the story",
  "synopsis": "A detailed paragraph summarising the full story arc",
  "worldbuilding": {
    "setting": "Where the story takes place",
    "time_period": "When the story takes place",
    "rules": "Key world rules, magic systems, technology, etc."
  },
  "characters": [
    {
      "name": "Character name",
      "role": "Protagonist / Antagonist / Supporting / etc.",
      "description": "Brief character description",
      "arc": "Character arc summary"
    }
  ],
  "themes": ["Theme 1", "Theme 2", ...],
  "plot_points": [
    {"act": "Act 1", "description": "Inciting incident / setup"},
    {"act": "Act 2", "description": "Rising action / confrontation"},
    {"act": "Act 3", "description": "Climax / resolution"}
  ]
}

Return ONLY valid JSON. No markdown, no explanation."""
    return prompt


def _build_chapter_prompt(story_data: Dict[str, Any], chapter_count: int) -> str:
    """Build the prompt for dividing a story into chapter outlines."""
    story_json = json.dumps(story_data, indent=2, ensure_ascii=False)

    prompt = f"""你是一位专业的叙事结构师。请将以下故事大纲拆分为恰好 {chapter_count} 个章节。

故事大纲：
{story_json}

Return a JSON object with the following structure:
{{
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "Chapter title",
      "summary": "Brief summary of this chapter",
      "key_scenes": ["Scene 1 description", "Scene 2 description", ...],
      "characters": ["Character names appearing in this chapter"],
      "duration": 5.0
    }}
  ]
}}

Requirements:
1. Each chapter must have a clear narrative purpose
2. Distribute plot points evenly across chapters
3. key_scenes should be descriptive scene summaries
4. characters should list character names (not full descriptions)
5. duration is the estimated reading/viewing time in minutes
6. Total chapters must be exactly {chapter_count}

Return ONLY valid JSON. No markdown, no explanation."""
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

    def __init__(self, llm: Optional[LLMProvider] = None):
        self.llm = llm or llm_provider

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
