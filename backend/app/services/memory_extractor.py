"""Automatic memory extraction from generated content.

After generating a script or storyboard, this service extracts
character state changes and relationships, saving them to the graph provider.
"""
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from ..providers.llm_provider import llm_provider
from ..services.graph import get_graph_provider
from ..core.logging_config import get_logger

logger = get_logger(__name__)

EXTRACT_PROMPT = """你是一个文本分析助手。请分析以下剧本内容，提取所有角色的状态变化。

剧本内容：
{content}

请返回 JSON 格式的分析结果：
{{
  "character_states": [
    {{
      "character_name": "角色名",
      "status": "alive/dead/injured/missing",
      "location": "当前所在位置",
      "faction": "当前所属势力",
      "summary": "本章中该角色的关键事件和状态变化简述"
    }}
  ],
  "relationships": [
    {{
      "source_name": "角色A",
      "relation_type": "mentor_of/rival_of/lover_of/friend_of/enemy_of/family_of",
      "target_name": "角色B"
    }}
  ]
}}

规则：
1. 只提取在文本中明确出现的信息
2. 没有变化的角色不提取
3. 不要虚构不存在的关系
4. 所有输出使用中文
"""


async def extract_from_script(project_id: str, content: str, chapter_number: int = 1) -> int:
    """Analyze script/storyboard content and extract character states.

    Returns number of state records created.
    """
    if not content or len(content) < 50:
        logger.info("Content too short for memory extraction, skipping")
        return 0

    prompt = EXTRACT_PROMPT.format(content=content[:8000])

    try:
        result = await llm_provider.generate({
            "prompt": prompt,
            "system_prompt": "你是一个文本分析助手。请严格按照格式返回 JSON。",
            "temperature": 0.3,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        })

        if not result.file_paths:
            logger.warning("Memory extraction LLM returned no output")
            return 0

        raw_text = result.file_paths[0].read_text(encoding="utf-8")
        # Strip markdown fences
        import re
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw_text, re.DOTALL)
        if match:
            raw_text = match.group(1).strip()

        data = json.loads(raw_text)
    except Exception as e:
        logger.warning("Failed to parse memory extraction result: %s", e)
        return 0

    graph = get_graph_provider()
    created = 0

    states: List[Dict[str, Any]] = data.get("character_states", [])
    for s in states:
        try:
            await graph.save_character_state(
                project_id=project_id,
                character_name=s.get("character_name", "未知"),
                chapter_number=chapter_number,
                status=s.get("status", "alive"),
                location=s.get("location"),
                faction=s.get("faction"),
                summary=s.get("summary"),
            )
            created += 1
        except Exception as e:
            logger.warning("Failed to save character state: %s", e)

    relationships: List[Dict[str, Any]] = data.get("relationships", [])
    for r in relationships:
        try:
            await graph.create_relation(
                project_id=project_id,
                source_type="character",
                source_name=r["source_name"],
                relation_type=r["relation_type"],
                target_type="character",
                target_name=r["target_name"],
            )
            created += 1
        except Exception as e:
            logger.warning("Failed to save relation: %s", e)

    if created > 0:
        logger.info("Memory extraction: %d items saved for project %s", created, project_id)

    return created
